import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from app.database import Base

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    operation_id = Column(String(50), nullable=True, index=True)
    user_request = Column(Text, nullable=True)
    agent_plan = Column(Text, nullable=True)
    tool_name = Column(String(100), nullable=False, index=True)
    service_id = Column(String(50), nullable=True, index=True)
    parameters_json = Column(Text, default="{}")
    approval_status = Column(String(50), default="auto_approved") # auto_approved, manually_approved, rejected
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    exit_code = Column(Integer, default=0)
    duration_ms = Column(Float, default=0.0)
    final_result = Column(String(50), default="success") # success, failure, aborted
