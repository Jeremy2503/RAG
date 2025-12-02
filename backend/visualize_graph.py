"""
Visualize the LangGraph workflow.
This script generates a visual representation of the agent orchestration graph.
"""

from app.repositories.chroma_repo import ChromaRepository
from app.agents.graph_orchestrator import AgentOrchestrator


def visualize_graph():
    """Generate and display the graph structure."""
    print("="*80)
    print("LANGGRAPH MULTI-AGENT WORKFLOW VISUALIZATION")
    print("="*80)
    
    # Initialize orchestrator
    chroma_repo = ChromaRepository()
    orchestrator = AgentOrchestrator(chroma_repo)
    
    # Get the compiled graph
    graph = orchestrator.graph
    
    print("\n📊 Graph Structure:\n")
    print("Nodes:")
    print("  1. START (entry point)")
    print("  2. coordinator - Routes query to appropriate agents")
    print("  3. execute_agents - Executes selected agents in parallel")
    print("  4. research - Research Agent (fallback)")
    print("  5. it_policy - IT Policy Agent")
    print("  6. hr_policy - HR Policy Agent")
    print("  7. synthesize - Combines agent responses")
    print("  8. END (exit point)")
    
    print("\n🔀 Edges (Flow):")
    print("  START → coordinator")
    print("  coordinator → execute_agents")
    print("  execute_agents → synthesize")
    print("  synthesize → END")
    
    print("\n⚡ Features:")
    print("  • Parallel Agent Execution")
    print("  • State Reducers for Response Accumulation")
    print("  • LLM-based Response Synthesis")
    print("  • Structured Routing Decisions")
    print("  • Confidence Scoring")
    
    print("\n📦 State Schema:")
    print("  {")
    print("    query: str,")
    print("    user_id: str,")
    print("    session_id: str,")
    print("    routing_decision: Dict,")
    print("    agents_to_invoke: List[str],")
    print("    agent_responses: List[Dict] (with reducer),")
    print("    final_answer: str,")
    print("    primary_agent: str,")
    print("    sources: List[Dict],")
    print("    processing_time: float,")
    print("    start_time: float,")
    print("    error: str")
    print("  }")
    
    print("\n" + "="*80)
    print("Graph visualization complete!")
    print("="*80)
    
    # Try to generate a mermaid diagram
    print("\n🎨 Mermaid Diagram (copy to https://mermaid.live):\n")
    mermaid = """
graph TD
    START([START]) --> coordinator[Coordinator Agent]
    coordinator -->|Routing Decision| execute_agents[Execute Agents Parallel]
    
    execute_agents -.->|Invoke if selected| research[Research Agent]
    execute_agents -.->|Invoke if selected| it_policy[IT Policy Agent]
    execute_agents -.->|Invoke if selected| hr_policy[HR Policy Agent]
    
    research -.->|Response| execute_agents
    it_policy -.->|Response| execute_agents
    hr_policy -.->|Response| execute_agents
    
    execute_agents -->|All Responses| synthesize[Synthesize Node]
    synthesize --> END([END])
    
    style START fill:#90EE90
    style END fill:#FFB6C1
    style coordinator fill:#87CEEB
    style execute_agents fill:#FFD700
    style synthesize fill:#DDA0DD
    style research fill:#F0E68C
    style it_policy fill:#F0E68C
    style hr_policy fill:#F0E68C
"""
    print(mermaid)


if __name__ == "__main__":
    visualize_graph()

