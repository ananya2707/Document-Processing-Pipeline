from pydantic import BaseModel
from datetime import datetime
from .models import DocumentStatus

# Base model for document properties
class DocumentBase(BaseModel):
    filename: str

# Schema for creating a document
class DocumentCreate(DocumentBase):
    s3_path: str

# Schema for reading a document (API response)
class Document(DocumentBase):
    id: int
    s3_path: str
    upload_time: datetime
    status: DocumentStatus

    class Config:
        orm_mode = True # Allows Pydantic to read data from ORM objects