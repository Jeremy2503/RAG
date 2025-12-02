"""
ChromaDB Repository
Handles vector database operations for document embeddings.
"""

import chromadb
from typing import List, Dict, Any, Optional
import logging
import uuid

from app.config import settings

logger = logging.getLogger(__name__)


class ChromaRepository:
    """
    ChromaDB repository for vector storage and similarity search.
    Manages document embeddings and retrieval.
    """
    
    def __init__(self):
        """Initialize ChromaDB client."""
        self.client = None
        self.collection = None
    
    def connect(self):
        """
        Establish connection to ChromaDB.
        Uses persistent storage for production use.
        """
        try:
            # Initialize persistent ChromaDB client (modern API)
            self.client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"description": "Policy documents and embeddings"}
            )
            
            logger.info(f"Connected to ChromaDB. Collection: {settings.chroma_collection_name}")
            logger.info(f"ChromaDB persist directory: {settings.chroma_persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    
    def disconnect(self):
        """Close ChromaDB connection and persist data."""
        if self.client:
            # ChromaDB automatically persists on close
            logger.info("ChromaDB connection closed")
    
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents with embeddings to the collection.
        
        Args:
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dicts for each document
            ids: Optional list of document IDs (generated if not provided)
            
        Returns:
            List of document IDs
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized")
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        
        # Ensure metadatas exists
        if metadatas is None:
            metadatas = [{} for _ in range(len(documents))]
        
        try:
            # ChromaDB has a max batch size limit (usually around 5461)
            # Split into smaller batches to avoid errors
            batch_size = 1000
            total_docs = len(documents)
            
            for i in range(0, total_docs, batch_size):
                end_idx = min(i + batch_size, total_docs)
                batch_docs = documents[i:end_idx]
                batch_embeddings = embeddings[i:end_idx] if embeddings else None
                batch_metadatas = metadatas[i:end_idx]
                batch_ids = ids[i:end_idx]
                
                self.collection.add(
                    documents=batch_docs,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                
                logger.info(f"Added batch {i//batch_size + 1}: {len(batch_docs)} documents (total: {end_idx}/{total_docs})")
            
            logger.info(f"Successfully added all {total_docs} documents to ChromaDB")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {e}")
            raise
    
    def query_documents(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the collection for similar documents.
        
        Args:
            query_embeddings: List of query embedding vectors
            n_results: Number of results to return per query
            where: Metadata filters (e.g., {"document_type": "hr_policy"})
            where_document: Document content filters
            
        Returns:
            Query results with documents, distances, and metadata
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized")
        
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            
            logger.info(f"Queried {len(query_embeddings)} embeddings, returning top {n_results}")
            return results
            
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            raise
    
    def query_by_text(
        self,
        query_text: str,
        query_embedding: List[float],
        n_results: int = 5,
        document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents using text and its embedding.
        
        Args:
            query_text: The query text (for logging/debugging)
            query_embedding: Embedding vector of the query
            n_results: Number of results to return
            document_type: Optional filter by document type
            
        Returns:
            List of relevant documents with metadata and scores
        """
        where_filter = None
        if document_type:
            where_filter = {"document_type": document_type}
        
        results = self.query_documents(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )
        
        # Format results
        formatted_results = []
        
        if results and 'documents' in results and len(results['documents']) > 0:
            documents = results['documents'][0]  # First query results
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            ids = results.get('ids', [[]])[0]
            
            for i, doc in enumerate(documents):
                formatted_results.append({
                    "id": ids[i] if i < len(ids) else None,
                    "content": doc,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else None,
                    "similarity": 1 - distances[i] if i < len(distances) else None
                })
        
        return formatted_results
    
    def delete_documents(self, ids: List[str]) -> bool:
        """
        Delete documents from the collection.
        
        Args:
            ids: List of document IDs to delete
            
        Returns:
            True if successful
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized")
        
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents from ChromaDB: {e}")
            return False
    
    def delete_by_metadata(self, where: Dict[str, Any]) -> bool:
        """
        Delete documents matching metadata criteria.
        
        Args:
            where: Metadata filter (e.g., {"document_id": "123"})
            
        Returns:
            True if successful
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized")
        
        try:
            self.collection.delete(where=where)
            logger.info(f"Deleted documents matching filter: {where}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents by metadata: {e}")
            return False
    
    def get_collection_count(self) -> int:
        """
        Get the number of documents in the collection.
        
        Returns:
            Number of documents
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized")
        
        return self.collection.count()
    
    def peek(self, limit: int = 10) -> Dict[str, Any]:
        """
        Peek at documents in the collection.
        
        Args:
            limit: Number of documents to return
            
        Returns:
            Sample documents with metadata
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized")
        
        return self.collection.peek(limit=limit)


# Global ChromaDB repository instance
_chroma_repo = None


def get_chroma_repo() -> ChromaRepository:
    """
    Get or create the global ChromaDB repository instance.
    Dependency injection function for FastAPI.
    """
    global _chroma_repo
    if _chroma_repo is None:
        _chroma_repo = ChromaRepository()
        _chroma_repo.connect()
    return _chroma_repo

