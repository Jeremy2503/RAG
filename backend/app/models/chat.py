"""
Chat Models
Defines chat message and session data structures.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AgentType(str, Enum):
    """Agent type enumeration."""
    COORDINATOR = "coordinator"
    RESEARCH = "research"
    IT_POLICY = "it_policy"
    HR_POLICY = "hr_policy"


class ChatMessage(BaseModel):
    """Individual chat message model."""
    id: str = Field(default=None)
    role: MessageRole
    content: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_type: Optional[AgentType] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatSession(BaseModel):
    """
    Chat session model representing a conversation thread.
    Stored in MongoDB.
    """
    id: str = Field(default=None, alias="_id")
    user_id: str = Field(..., description="Owner of this chat session")
    title: str = Field(default="New Conversation", max_length=200)
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_archived: bool = False
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def model_dump(self, **kwargs):
        """Override to ensure 'id' is always in the output, not '_id'."""
        data = super().model_dump(**kwargs)
        # Ensure we're using 'id' not '_id'
        if '_id' in data and 'id' not in data:
            data['id'] = data.pop('_id')
        return data


class ChatRequest(BaseModel):
    """Request model for sending a chat message."""
    session_id: Optional[str] = None  # If None, create new session
    message: str = Field(..., min_length=1, max_length=5000)
    context: Optional[Dict[str, Any]] = None


class ConfidenceLevel(str, Enum):
    """Confidence level enumeration for routing decisions."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class EvaluationMetrics(BaseModel):
    """Detailed evaluation metrics for response quality."""
    hallucination_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Hallucination detection score (0=no hallucination, 1=hallucinated)"
    )
    answer_relevance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="How relevant the answer is to the question (0-1)"
    )
    context_recall_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="How well the context covers the expected answer (0-1)"
    )
    context_precision_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="How precise the retrieved context is (0-1)"
    )
    evaluation_method: str = Field(
        default="unknown",
        description="Method used for evaluation (opik or heuristic)"
    )


class ChatResponse(BaseModel):
    """Response model for chat queries."""
    session_id: str
    message: ChatMessage
    agent_used: AgentType
    sources: Optional[List[Dict[str, Any]]] = None
    processing_time: float  # seconds
    
    # Confidence and evaluation fields
    confidence: Optional[float] = Field(
        default=None, 
        ge=0.0, 
        le=1.0,
        description="Overall confidence score (0-1)"
    )
    confidence_level: Optional[ConfidenceLevel] = Field(
        default=None,
        description="Human-readable confidence level"
    )
    confidence_explanation: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of confidence"
    )
    
    # Detailed evaluation metrics (optional)
    evaluation: Optional[EvaluationMetrics] = Field(
        default=None,
        description="Detailed evaluation metrics from Opik"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionListResponse(BaseModel):
    """Response model for listing chat sessions."""
    sessions: List[ChatSession]
    total: int
    page: int
    page_size: int

