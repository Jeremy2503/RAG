"""
FastAPI Main Application
Entry point for the Multi-Agent RAG Platform backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.api import api_router
from app.repositories.mongodb_repo import get_mongodb_repo
from app.repositories.chroma_repo import get_chroma_repo

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting Multi-Agent RAG Platform...")
    
    try:
        # Initialize MongoDB
        db_repo = await get_mongodb_repo()
        logger.info("MongoDB initialized")
        
        # Initialize ChromaDB
        chroma_repo = get_chroma_repo()
        logger.info("ChromaDB initialized")
        
        logger.info("Application startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down application...")
        
        try:
            db_repo = await get_mongodb_repo()
            await db_repo.disconnect()
            logger.info("MongoDB disconnected")
        except:
            pass
        
        try:
            chroma_repo = get_chroma_repo()
            chroma_repo.disconnect()
            logger.info("ChromaDB disconnected")
        except:
            pass
        
        logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise Multi-Agent RAG Platform for HR and IT Policy Management",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

