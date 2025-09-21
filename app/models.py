import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from .database import Base

class DocumentStatus(enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    s3_path = Column(String)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.QUEUED)