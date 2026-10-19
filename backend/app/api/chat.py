import uuid
import json
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, AsyncSessionLocal
from app.models.service import ServiceModel
from app.models.operation import OperationModel
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.agent.planner import planner
from app.agent.executor import executor

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatMessageResponse)
async def handle_chat_message(
    chat_req: ChatMessageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Fetch all services for context
    stmt = select(ServiceModel)
    result = await db.execute(stmt)
    services = result.scalars().all()
    service_dicts = [{
        "id": s.id,
        "name": s.name,
        "path": s.path,
        "branch": s.branch,
        "compose_file": s.compose_file,
        "health_url": s.health_url,
        "deployment_type": s.deployment_type
    } for s in services]

    # Generate plan
    plan = await planner.create_plan(chat_req.message, service_dicts)

    # If conversational message without steps, reply directly
    if not plan.steps and plan.explanation:
        return ChatMessageResponse(
            reply=plan.explanation,
            operation_id=None,
            requires_approval=False,
            approval_prompt=None,
            plan_title=plan.title,
            steps=[]
        )

    op_id = f"op_{uuid.uuid4().hex[:10]}"
    op = OperationModel(
        id=op_id,
        name=plan.title,
        service_id=plan.service_id,
        action_type="chat_command",
        status="requires_approval" if plan.requires_approval else "pending",
        initiator="agent",
        prompt=chat_req.message,
        plan_json=json.dumps([s.model_dump() for s in plan.steps]),
        steps_json=json.dumps([{
            "step_index": s.step_index,
            "name": s.name,
            "tool_name": s.tool_name,
            "status": "pending",
            "description": s.description,
            "log": "",
            "duration_ms": 0.0
        } for s in plan.steps]),
        requires_approval="true" if plan.requires_approval else "false",
        approval_prompt=plan.approval_prompt,
        approval_status="awaiting" if plan.requires_approval else "not_required"
    )
    db.add(op)
    await db.commit()
    await db.refresh(op)

    # If safe, execute automatically in background
    if not plan.requires_approval:
        async def run_safe_op():
            async with AsyncSessionLocal() as local_db:
                reloaded = await local_db.get(OperationModel, op_id)
                if reloaded:
                    await executor.execute_plan(local_db, reloaded, plan)
        background_tasks.add_task(run_safe_op)
        
        reply_text = f"I've initiated **{plan.title}**. Executing {len(plan.steps)} safe operation steps in real-time."
    else:
        reply_text = (
            f"Here is the execution plan for **{plan.title}**:\n\n" +
            "\n".join([f"{i+1}. {s.name} ({s.tool_name})" for i, s in enumerate(plan.steps)]) +
            f"\n\n{plan.approval_prompt or 'This operation modifies server workloads and requires your confirmation.'}"
        )

    return ChatMessageResponse(
        reply=reply_text,
        operation_id=op.id,
        requires_approval=plan.requires_approval,
        approval_prompt=plan.approval_prompt,
        plan_title=plan.title,
        steps=[s.model_dump() for s in plan.steps]
    )
