"""
Health Check Endpoints
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime

from app.config import settings
from app.repositories.mongodb_repo import get_mongodb_repo, MongoDBRepository
from app.repositories.chroma_repo import get_chroma_repo, ChromaRepository

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.app_name,
        "version": settings.app_version
    }


@router.get("/health/detailed")
async def detailed_health_check(
    db_repo: MongoDBRepository = Depends(get_mongodb_repo),
    chroma_repo: ChromaRepository = Depends(get_chroma_repo)
) -> Dict[str, Any]:
    """
    Detailed health check including database connections.
    
    Returns:
        Detailed health status
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.app_name,
        "version": settings.app_version,
        "components": {}
    }
    
    # Check MongoDB
    try:
        await db_repo.client.admin.command('ping')
        health_status["components"]["mongodb"] = "healthy"
    except Exception as e:
        health_status["components"]["mongodb"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check ChromaDB
    try:
        count = chroma_repo.get_collection_count()
        health_status["components"]["chromadb"] = f"healthy ({count} documents)"
    except Exception as e:
        health_status["components"]["chromadb"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

