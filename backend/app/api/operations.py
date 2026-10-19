import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db, AsyncSessionLocal
from app.models.operation import OperationModel
from app.schemas.operation import OperationResponse, ApprovalDecision
from app.agent.planner import ExecutionPlan, PlanStep
from app.agent.executor import executor

router = APIRouter(prefix="/operations", tags=["operations"])

@router.get("", response_model=List[OperationResponse])
async def list_operations(limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(OperationModel).order_by(desc(OperationModel.created_at)).limit(limit)
    res = await db.execute(stmt)
    ops = res.scalars().all()
    
    response = []
    for op in ops:
        steps_list = []
        if op.steps_json:
            try:
                steps_list = json.loads(op.steps_json)
            except Exception:
                pass
        
        response.append(OperationResponse(
            id=op.id,
            name=op.name,
            service_id=op.service_id,
            action_type=op.action_type,
            status=op.status,
            initiator=op.initiator,
            prompt=op.prompt,
            current_step_index=op.current_step_index,
            current_step_name=op.current_step_name,
            requires_approval=op.requires_approval,
            approval_prompt=op.approval_prompt,
            approval_status=op.approval_status,
            steps=steps_list,
            output_log=op.output_log,
            error_details=op.error_details,
            duration_seconds=op.duration_seconds,
            created_at=op.created_at
        ))
    return response

@router.get("/{operation_id}", response_model=OperationResponse)
async def get_operation(operation_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(OperationModel).where(OperationModel.id == operation_id)
    res = await db.execute(stmt)
    op = res.scalar_one_or_none()
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")

    steps_list = []
    if op.steps_json:
        try:
            steps_list = json.loads(op.steps_json)
        except Exception:
            pass

    return OperationResponse(
        id=op.id,
        name=op.name,
        service_id=op.service_id,
        action_type=op.action_type,
        status=op.status,
        initiator=op.initiator,
        prompt=op.prompt,
        current_step_index=op.current_step_index,
        current_step_name=op.current_step_name,
        requires_approval=op.requires_approval,
        approval_prompt=op.approval_prompt,
        approval_status=op.approval_status,
        steps=steps_list,
        output_log=op.output_log,
        error_details=op.error_details,
        duration_seconds=op.duration_seconds,
        created_at=op.created_at
    )

@router.post("/{operation_id}/decision", response_model=OperationResponse)
async def decide_operation(
    operation_id: str,
    decision: ApprovalDecision,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(OperationModel).where(OperationModel.id == operation_id)
    res = await db.execute(stmt)
    op = res.scalar_one_or_none()
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")

    if op.status not in ["pending", "requires_approval"]:
        raise HTTPException(status_code=400, detail=f"Operation is already in state '{op.status}'")

    if decision.decision == "reject":
        op.status = "cancelled"
        op.approval_status = "rejected"
        op.output_log = (op.output_log or "") + "\nOperation cancelled by user."
        await db.commit()
        await executor.broadcast("operation_update", {"operation_id": op.id, "status": "cancelled"})
        return await get_operation(operation_id, db)

    # User approved!
    op.approval_status = "approved"
    op.status = "running"
    await db.commit()

    # Reconstruct ExecutionPlan from plan_json
    raw_steps = json.loads(op.plan_json) if op.plan_json else []
    plan_steps = [PlanStep(**s) for s in raw_steps]
    plan = ExecutionPlan(
        title=op.name,
        user_request=op.prompt or "",
        service_id=op.service_id,
        steps=plan_steps,
        requires_approval=False
    )

    async def execute_approved():
        async with AsyncSessionLocal() as local_db:
            reloaded_op = await local_db.get(OperationModel, operation_id)
            if reloaded_op:
                await executor.execute_plan(local_db, reloaded_op, plan, approved_by_user=True)

    background_tasks.add_task(execute_approved)

    return await get_operation(operation_id, db)
