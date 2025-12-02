"""
Chat Service
Manages chat sessions and message history.
"""

from typing import List, Optional
from datetime import datetime
import logging
import uuid

from app.models.chat import (
    ChatSession,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    MessageRole,
    AgentType,
    SessionListResponse
)
from app.models.user import User
from app.repositories.mongodb_repo import MongoDBRepository

logger = logging.getLogger(__name__)


class ChatService:
    """
    Chat service for managing conversation sessions and messages.
    """
    
    def __init__(self, db_repo: MongoDBRepository):
        """
        Initialize chat service.
        
        Args:
            db_repo: MongoDB repository instance
        """
        self.db_repo = db_repo
    
    async def create_session(
        self,
        user: User,
        title: str = "New Conversation"
    ) -> ChatSession:
        """
        Create a new chat session for a user.
        
        Args:
            user: User object
            title: Session title
            
        Returns:
            Created chat session
        """
        try:
            session = await self.db_repo.create_chat_session(user.id, title)
            logger.info(f"Created chat session {session.id} for user {user.email}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise
    
    async def get_session(
        self,
        session_id: str,
        user: User
    ) -> Optional[ChatSession]:
        """
        Get a chat session by ID.
        
        Args:
            session_id: Session ID
            user: User object (for authorization)
            
        Returns:
            Chat session if found and authorized
        """
        session = await self.db_repo.get_chat_session(session_id, user.id)
        return session
    
    async def add_message(
        self,
        session_id: str,
        user: User,
        role: MessageRole,
        content: str,
        agent_type: Optional[AgentType] = None,
        metadata: Optional[dict] = None
    ) -> ChatMessage:
        """
        Add a message to a chat session.
        
        Args:
            session_id: Session ID
            user: User object
            role: Message role (user/assistant)
            content: Message content
            agent_type: Which agent generated the message (for assistant messages)
            metadata: Optional metadata
            
        Returns:
            Created message
        """
        message = ChatMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            agent_type=agent_type,
            metadata=metadata
        )
        
        success = await self.db_repo.add_message_to_session(
            session_id,
            user.id,
            message
        )
        
        if not success:
            raise Exception("Failed to add message to session")
        
        logger.info(f"Added {role.value} message to session {session_id}")
        return message
    
    async def get_user_sessions(
        self,
        user: User,
        page: int = 1,
        page_size: int = 50,
        include_archived: bool = False
    ) -> SessionListResponse:
        """
        Get all chat sessions for a user.
        
        Args:
            user: User object
            page: Page number (1-indexed)
            page_size: Number of sessions per page
            include_archived: Whether to include archived sessions
            
        Returns:
            Session list response with pagination
        """
        skip = (page - 1) * page_size
        
        sessions = await self.db_repo.get_user_chat_sessions(
            user.id,
            skip=skip,
            limit=page_size,
            include_archived=include_archived
        )
        
        # Note: For simplicity, not implementing total count query
        # In production, add a separate count query
        total = len(sessions)
        
        return SessionListResponse(
            sessions=sessions,
            total=total,
            page=page,
            page_size=page_size
        )
    
    async def update_session_title(
        self,
        session_id: str,
        user: User,
        title: str
    ) -> bool:
        """
        Update chat session title.
        
        Args:
            session_id: Session ID
            user: User object
            title: New title
            
        Returns:
            True if successful
        """
        success = await self.db_repo.update_session_title(
            session_id,
            user.id,
            title
        )
        
        if success:
            logger.info(f"Updated title for session {session_id}")
        
        return success
    
    async def archive_session(
        self,
        session_id: str,
        user: User
    ) -> bool:
        """
        Archive a chat session.
        
        Args:
            session_id: Session ID
            user: User object
            
        Returns:
            True if successful
        """
        success = await self.db_repo.archive_session(session_id, user.id)
        
        if success:
            logger.info(f"Archived session {session_id}")
        
        return success
    
    def generate_title_from_first_message(self, message: str) -> str:
        """
        Generate a session title from the first user message.
        
        Args:
            message: First message content
            
        Returns:
            Generated title
        """
        # Simple title generation: take first 50 characters
        max_length = 50
        
        if len(message) <= max_length:
            return message
        
        # Truncate at word boundary
        truncated = message[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated + "..."

