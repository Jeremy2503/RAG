"""
Initialize ChromaDB collections.
Run this script once to set up the vector database collections.
"""
import logging
from app.repositories.chroma_repo import ChromaRepository

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_collections():
    """Initialize all ChromaDB collections."""
    try:
        logger.info("Initializing ChromaDB repository...")
        chroma_repo = ChromaRepository()
        
        logger.info("Creating collections...")
        
        # The ChromaRepository __init__ already creates collections
        # Just verify they exist
        collections = chroma_repo.client.list_collections()
        
        logger.info(f"Collections found: {[c.name for c in collections]}")
        
        # Verify each collection
        for collection_name in ["general", "hr_policy", "it_policy"]:
            try:
                collection = chroma_repo.client.get_collection(collection_name)
                count = collection.count()
                logger.info(f"  - {collection_name}: {count} documents")
            except Exception as e:
                logger.warning(f"  - {collection_name}: Not found or error - {e}")
        
        logger.info("ChromaDB initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing ChromaDB: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Initializing ChromaDB Collections")
    print("=" * 60)
    
    success = init_collections()
    
    print("\n" + "=" * 60)
    if success:
        print("SUCCESS - ChromaDB initialized")
        print("\nNext steps:")
        print("1. Upload documents via the Admin Dashboard")
        print("2. Or use the document API to add documents")
    else:
        print("FAILED - Check logs above for error details")
    print("=" * 60)

