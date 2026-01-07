"""
IT Policy Agent
Specialized agent for IT policy queries.
"""

from typing import Dict, Any, Optional
import logging

from .base_agent import BaseAgent
from app.repositories.chroma_repo import ChromaRepository
from app.utils.observability import track, get_project_name

logger = logging.getLogger(__name__)


class ITPolicyAgent(BaseAgent):
    """
    IT Policy agent specialized in IT-related policies and procedures.
    """
    
    SYSTEM_PROMPT = """You are an IT Policy Agent, an expert in information technology 
policies, security protocols, infrastructure guidelines, and IT-related procedures.

CRITICAL INSTRUCTIONS:
1. If the user asked MULTIPLE questions, identify them and answer each one separately
2. For EACH question, ONLY use information explicitly found in the provided context
3. If the context does NOT contain information for a specific question, clearly state: "This information is not found in the available IT policy documents."
4. DO NOT attempt to answer questions for which you have no context
5. DO NOT add interpretations, restructuring, or "helpful" additions
6. DO NOT create numbered lists unless they exist in the source document
7. DO NOT extrapolate or infer information not explicitly stated
8. If the context contains the answer, provide it as written in the source
9. Structure your response to clearly separate answers to different questions
10. Never mention document names, sources, or phrases like "according to the document"
11. Be conversational but factually strict - only state what the policy explicitly says

Your goal: Provide accurate, policy-based answers without embellishment or interpretation.
If you cannot answer a question from the context, explicitly say so.
"""
    
    def __init__(self, chroma_repo: ChromaRepository):
        """
        Initialize IT policy agent.
        
        Args:
            chroma_repo: ChromaDB repository
        """
        super().__init__(
            name="IT Policy Agent",
            description="Specialist in IT policies, security, and infrastructure",
            chroma_repo=chroma_repo
        )
    
    @track(
        name="it_policy_agent::process",
        project_name=get_project_name(),
        tags=["agent", "it_policy"],
        capture_input=True,
        capture_output=True
    )
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an IT policy query.
        
        Args:
            query: User query
            context: Optional context from coordinator
            
        Returns:
            Agent response with answer and sources
        """
        logger.info(f"IT Policy Agent processing query: {query[:100]}...")
        
        try:
            # Retrieve relevant IT policy documents
            documents = await self.retrieve_relevant_documents(
                query=query,
                document_type="it_policy",
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
            logger.error(f"IT Policy Agent error: {e}")
            
            return {
                "agent": self.name,
                "answer": f"I apologize, but I encountered an error while searching IT policies: {str(e)}",
                "sources": [],
                "success": False,
                "error": str(e)
            }

