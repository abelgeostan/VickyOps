from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class StepDetail(BaseModel):
    step_index: int
    name: str
    tool_name: str
    status: str
    description: str
    log: Optional[str] = ""
    duration_ms: Optional[float] = 0.0

class OperationResponse(BaseModel):
    id: str
    name: str
    service_id: Optional[str] = None
    action_type: str
    status: str
    initiator: str
    prompt: Optional[str] = None
    current_step_index: int = 0
    current_step_name: Optional[str] = None
    requires_approval: str = "false"
    approval_prompt: Optional[str] = None
    approval_status: str
    steps: List[StepDetail] = []
    output_log: Optional[str] = None
    error_details: Optional[str] = None
    duration_seconds: float = 0.0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ApprovalDecision(BaseModel):
    decision: str # "approve" or "reject"
    notes: Optional[str] = None
