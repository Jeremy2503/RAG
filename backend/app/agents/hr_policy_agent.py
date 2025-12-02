"""
HR Policy Agent
Specialized agent for HR policy queries.
"""

from typing import Dict, Any, Optional
import logging

from .base_agent import BaseAgent
from app.repositories.chroma_repo import ChromaRepository

logger = logging.getLogger(__name__)


class HRPolicyAgent(BaseAgent):
    """
    HR Policy agent specialized in human resources policies and procedures.
    """
    
    SYSTEM_PROMPT = """You are an HR Policy Agent, an expert in human resources policies, 
employee benefits, workplace procedures, and HR-related guidelines.

CRITICAL INSTRUCTIONS:
1. Answer ONLY using the exact information from the provided context
2. Do NOT add interpretations, restructuring, or "helpful" additions
3. Do NOT create numbered lists unless they exist in the source document
4. Do NOT extrapolate or infer information not explicitly stated
5. If the context contains the answer, provide it as written in the source
6. If the context does NOT contain the answer, clearly state: "This information is not found in the available HR policy documents."
7. Never mention document names, sources, or phrases like "according to the document"
8. Be conversational and empathetic, but factually strict - only state what the policy explicitly says

Your goal: Provide accurate, policy-based answers without embellishment or interpretation.
"""
    
    def __init__(self, chroma_repo: ChromaRepository):
        """
        Initialize HR policy agent.
        
        Args:
            chroma_repo: ChromaDB repository
        """
        super().__init__(
            name="HR Policy Agent",
            description="Specialist in HR policies, benefits, and employee procedures",
            chroma_repo=chroma_repo
        )
    
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an HR policy query.
        
        Args:
            query: User query
            context: Optional context from coordinator
            
        Returns:
            Agent response with answer and sources
        """
        logger.info(f"HR Policy Agent processing query: {query[:100]}...")
        
        try:
            # Retrieve relevant HR policy documents
            documents = await self.retrieve_relevant_documents(
                query=query,
                document_type="hr_policy",
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
            logger.error(f"HR Policy Agent error: {e}")
            
            return {
                "agent": self.name,
                "answer": f"I apologize, but I encountered an error while searching HR policies: {str(e)}",
                "sources": [],
                "success": False,
                "error": str(e)
            }

