import uuid
import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.service import ServiceModel
from app.models.operation import OperationModel
from app.schemas.service import ServiceResponse, ServiceCreate, ServiceUpdate, ServiceActionRequest
from app.schemas.operation import OperationResponse
from app.agent.planner import planner
from app.agent.executor import executor
from app.tools.registry import tool_registry

router = APIRouter(prefix="/services", tags=["services"])

@router.get("", response_model=List[ServiceResponse])
async def list_services(db: AsyncSession = Depends(get_db)):
    stmt = select(ServiceModel)
    result = await db.execute(stmt)
    services = result.scalars().all()
    
    # Query docker containers to populate live status
    container_tool = tool_registry.get_tool("docker.list_containers")
    containers = []
    if container_tool:
        c_res = await container_tool.execute(all=True)
        if c_res.success:
            containers = c_res.data.get("containers", [])

    response_list = []
    for s in services:
        s_dict = {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "repository": s.repository,
            "branch": s.branch,
            "path": s.path,
            "compose_file": s.compose_file,
            "health_url": s.health_url,
            "deployment_type": s.deployment_type,
            "requires_approval": s.requires_approval,
            "is_active": s.is_active,
            "status": s.status,
            "docker_status": s.docker_status,
            "current_commit": s.current_commit,
            "remote_commit": s.remote_commit,
            "last_deployment": s.last_deployment,
            "health_status": s.health_status,
            "updated_at": s.updated_at,
            "containers": []
        }
        
        # Match containers belonging to this service by name or label
        prefix = s.id.lower().replace("-", "_")
        matched_c = [c for c in containers if prefix in c.get("name", "").lower() or s.id in c.get("name", "").lower()]
        s_dict["containers"] = matched_c
        if matched_c:
            any_up = any("Up" in c.get("status", "") for c in matched_c)
            all_up = all("Up" in c.get("status", "") for c in matched_c)
            s_dict["docker_status"] = f"{sum(1 for c in matched_c if 'Up' in c.get('status', ''))}/{len(matched_c)} Up"
            s_dict["status"] = "running" if all_up else ("degraded" if any_up else "stopped")
        else:
            s_dict["docker_status"] = "Not Running"
            s_dict["status"] = "stopped"

        response_list.append(ServiceResponse(**s_dict))

    return response_list

@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ServiceModel).where(ServiceModel.id == service_id)
    result = await db.execute(stmt)
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return ServiceResponse(
        id=service.id,
        name=service.name,
        description=service.description,
        repository=service.repository,
        branch=service.branch,
        path=service.path,
        compose_file=service.compose_file,
        health_url=service.health_url,
        deployment_type=service.deployment_type,
        requires_approval=service.requires_approval,
        is_active=service.is_active,
        status=service.status,
        docker_status=service.docker_status,
        current_commit=service.current_commit,
        remote_commit=service.remote_commit,
        last_deployment=service.last_deployment,
        health_status=service.health_status,
        updated_at=service.updated_at,
        containers=[]
    )

@router.get("/{service_id}/compat")
async def check_service_compatibility(service_id: str, db: AsyncSession = Depends(get_db)):
    """Phase 3: Inspect compatibility with the standardized VickyAI deployment model."""
    stmt = select(ServiceModel).where(ServiceModel.id == service_id)
    result = await db.execute(stmt)
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if service.id == "vickyai":
        return {
            "service_id": service.id,
            "compatible": True,
            "model": "Standardized Git-Compose",
            "message": "VickyAI is the reference deployment model. Fully supports GitHub -> git pull -> docker compose up -d --build.",
            "required_changes": []
        }
    
    # Analyze other services
    required_changes = []
    if not service.repository:
        required_changes.append(f"Configure Git remote repository URL for {service.name}")
    if service.deployment_type == "image_compose":
        required_changes.append(f"Initialize Git working tree in '{service.path}'")
        required_changes.append("Update compose configuration from prebuilt image tags to local source builds or standardized image deployment")
    if not service.health_url:
        required_changes.append("Configure automated HTTP health check endpoint")

    message = f"{service.name} cannot currently use the standardized deployment workflow because its Docker Compose configuration differs from VickyAI."

    return {
        "service_id": service.id,
        "compatible": len(required_changes) == 0,
        "model": service.deployment_type,
        "message": message if required_changes else f"{service.name} is ready for standardized deployment.",
        "required_changes": required_changes
    }

@router.post("/{service_id}/action", response_model=OperationResponse)
async def trigger_service_action(
    service_id: str,
    action_req: ServiceActionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers an action from the visual dashboard (e.g. 'Deploy Update', 'Restart', 'Health Check').
    Generates a structured plan and launches the operation.
    """
    stmt = select(ServiceModel).where(ServiceModel.id == service_id)
    result = await db.execute(stmt)
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Construct request phrase
    action_map = {
        "deploy": f"Update {service.name}",
        "restart": f"Restart {service.name}",
        "stop": f"Stop {service.name}",
        "start": f"Start {service.name}",
        "health_check": f"Health check for {service.name}",
        "check_updates": f"Check updates for {service.name}",
        "backup": f"Backup {service.name}"
    }
    prompt_text = action_map.get(action_req.action, f"{action_req.action} {service.name}")

    # Create plan
    plan = await planner.create_plan(prompt_text, [{
        "id": service.id,
        "name": service.name,
        "path": service.path,
        "branch": service.branch,
        "compose_file": service.compose_file,
        "health_url": service.health_url,
        "deployment_type": service.deployment_type
    }])

    op_id = f"op_{uuid.uuid4().hex[:10]}"
    op = OperationModel(
        id=op_id,
        name=plan.title,
        service_id=service.id,
        action_type=action_req.action,
        status="pending",
        initiator="dashboard",
        prompt=prompt_text,
        plan_json=json.dumps([s.dict() for s in plan.steps]),
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

    # Launch execution in background task if it does not require approval or auto-approves safe
    if not plan.requires_approval:
        async def run_op():
            async with get_db() as local_db:
                # reload op
                local_op = await local_db.get(OperationModel, op_id)
                if local_op:
                    await executor.execute_plan(local_db, local_op, plan)
        background_tasks.add_task(run_op)

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
        steps=[{
            "step_index": s.step_index,
            "name": s.name,
            "tool_name": s.tool_name,
            "status": "pending",
            "description": s.description,
            "log": "",
            "duration_ms": 0.0
        } for s in plan.steps],
        created_at=op.created_at
    )
