import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.database import Base

class ServiceModel(Base):
    __tablename__ = "services"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    repository = Column(String(255), nullable=True)
    branch = Column(String(50), default="main")
    path = Column(String(255), nullable=False)
    compose_file = Column(String(100), default="docker-compose.yml")
    health_url = Column(String(255), nullable=True)
    deployment_type = Column(String(50), default="git_compose")  # git_compose, image_compose, etc.
    requires_approval = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # Cached status info
    status = Column(String(50), default="unknown")  # running, stopped, degraded, unknown
    docker_status = Column(String(100), default="unknown")
    current_commit = Column(String(40), nullable=True)
    remote_commit = Column(String(40), nullable=True)
    last_deployment = Column(DateTime, nullable=True)
    health_status = Column(String(50), default="unknown")
    meta_json = Column(Text, default="{}")
    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
