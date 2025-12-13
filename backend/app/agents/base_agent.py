"""
Base Agent Class
Abstract base class for all agents in the system.
Includes Opik observability for tracing and confidence tracking.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import logging
import time

from app.config import settings
from app.repositories.chroma_repo import ChromaRepository
from app.utils.embeddings import get_embedding_generator
from app.utils.observability import (
    get_opik_tracer,
    is_opik_enabled,
    log_agent_metrics,
    create_langchain_callbacks
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Provides common functionality for RAG-based agents.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        chroma_repo: Optional[ChromaRepository] = None
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            description: Agent description/purpose
            chroma_repo: ChromaDB repository for RAG
        """
        self.name = name
        self.description = description
        self.chroma_repo = chroma_repo
        self.embedding_generator = get_embedding_generator()
        
        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            openai_api_key=settings.openai_api_key
        )
    
    @abstractmethod
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query and return a response.
        
        Args:
            query: User query
            context: Optional context from previous agents
            
        Returns:
            Agent response with answer and metadata
        """
        pass
    
    async def retrieve_relevant_documents(
        self,
        query: str,
        document_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from vector database.
        
        Args:
            query: Search query
            document_type: Filter by document type
            n_results: Number of results to retrieve
            
        Returns:
            List of relevant documents with metadata
        """
        if not self.chroma_repo:
            logger.warning(f"{self.name}: No ChromaDB repository available")
            return []
        
        try:
            # Generate query embedding using OpenAI (must match document embeddings)
            query_embedding = await self.embedding_generator.generate_embeddings_openai([query])
            query_embedding = query_embedding[0]  # Extract single embedding
            
            # Query ChromaDB (get MANY extra results to account for filtering)
            # Many documents have tons of tiny header/footer chunks
            results = self.chroma_repo.query_by_text(
                query_text=query,
                query_embedding=query_embedding,
                n_results=100,  # Get 100 results to ensure we find good chunks after filtering
                document_type=document_type
            )
            
            # Filter out very short chunks (headers, footers, page numbers)
            MIN_CHUNK_LENGTH = 100
            filtered_results = [
                doc for doc in results 
                if len(doc.get('content', '').strip()) >= MIN_CHUNK_LENGTH
            ]
            
            # Take only the requested number after filtering
            filtered_results = filtered_results[:n_results]
            
            logger.info(f"{self.name}: Retrieved {len(results)} documents, {len(filtered_results)} after filtering (wanted {n_results})")
            
            if len(filtered_results) < n_results:
                logger.warning(f"{self.name}: Only found {len(filtered_results)} substantial chunks out of {len(results)} retrieved")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"{self.name}: Error retrieving documents: {e}")
            return []
    
    def format_context_from_documents(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into context string for LLM.
        
        Args:
            documents: Retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            content = doc.get('content', '')
            # Don't include document names/titles to keep responses clean
            context_parts.append(
                f"[Source {i}]\n{content}\n"
            )
        
        return "\n".join(context_parts)
    
    async def generate_response(
        self,
        query: str,
        context: str,
        system_prompt: str
    ) -> str:
        """
        Generate a response using the LLM.
        Instrumented with Opik for observability.
        
        Args:
            query: User query
            context: Context from retrieved documents
            system_prompt: System prompt for the agent
            
        Returns:
            Generated response
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Context:\n{context}\n\nQuestion: {query}\n\nProvide a detailed and accurate answer based on the context.")
        ])
        
        chain = prompt | self.llm
        
        # Get Opik callbacks for tracing
        callbacks = create_langchain_callbacks()
        
        start_time = time.time()
        
        try:
            # Invoke with Opik tracing callbacks
            config = {"callbacks": callbacks} if callbacks else {}
            response = await chain.ainvoke(
                {"context": context, "query": query},
                config=config
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Log metrics for observability
            log_agent_metrics(
                agent_name=self.name,
                latency_ms=latency_ms,
                success=True
            )
            
            logger.info(f"{self.name}: Generated response in {latency_ms:.0f}ms")
            
            return response.content
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            # Log error metrics
            log_agent_metrics(
                agent_name=self.name,
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            )
            
            logger.error(f"{self.name}: Error generating response: {e}")
            return f"I apologize, but I encountered an error processing your query: {str(e)}"
    
    def get_info(self) -> Dict[str, str]:
        """
        Get agent information.
        
        Returns:
            Agent name and description
        """
        return {
            "name": self.name,
            "description": self.description
        }

