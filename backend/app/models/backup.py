import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger
from app.database import Base

class BackupModel(Base):
    __tablename__ = "backups"

    id = Column(String(50), primary_key=True, index=True)
    service_id = Column(String(50), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    size_bytes = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text, nullable=True)
