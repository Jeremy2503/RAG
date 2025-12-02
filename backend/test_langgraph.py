"""
Test script for the LangGraph-based multi-agent system.
This script demonstrates the improved LangGraph implementation.
"""

import asyncio
import logging
from app.repositories.chroma_repo import ChromaRepository
from app.agents.graph_orchestrator import AgentOrchestrator
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_single_agent_query():
    """Test query that should route to a single agent."""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Single Agent Query (HR Policy)")
    logger.info("="*80)
    
    chroma_repo = ChromaRepository()
    orchestrator = AgentOrchestrator(chroma_repo)
    
    query = "What is the vacation policy for employees?"
    
    result = await orchestrator.process_query(
        query=query,
        user_id="test_user",
        session_id="test_session_1"
    )
    
    logger.info(f"\nQuery: {query}")
    logger.info(f"Primary Agent: {result['primary_agent']}")
    logger.info(f"Answer: {result['answer'][:200]}...")
    logger.info(f"Processing Time: {result['processing_time']:.2f}s")
    logger.info(f"Sources: {len(result['sources'])} documents")
    
    return result


async def test_multi_agent_query():
    """Test query that should route to multiple agents."""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Multi-Agent Query (HR + IT)")
    logger.info("="*80)
    
    chroma_repo = ChromaRepository()
    orchestrator = AgentOrchestrator(chroma_repo)
    
    query = "What are the policies for remote work access and work from home benefits?"
    
    result = await orchestrator.process_query(
        query=query,
        user_id="test_user",
        session_id="test_session_2"
    )
    
    logger.info(f"\nQuery: {query}")
    logger.info(f"Primary Agent: {result['primary_agent']}")
    logger.info(f"Answer: {result['answer'][:300]}...")
    logger.info(f"Processing Time: {result['processing_time']:.2f}s")
    logger.info(f"Sources: {len(result['sources'])} documents")
    
    return result


async def test_research_agent_query():
    """Test query that should route to research agent."""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Research Agent Query")
    logger.info("="*80)
    
    chroma_repo = ChromaRepository()
    orchestrator = AgentOrchestrator(chroma_repo)
    
    query = "What information is available in the uploaded documents?"
    
    result = await orchestrator.process_query(
        query=query,
        user_id="test_user",
        session_id="test_session_3"
    )
    
    logger.info(f"\nQuery: {query}")
    logger.info(f"Primary Agent: {result['primary_agent']}")
    logger.info(f"Answer: {result['answer'][:200]}...")
    logger.info(f"Processing Time: {result['processing_time']:.2f}s")
    logger.info(f"Sources: {len(result['sources'])} documents")
    
    return result


async def test_it_policy_query():
    """Test query that should route to IT policy agent."""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: IT Policy Agent Query")
    logger.info("="*80)
    
    chroma_repo = ChromaRepository()
    orchestrator = AgentOrchestrator(chroma_repo)
    
    query = "What are the password requirements and security policies?"
    
    result = await orchestrator.process_query(
        query=query,
        user_id="test_user",
        session_id="test_session_4"
    )
    
    logger.info(f"\nQuery: {query}")
    logger.info(f"Primary Agent: {result['primary_agent']}")
    logger.info(f"Answer: {result['answer'][:200]}...")
    logger.info(f"Processing Time: {result['processing_time']:.2f}s")
    logger.info(f"Sources: {len(result['sources'])} documents")
    
    return result


async def main():
    """Run all tests."""
    logger.info("="*80)
    logger.info("LANGGRAPH MULTI-AGENT SYSTEM TEST SUITE")
    logger.info("="*80)
    
    try:
        # Run all tests
        await test_single_agent_query()
        await test_multi_agent_query()
        await test_research_agent_query()
        await test_it_policy_query()
        
        logger.info("\n" + "="*80)
        logger.info("ALL TESTS COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())

