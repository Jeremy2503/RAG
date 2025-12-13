"""
Evaluation Service
Comprehensive evaluation service for RAG responses using Opik metrics.
Provides real-time evaluation during chat and batch evaluation capabilities.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from app.utils.observability import (
    is_opik_enabled,
    get_opik_client,
    evaluate_rag_response,
    get_evaluation_metrics,
    EvaluationMetrics
)

logger = logging.getLogger(__name__)


class ResponseEvaluation:
    """
    Container for evaluation results of a single response.
    """
    
    def __init__(
        self,
        query: str,
        answer: str,
        context: List[str],
        sources_count: int = 0,
        routing_confidence: float = 0.5,
        agent_name: str = "Unknown"
    ):
        self.query = query
        self.answer = answer
        self.context = context
        self.sources_count = sources_count
        self.routing_confidence = routing_confidence
        self.agent_name = agent_name
        self.evaluation_results: Dict[str, Any] = {}
        self.evaluated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "query": self.query[:100] + "..." if len(self.query) > 100 else self.query,
            "agent_name": self.agent_name,
            "sources_count": self.sources_count,
            "routing_confidence": self.routing_confidence,
            "evaluation": self.evaluation_results,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None
        }


class EvaluationService:
    """
    Service for evaluating RAG responses.
    Supports both real-time evaluation during chat and batch evaluation.
    """
    
    def __init__(self):
        """Initialize evaluation service."""
        self.metrics = get_evaluation_metrics()
        self._opik_enabled = is_opik_enabled()
        
        if self._opik_enabled:
            logger.info("✅ Evaluation Service initialized with Opik metrics")
        else:
            logger.info("ℹ️ Evaluation Service initialized with heuristic metrics (Opik not available)")
    
    async def evaluate_response(
        self,
        query: str,
        answer: str,
        context: List[str],
        sources_count: int = 0,
        routing_confidence: float = 0.5,
        agent_name: str = "Unknown",
        include_detailed_metrics: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate a single RAG response.
        
        Args:
            query: User's question
            answer: Generated answer
            context: List of context strings used to generate the answer
            sources_count: Number of sources retrieved
            routing_confidence: Confidence from routing decision
            agent_name: Name of the agent that generated the response
            include_detailed_metrics: Whether to include all detailed metrics
            
        Returns:
            Evaluation results dictionary
        """
        start_time = datetime.utcnow()
        
        # Run evaluation
        evaluation = await evaluate_rag_response(
            query=query,
            answer=answer,
            context=context,
            routing_confidence=routing_confidence,
            sources_count=sources_count
        )
        
        # Build response
        result = {
            "agent_name": agent_name,
            "overall_confidence": evaluation.get("overall_confidence"),
            "quality_level": evaluation.get("quality_level", "UNKNOWN"),
            "evaluation_method": evaluation.get("evaluation_method", "unknown"),
            "evaluated_at": start_time.isoformat()
        }
        
        # Add detailed metrics if requested
        if include_detailed_metrics:
            result["detailed_metrics"] = {
                "hallucination_score": evaluation.get("hallucination_score"),
                "answer_relevance_score": evaluation.get("answer_relevance_score"),
                "context_recall_score": evaluation.get("context_recall_score"),
                "context_precision_score": evaluation.get("context_precision_score"),
                "routing_confidence": routing_confidence,
                "sources_count": sources_count
            }
            
            if "factors" in evaluation:
                result["detailed_metrics"]["heuristic_factors"] = evaluation["factors"]
        
        logger.info(
            f"[EVALUATION] {agent_name} | "
            f"Confidence: {result['overall_confidence']:.0%} ({result['quality_level']}) | "
            f"Method: {result['evaluation_method']}"
        )
        
        return result
    
    async def batch_evaluate(
        self,
        evaluations: List[ResponseEvaluation]
    ) -> Dict[str, Any]:
        """
        Batch evaluate multiple responses.
        
        Args:
            evaluations: List of ResponseEvaluation objects
            
        Returns:
            Batch evaluation results with summary statistics
        """
        start_time = datetime.utcnow()
        results = []
        
        # Process evaluations concurrently
        tasks = [
            self.evaluate_response(
                query=e.query,
                answer=e.answer,
                context=e.context,
                sources_count=e.sources_count,
                routing_confidence=e.routing_confidence,
                agent_name=e.agent_name,
                include_detailed_metrics=True
            )
            for e in evaluations
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle errors
        successful_results = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({
                    "index": i,
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        # Calculate summary statistics
        summary = self._calculate_summary(successful_results)
        
        return {
            "batch_size": len(evaluations),
            "successful": len(successful_results),
            "errors": len(errors),
            "error_details": errors if errors else None,
            "summary": summary,
            "results": successful_results,
            "evaluated_at": start_time.isoformat(),
            "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
        }
    
    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate summary statistics from evaluation results.
        
        Args:
            results: List of evaluation result dictionaries
            
        Returns:
            Summary statistics
        """
        if not results:
            return {
                "average_confidence": None,
                "quality_distribution": {},
                "evaluation_methods": {}
            }
        
        # Calculate averages
        confidences = [
            r.get("overall_confidence", 0) 
            for r in results 
            if r.get("overall_confidence") is not None
        ]
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else None
        
        # Count quality levels
        quality_distribution = {}
        for r in results:
            level = r.get("quality_level", "UNKNOWN")
            quality_distribution[level] = quality_distribution.get(level, 0) + 1
        
        # Count evaluation methods
        method_distribution = {}
        for r in results:
            method = r.get("evaluation_method", "unknown")
            method_distribution[method] = method_distribution.get(method, 0) + 1
        
        # Detailed metric averages (if available)
        detailed_averages = {}
        metric_keys = [
            "hallucination_score",
            "answer_relevance_score", 
            "context_recall_score",
            "context_precision_score"
        ]
        
        for key in metric_keys:
            values = [
                r.get("detailed_metrics", {}).get(key)
                for r in results
                if r.get("detailed_metrics", {}).get(key) is not None
            ]
            if values:
                detailed_averages[key] = sum(values) / len(values)
        
        return {
            "average_confidence": round(avg_confidence, 3) if avg_confidence else None,
            "quality_distribution": quality_distribution,
            "evaluation_methods": method_distribution,
            "detailed_averages": detailed_averages if detailed_averages else None,
            "total_evaluated": len(results)
        }
    
    def get_confidence_explanation(self, evaluation: Dict[str, Any]) -> str:
        """
        Generate a human-readable explanation of the confidence score.
        
        Args:
            evaluation: Evaluation result dictionary
            
        Returns:
            Human-readable explanation string
        """
        confidence = evaluation.get("overall_confidence")
        quality_level = evaluation.get("quality_level", "UNKNOWN")
        method = evaluation.get("evaluation_method", "unknown")
        
        if confidence is None:
            return "Unable to evaluate response confidence."
        
        explanations = {
            "HIGH": (
                f"This response has high confidence ({confidence:.0%}). "
                "The answer appears well-supported by the retrieved context and relevant to your question."
            ),
            "MEDIUM": (
                f"This response has moderate confidence ({confidence:.0%}). "
                "The answer is reasonably supported by context, but some aspects may need verification."
            ),
            "LOW": (
                f"This response has low confidence ({confidence:.0%}). "
                "The answer may not be fully supported by the available context. Consider reviewing the sources."
            ),
            "VERY_LOW": (
                f"This response has very low confidence ({confidence:.0%}). "
                "The answer should be verified against authoritative sources before use."
            )
        }
        
        base_explanation = explanations.get(quality_level, f"Confidence: {confidence:.0%}")
        
        # Add method-specific details
        if method == "opik":
            base_explanation += " (Evaluated using Opik AI metrics)"
        elif method == "heuristic":
            base_explanation += " (Evaluated using response characteristics)"
        
        return base_explanation
    
    def is_opik_available(self) -> bool:
        """Check if Opik metrics are available."""
        return self._opik_enabled


# Singleton instance
_evaluation_service: Optional[EvaluationService] = None


def get_evaluation_service() -> EvaluationService:
    """
    Get the global evaluation service instance.
    
    Returns:
        EvaluationService instance
    """
    global _evaluation_service
    if _evaluation_service is None:
        _evaluation_service = EvaluationService()
    return _evaluation_service

