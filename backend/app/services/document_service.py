"""
Document Service
Handles document upload, processing, and embedding generation.
"""

from typing import List, Optional
from pathlib import Path
import aiofiles
import uuid
from datetime import datetime
import logging

from app.models.document import (
    Document,
    DocumentUpload,
    DocumentResponse,
    DocumentStatus,
    DocumentType
)
from app.models.user import User
from app.repositories.mongodb_repo import MongoDBRepository
from app.repositories.chroma_repo import ChromaRepository
from app.utils.embeddings import get_embedding_generator
from app.utils.validators import validate_file_extension, validate_file_size, sanitize_filename
from app.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service for handling document upload and processing.
    Integrates with MongoDB (metadata) and ChromaDB (embeddings).
    """
    
    def __init__(
        self,
        db_repo: MongoDBRepository,
        chroma_repo: ChromaRepository
    ):
        """
        Initialize document service.
        
        Args:
            db_repo: MongoDB repository
            chroma_repo: ChromaDB repository
        """
        self.db_repo = db_repo
        self.chroma_repo = chroma_repo
        self.embedding_generator = get_embedding_generator()
        self.upload_dir = Path("./data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        file_size: int,
        file_type: str,
        user: User,
        metadata: DocumentUpload
    ) -> Document:
        """
        Upload and process a document.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_size: File size in bytes
            file_type: MIME type
            user: User uploading the document
            metadata: Document metadata
            
        Returns:
            Created document object
        """
        logger.critical("=" * 80)
        logger.critical(f"🚀 UPLOAD_DOCUMENT CALLED! File: {filename}, Size: {file_size}")
        logger.critical("=" * 80)
        
        # Validate file
        validate_file_extension(filename)
        validate_file_size(file_size)
        
        # Sanitize filename and generate unique filename
        clean_filename = sanitize_filename(filename)
        unique_filename = f"{uuid.uuid4()}_{clean_filename}"
        file_path = self.upload_dir / unique_filename
        
        # Save file to disk
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        logger.info(f"Saved file to {file_path}")
        
        # Create document record in MongoDB
        document = Document(
            filename=unique_filename,
            original_filename=clean_filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_type,
            document_type=metadata.document_type,
            uploaded_by=user.id,
            uploaded_at=datetime.utcnow(),
            status=DocumentStatus.PENDING,
            title=metadata.title or clean_filename,
            description=metadata.description,
            tags=metadata.tags,
            chroma_collection=settings.chroma_collection_name
        )
        
        document = await self.db_repo.create_document(document)
        logger.info(f"Created document record: {document.id}")
        
        logger.critical(f"📝 About to call _process_document for document {document.id}")
        
        # Process document asynchronously (in background)
        # For simplicity, we'll process it immediately here
        # In production, use a task queue (Celery, etc.)
        await self._process_document(document)
        
        logger.critical(f"✅ _process_document completed for document {document.id}")
        
        return document
    
    async def _process_document(self, document: Document):
        """
        Process document: extract text, generate embeddings, store in ChromaDB.
        
        Args:
            document: Document to process
        """
        logger.critical(f"🔥 _PROCESS_DOCUMENT STARTED for {document.id}")
        try:
            logger.critical(f"📊 Updating status to PROCESSING for {document.id}")
            await self.db_repo.update_document_status(
                document.id,
                DocumentStatus.PROCESSING.value
            )
            logger.critical(f"✓ Status updated successfully")
            logger.info(f"Starting text extraction for document {document.id}...")
            text_content = await self._extract_text(document.file_path, document.file_type)
            logger.info(f"Successfully extracted {len(text_content)} characters from {document.original_filename}")

            if not text_content:
                raise Exception("No text extracted from document")
            
            logger.info(f"Starting chunking for document {document.id}...")
            chunks = self.embedding_generator.chunk_text(
                text_content,
                chunk_size=500,
                chunk_overlap=50
            )
            
            logger.info(f"Document {document.id} split into {len(chunks)} chunks (before filtering)")
            
            # Filter out very short chunks (headers, footers, page numbers)
            MIN_CHUNK_LENGTH = 100
            chunks_before = len(chunks)
            chunks = [chunk for chunk in chunks if len(chunk.strip()) >= MIN_CHUNK_LENGTH]
            chunks_filtered = chunks_before - len(chunks)
            
            if chunks_filtered > 0:
                logger.info(f"Filtered out {chunks_filtered} short chunks (<{MIN_CHUNK_LENGTH} chars)")
            logger.info(f"Final chunk count: {len(chunks)} chunks")
            
            logger.info(f"Starting embedding generation for {len(chunks)} texts using OpenAI...")
            embeddings = await self.embedding_generator.generate_embeddings_openai(chunks)
            logger.info(f"Successfully generated {len(embeddings)} embeddings for document {document.id}")
            
            # Prepare metadata for each chunk
            metadatas = []
            chunk_ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document.id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                
                metadatas.append({
                    "document_id": document.id,
                    "document_type": document.document_type.value,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "title": document.title or document.original_filename,
                    "uploaded_by": document.uploaded_by,
                    "uploaded_at": document.uploaded_at.isoformat()
                })
            
            # Store in ChromaDB
            self.chroma_repo.add_documents(
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=chunk_ids
            )
            
            logger.info(f"Stored {len(chunks)} embeddings in ChromaDB")
            
            # Update document status
            await self.db_repo.update_document_status(
                document.id,
                DocumentStatus.COMPLETED.value
            )
            
            # Update document metadata
            await self.db_repo.db.documents.update_one(
                {"_id": document.id},
                {
                    "$set": {
                        "chunks_count": len(chunks),
                        "embeddings_stored": True,
                        "processing_completed_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Document {document.id} processed successfully")
            
        except Exception as e:
            logger.critical(f"💥 EXCEPTION in _process_document for {document.id}: {type(e).__name__}: {e}")
            logger.error(f"Error processing document {document.id}: {e}", exc_info=True)
            
            # Update status to failed
            await self.db_repo.update_document_status(
                document.id,
                DocumentStatus.FAILED.value,
                error=str(e)
            )
    
    async def _extract_text(self, file_path: str, file_type: str) -> str:
        """
        Extract text from various document formats.
        
        Args:
            file_path: Path to the file
            file_type: MIME type
            
        Returns:
            Extracted text
        """
        path = Path(file_path)
        
        try:
            # Handle different file types
            
            if file_type in ['text/plain', 'text/markdown']:
                async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                    return await f.read()
            
            elif file_type == 'application/pdf':
                return await self._extract_pdf(path)
            
            elif file_type in [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword'
            ]:
                return await self._extract_docx(path)
            
            elif file_type in [
                'image/jpeg', 'image/jpg', 'image/png', 'image/webp',
                'image/bmp', 'image/tiff', 'image/tif'
            ]:
                # Extract text from images using OCR
                return await self._extract_image_ocr(path)
            
            else:
                # Try reading as text
                async with aiofiles.open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return await f.read()
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    async def _extract_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF using PyPDF2.
        """
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(str(file_path))
            text_parts = []
            
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num}: {e}")
                    continue
            
            if not text_parts:
                logger.warning(f"No text extracted from PDF: {file_path}")
                return f"[Empty PDF or text extraction failed for {file_path.name}]"
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"Successfully extracted {len(full_text)} characters from {file_path.name}")
            return full_text
            
        except ImportError:
            logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            return f"[PDF extraction requires PyPDF2 library]"
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {e}")
            return f"[Error extracting PDF: {str(e)}]"
    
    async def _extract_docx(self, file_path: Path) -> str:
        """
        Extract text from DOCX.
        Placeholder implementation.
        """
        # TODO: Implement using python-docx
        logger.warning(f"DOCX extraction not fully implemented for {file_path}")
        return f"[DOCX content from {file_path.name}]"
    
    async def _extract_image_ocr(self, file_path: Path) -> str:
        """
        Extract text from images using OCR (Optical Character Recognition).
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Extracted text from the image
        """
        try:
            import easyocr
            from PIL import Image
            
            logger.info(f"Starting OCR extraction for {file_path.name}")
            
            # Open and validate image
            try:
                image = Image.open(str(file_path))
                logger.info(f"Image opened: {image.size[0]}x{image.size[1]} pixels, mode: {image.mode}")
            except Exception as e:
                logger.error(f"Error opening image {file_path}: {e}")
                return f"[Error opening image: {str(e)}]"
            
            # Initialize EasyOCR reader (supports multiple languages)
            # Using English by default, can add more languages: ['en', 'es', 'fr', etc.]
            try:
                logger.info("Initializing EasyOCR reader...")
                reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have CUDA
                logger.info("EasyOCR reader initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing EasyOCR: {e}")
                return f"[Error initializing OCR: {str(e)}]"
            
            # Perform OCR
            try:
                logger.info(f"Running OCR on {file_path.name}...")
                results = reader.readtext(str(file_path), detail=0, paragraph=True)
                
                if not results:
                    logger.warning(f"No text detected in image: {file_path.name}")
                    return f"[No text detected in image {file_path.name}]"
                
                # Join all detected text
                extracted_text = "\n".join(results)
                
                logger.info(f"Successfully extracted {len(extracted_text)} characters from {file_path.name}")
                return extracted_text
                
            except Exception as e:
                logger.error(f"Error during OCR processing: {e}")
                return f"[Error during OCR processing: {str(e)}]"
            
        except ImportError as e:
            logger.error(f"OCR libraries not installed: {e}")
            return f"[OCR requires easyocr and Pillow libraries. Install with: pip install easyocr Pillow]"
        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {e}")
            return f"[Error extracting text from image: {str(e)}]"
    
    async def get_document(self, document_id: str, user: User) -> Optional[Document]:
        """
        Get document by ID.
        
        Args:
            document_id: Document ID
            user: Current user
            
        Returns:
            Document if found
        """
        document = await self.db_repo.get_document(document_id)
        
        # Authorization check
        if document and document.uploaded_by != user.id and user.role.value != "admin":
            return None
        
        return document
    
    async def get_user_documents(
        self,
        user: User,
        page: int = 1,
        page_size: int = 50
    ) -> List[DocumentResponse]:
        """
        Get documents uploaded by user.
        
        Args:
            user: User object
            page: Page number
            page_size: Items per page
            
        Returns:
            List of document responses
        """
        skip = (page - 1) * page_size
        documents = await self.db_repo.get_user_documents(user.id, skip, page_size)
        
        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                original_filename=doc.original_filename,
                file_size=doc.file_size,
                document_type=doc.document_type,
                uploaded_by=doc.uploaded_by,
                uploaded_at=doc.uploaded_at,
                status=doc.status,
                chunks_count=doc.chunks_count,
                embeddings_stored=doc.embeddings_stored,
                title=doc.title,
                tags=doc.tags
            )
            for doc in documents
        ]
    
    async def delete_document(self, document_id: str, user: User) -> bool:
        """
        Delete a document and its embeddings.
        
        Args:
            document_id: Document ID
            user: User requesting deletion
            
        Returns:
            True if successful
        """
        document = await self.get_document(document_id, user)
        
        if not document:
            return False
        
        try:
            # Delete from ChromaDB
            self.chroma_repo.delete_by_metadata({"document_id": document_id})
            
            # Delete file from disk
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Delete from MongoDB
            deleted = await self.db_repo.delete_document(document_id)
            if not deleted:
                logger.warning(f"Document {document_id} not found in MongoDB during deletion")
            
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False

