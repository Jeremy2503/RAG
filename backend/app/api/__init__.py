"""
API Routes
FastAPI endpoint definitions.
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .chat import router as chat_router
from .documents import router as documents_router
from .health import router as health_router
from .evaluation import router as evaluation_router

# Main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(evaluation_router, prefix="/evaluation", tags=["Evaluation"])

__all__ = ["api_router"]

