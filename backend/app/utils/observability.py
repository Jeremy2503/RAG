"""
Opik Observability Module
Provides LLM tracing, agent observability, confidence tracking, and evaluation metrics.
All traces and evaluations are logged to Opik projects for dashboard visibility.
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
import asyncio
import time
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Opik imports - will be None if not installed or not configured
_opik_available = False
_opik_client = None
_opik_tracer = None
_project_name = "multi-agent-rag"  # Default project name

# Evaluation metric classes
Hallucination = None
AnswerRelevance = None
ContextRecall = None
ContextPrecision = None
Moderation = None

try:
    import opik
    from opik import track, opik_context, Opik
    from opik.integrations.langchain import OpikTracer
    
    # Import evaluation metrics
    try:
        from opik.evaluation.metrics import (
            Hallucination as _Hallucination,
            AnswerRelevance as _AnswerRelevance,
            ContextRecall as _ContextRecall,
            ContextPrecision as _ContextPrecision,
            Moderation as _Moderation,
        )
        Hallucination = _Hallucination
        AnswerRelevance = _AnswerRelevance
        ContextRecall = _ContextRecall
        ContextPrecision = _ContextPrecision
        Moderation = _Moderation
        logger.info("Opik evaluation metrics loaded successfully")
    except ImportError as e:
        logger.warning(f"Opik evaluation metrics not available: {e}")
    
    _opik_available = True
except ImportError:
    logger.warning("Opik not installed. Agent observability will be disabled.")
    track = None
    opik_context = None
    OpikTracer = None
    Opik = None


def init_opik(
    api_key: Optional[str] = None, 
    workspace: Optional[str] = None,
    project_name: str = "multi-agent-rag"
) -> bool:
    """
    Initialize Opik for observability with project tracking.
    
    Args:
        api_key: Opik API key (uses env var if not provided)
        workspace: Opik workspace name
        project_name: Name of the project in Opik dashboard
        
    Returns:
        True if initialization successful, False otherwise
    """
    global _opik_client, _opik_tracer, _opik_available, _project_name
    
    if not _opik_available:
        logger.warning("Opik not available - observability disabled")
        return False
    
    _project_name = project_name
    
    try:
        # Configure Opik
        if api_key:
            opik.configure(api_key=api_key, workspace=workspace, use_local=False)
        else:
            # Will use OPIK_API_KEY env var
            opik.configure(use_local=False)
        
        # Create client for programmatic access
        _opik_client = Opik()
        
        # Create tracer for LangChain integration with project name
        _opik_tracer = OpikTracer(
            project_name=_project_name,
            tags=["multi-agent-rag", "production", "langchain"]
        )
        
        logger.info(f"✅ Opik observability initialized - Project: {_project_name}")
        logger.info(f"   View traces at: https://www.comet.com/opik")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Opik: {e}")
        _opik_available = False
        return False


def get_project_name() -> str:
    """Get the current Opik project name."""
    return _project_name


def get_opik_client() -> Optional["Opik"]:
    """
    Get the Opik client for programmatic access.
    
    Returns:
        Opik client instance or None if not available
    """
    return _opik_client


def get_opik_tracer() -> Optional["OpikTracer"]:
    """
    Get the Opik tracer for LangChain callbacks.
    
    Returns:
        OpikTracer instance or None if not available
    """
    return _opik_tracer


def is_opik_enabled() -> bool:
    """Check if Opik is available and configured."""
    return _opik_available and _opik_tracer is not None


def opik_track(
    name: str = None, 
    capture_input: bool = True, 
    capture_output: bool = True,
    tags: List[str] = None
):
    """
    Decorator for tracing functions with Opik.
    Falls back to no-op if Opik is not available.
    
    Args:
        name: Optional name for the trace
        capture_input: Whether to capture function inputs
        capture_output: Whether to capture function outputs
        tags: Optional list of tags for the trace
    """
    def decorator(func):
        if not _opik_available or not track:
            return func
        
        # Use Opik's track decorator with project
        return track(
            name=name or func.__name__,
            capture_input=capture_input,
            capture_output=capture_output,
            project_name=_project_name,
            tags=tags or []
        )(func)
    
    return decorator


class OpikProjectTracer:
    """
    Enhanced tracer that logs all operations to an Opik project.
    Use this for comprehensive tracing of RAG operations.
    """
    
    def __init__(self, operation_name: str, tags: List[str] = None):
        """
        Initialize a project tracer.
        
        Args:
            operation_name: Name of the operation being traced
            tags: Optional tags for categorization
        """
        self.operation_name = operation_name
        self.tags = tags or []
        self.trace_id = None
        self.span_id = None
        self._start_time = None
        self._metadata = {}
    
    async def __aenter__(self):
        self._start_time = time.time()
        
        if _opik_available and _opik_client:
            try:
                # Create a new trace in the project
                trace = _opik_client.trace(
                    name=self.operation_name,
                    project_name=_project_name,
                    tags=self.tags + ["async"]
                )
                self.trace_id = trace.id if hasattr(trace, 'id') else None
                logger.debug(f"Started Opik trace: {self.operation_name}")
            except Exception as e:
                logger.debug(f"Could not create Opik trace: {e}")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.time() - self._start_time) * 1000 if self._start_time else 0
        self._metadata["duration_ms"] = elapsed_ms
        
        if exc_type is not None:
            self._metadata["error"] = str(exc_val)
            self._metadata["status"] = "error"
        else:
            self._metadata["status"] = "success"
        
        # Log final metadata
        if _opik_client and self.trace_id:
            try:
                # End trace is handled automatically
                pass
            except Exception as e:
                logger.debug(f"Could not finalize trace: {e}")
    
    def log_input(self, input_data: Dict[str, Any]):
        """Log input data to the trace."""
        self._metadata["input"] = input_data
    
    def log_output(self, output_data: Dict[str, Any]):
        """Log output data to the trace."""
        self._metadata["output"] = output_data
    
    def log_metadata(self, key: str, value: Any):
        """Log arbitrary metadata."""
        self._metadata[key] = value
    
    def add_feedback_score(self, name: str, value: float, reason: str = None):
        """
        Add a feedback score to the current trace.
        This will appear in the Opik dashboard.
        
        Args:
            name: Score name (e.g., "confidence", "relevance")
            value: Score value (0-1)
            reason: Optional explanation
        """
        if _opik_client and self.trace_id:
            try:
                _opik_client.log_traces_feedback_scores(
                    project_name=_project_name,
                    trace_ids=[self.trace_id],
                    scores=[{
                        "name": name,
                        "value": value,
                        "reason": reason or ""
                    }]
                )
                logger.debug(f"Logged feedback score: {name}={value}")
            except Exception as e:
                logger.debug(f"Could not log feedback score: {e}")


def track_rag_query(
    query: str,
    user_id: str = None,
    session_id: str = None,
    tags: List[str] = None
):
    """
    Decorator to track a complete RAG query with full observability.
    
    Args:
        query: The user's query
        user_id: Optional user identifier
        session_id: Optional session identifier
        tags: Optional tags
    """
    def decorator(func):
        if not _opik_available or not track:
            return func
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create tracked function with project
            @track(
                name="rag_query",
                project_name=_project_name,
                tags=tags or ["rag", "query"],
                capture_input=True,
                capture_output=True
            )
            async def tracked_func():
                return await func(*args, **kwargs)
            
            result = await tracked_func()
            
            # Log additional scores if result has evaluation data
            if isinstance(result, dict) and _opik_client:
                try:
                    confidence = result.get("confidence")
                    if confidence is not None:
                        # Get current trace to add feedback
                        current_span = opik_context.get_current_span_data()
                        if current_span and hasattr(current_span, 'trace_id'):
                            _opik_client.log_traces_feedback_scores(
                                project_name=_project_name,
                                trace_ids=[current_span.trace_id],
                                scores=[
                                    {"name": "confidence", "value": confidence},
                                ]
                            )
                except Exception as e:
                    logger.debug(f"Could not log RAG feedback: {e}")
            
            return result
        
        return wrapper
    return decorator


class EvaluationMetrics:
    """
    Evaluation metrics for RAG responses using Opik.
    Provides confidence, relevance, and hallucination detection.
    All evaluations are logged to the Opik project.
    """
    
    def __init__(self):
        """Initialize evaluation metrics."""
        self._hallucination_metric = None
        self._answer_relevance_metric = None
        self._context_recall_metric = None
        self._context_precision_metric = None
        self._moderation_metric = None
        
        if Hallucination:
            try:
                self._hallucination_metric = Hallucination()
                logger.info("Hallucination metric initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Hallucination metric: {e}")
        
        if AnswerRelevance:
            try:
                self._answer_relevance_metric = AnswerRelevance()
                logger.info("AnswerRelevance metric initialized")
            except Exception as e:
                logger.warning(f"Could not initialize AnswerRelevance metric: {e}")
        
        if ContextRecall:
            try:
                self._context_recall_metric = ContextRecall()
                logger.info("ContextRecall metric initialized")
            except Exception as e:
                logger.warning(f"Could not initialize ContextRecall metric: {e}")
        
        if ContextPrecision:
            try:
                self._context_precision_metric = ContextPrecision()
                logger.info("ContextPrecision metric initialized")
            except Exception as e:
                logger.warning(f"Could not initialize ContextPrecision metric: {e}")
    
    async def evaluate_response(
        self,
        query: str,
        answer: str,
        context: List[str],
        expected_answer: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a RAG response for quality metrics.
        Results are logged to the Opik project.
        
        Args:
            query: The user's question
            answer: The generated answer
            context: List of context strings used to generate the answer
            expected_answer: Optional ground truth answer for comparison
            trace_id: Optional trace ID to associate scores with
            
        Returns:
            Dictionary containing evaluation scores
        """
        evaluation_results = {
            "evaluated_at": datetime.utcnow().isoformat(),
            "hallucination_score": None,
            "answer_relevance_score": None,
            "context_recall_score": None,
            "context_precision_score": None,
            "overall_confidence": None,
            "quality_level": "UNKNOWN"
        }
        
        # Run evaluations
        scores = []
        feedback_scores = []
        
        # Hallucination detection
        if self._hallucination_metric:
            try:
                result = self._hallucination_metric.score(
                    input=query,
                    output=answer,
                    context=context
                )
                evaluation_results["hallucination_score"] = result.value
                # Invert hallucination score (lower hallucination = higher quality)
                inverted = 1.0 - result.value if result.value is not None else 0.5
                scores.append(inverted)
                feedback_scores.append({
                    "name": "hallucination",
                    "value": result.value,
                    "reason": "Lower is better (0 = no hallucination)"
                })
                logger.debug(f"Hallucination score: {result.value}")
            except Exception as e:
                logger.warning(f"Hallucination evaluation failed: {e}")
        
        # Answer relevance
        if self._answer_relevance_metric:
            try:
                result = self._answer_relevance_metric.score(
                    input=query,
                    output=answer,
                    context=context
                )
                evaluation_results["answer_relevance_score"] = result.value
                if result.value is not None:
                    scores.append(result.value)
                    feedback_scores.append({
                        "name": "answer_relevance",
                        "value": result.value,
                        "reason": "How relevant the answer is to the question"
                    })
                logger.debug(f"Answer relevance score: {result.value}")
            except Exception as e:
                logger.warning(f"Answer relevance evaluation failed: {e}")
        
        # Context recall (requires expected answer)
        if self._context_recall_metric and expected_answer:
            try:
                result = self._context_recall_metric.score(
                    input=query,
                    output=answer,
                    context=context,
                    expected_output=expected_answer
                )
                evaluation_results["context_recall_score"] = result.value
                if result.value is not None:
                    scores.append(result.value)
                    feedback_scores.append({
                        "name": "context_recall",
                        "value": result.value,
                        "reason": "How well context covers the expected answer"
                    })
                logger.debug(f"Context recall score: {result.value}")
            except Exception as e:
                logger.warning(f"Context recall evaluation failed: {e}")
        
        # Context precision
        if self._context_precision_metric:
            try:
                result = self._context_precision_metric.score(
                    input=query,
                    output=answer,
                    context=context
                )
                evaluation_results["context_precision_score"] = result.value
                if result.value is not None:
                    scores.append(result.value)
                    feedback_scores.append({
                        "name": "context_precision",
                        "value": result.value,
                        "reason": "Precision of retrieved context"
                    })
                logger.debug(f"Context precision score: {result.value}")
            except Exception as e:
                logger.warning(f"Context precision evaluation failed: {e}")
        
        # Calculate overall confidence
        if scores:
            evaluation_results["overall_confidence"] = sum(scores) / len(scores)
            confidence = evaluation_results["overall_confidence"]
            
            if confidence >= 0.8:
                evaluation_results["quality_level"] = "HIGH"
            elif confidence >= 0.6:
                evaluation_results["quality_level"] = "MEDIUM"
            elif confidence >= 0.4:
                evaluation_results["quality_level"] = "LOW"
            else:
                evaluation_results["quality_level"] = "VERY_LOW"
            
            # Add overall confidence to feedback
            feedback_scores.append({
                "name": "overall_confidence",
                "value": confidence,
                "reason": f"Overall quality: {evaluation_results['quality_level']}"
            })
        
        # Log feedback scores to Opik project
        if _opik_client and feedback_scores:
            try:
                # Try to get current trace ID
                current_trace_id = trace_id
                if not current_trace_id and opik_context:
                    try:
                        span = opik_context.get_current_span_data()
                        if span and hasattr(span, 'trace_id'):
                            current_trace_id = span.trace_id
                    except:
                        pass
                
                if current_trace_id:
                    _opik_client.log_traces_feedback_scores(
                        project_name=_project_name,
                        trace_ids=[current_trace_id],
                        scores=feedback_scores
                    )
                    logger.info(f"Logged {len(feedback_scores)} evaluation scores to Opik")
            except Exception as e:
                logger.debug(f"Could not log evaluation scores to Opik: {e}")
        
        return evaluation_results
    
    def calculate_simple_confidence(
        self,
        answer: str,
        sources_count: int,
        has_context: bool,
        routing_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculate a simple confidence score based on response characteristics.
        Used as a fallback when Opik metrics are not available.
        
        Args:
            answer: The generated answer
            sources_count: Number of sources retrieved
            has_context: Whether context was available
            routing_confidence: Confidence from the routing decision
            
        Returns:
            Simple confidence metrics
        """
        scores = []
        
        # Factor 1: Routing confidence (30%)
        scores.append(("routing", routing_confidence, 0.30))
        
        # Factor 2: Sources availability (25%)
        if sources_count >= 3:
            source_score = 1.0
        elif sources_count >= 1:
            source_score = 0.7
        else:
            source_score = 0.2
        scores.append(("sources", source_score, 0.25))
        
        # Factor 3: Context availability (20%)
        context_score = 0.9 if has_context else 0.3
        scores.append(("context", context_score, 0.20))
        
        # Factor 4: Answer length/quality heuristic (25%)
        answer_len = len(answer) if answer else 0
        if answer_len > 200:
            length_score = 0.9
        elif answer_len > 100:
            length_score = 0.7
        elif answer_len > 50:
            length_score = 0.5
        else:
            length_score = 0.3
        scores.append(("answer_quality", length_score, 0.25))
        
        # Calculate weighted average
        total_confidence = sum(score * weight for _, score, weight in scores)
        
        # Determine confidence level
        if total_confidence >= 0.8:
            level = "HIGH"
        elif total_confidence >= 0.6:
            level = "MEDIUM"
        elif total_confidence >= 0.4:
            level = "LOW"
        else:
            level = "VERY_LOW"
        
        return {
            "overall_confidence": round(total_confidence, 3),
            "quality_level": level,
            "factors": {name: round(score, 3) for name, score, _ in scores},
            "evaluation_method": "heuristic"
        }


# Global evaluation metrics instance
_evaluation_metrics: Optional[EvaluationMetrics] = None


def get_evaluation_metrics() -> EvaluationMetrics:
    """
    Get the global evaluation metrics instance.
    Creates one if it doesn't exist.
    """
    global _evaluation_metrics
    if _evaluation_metrics is None:
        _evaluation_metrics = EvaluationMetrics()
    return _evaluation_metrics


class AgentTrace:
    """
    Context manager for tracing agent execution.
    Tracks agent name, query, confidence, and metadata.
    All data is logged to the Opik project.
    """
    
    def __init__(
        self,
        agent_name: str,
        query: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.agent_name = agent_name
        self.query = query
        self.metadata = metadata or {}
        self.trace = None
        self.trace_id = None
        self._span = None
        self._start_time = None
    
    async def __aenter__(self):
        self._start_time = time.time()
        
        if _opik_available and _opik_client:
            try:
                # Create a trace in the project
                self.trace = _opik_client.trace(
                    name=f"agent:{self.agent_name}",
                    project_name=_project_name,
                    input={"query": self.query[:500]},  # Truncate long queries
                    tags=["agent", self.agent_name.lower().replace(" ", "_")]
                )
                self.trace_id = self.trace.id if hasattr(self.trace, 'id') else None
                
                # Update metadata
                self.metadata.update({
                    "agent_name": self.agent_name,
                    "query_preview": self.query[:100] if self.query else "",
                    "start_time": datetime.utcnow().isoformat(),
                    "trace_id": self.trace_id
                })
                
                logger.debug(f"Started agent trace: {self.agent_name} (ID: {self.trace_id})")
                    
            except Exception as e:
                logger.debug(f"Could not start agent trace: {e}")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self._start_time if self._start_time else 0
        self.metadata["latency_ms"] = elapsed * 1000
        
        if exc_type is not None:
            self.metadata["error"] = str(exc_val)
            self.metadata["success"] = False
        else:
            self.metadata["success"] = True
        
        # End the trace
        if self.trace and hasattr(self.trace, 'end'):
            try:
                self.trace.end(output=self.metadata)
            except Exception as e:
                logger.debug(f"Could not end trace: {e}")
    
    def log_confidence(self, confidence: float):
        """Log confidence score for the agent's response."""
        self.metadata["confidence"] = confidence
        
        # Log to Opik as feedback score
        if _opik_client and self.trace_id:
            try:
                _opik_client.log_traces_feedback_scores(
                    project_name=_project_name,
                    trace_ids=[self.trace_id],
                    scores=[{
                        "name": "confidence",
                        "value": confidence,
                        "reason": f"Agent confidence: {confidence:.0%}"
                    }]
                )
            except Exception as e:
                logger.debug(f"Could not log confidence: {e}")
    
    def log_routing(self, agents: List[str], reasoning: str):
        """Log routing decision metadata."""
        self.metadata["routed_to_agents"] = agents
        self.metadata["routing_reasoning"] = reasoning
    
    def log_sources(self, source_count: int, sources: List[Dict[str, Any]]):
        """Log retrieved sources metadata."""
        self.metadata["source_count"] = source_count
        self.metadata["sources"] = [
            {
                "document_id": s.get("document_id", "unknown"),
                "chunk_index": s.get("chunk_index", 0),
                "relevance_score": s.get("distance", 0)
            }
            for s in sources[:5]  # Limit to first 5 for brevity
        ]
        
        # Log sources count as feedback
        if _opik_client and self.trace_id:
            try:
                _opik_client.log_traces_feedback_scores(
                    project_name=_project_name,
                    trace_ids=[self.trace_id],
                    scores=[{
                        "name": "sources_retrieved",
                        "value": min(source_count / 5.0, 1.0),  # Normalize to 0-1
                        "reason": f"Retrieved {source_count} sources"
                    }]
                )
            except Exception as e:
                logger.debug(f"Could not log sources: {e}")
    
    def log_evaluation(self, evaluation_results: Dict[str, Any]):
        """Log evaluation metrics."""
        self.metadata["evaluation"] = evaluation_results
    
    def log_error(self, error: str):
        """Log error information."""
        self.metadata["error"] = error
        self.metadata["success"] = False


def traced_agent(agent_name: str, tags: List[str] = None):
    """
    Decorator for tracing agent methods with Opik project logging.
    Automatically logs execution time, inputs, outputs, and errors.
    
    Args:
        agent_name: Name of the agent for tracing
        tags: Optional tags for the trace
        
    Usage:
        @traced_agent("IT Policy Agent")
        async def process(self, query: str) -> Dict[str, Any]:
            ...
    """
    def decorator(func):
        if not _opik_available or not track:
            return func
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract query from args/kwargs
            query = kwargs.get('query', args[1] if len(args) > 1 else 'unknown')
            
            try:
                # Use Opik track decorator with project
                @track(
                    name=f"{agent_name}::process",
                    project_name=_project_name,
                    tags=tags or ["agent", agent_name.lower().replace(" ", "_")],
                    capture_input=True,
                    capture_output=True
                )
                async def tracked_call():
                    return await func(*args, **kwargs)
                
                result = await tracked_call()
                
                # Log additional feedback scores if available
                if isinstance(result, dict) and _opik_client:
                    try:
                        confidence = result.get('confidence', None)
                        if confidence is not None:
                            # Get trace ID and log feedback
                            span = opik_context.get_current_span_data()
                            if span and hasattr(span, 'trace_id'):
                                _opik_client.log_traces_feedback_scores(
                                    project_name=_project_name,
                                    trace_ids=[span.trace_id],
                                    scores=[{
                                        "name": "confidence",
                                        "value": confidence,
                                        "reason": f"Agent: {agent_name}"
                                    }]
                                )
                            logger.info(f"[OPIK] {agent_name} confidence: {confidence:.2%}")
                    except Exception as e:
                        logger.debug(f"Could not log agent feedback: {e}")
                
                return result
                
            except Exception as e:
                logger.error(f"[OPIK] {agent_name} error: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def log_agent_metrics(
    agent_name: str,
    confidence: Optional[float] = None,
    latency_ms: Optional[float] = None,
    token_usage: Optional[Dict[str, int]] = None,
    sources_retrieved: Optional[int] = None,
    success: bool = True,
    error: Optional[str] = None,
    evaluation: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None
):
    """
    Log agent performance metrics to Opik project.
    
    Args:
        agent_name: Name of the agent
        confidence: Confidence score (0-1)
        latency_ms: Response latency in milliseconds
        token_usage: Token usage dict with prompt/completion tokens
        sources_retrieved: Number of RAG sources retrieved
        success: Whether the operation succeeded
        error: Error message if failed
        evaluation: Evaluation metrics from Opik
        trace_id: Optional trace ID to log against
    """
    metrics = {
        "agent_name": agent_name,
        "success": success,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    feedback_scores = []
    
    if confidence is not None:
        metrics["confidence"] = confidence
        metrics["confidence_level"] = (
            "HIGH" if confidence >= 0.8 
            else "MEDIUM" if confidence >= 0.5 
            else "LOW"
        )
        feedback_scores.append({
            "name": "confidence",
            "value": confidence,
            "reason": f"{agent_name}: {metrics['confidence_level']}"
        })
    
    if latency_ms is not None:
        metrics["latency_ms"] = latency_ms
        # Normalize latency (assume 5000ms is bad, 500ms is good)
        latency_score = max(0, min(1, 1 - (latency_ms / 5000)))
        feedback_scores.append({
            "name": "latency_score",
            "value": latency_score,
            "reason": f"Response time: {latency_ms:.0f}ms"
        })
    
    if token_usage:
        metrics["prompt_tokens"] = token_usage.get("prompt_tokens", 0)
        metrics["completion_tokens"] = token_usage.get("completion_tokens", 0)
        metrics["total_tokens"] = token_usage.get("total_tokens", 0)
    
    if sources_retrieved is not None:
        metrics["sources_retrieved"] = sources_retrieved
        # Normalize sources (0-5 is good range)
        sources_score = min(sources_retrieved / 5.0, 1.0)
        feedback_scores.append({
            "name": "sources_retrieved",
            "value": sources_score,
            "reason": f"Retrieved {sources_retrieved} sources"
        })
    
    if error:
        metrics["error"] = error
    
    if evaluation:
        metrics["evaluation"] = evaluation
    
    # Log locally
    logger.info(f"[AGENT_METRICS] {agent_name}: confidence={confidence}, latency={latency_ms}ms, sources={sources_retrieved}")
    
    # Log feedback scores to Opik project
    if _opik_client and feedback_scores:
        try:
            # Get trace ID
            current_trace_id = trace_id
            if not current_trace_id and opik_context:
                try:
                    span = opik_context.get_current_span_data()
                    if span and hasattr(span, 'trace_id'):
                        current_trace_id = span.trace_id
                except:
                    pass
            
            if current_trace_id:
                _opik_client.log_traces_feedback_scores(
                    project_name=_project_name,
                    trace_ids=[current_trace_id],
                    scores=feedback_scores
                )
                logger.debug(f"Logged {len(feedback_scores)} metrics to Opik project: {_project_name}")
        except Exception as e:
            logger.debug(f"Could not log metrics to Opik: {e}")
    
    return metrics


def create_langchain_callbacks() -> List:
    """
    Create LangChain callback handlers including Opik tracer.
    The tracer is configured with the project name.
    
    Returns:
        List of callback handlers for LangChain
    """
    callbacks = []
    
    if _opik_tracer:
        callbacks.append(_opik_tracer)
    
    return callbacks


async def evaluate_rag_response(
    query: str,
    answer: str,
    context: List[str],
    routing_confidence: float = 0.5,
    sources_count: int = 0,
    expected_answer: Optional[str] = None,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to evaluate a RAG response.
    Uses Opik metrics if available, falls back to heuristics.
    Results are logged to the Opik project.
    
    Args:
        query: User query
        answer: Generated answer
        context: List of context strings
        routing_confidence: Confidence from routing decision
        sources_count: Number of sources retrieved
        expected_answer: Optional ground truth for comparison
        trace_id: Optional trace ID for logging
        
    Returns:
        Evaluation results
    """
    metrics = get_evaluation_metrics()
    
    # Try Opik-based evaluation first
    if _opik_available and (Hallucination or AnswerRelevance):
        try:
            evaluation = await metrics.evaluate_response(
                query=query,
                answer=answer,
                context=context,
                expected_answer=expected_answer,
                trace_id=trace_id
            )
            evaluation["evaluation_method"] = "opik"
            return evaluation
        except Exception as e:
            logger.warning(f"Opik evaluation failed, using heuristics: {e}")
    
    # Fall back to simple heuristic evaluation
    return metrics.calculate_simple_confidence(
        answer=answer,
        sources_count=sources_count,
        has_context=bool(context),
        routing_confidence=routing_confidence
    )


def log_trace_to_project(
    name: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    feedback_scores: List[Dict[str, Any]] = None,
    tags: List[str] = None,
    duration_ms: float = None
) -> Optional[str]:
    """
    Log a complete trace to the Opik project.
    Use this for custom operations not covered by decorators.
    
    Args:
        name: Name of the operation
        input_data: Input data dictionary
        output_data: Output data dictionary
        feedback_scores: List of feedback scores
        tags: Tags for the trace
        duration_ms: Duration in milliseconds
        
    Returns:
        Trace ID if successful
    """
    if not _opik_client:
        return None
    
    try:
        # Create and complete trace
        trace = _opik_client.trace(
            name=name,
            project_name=_project_name,
            input=input_data,
            output=output_data,
            tags=tags or []
        )
        
        trace_id = trace.id if hasattr(trace, 'id') else None
        
        # Log feedback scores
        if trace_id and feedback_scores:
            _opik_client.log_traces_feedback_scores(
                project_name=_project_name,
                trace_ids=[trace_id],
                scores=feedback_scores
            )
        
        # End trace
        if hasattr(trace, 'end'):
            trace.end()
        
        logger.debug(f"Logged trace to Opik project: {name} (ID: {trace_id})")
        return trace_id
        
    except Exception as e:
        logger.warning(f"Could not log trace to Opik: {e}")
        return None


# Export commonly used items
__all__ = [
    "init_opik",
    "get_project_name",
    "get_opik_client",
    "get_opik_tracer",
    "is_opik_enabled",
    "opik_track",
    "OpikProjectTracer",
    "track_rag_query",
    "AgentTrace",
    "traced_agent",
    "log_agent_metrics",
    "create_langchain_callbacks",
    "EvaluationMetrics",
    "get_evaluation_metrics",
    "evaluate_rag_response",
    "log_trace_to_project",
]
