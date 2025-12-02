"""
Embedding Generation Module
Handles text embedding generation using Sentence Transformers and OpenAI.
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer
from langchain_openai import OpenAIEmbeddings
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates embeddings for text using multiple strategies.
    Supports both local (Sentence Transformers) and API-based (OpenAI) embeddings.
    """
    
    def __init__(self):
        """Initialize the embedding generator."""
        self._local_model = None
        self._openai_embeddings = None
    
    @property
    def local_model(self) -> SentenceTransformer:
        """
        Lazy-load the Sentence Transformer model.
        This prevents loading the model until actually needed.
        """
        if self._local_model is None:
            logger.info(f"Loading Sentence Transformer model: {settings.sentence_transformer_model}")
            self._local_model = SentenceTransformer(settings.sentence_transformer_model)
        return self._local_model
    
    @property
    def openai_embeddings(self) -> OpenAIEmbeddings:
        """
        Lazy-load the OpenAI embeddings client.
        """
        if self._openai_embeddings is None:
            logger.info("Initializing OpenAI embeddings client")
            self._openai_embeddings = OpenAIEmbeddings(
                model=settings.openai_embedding_model,
                openai_api_key=settings.openai_api_key
            )
        return self._openai_embeddings
    
    def generate_embeddings_local(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings using local Sentence Transformer model.
        
        Args:
            texts: Single text or list of texts to embed
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
            
        Returns:
            List of embedding vectors
        """
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            embeddings = self.local_model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            
            # Convert numpy arrays to lists for JSON serialization
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error generating local embeddings: {e}")
            raise
    
    async def generate_embeddings_openai(
        self,
        texts: Union[str, List[str]]
    ) -> List[List[float]]:
        """
        Generate embeddings using OpenAI's embedding API via LangChain.
        
        Args:
            texts: Single text or list of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts using OpenAI...")
            embeddings = await self.openai_embeddings.aembed_documents(texts)
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings: {e}", exc_info=True)
            raise
    
    def generate_embeddings(
        self,
        texts: Union[str, List[str]],
        use_openai: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings using the configured strategy.
        
        Args:
            texts: Single text or list of texts to embed
            use_openai: Whether to use OpenAI (True) or local model (False)
            
        Returns:
            List of embedding vectors
        """
        if use_openai:
            # Note: This is synchronous wrapper for async function
            # In production, use async version directly
            import asyncio
            return asyncio.run(self.generate_embeddings_openai(texts))
        else:
            return self.generate_embeddings_local(texts)
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[str]:
        """
        Split text into chunks for embedding.
        
        Args:
            text: Text to chunk
            chunk_size: Target size of each chunk (in characters)
            chunk_overlap: Overlap between chunks (in characters)
            
        Returns:
            List of text chunks
        """
        logger.info(f"Chunking {len(text)} characters with chunk_size={chunk_size}, overlap={chunk_overlap}")
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            if len(chunks) % 100 == 0 and len(chunks) > 0:
                logger.info(f"Chunking progress: {len(chunks)} chunks created, {start}/{text_length} characters processed")
            
            end = min(start + chunk_size, text_length)
            
            # Find the nearest sentence boundary
            if end < text_length:
                # Look for sentence endings within the chunk
                best_end = end
                for delimiter in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    last_delimiter = text.rfind(delimiter, start, end)
                    if last_delimiter != -1 and last_delimiter > start:
                        best_end = last_delimiter + len(delimiter)
                        break
                end = best_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Calculate next start position, ensuring we always move forward
            next_start = end - chunk_overlap
            # CRITICAL: Always advance at least to end position to avoid infinite loops
            if next_start <= start:
                next_start = start + 1
            
            start = next_start
        
        logger.info(f"Chunking complete: {len(chunks)} total chunks created")
        return chunks


# Global embedding generator instance
_embedding_generator = None


def get_embedding_generator() -> EmbeddingGenerator:
    """
    Get or create the global embedding generator instance.
    Singleton pattern for efficient resource usage.
    """
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator

