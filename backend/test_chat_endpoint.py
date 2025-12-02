"""
Quick test script to diagnose the chat endpoint issue.
"""
import asyncio
import logging
from app.repositories.chroma_repo import ChromaRepository
from app.agents.graph_orchestrator import AgentOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_orchestrator():
    """Test the orchestrator directly."""
    try:
        logger.info("Initializing ChromaDB...")
        chroma_repo = ChromaRepository()
        
        logger.info("Initializing Orchestrator...")
        orchestrator = AgentOrchestrator(chroma_repo)
        
        logger.info("Processing test query...")
        result = await orchestrator.process_query(
            query="What is the vacation policy?",
            user_id="test_user",
            session_id="test_session"
        )
        
        logger.info(f"✅ Success! Result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Chat Orchestrator")
    print("=" * 60)
    
    result = asyncio.run(test_orchestrator())
    
    print("\n" + "=" * 60)
    if result:
        print("✅ TEST PASSED")
        print(f"Answer: {result.get('answer', 'No answer')}")
    else:
        print("❌ TEST FAILED - Check logs above for error details")
    print("=" * 60)

