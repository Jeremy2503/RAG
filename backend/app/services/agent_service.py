"""
Agent Service
High-level service for interacting with the multi-agent system.
Integrates with Opik evaluation for confidence and quality metrics.
"""

from typing import Dict, Any
import logging
import time

from app.agents.graph_orchestrator import AgentOrchestrator
from app.repositories.chroma_repo import ChromaRepository
from app.models.chat import (
    ChatResponse, 
    ChatMessage, 
    MessageRole, 
    AgentType, 
    ConfidenceLevel,
    EvaluationMetrics
)
from app.services.evaluation_service import get_evaluation_service
from app.utils.observability import track, get_project_name

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service layer for the multi-agent RAG system.
    Provides a clean interface for the FastAPI endpoints.
    Integrates with Opik for response evaluation.
    """
    
    def __init__(self, chroma_repo: ChromaRepository):
        """
        Initialize agent service.
        
        Args:
            chroma_repo: ChromaDB repository
        """
        self.chroma_repo = chroma_repo
        self.orchestrator = AgentOrchestrator(chroma_repo)
        self.evaluation_service = get_evaluation_service()
        
        logger.info("Agent Service initialized with evaluation support")
    
    @track(
        name="agent_service::process_query",
        project_name=get_project_name(),
        tags=["service", "agent_service", "query"],
        capture_input=True,
        capture_output=True
    )
    async def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        include_detailed_evaluation: bool = True
    ) -> ChatResponse:
        """
        Process a user query through the multi-agent system.
        Includes Opik-based evaluation for confidence and quality metrics.
        
        Args:
            query: User query
            user_id: User ID
            session_id: Chat session ID
            include_detailed_evaluation: Whether to include detailed evaluation metrics
            
        Returns:
            Chat response with answer, metadata, and evaluation
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
        
        # Extract routing confidence
        routing_confidence = result.get("confidence", 0.5)
        
        # Extract context from sources for evaluation
        sources = result.get("sources", [])
        context = [s.get("content", "") for s in sources if s.get("content")]
        
        # Run evaluation
        evaluation_result = await self.evaluation_service.evaluate_response(
            query=query,
            answer=result.get("answer", ""),
            context=context,
            sources_count=len(sources),
            routing_confidence=routing_confidence,
            agent_name=result.get("primary_agent", "Unknown"),
            include_detailed_metrics=include_detailed_evaluation
        )
        
        # Extract confidence from evaluation
        overall_confidence = evaluation_result.get("overall_confidence", routing_confidence)
        confidence_level_str = evaluation_result.get("quality_level", "UNKNOWN")
        confidence_level = self._map_confidence_level(confidence_level_str)
        
        # Generate confidence explanation
        confidence_explanation = self.evaluation_service.get_confidence_explanation(evaluation_result)
        
        # Build evaluation metrics if detailed evaluation was requested
        evaluation_metrics = None
        if include_detailed_evaluation and "detailed_metrics" in evaluation_result:
            detailed = evaluation_result["detailed_metrics"]
            evaluation_metrics = EvaluationMetrics(
                hallucination_score=detailed.get("hallucination_score"),
                answer_relevance_score=detailed.get("answer_relevance_score"),
                context_recall_score=detailed.get("context_recall_score"),
                context_precision_score=detailed.get("context_precision_score"),
                evaluation_method=evaluation_result.get("evaluation_method", "unknown")
            )
        
        # Create ChatMessage for the response
        message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=result.get("answer", "No answer generated"),
            agent_type=agent_type,
            metadata={
                "routing_decision": result.get("routing_decision", {}),
                "sources_count": len(sources),
                "confidence": overall_confidence,
                "confidence_level": confidence_level_str,
                "evaluation_method": evaluation_result.get("evaluation_method", "unknown")
            }
        )
        
        # Create ChatResponse with evaluation data
        response = ChatResponse(
            session_id=session_id,
            message=message,
            agent_used=agent_type,
            sources=sources,
            processing_time=processing_time,
            confidence=overall_confidence,
            confidence_level=confidence_level,
            confidence_explanation=confidence_explanation,
            evaluation=evaluation_metrics
        )
        
        logger.info(
            f"Query processed in {processing_time:.2f}s by {agent_type.value} | "
            f"Confidence: {overall_confidence:.0%} ({confidence_level_str}) | "
            f"Method: {evaluation_result.get('evaluation_method', 'unknown')}"
        )
        
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
    
    def _map_confidence_level(self, confidence_level_str: str) -> ConfidenceLevel:
        """
        Map confidence level string to ConfidenceLevel enum.
        
        Args:
            confidence_level_str: Confidence level string
            
        Returns:
            Corresponding ConfidenceLevel
        """
        try:
            return ConfidenceLevel(confidence_level_str.upper())
        except ValueError:
            return ConfidenceLevel.UNKNOWN
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about available agents.
        
        Returns:
            Agent information including evaluation capabilities
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
            "orchestration": "LangGraph-based multi-agent workflow",
            "evaluation": {
                "enabled": True,
                "provider": "Opik" if self.evaluation_service.is_opik_available() else "Heuristic",
                "metrics": [
                    "overall_confidence",
                    "hallucination_detection",
                    "answer_relevance",
                    "context_precision",
                    "context_recall"
                ] if self.evaluation_service.is_opik_available() else [
                    "overall_confidence",
                    "routing_score",
                    "source_availability",
                    "answer_quality"
                ]
            }
        }
