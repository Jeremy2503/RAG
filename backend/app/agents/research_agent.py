"""
Research Agent
Handles general research queries and fallback cases.
"""

from typing import Dict, Any, Optional
import logging

from .base_agent import BaseAgent
from app.repositories.chroma_repo import ChromaRepository

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research agent for general queries.
    Searches across all document types.
    """
    
    SYSTEM_PROMPT = """You are a Research Agent specialized in providing accurate, 
well-researched answers to user queries based on available documentation.

CRITICAL INSTRUCTIONS:
1. Answer ONLY using the exact information from the provided context
2. Do NOT add interpretations, restructuring, or "helpful" additions
3. Do NOT create numbered lists unless they exist in the source document
4. Do NOT extrapolate or infer information not explicitly stated
5. If the context contains the answer, provide it as written in the source
6. If the context does NOT contain the answer, clearly state: "This information is not found in the available documents."
7. Never mention document names, sources, or phrases like "according to the document"
8. Be conversational but factually strict - only state what the documents explicitly say

Your goal: Provide accurate, document-based answers without embellishment or interpretation.
"""
    
    def __init__(self, chroma_repo: ChromaRepository):
        """
        Initialize research agent.
        
        Args:
            chroma_repo: ChromaDB repository
        """
        super().__init__(
            name="Research Agent",
            description="Handles general research queries across all document types",
            chroma_repo=chroma_repo
        )
    
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a research query.
        
        Args:
            query: User query
            context: Optional context from coordinator
            
        Returns:
            Agent response with answer and sources
        """
        logger.info(f"Research Agent processing query: {query[:100]}...")
        
        try:
            # Retrieve relevant documents (search all types)
            documents = await self.retrieve_relevant_documents(
                query=query,
                document_type=None,  # Search all document types
                n_results=5
            )
            
            # Format context
            context_str = self.format_context_from_documents(documents)
            
            # Generate response
            answer = await self.generate_response(
                query=query,
                context=context_str,
                system_prompt=self.SYSTEM_PROMPT
            )
            
            return {
                "agent": self.name,
                "answer": answer,
                "sources": documents,
                "success": True,
                "document_count": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Research Agent error: {e}")
            
            return {
                "agent": self.name,
                "answer": f"I apologize, but I encountered an error while researching your query: {str(e)}",
                "sources": [],
                "success": False,
                "error": str(e)
            }

