"""
Agent Service
High-level service for interacting with the multi-agent system.
"""

from typing import Dict, Any
import logging
import time

from app.agents.graph_orchestrator import AgentOrchestrator
from app.repositories.chroma_repo import ChromaRepository
from app.models.chat import ChatResponse, ChatMessage, MessageRole, AgentType

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service layer for the multi-agent RAG system.
    Provides a clean interface for the FastAPI endpoints.
    """
    
    def __init__(self, chroma_repo: ChromaRepository):
        """
        Initialize agent service.
        
        Args:
            chroma_repo: ChromaDB repository
        """
        self.chroma_repo = chroma_repo
        self.orchestrator = AgentOrchestrator(chroma_repo)
        
        logger.info("Agent Service initialized")
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str
    ) -> ChatResponse:
        """
        Process a user query through the multi-agent system.
        
        Args:
            query: User query
            user_id: User ID
            session_id: Chat session ID
            
        Returns:
            Chat response with answer and metadata
        """
        start_time = time.time()
        
        logger.info(f"Agent Service processing query for user {user_id}")
        
        # Process through orchestrator
        result = await self.orchestrator.process_query(
            query=query,
            user_id=user_id,
            session_id=session_id
        )
        
        processing_time = time.time() - start_time
        
        # Map agent name to AgentType
        agent_type = self._map_agent_type(result.get("primary_agent", "research"))
        
        # Create ChatMessage for the response
        message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=result.get("answer", "No answer generated"),
            agent_type=agent_type,
            metadata={
                "routing_decision": result.get("routing_decision", {}),
                "sources_count": len(result.get("sources", []))
            }
        )
        
        # Create ChatResponse
        response = ChatResponse(
            session_id=session_id,
            message=message,
            agent_used=agent_type,
            sources=result.get("sources", []),
            processing_time=processing_time
        )
        
        logger.info(f"Query processed in {processing_time:.2f}s by {agent_type.value}")
        
        return response
    
    def _map_agent_type(self, agent_name: str) -> AgentType:
        """
        Map agent name to AgentType enum.
        
        Args:
            agent_name: Agent name string
            
        Returns:
            Corresponding AgentType
        """
        name_lower = agent_name.lower()
        
        if "it" in name_lower:
            return AgentType.IT_POLICY
        elif "hr" in name_lower:
            return AgentType.HR_POLICY
        elif "coordinator" in name_lower:
            return AgentType.COORDINATOR
        else:
            return AgentType.RESEARCH
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about available agents.
        
        Returns:
            Agent information
        """
        return {
            "agents": [
                {
                    "name": "Coordinator Agent",
                    "type": "coordinator",
                    "description": "Routes queries to appropriate specialist agents"
                },
                {
                    "name": "Research Agent",
                    "type": "research",
                    "description": "Handles general research queries across all documents"
                },
                {
                    "name": "IT Policy Agent",
                    "type": "it_policy",
                    "description": "Specialist in IT policies and procedures"
                },
                {
                    "name": "HR Policy Agent",
                    "type": "hr_policy",
                    "description": "Specialist in HR policies and employee procedures"
                }
            ],
            "orchestration": "LangGraph-based multi-agent workflow"
        }

