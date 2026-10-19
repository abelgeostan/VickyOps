import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from app.database import Base

class OperationModel(Base):
    __tablename__ = "operations"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    service_id = Column(String(50), nullable=True, index=True)
    action_type = Column(String(50), nullable=False)  # deploy, restart, stop, start, health_check, backup, custom
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed, requires_approval, cancelled
    initiator = Column(String(50), default="user")  # user, agent, dashboard, schedule
    prompt = Column(Text, nullable=True)
    
    # Execution breakdown
    plan_json = Column(Text, default="[]")  # List of steps planned
    steps_json = Column(Text, default="[]") # List of step execution details & logs
    current_step_index = Column(Integer, default=0)
    current_step_name = Column(String(100), nullable=True)
    
    # Approval state
    requires_approval = Column(String(10), default="false") # "true", "false"
    approval_prompt = Column(Text, nullable=True)
    approval_status = Column(String(50), default="not_required") # not_required, awaiting, approved, rejected
    
    # Result & metrics
    output_log = Column(Text, default="")
    error_details = Column(Text, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
