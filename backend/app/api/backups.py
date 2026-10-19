from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.tools.registry import tool_registry

router = APIRouter(prefix="/backups", tags=["backups"])

class BackupCreateRequest(BaseModel):
    service_id: str
    service_path: str

class BackupRestoreRequest(BaseModel):
    backup_filename: str
    target_path: str

@router.get("")
async def list_backups():
    tool = tool_registry.get_tool("backup.list")
    if tool:
        res = await tool.execute()
        if res.success:
            return res.data
    return {"backups": [], "count": 0}

@router.post("")
async def create_backup(req: BackupCreateRequest):
    tool = tool_registry.get_tool("backup.create")
    if not tool:
        raise HTTPException(status_code=500, detail="Backup tool unavailable")
    res = await tool.execute(service_path=req.service_path, service_name=req.service_id)
    if not res.success:
        raise HTTPException(status_code=500, detail=res.error or "Backup failed")
    return res.data

@router.post("/restore")
async def restore_backup(req: BackupRestoreRequest):
    tool = tool_registry.get_tool("backup.restore")
    if not tool:
        raise HTTPException(status_code=500, detail="Restore tool unavailable")
    res = await tool.execute(backup_filename=req.backup_filename, target_path=req.target_path)
    if not res.success:
        raise HTTPException(status_code=500, detail=res.error or "Restore failed")
    return {"message": "Backup restored successfully", "output": res.output}
