"""
Evaluation API Endpoints
Provides endpoints for response evaluation and batch evaluation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from app.models.user import User
from app.api.auth import get_current_user
from app.services.evaluation_service import (
    get_evaluation_service,
    EvaluationService,
    ResponseEvaluation
)
from app.utils.observability import is_opik_enabled

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class EvaluateRequestModel(BaseModel):
    """Request model for single response evaluation."""
    query: str = Field(..., min_length=1, max_length=5000, description="The user's question")
    answer: str = Field(..., min_length=1, description="The generated answer")
    context: List[str] = Field(default_factory=list, description="Context strings used")
    sources_count: int = Field(default=0, ge=0, description="Number of sources retrieved")
    routing_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Routing confidence")
    agent_name: str = Field(default="Unknown", description="Name of the agent")


class BatchEvaluateRequestModel(BaseModel):
    """Request model for batch evaluation."""
    evaluations: List[EvaluateRequestModel] = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="List of responses to evaluate"
    )


class EvaluationResponseModel(BaseModel):
    """Response model for evaluation results."""
    agent_name: str
    overall_confidence: Optional[float]
    quality_level: str
    evaluation_method: str
    evaluated_at: str
    detailed_metrics: Optional[Dict[str, Any]] = None
    confidence_explanation: Optional[str] = None


class BatchEvaluationResponseModel(BaseModel):
    """Response model for batch evaluation results."""
    batch_size: int
    successful: int
    errors: int
    error_details: Optional[List[Dict[str, Any]]]
    summary: Dict[str, Any]
    results: List[Dict[str, Any]]
    evaluated_at: str
    duration_ms: float


class EvaluationStatusModel(BaseModel):
    """Status of the evaluation service."""
    enabled: bool
    provider: str
    available_metrics: List[str]


# Dependencies
def get_eval_service() -> EvaluationService:
    """Get evaluation service instance."""
    return get_evaluation_service()


# Endpoints
@router.get("/status", response_model=EvaluationStatusModel)
async def get_evaluation_status(
    current_user: User = Depends(get_current_user)
) -> EvaluationStatusModel:
    """
    Get the status of the evaluation service.
    
    Returns:
        Evaluation service status including available metrics
    """
    opik_enabled = is_opik_enabled()
    
    if opik_enabled:
        metrics = [
            "hallucination_detection",
            "answer_relevance",
            "context_recall",
            "context_precision",
            "overall_confidence"
        ]
        provider = "Opik"
    else:
        metrics = [
            "routing_confidence",
            "source_availability",
            "context_availability",
            "answer_quality_heuristic",
            "overall_confidence"
        ]
        provider = "Heuristic"
    
    return EvaluationStatusModel(
        enabled=True,
        provider=provider,
        available_metrics=metrics
    )


@router.post("/evaluate", response_model=EvaluationResponseModel)
async def evaluate_response(
    request: EvaluateRequestModel,
    current_user: User = Depends(get_current_user),
    eval_service: EvaluationService = Depends(get_eval_service)
) -> Dict[str, Any]:
    """
    Evaluate a single RAG response.
    
    Args:
        request: Evaluation request with query, answer, and context
        current_user: Authenticated user
        eval_service: Evaluation service
        
    Returns:
        Evaluation results with confidence and quality metrics
    """
    try:
        result = await eval_service.evaluate_response(
            query=request.query,
            answer=request.answer,
            context=request.context,
            sources_count=request.sources_count,
            routing_confidence=request.routing_confidence,
            agent_name=request.agent_name,
            include_detailed_metrics=True
        )
        
        # Add confidence explanation
        result["confidence_explanation"] = eval_service.get_confidence_explanation(result)
        
        logger.info(f"Evaluated response for user {current_user.email}: {result['quality_level']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Evaluation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.post("/batch", response_model=BatchEvaluationResponseModel)
async def batch_evaluate(
    request: BatchEvaluateRequestModel,
    current_user: User = Depends(get_current_user),
    eval_service: EvaluationService = Depends(get_eval_service)
) -> Dict[str, Any]:
    """
    Evaluate multiple RAG responses in batch.
    
    Args:
        request: Batch evaluation request
        current_user: Authenticated user
        eval_service: Evaluation service
        
    Returns:
        Batch evaluation results with summary statistics
    """
    try:
        # Convert request models to ResponseEvaluation objects
        evaluations = [
            ResponseEvaluation(
                query=e.query,
                answer=e.answer,
                context=e.context,
                sources_count=e.sources_count,
                routing_confidence=e.routing_confidence,
                agent_name=e.agent_name
            )
            for e in request.evaluations
        ]
        
        result = await eval_service.batch_evaluate(evaluations)
        
        logger.info(
            f"Batch evaluation for user {current_user.email}: "
            f"{result['successful']}/{result['batch_size']} successful"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Batch evaluation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch evaluation failed: {str(e)}"
        )


@router.get("/explain/{confidence_level}")
async def explain_confidence_level(
    confidence_level: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get an explanation of what a confidence level means.
    
    Args:
        confidence_level: The confidence level (HIGH, MEDIUM, LOW, VERY_LOW)
        current_user: Authenticated user
        
    Returns:
        Explanation of the confidence level
    """
    explanations = {
        "HIGH": {
            "level": "HIGH",
            "range": "80-100%",
            "description": "The response is well-supported by the retrieved context and highly relevant to the question.",
            "recommendation": "This response can be trusted for most use cases.",
            "factors": [
                "Strong match between question and retrieved documents",
                "Answer is directly supported by context",
                "Low risk of hallucination"
            ]
        },
        "MEDIUM": {
            "level": "MEDIUM",
            "range": "60-79%",
            "description": "The response is reasonably supported but may have some gaps or less certain elements.",
            "recommendation": "Consider reviewing the source documents for critical decisions.",
            "factors": [
                "Moderate match between question and documents",
                "Some parts of answer may need verification",
                "Context covers most but not all aspects"
            ]
        },
        "LOW": {
            "level": "LOW",
            "range": "40-59%",
            "description": "The response may not be fully supported by the available context.",
            "recommendation": "Verify this response against authoritative sources before use.",
            "factors": [
                "Limited relevant documents found",
                "Answer may include inferences beyond context",
                "Higher uncertainty in response accuracy"
            ]
        },
        "VERY_LOW": {
            "level": "VERY_LOW",
            "range": "0-39%",
            "description": "The response has very limited support from retrieved documents.",
            "recommendation": "This response should be independently verified before any use.",
            "factors": [
                "Few or no relevant documents found",
                "High risk of inaccurate information",
                "Consider rephrasing the question or uploading relevant documents"
            ]
        }
    }
    
    level_upper = confidence_level.upper()
    
    if level_upper not in explanations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown confidence level. Valid levels: {list(explanations.keys())}"
        )
    
    return explanations[level_upper]

