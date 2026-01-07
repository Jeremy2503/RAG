"""
Agent Service
High-level service for interacting with the multi-agent system.
Integrates with Opik evaluation for confidence and quality metrics.
"""

from typing import Dict, Any, List
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
from app.utils.question_detector import detect_multiple_questions, combine_multiple_answers
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
        Handles multiple questions by processing them separately.
        Includes Opik-based evaluation for confidence and quality metrics.
        
        Args:
            query: User query (may contain multiple questions)
            user_id: User ID
            session_id: Chat session ID
            include_detailed_evaluation: Whether to include detailed evaluation metrics
            
        Returns:
            Chat response with answer, metadata, and evaluation
        """
        start_time = time.time()
        
        logger.info(f"Agent Service processing query for user {user_id}")
        
        # Detect and split multiple questions
        questions = detect_multiple_questions(query)
        
        if len(questions) > 1:
            # Process each question separately
            logger.info(f"Detected {len(questions)} questions, processing separately")
            question_responses = []
            all_sources = []
            all_processing_times = []
            
            for question in questions:
                question = question.strip()
                if not question:
                    continue
                
                logger.info(f"Processing question: {question[:100]}...")
                q_start_time = time.time()
                
                # Process each question through the orchestrator
                result = await self.orchestrator.process_query(
                    query=question,
                    user_id=user_id,
                    session_id=session_id
                )
                
                q_processing_time = time.time() - q_start_time
                all_processing_times.append(q_processing_time)
                
                question_responses.append({
                    "question": question,
                    "answer": result.get("answer", ""),
                    "sources": result.get("sources", []),
                    "primary_agent": result.get("primary_agent", "Unknown"),
                    "confidence": result.get("confidence", 0.5)
                })
                
                # Collect sources
                all_sources.extend(result.get("sources", []))
            
            # Deduplicate sources by content (keep unique sources)
            seen_source_ids = set()
            unique_sources = []
            for source in all_sources:
                # Create a unique ID from source content or metadata
                source_id = source.get("id") or source.get("content", "")[:100]
                if source_id not in seen_source_ids:
                    seen_source_ids.add(source_id)
                    unique_sources.append(source)
            
            # Combine answers from all questions
            combined_answer = combine_multiple_answers(question_responses)
            
            # Calculate average confidence
            avg_confidence = sum(qr["confidence"] for qr in question_responses) / len(question_responses) if question_responses else 0.5
            
            # Determine primary agent (use most common or "Multiple Agents")
            primary_agent = "Multiple Agents" if len(set(qr["primary_agent"] for qr in question_responses)) > 1 else question_responses[0]["primary_agent"]
            
            processing_time = time.time() - start_time
            
            # Extract context from sources for evaluation
            context = [s.get("content", "") for s in unique_sources if s.get("content")]
            
            # Run evaluation on combined answer
            evaluation_result = await self.evaluation_service.evaluate_response(
                query=query,
                answer=combined_answer,
                context=context,
                sources_count=len(unique_sources),
                routing_confidence=avg_confidence,
                agent_name=primary_agent,
                include_detailed_metrics=include_detailed_evaluation
            )
            
            # Extract confidence from evaluation
            overall_confidence = evaluation_result.get("overall_confidence", avg_confidence)
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
            
            # Map agent type
            agent_type = AgentType.RESEARCH  # Default for multiple questions
            
            # Create ChatMessage for the response
            message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=combined_answer,
                agent_type=agent_type,
                metadata={
                    "questions_processed": len(questions),
                    "sources_count": len(unique_sources),
                    "confidence": overall_confidence,
                    "confidence_level": confidence_level_str,
                    "evaluation_method": evaluation_result.get("evaluation_method", "unknown"),
                    "multiple_questions": True
                }
            )
            
            # Create ChatResponse with evaluation data
            response = ChatResponse(
                session_id=session_id,
                message=message,
                agent_used=agent_type,
                sources=unique_sources,
                processing_time=processing_time,
                confidence=overall_confidence,
                confidence_level=confidence_level,
                confidence_explanation=confidence_explanation,
                evaluation=evaluation_metrics
            )
            
            logger.info(
                f"Processed {len(questions)} questions in {processing_time:.2f}s | "
                f"Confidence: {overall_confidence:.0%} ({confidence_level_str})"
            )
            
            return response
        
        # Single question - process normally
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
