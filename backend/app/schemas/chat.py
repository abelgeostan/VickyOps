from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = "default"

class ChatMessageResponse(BaseModel):
    reply: str
    operation_id: Optional[str] = None
    requires_approval: bool = False
    approval_prompt: Optional[str] = None
    plan_title: Optional[str] = None
    steps: List[Dict[str, Any]] = []
