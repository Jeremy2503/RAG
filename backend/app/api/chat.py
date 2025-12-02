"""
Chat Endpoints
Handles chat sessions and message processing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
import logging

from app.models.chat import (
    ChatRequest,
    ChatResponse,
    ChatSession,
    SessionListResponse,
    ChatMessage,
    MessageRole
)
from app.models.user import User
from app.services.chat_service import ChatService
from app.services.agent_service import AgentService
from app.repositories.mongodb_repo import get_mongodb_repo, MongoDBRepository
from app.repositories.chroma_repo import get_chroma_repo, ChromaRepository
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# Dependencies
async def get_chat_service(
    db_repo: MongoDBRepository = Depends(get_mongodb_repo)
) -> ChatService:
    """Get chat service instance."""
    return ChatService(db_repo)


async def get_agent_service(
    chroma_repo: ChromaRepository = Depends(get_chroma_repo)
) -> AgentService:
    """Get agent service instance."""
    return AgentService(chroma_repo)


@router.post("/query", response_model=ChatResponse)
async def process_chat_query(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    agent_service: AgentService = Depends(get_agent_service)
) -> ChatResponse:
    """
    Process a chat query through the multi-agent system.
    
    Args:
        request: Chat request with message and optional session ID
        current_user: Current authenticated user
        chat_service: Chat service
        agent_service: Agent service
        
    Returns:
        Chat response with answer and sources
    """
    logger.info(f"Processing chat query for user {current_user.email}")
    
    try:
        # Get or create session
        if request.session_id:
            session = await chat_service.get_session(request.session_id, current_user)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )
        else:
            # Create new session
            title = chat_service.generate_title_from_first_message(request.message)
            session = await chat_service.create_session(current_user, title)
        
        # Add user message to session
        await chat_service.add_message(
            session_id=session.id,
            user=current_user,
            role=MessageRole.USER,
            content=request.message
        )
        
        # Process query through agent system
        response = await agent_service.process_query(
            query=request.message,
            user_id=current_user.id,
            session_id=session.id
        )
        
        # Add assistant message to session
        await chat_service.add_message(
            session_id=session.id,
            user=current_user,
            role=MessageRole.ASSISTANT,
            content=response.message.content,
            agent_type=response.agent_used,
            metadata=response.message.metadata
        )
        
        logger.info(f"Chat query processed successfully for session {session.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat query: {str(e)}"
        )


@router.get("/sessions")
async def get_chat_sessions(
    page: int = 1,
    page_size: int = 50,
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
) -> Dict[str, Any]:
    """
    Get all chat sessions for the current user.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of sessions per page
        include_archived: Include archived sessions
        current_user: Current authenticated user
        chat_service: Chat service
        
    Returns:
        List of chat sessions
    """
    result = await chat_service.get_user_sessions(
        user=current_user,
        page=page,
        page_size=page_size,
        include_archived=include_archived
    )
    
    # Convert to dict with by_alias=False to ensure 'id' is used
    return result.model_dump(by_alias=False)


@router.get("/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
) -> Dict[str, Any]:
    """
    Get a specific chat session by ID.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        chat_service: Chat service
        
    Returns:
        Chat session
    """
    session = await chat_service.get_session(session_id, current_user)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Convert to dict with by_alias=False to ensure 'id' is used
    return session.model_dump(by_alias=False)


@router.put("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    title: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
) -> Dict[str, Any]:
    """
    Update chat session title.
    
    Args:
        session_id: Session ID
        title: New title
        current_user: Current authenticated user
        chat_service: Chat service
        
    Returns:
        Success message
    """
    success = await chat_service.update_session_title(
        session_id=session_id,
        user=current_user,
        title=title
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or update failed"
        )
    
    return {"message": "Session title updated successfully"}


@router.delete("/sessions/{session_id}")
async def archive_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
) -> Dict[str, Any]:
    """
    Archive a chat session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        chat_service: Chat service
        
    Returns:
        Success message
    """
    success = await chat_service.archive_session(session_id, current_user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or archive failed"
        )
    
    return {"message": "Session archived successfully"}


@router.get("/agents/info")
async def get_agent_info(
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get information about available agents.
    
    Args:
        agent_service: Agent service
        current_user: Current authenticated user
        
    Returns:
        Agent information
    """
    return agent_service.get_agent_info()

