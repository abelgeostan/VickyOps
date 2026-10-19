from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class ServerMetrics(BaseModel):
    hostname: str
    uptime: str
    kernel: str
    docker_version: str
    cpu_percent: float
    cpu_load: Dict[str, float]
    ram: Dict[str, Any]
    disk: Dict[str, Any]
    network: Dict[str, Any]

class CloudflareStatusResponse(BaseModel):
    tunnel_count: int
    active_count: int
    overall_status: str
    tunnels: List[Dict[str, Any]]

class AuditLogItem(BaseModel):
    id: int
    timestamp: datetime
    operation_id: Optional[str]
    user_request: Optional[str]
    agent_plan: Optional[str]
    tool_name: str
    service_id: Optional[str]
    parameters: Dict[str, Any] = {}
    approval_status: str
    output: Optional[str]
    error: Optional[str]
    exit_code: int
    duration_ms: float
    final_result: str

    class Config:
        from_attributes = True
