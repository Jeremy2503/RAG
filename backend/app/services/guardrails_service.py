"""
Guardrails Service
Validates user inputs using custom injection pattern detection.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Custom exception for guardrail validation failures
class GuardrailValidationError(Exception):
    """
    Custom exception for guardrail validation failures.
    """
    def __init__(self, message: str, violation_type: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.violation_type = violation_type
        self.details = details or {}
        super().__init__(self.message)


class GuardrailsService:
    """
    Service for validating user inputs using custom injection detection.
    """
    
    def __init__(self):
        """Initialize guardrails service."""
        # Custom injection patterns
        self.injection_patterns = [
            r'ignore\s+(previous|all|above|instructions)',
            r'forget\s+(previous|all|above|instructions)',
            r'system\s*:',
            r'you\s+are\s+now',
            r'act\s+as\s+if',
            r'pretend\s+to\s+be',
            r'disregard\s+(previous|all|above)',
            r'override\s+(previous|all|above)',
            r'new\s+instructions\s*:',
            r'<\|system\|>',
            r'<\|assistant\|>',
            r'<\|user\|>',
            r'\[INST\]',
            r'\[/INST\]',
            r'<s>',
            r'</s>',
        ]
        
        logger.info("✅ Guardrails service initialized with custom injection pattern detection")
    
    def validate_input(self, query: str) -> Dict[str, Any]:
        """
        Validate user input against custom injection patterns.
        
        Args:
            query: User query string
            
        Returns:
            Dict with validation result and details
            
        Raises:
            GuardrailValidationError: If validation fails
        """
        validation_result = {
            "passed": True,
            "violations": [],
            "reason": None,
            "violation_type": None
        }
        
        # Check for prompt injection patterns
        injection_detected, pattern = self._detect_injection(query)
        if injection_detected:
            validation_result["passed"] = False
            validation_result["violations"].append("prompt_injection")
            validation_result["violation_type"] = "injection"
            validation_result["reason"] = f"Potential prompt injection detected: {pattern}"
            
            error_msg = (
                "Your query contains patterns that may be used to manipulate the system. "
                "Please rephrase your question to focus on HR or IT policy information."
            )
            
            raise GuardrailValidationError(
                message=error_msg,
                violation_type="injection",
                details={"pattern": pattern, "query_preview": query[:100]}
            )
        
        logger.debug(f"Input validation passed for query: {query[:50]}...")
        return validation_result
    
    def _detect_injection(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Detect prompt injection patterns using regex.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (is_injection_detected, detected_pattern)
        """
        query_lower = query.lower()
        
        for pattern in self.injection_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.warning(f"Injection pattern detected: {pattern} in query: {query[:100]}")
                return True, pattern
        
        return False, None
    
    def is_enabled(self) -> bool:
        """Check if guardrails are enabled."""
        return len(self.injection_patterns) > 0


# Global singleton instance
_guardrails_service: Optional[GuardrailsService] = None


# Export the custom exception
__all__ = ["GuardrailsService", "GuardrailValidationError", "get_guardrails_service"]

def get_guardrails_service() -> GuardrailsService:
    """
    Get the global guardrails service instance.
    Creates one if it doesn't exist.
    
    Returns:
        GuardrailsService instance
    """
    global _guardrails_service
    if _guardrails_service is None:
        _guardrails_service = GuardrailsService()
    return _guardrails_service

