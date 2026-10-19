import asyncio
import time
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.operation import OperationModel
from app.models.audit import AuditLogModel
from app.models.service import ServiceModel
from app.tools.registry import tool_registry
from app.agent.planner import ExecutionPlan, PlanStep

logger = logging.getLogger("vickyops.executor")

class PlanExecutor:
    def __init__(self):
        self._active_listeners: List[Callable[[Dict[str, Any]], Any]] = []

    def subscribe(self, callback: Callable[[Dict[str, Any]], Any]):
        self._active_listeners.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any]], Any]):
        if callback in self._active_listeners:
            self._active_listeners.remove(callback)

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        message = {"event": event_type, "data": data, "timestamp": time.time()}
        for listener in self._active_listeners:
            try:
                res = listener(message)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error(f"Broadcast listener failed: {e}")

    async def execute_plan(
        self,
        db: AsyncSession,
        operation: OperationModel,
        plan: ExecutionPlan,
        approved_by_user: bool = False
    ) -> OperationModel:
        """
        Executes an execution plan against the backend tool registry,
        streaming step progress, checking approval thresholds, and recording audit logs.
        """
        import datetime
        operation.status = "running"
        operation.started_at = datetime.datetime.utcnow()
        steps = plan.steps
        
        # Load or initialize steps execution state
        current_step_states = json.loads(operation.steps_json) if operation.steps_json else []
        if not current_step_states:
            for s in steps:
                current_step_states.append({
                    "step_index": s.step_index,
                    "name": s.name,
                    "tool_name": s.tool_name,
                    "status": "pending",
                    "description": s.description,
                    "log": "",
                    "duration_ms": 0.0
                })

        operation.steps_json = json.dumps(current_step_states)
        await db.commit()
        await self.broadcast("operation_update", {"operation_id": operation.id, "status": "running"})

        overall_success = True
        accumulated_output = []

        for idx, step in enumerate(steps):
            # Check if this step was already completed in a prior turn
            if current_step_states[idx]["status"] == "completed":
                continue

            # Check approval requirements
            tool = tool_registry.get_tool(step.tool_name)
            step_is_dangerous = step.is_dangerous or (tool.is_dangerous if tool else False)
            
            if step_is_dangerous and not approved_by_user and operation.approval_status != "approved":
                operation.status = "requires_approval"
                operation.approval_status = "awaiting"
                operation.approval_prompt = plan.approval_prompt or f"⚠️ Step '{step.name}' ({step.tool_name}) requires confirmation before modifying the server. Proceed?"
                operation.current_step_index = idx
                operation.current_step_name = step.name
                current_step_states[idx]["status"] = "awaiting_approval"
                operation.steps_json = json.dumps(current_step_states)
                await db.commit()
                
                await self.broadcast("operation_approval_required", {
                    "operation_id": operation.id,
                    "prompt": operation.approval_prompt,
                    "step_name": step.name,
                    "service_id": operation.service_id
                })
                return operation

            # Mark step as running
            current_step_states[idx]["status"] = "running"
            operation.current_step_index = idx
            operation.current_step_name = step.name
            operation.steps_json = json.dumps(current_step_states)
            await db.commit()
            
            await self.broadcast("step_progress", {
                "operation_id": operation.id,
                "step_index": idx,
                "step_name": step.name,
                "status": "running"
            })

            # Execute controlled backend tool
            start_step_time = time.time()
            
            # Step streaming callback for complex workflows like service.deploy
            def on_substep(step_name, status, msg):
                asyncio.create_task(self.broadcast("substep_log", {
                    "operation_id": operation.id,
                    "step_index": idx,
                    "substep": step_name,
                    "status": status,
                    "message": msg
                }))

            call_params = dict(step.parameters)
            if step.tool_name == "service.deploy":
                call_params["step_callback"] = on_substep

            tool_result = await tool_registry.execute(step.tool_name, **call_params)
            step_duration = (time.time() - start_step_time) * 1000

            # Record Audit Log
            audit_entry = AuditLogModel(
                operation_id=operation.id,
                user_request=plan.user_request,
                agent_plan=plan.title,
                tool_name=step.tool_name,
                service_id=operation.service_id,
                parameters_json=json.dumps(step.parameters),
                approval_status="manually_approved" if approved_by_user else "auto_approved",
                output=tool_result.output,
                error=tool_result.error,
                exit_code=tool_result.exit_code,
                duration_ms=step_duration,
                final_result="success" if tool_result.success else "failure"
            )
            db.add(audit_entry)

            if tool_result.success:
                current_step_states[idx]["status"] = "completed"
                current_step_states[idx]["log"] = tool_result.output
                current_step_states[idx]["duration_ms"] = step_duration
                accumulated_output.append(f"✓ {step.name}: {tool_result.output}")
                operation.steps_json = json.dumps(current_step_states)
                await db.commit()
                
                await self.broadcast("step_progress", {
                    "operation_id": operation.id,
                    "step_index": idx,
                    "step_name": step.name,
                    "status": "completed",
                    "output": tool_result.output
                })
            else:
                current_step_states[idx]["status"] = "failed"
                current_step_states[idx]["log"] = tool_result.error or tool_result.output
                current_step_states[idx]["duration_ms"] = step_duration
                accumulated_output.append(f"✕ {step.name} failed: {tool_result.error}")
                overall_success = False
                
                await self.broadcast("step_progress", {
                    "operation_id": operation.id,
                    "step_index": idx,
                    "step_name": step.name,
                    "status": "failed",
                    "error": tool_result.error
                })
                break

        # Finalize operation
        operation.status = "completed" if overall_success else "failed"
        operation.steps_json = json.dumps(current_step_states)
        operation.output_log = "\n".join(accumulated_output)
        operation.completed_at = datetime.datetime.utcnow()
        if operation.started_at:
            operation.duration_seconds = (operation.completed_at - operation.started_at).total_seconds()
        
        # If service was deployed or restarted, update service model record in DB
        if operation.service_id and overall_success:
            s_stmt = select(ServiceModel).where(ServiceModel.id == operation.service_id)
            res = await db.execute(s_stmt)
            service_obj = res.scalar_one_or_none()
            if service_obj:
                service_obj.status = "running"
                if "deploy" in operation.action_type.lower():
                    import datetime
                    service_obj.last_deployment = datetime.datetime.utcnow()

        await db.commit()

        await self.broadcast("operation_completed", {
            "operation_id": operation.id,
            "status": operation.status,
            "output": operation.output_log
        })

        return operation

executor = PlanExecutor()
