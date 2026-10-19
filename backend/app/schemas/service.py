from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    repository: Optional[str] = None
    branch: str = "main"
    path: str
    compose_file: str = "docker-compose.yml"
    health_url: Optional[str] = None
    deployment_type: str = "git_compose"
    requires_approval: bool = True

class ServiceCreate(ServiceBase):
    id: str

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    repository: Optional[str] = None
    branch: Optional[str] = None
    path: Optional[str] = None
    compose_file: Optional[str] = None
    health_url: Optional[str] = None
    deployment_type: Optional[str] = None
    requires_approval: Optional[bool] = None

class ServiceResponse(ServiceBase):
    id: str
    status: str
    docker_status: Optional[str] = None
    current_commit: Optional[str] = None
    remote_commit: Optional[str] = None
    last_deployment: Optional[datetime] = None
    health_status: Optional[str] = None
    is_active: bool
    updated_at: Optional[datetime] = None
    containers: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True

class ServiceActionRequest(BaseModel):
    action: str  # deploy, restart, stop, start, health_check, check_updates, logs, backup
    parameters: Optional[Dict[str, Any]] = None
