"""
Coordinator Agent
Routes queries to appropriate specialist agents.
Optimized for LangGraph multi-agent orchestration.
Includes Opik observability for routing decisions and confidence tracking.
"""

from typing import Dict, Any, Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import logging
import time

from .base_agent import BaseAgent
from app.utils.observability import (
    log_agent_metrics,
    create_langchain_callbacks,
    is_opik_enabled
)

logger = logging.getLogger(__name__)


class RoutingDecision(BaseModel):
    """Structured output for routing decisions."""
    agents: List[str] = Field(
        description="List of agent names to invoke (it_policy, hr_policy, research)"
    )
    reasoning: str = Field(
        description="Brief explanation of why these agents were selected"
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1",
        ge=0.0,
        le=1.0,
        default=0.8
    )


class CoordinatorAgent(BaseAgent):
    """
    Coordinator agent that analyzes queries and routes to appropriate specialists.
    Acts as the orchestrator of the multi-agent system.
    Supports parallel routing to multiple agents.
    """
    
    SYSTEM_PROMPT = """You are a Coordinator Agent responsible for analyzing user queries 
and determining which specialist agent(s) should handle them.

Available specialist agents:
1. IT Policy Agent - Handles IT policies, security, infrastructure, software, hardware, network, cybersecurity
2. HR Policy Agent - Handles HR policies, benefits, leave, compensation, onboarding, performance reviews, workplace conduct
3. Research Agent - Handles general research queries that don't fit specific domains

Your task is to:
1. Analyze the user's query carefully
2. Determine which agent(s) are most appropriate (can be multiple agents for complex queries)
3. Provide a brief reasoning for your decision
4. Assign a confidence score (0-1) to your routing decision

Important:
- You can select MULTIPLE agents if the query spans multiple domains
- For queries clearly about one domain, select only that agent
- For ambiguous queries, default to the research agent
- Higher confidence (>0.8) for clear domain-specific queries
- Lower confidence (<0.5) for ambiguous queries

{format_instructions}
"""
    
    def __init__(self):
        """Initialize coordinator agent."""
        super().__init__(
            name="Coordinator",
            description="Routes queries to appropriate specialist agents",
            chroma_repo=None  # Coordinator doesn't need RAG
        )
        self.output_parser = PydanticOutputParser(pydantic_object=RoutingDecision)
    
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze query and determine which agents should handle it.
        Uses structured output for reliable parsing.
        Instrumented with Opik for observability.
        
        Args:
            query: User query
            context: Optional context
            
        Returns:
            Routing decision with agents and reasoning
        """
        logger.info(f"Coordinator analyzing query: {query[:100]}...")
        start_time = time.time()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", "{query}")
        ])
        
        # Get Opik callbacks for tracing
        callbacks = create_langchain_callbacks()
        chain = prompt | self.llm | self.output_parser
        
        try:
            config = {"callbacks": callbacks} if callbacks else {}
            routing_decision: RoutingDecision = await chain.ainvoke(
                {
                    "query": query,
                    "format_instructions": self.output_parser.get_format_instructions()
                },
                config=config
            )
            
            # Validate agents
            valid_agents = ["it_policy", "hr_policy", "research"]
            filtered_agents = [a for a in routing_decision.agents if a in valid_agents]
            
            # Default to research if no valid agents
            if not filtered_agents:
                filtered_agents = ["research"]
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Log observability metrics with confidence
            log_agent_metrics(
                agent_name=self.name,
                confidence=routing_decision.confidence,
                latency_ms=latency_ms,
                success=True
            )
            
            # Enhanced logging for confidence tracking
            confidence_level = (
                "HIGH" if routing_decision.confidence >= 0.8 
                else "MEDIUM" if routing_decision.confidence >= 0.5 
                else "LOW"
            )
            logger.info(
                f"[ROUTING] {filtered_agents} | "
                f"Confidence: {routing_decision.confidence:.0%} ({confidence_level}) | "
                f"Latency: {latency_ms:.0f}ms"
            )
            
            return {
                "agent": self.name,
                "agents_to_invoke": filtered_agents,
                "reasoning": routing_decision.reasoning,
                "confidence": routing_decision.confidence,
                "confidence_level": confidence_level,
                "latency_ms": latency_ms,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Coordinator error: {e}, attempting fallback parsing")
            
            # Fallback: try manual parsing
            try:
                prompt_fallback = ChatPromptTemplate.from_messages([
                    ("system", """You are a Coordinator Agent. Analyze the query and respond with:
AGENTS: [comma-separated list: it_policy, hr_policy, or research]
REASONING: [brief explanation]"""),
                    ("human", "{query}")
                ])
                
                chain_fallback = prompt_fallback | self.llm
                config = {"callbacks": callbacks} if callbacks else {}
                response = await chain_fallback.ainvoke({"query": query}, config=config)
                routing_decision = self._parse_routing_response(response.content)
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Log fallback metrics (lower confidence)
                log_agent_metrics(
                    agent_name=self.name,
                    confidence=0.5,
                    latency_ms=latency_ms,
                    success=True
                )
                
                logger.info(f"[ROUTING FALLBACK] {routing_decision['agents']} | Confidence: 50% (MEDIUM)")
                
                return {
                    "agent": self.name,
                    "agents_to_invoke": routing_decision["agents"],
                    "reasoning": routing_decision["reasoning"],
                    "confidence": 0.5,
                    "confidence_level": "MEDIUM",
                    "latency_ms": latency_ms,
                    "success": True
                }
            except Exception as fallback_error:
                logger.error(f"Coordinator fallback error: {fallback_error}")
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Log error metrics
                log_agent_metrics(
                    agent_name=self.name,
                    confidence=0.3,
                    latency_ms=latency_ms,
                    success=False,
                    error=str(e)
                )
                
                # Ultimate fallback: route to research agent
                return {
                    "agent": self.name,
                    "agents_to_invoke": ["research"],
                    "reasoning": "Error in routing, defaulting to research agent",
                    "confidence": 0.3,
                    "confidence_level": "LOW",
                    "latency_ms": latency_ms,
                    "success": False,
                    "error": str(e)
                }
    
    def _parse_routing_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM's routing response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed routing decision
        """
        agents = []
        reasoning = "No reasoning provided"
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("AGENTS:"):
                agent_str = line.replace("AGENTS:", "").strip()
                agents = [a.strip().lower() for a in agent_str.split(',')]
            
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
        
        # Validate agents
        valid_agents = ["it_policy", "hr_policy", "research"]
        agents = [a for a in agents if a in valid_agents]
        
        # Default to research if no valid agents
        if not agents:
            agents = ["research"]
        
        return {
            "agents": agents,
            "reasoning": reasoning
        }
    
    def should_invoke_multiple_agents(self, agents: List[str]) -> bool:
        """
        Determine if multiple agents should be invoked.
        
        Args:
            agents: List of agent names
            
        Returns:
            True if multiple agents needed
        """
        return len(agents) > 1

