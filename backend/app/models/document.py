"""
Document Models
Defines document upload and management data structures.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Document type enumeration."""
    HR_POLICY = "hr_policy"
    IT_POLICY = "it_policy"
    GENERAL = "general"


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    """
    Document model stored in MongoDB.
    Metadata about uploaded documents (not the embeddings).
    """
    id: str = Field(default=None, alias="_id")
    filename: str
    original_filename: str
    file_path: str
    file_size: int  # bytes
    file_type: str  # MIME type
    document_type: DocumentType = DocumentType.GENERAL
    
    uploaded_by: str  # user_id
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    status: DocumentStatus = DocumentStatus.PENDING
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    
    # Embedding metadata
    chunks_count: int = 0
    embeddings_stored: bool = False
    chroma_collection: Optional[str] = None
    
    # Document metadata
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentUpload(BaseModel):
    """Request model for document upload metadata."""
    document_type: DocumentType = DocumentType.GENERAL
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DocumentResponse(BaseModel):
    """Response model for document information."""
    id: str
    filename: str
    original_filename: str
    file_size: int
    document_type: DocumentType
    uploaded_by: str
    uploaded_at: datetime
    status: DocumentStatus
    chunks_count: int
    embeddings_stored: bool
    title: Optional[str] = None
    tags: List[str] = []
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int

