"""
LangGraph Agent Orchestrator
Coordinates multi-agent workflow using LangGraph for state management.
Implements proper parallel agent execution and state reducers.
"""

from typing import Dict, Any, List, TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import BaseMessage
import logging
import asyncio
from datetime import datetime
import operator

from .coordinator_agent import CoordinatorAgent
from .research_agent import ResearchAgent
from .it_policy_agent import ITPolicyAgent
from .hr_policy_agent import HRPolicyAgent
from app.repositories.chroma_repo import ChromaRepository

logger = logging.getLogger(__name__)


def reduce_agent_responses(left: List[Dict[str, Any]], right: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Reducer function to append agent responses."""
    if not left:
        return right
    if not right:
        return left
    return left + right


class AgentState(TypedDict):
    """
    State object passed between agents in the graph.
    Uses Annotated types with reducers for proper state management.
    """
    query: str
    user_id: str
    session_id: str
    
    # Coordinator output
    routing_decision: Dict[str, Any]
    agents_to_invoke: List[str]
    
    # Specialist agent outputs - use reducer to append responses
    agent_responses: Annotated[List[Dict[str, Any]], reduce_agent_responses]
    
    # Final output
    final_answer: str
    primary_agent: str
    sources: List[Dict[str, Any]]
    
    # Metadata
    processing_time: float
    start_time: float
    error: str


class AgentOrchestrator:
    """
    Orchestrates the multi-agent workflow using LangGraph.
    Manages state transitions and agent coordination.
    """
    
    def __init__(self, chroma_repo: ChromaRepository):
        """
        Initialize the agent orchestrator.
        
        Args:
            chroma_repo: ChromaDB repository for RAG
        """
        self.chroma_repo = chroma_repo
        
        # Initialize agents
        self.coordinator = CoordinatorAgent()
        self.research_agent = ResearchAgent(chroma_repo)
        self.it_agent = ITPolicyAgent(chroma_repo)
        self.hr_agent = HRPolicyAgent(chroma_repo)
        
        # Build the workflow graph
        self.graph = self._build_graph()
        
        logger.info("Agent Orchestrator initialized")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow with parallel agent execution support.
        
        Returns:
            Compiled state graph
        """
        # Create workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes (agent functions)
        workflow.add_node("coordinator", self._coordinator_node)
        workflow.add_node("research", self._research_node)
        workflow.add_node("it_policy", self._it_policy_node)
        workflow.add_node("hr_policy", self._hr_policy_node)
        workflow.add_node("execute_agents", self._execute_agents_node)
        workflow.add_node("synthesize", self._synthesize_node)
        
        # Set entry point
        workflow.add_edge(START, "coordinator")
        
        # Coordinator routes to execute_agents node which handles parallel execution
        workflow.add_edge("coordinator", "execute_agents")
        
        # Execute agents node invokes the appropriate agents in parallel
        workflow.add_edge("execute_agents", "synthesize")
        
        # Synthesis is the end
        workflow.add_edge("synthesize", END)
        
        # Compile the graph
        return workflow.compile()
    
    async def _coordinator_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Coordinator node: routes query to appropriate agents.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with routing decision
        """
        logger.info("Executing Coordinator node")
        
        routing = await self.coordinator.process(state["query"])
        
        return {
            "routing_decision": routing,
            "agents_to_invoke": routing.get("agents_to_invoke", ["research"])
        }
    
    async def _execute_agents_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the selected agents in parallel.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with agent responses
        """
        agents_to_invoke = state.get("agents_to_invoke", ["research"])
        logger.info(f"Executing agents in parallel: {agents_to_invoke}")
        
        # Create tasks for parallel execution
        tasks = []
        for agent_name in agents_to_invoke:
            if agent_name == "research":
                tasks.append(self.research_agent.process(state["query"]))
            elif agent_name == "it_policy":
                tasks.append(self.it_agent.process(state["query"]))
            elif agent_name == "hr_policy":
                tasks.append(self.hr_agent.process(state["query"]))
        
        # Execute all agents in parallel
        if tasks:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and collect valid responses
            valid_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.error(f"Agent {agents_to_invoke[i]} failed: {response}")
                else:
                    valid_responses.append(response)
            
            return {"agent_responses": valid_responses}
        
        return {"agent_responses": []}
    
    async def _research_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Research agent node (kept for potential direct invocation).
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with research response
        """
        logger.info("Executing Research Agent node")
        
        response = await self.research_agent.process(state["query"])
        
        return {"agent_responses": [response]}
    
    async def _it_policy_node(self, state: AgentState) -> Dict[str, Any]:
        """
        IT Policy agent node (kept for potential direct invocation).
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with IT policy response
        """
        logger.info("Executing IT Policy Agent node")
        
        response = await self.it_agent.process(state["query"])
        
        return {"agent_responses": [response]}
    
    async def _hr_policy_node(self, state: AgentState) -> Dict[str, Any]:
        """
        HR Policy agent node (kept for potential direct invocation).
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with HR policy response
        """
        logger.info("Executing HR Policy Agent node")
        
        response = await self.hr_agent.process(state["query"])
        
        return {"agent_responses": [response]}
    
    async def _synthesize_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Synthesis node: combines responses from multiple agents.
        
        Args:
            state: Current agent state
            
        Returns:
            Final state with synthesized answer
        """
        logger.info("Executing Synthesis node")
        
        agent_responses = state.get("agent_responses", [])
        
        if not agent_responses:
            return {
                "final_answer": "I apologize, but I couldn't generate a response.",
                "primary_agent": "None",
                "sources": [],
                "processing_time": datetime.now().timestamp() - state.get("start_time", datetime.now().timestamp())
            }
        
        # If only one agent responded, use its answer directly
        if len(agent_responses) == 1:
            response = agent_responses[0]
            return {
                "final_answer": response.get("answer", "No answer provided"),
                "primary_agent": response.get("agent", "Unknown"),
                "sources": response.get("sources", []),
                "processing_time": datetime.now().timestamp() - state.get("start_time", datetime.now().timestamp())
            }
        
        else:
            # Multiple agents: synthesize their responses using LLM
            synthesized = await self._llm_synthesis(state["query"], agent_responses)
            return {
                "final_answer": synthesized["answer"],
                "primary_agent": "Multiple Agents",
                "sources": synthesized["sources"],
                "processing_time": datetime.now().timestamp() - state.get("start_time", datetime.now().timestamp())
            }
    
    async def _llm_synthesis(self, query: str, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use LLM to synthesize multiple agent responses into a coherent answer.
        
        Args:
            query: Original user query
            responses: List of agent responses
            
        Returns:
            Synthesized response
        """
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
        from app.config import settings
        
        all_sources = []
        agent_answers = []
        
        for response in responses:
            agent_name = response.get("agent", "Unknown")
            answer = response.get("answer", "No answer")
            sources = response.get("sources", [])
            
            agent_answers.append(f"**{agent_name}:**\n{answer}")
            all_sources.extend(sources)
        
        # Prepare synthesis prompt
        synthesis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at synthesizing information from multiple sources.
Your task is to combine the following responses from different specialized agents into a single, 
coherent, and comprehensive answer to the user's question.

Guidelines:
1. Integrate information from all agents naturally
2. Remove redundancies
3. Maintain accuracy - don't add information not present in the responses
4. Structure the answer logically
5. Keep the tone professional and helpful"""),
            ("human", """User Question: {query}

Agent Responses:
{agent_responses}

Please provide a synthesized answer that combines the insights from all agents:""")
        ])
        
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            openai_api_key=settings.openai_api_key
        )
        
        chain = synthesis_prompt | llm
        
        try:
            result = await chain.ainvoke({
                "query": query,
                "agent_responses": "\n\n".join(agent_answers)
            })
            
            return {
                "answer": result.content,
                "sources": all_sources
            }
        except Exception as e:
            logger.error(f"Error in LLM synthesis: {e}")
            # Fallback to simple concatenation
            return {
                "answer": "\n\n".join(agent_answers),
                "sources": all_sources
            }
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent workflow.
        
        Args:
            query: User query
            user_id: User ID
            session_id: Chat session ID
            
        Returns:
            Final response with answer and metadata
        """
        logger.info(f"Processing query: {query[:100]}...")
        
        # Initialize state
        initial_state: AgentState = {
            "query": query,
            "user_id": user_id,
            "session_id": session_id,
            "routing_decision": {},
            "agents_to_invoke": [],
            "agent_responses": [],
            "final_answer": "",
            "primary_agent": "",
            "sources": [],
            "processing_time": 0.0,
            "start_time": datetime.now().timestamp(),
            "error": ""
        }
        
        try:
            # Execute the graph
            final_state = await self.graph.ainvoke(initial_state)
            
            logger.info("Query processing completed successfully")
            
            return {
                "answer": final_state.get("final_answer", "No answer generated"),
                "primary_agent": final_state.get("primary_agent", "Unknown"),
                "sources": final_state.get("sources", []),
                "processing_time": final_state.get("processing_time", 0.0),
                "routing_decision": final_state.get("routing_decision", {}),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            
            return {
                "answer": f"I apologize, but an error occurred while processing your query: {str(e)}",
                "primary_agent": "Error",
                "sources": [],
                "processing_time": 0.0,
                "routing_decision": {},
                "success": False,
                "error": str(e)
            }

