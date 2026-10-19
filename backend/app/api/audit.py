import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.audit import AuditLogModel
from app.schemas.metrics import AuditLogItem

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("", response_model=List[AuditLogItem])
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    service_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AuditLogModel).order_by(desc(AuditLogModel.timestamp)).limit(limit)
    if service_id:
        stmt = stmt.where(AuditLogModel.service_id == service_id)
    if tool_name:
        stmt = stmt.where(AuditLogModel.tool_name == tool_name)
    
    result = await db.execute(stmt)
    records = result.scalars().all()
    
    out = []
    for r in records:
        params = {}
        if r.parameters_json:
            try:
                params = json.loads(r.parameters_json)
            except Exception:
                pass

        out.append(AuditLogItem(
            id=r.id,
            timestamp=r.timestamp,
            operation_id=r.operation_id,
            user_request=r.user_request,
            agent_plan=r.agent_plan,
            tool_name=r.tool_name,
            service_id=r.service_id,
            parameters=params,
            approval_status=r.approval_status,
            output=r.output,
            error=r.error,
            exit_code=r.exit_code,
            duration_ms=r.duration_ms,
            final_result=r.final_result
        ))
    return out
