"""
Document Endpoints
Handles document upload and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
import logging

from app.models.document import DocumentUpload, DocumentResponse, DocumentType, DocumentListResponse
from app.models.user import User
from app.services.document_service import DocumentService
from app.repositories.mongodb_repo import get_mongodb_repo, MongoDBRepository
from app.repositories.chroma_repo import get_chroma_repo, ChromaRepository
from app.api.auth import get_current_user, verify_admin

logger = logging.getLogger(__name__)
router = APIRouter()


# Dependencies
async def get_document_service(
    db_repo: MongoDBRepository = Depends(get_mongodb_repo),
    chroma_repo: ChromaRepository = Depends(get_chroma_repo)
) -> DocumentService:
    """Get document service instance."""
    return DocumentService(db_repo, chroma_repo)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.GENERAL),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated tags
    current_user: User = Depends(verify_admin),  # Only admins can upload
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """
    Upload a document (Admin only).
    
    Args:
        file: File to upload
        document_type: Type of document (hr_policy, it_policy, general)
        title: Optional document title
        description: Optional description
        tags: Optional comma-separated tags
        current_user: Current authenticated admin user
        document_service: Document service
        
    Returns:
        Created document information
    """
    logger.info(f"Admin {current_user.email} uploading document: {file.filename}")
    
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Create metadata
        metadata = DocumentUpload(
            document_type=document_type,
            title=title,
            description=description,
            tags=tag_list
        )
        
        # Upload and process document
        document = await document_service.upload_document(
            file_content=file_content,
            filename=file.filename,
            file_size=file_size,
            file_type=file.content_type or "application/octet-stream",
            user=current_user,
            metadata=metadata
        )
        
        logger.info(f"Document uploaded successfully: {document.id}")
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            file_size=document.file_size,
            document_type=document.document_type,
            uploaded_by=document.uploaded_by,
            uploaded_at=document.uploaded_at,
            status=document.status,
            chunks_count=document.chunks_count,
            embeddings_stored=document.embeddings_stored,
            title=document.title,
            tags=document.tags
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(verify_admin),  # Only admins can list all documents
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentListResponse:
    """
    List documents uploaded by the current user (Admin).
    
    Args:
        page: Page number
        page_size: Items per page
        current_user: Current authenticated admin user
        document_service: Document service
        
    Returns:
        List of documents
    """
    documents = await document_service.get_user_documents(
        user=current_user,
        page=page,
        page_size=page_size
    )
    
    return DocumentListResponse(
        documents=documents,
        total=len(documents),
        page=page,
        page_size=page_size
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(verify_admin),
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """
    Get document by ID (Admin only).
    
    Args:
        document_id: Document ID
        current_user: Current authenticated admin user
        document_service: Document service
        
    Returns:
        Document information
    """
    document = await document_service.get_document(document_id, current_user)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        original_filename=document.original_filename,
        file_size=document.file_size,
        document_type=document.document_type,
        uploaded_by=document.uploaded_by,
        uploaded_at=document.uploaded_at,
        status=document.status,
        chunks_count=document.chunks_count,
        embeddings_stored=document.embeddings_stored,
        title=document.title,
        tags=document.tags
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(verify_admin),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Delete a document (Admin only).
    
    Args:
        document_id: Document ID
        current_user: Current authenticated admin user
        document_service: Document service
        
    Returns:
        Success message
    """
    success = await document_service.delete_document(document_id, current_user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or delete failed"
        )
    
    return {"message": "Document deleted successfully"}

