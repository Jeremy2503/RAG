"""
Question Detection Utility
Detects and splits multiple questions in a user query.
"""

import re
from typing import List
import logging

logger = logging.getLogger(__name__)


def detect_multiple_questions(query: str) -> List[str]:
    """
    Detect if query contains multiple questions and split them.
    
    This function identifies multiple questions in a single query string by:
    - Splitting on question marks
    - Detecting common connectors (and, also, what about, etc.)
    - Handling various question formats
    
    Args:
        query: User query string
        
    Returns:
        List of individual questions (or single-item list if only one question)
    """
    if not query or not query.strip():
        return [query]
    
    query = query.strip()
    questions = []
    
    # First, try splitting by question marks (most reliable)
    # Split on one or more question marks, keeping the question marks with the preceding text
    parts = re.split(r'(\?+)', query)
    
    # Reconstruct questions with their question marks
    current_question = ""
    for i, part in enumerate(parts):
        if part:
            if part.endswith('?'):
                # This part ends with question mark(s)
                current_question += part
                if current_question.strip():
                    questions.append(current_question.strip())
                current_question = ""
            else:
                # Regular text
                current_question += part
    
    # If there's leftover text, add it as a question
    if current_question.strip():
        questions.append(current_question.strip())
    
    # If we found multiple questions via question marks, return them
    if len(questions) > 1:
        logger.info(f"Detected {len(questions)} questions via question marks")
        return questions
    
    # NEW: Detect list-style questions: "what are X, Y and Z" or "what is X, Y, and Z"
    # This handles queries like "what are the hr policy objects, employment types and byod policy"
    list_question_patterns = [
        # Pattern for "what are/is X, Y and Z" or "what are/is X, Y, and Z"
        r'^(what (are|is|were|was))\s+(.+)$',
        # Pattern for "tell me about X, Y and Z"
        r'^(tell me about|explain|describe|list)\s+(.+)$',
    ]
    
    for pattern in list_question_patterns:
        match = re.match(pattern, query, re.IGNORECASE)
        if match:
            question_prefix = match.group(1).strip()  # "what are", "tell me about", etc.
            items_part = match.groups()[-1].strip()  # The part with items (last group)
            
            # Check if items_part contains commas or "and" - indicating a list
            if ',' in items_part or re.search(r'\s+and\s+', items_part, re.IGNORECASE):
                # Split items by comma and "and"
                # Handle both "X, Y and Z" and "X, Y, and Z" formats
                # Split on comma or "and" (but preserve the structure)
                items = re.split(r'\s*,\s*|\s+and\s+', items_part)
                items = [item.strip() for item in items if item.strip()]
                
                # Filter out empty items and very short ones
                items = [item for item in items if len(item) >= 2]
                
                # If we have multiple items, expand into separate questions
                if len(items) >= 2:
                    expanded_questions = []
                    for item in items:
                        # Reconstruct full question for each item
                        if question_prefix.lower().startswith('what are'):
                            expanded_questions.append(f"{question_prefix} {item}")
                        elif question_prefix.lower().startswith('what is'):
                            expanded_questions.append(f"{question_prefix} {item}")
                        elif question_prefix.lower().startswith('what were'):
                            expanded_questions.append(f"{question_prefix} {item}")
                        elif question_prefix.lower().startswith('what was'):
                            expanded_questions.append(f"{question_prefix} {item}")
                        else:
                            # For "tell me about", "explain", "describe", "list"
                            expanded_questions.append(f"{question_prefix} {item}")
                    
                    # Validate expanded questions (must be at least 3 words each)
                    validated_questions = [
                        q for q in expanded_questions 
                        if len(q.split()) >= 3  # At least 3 words for a meaningful question
                    ]
                    
                    if len(validated_questions) >= 2:
                        logger.info(f"Detected {len(validated_questions)} questions from list-style query: {[q[:50] for q in validated_questions]}")
                        return validated_questions
    
    # If no question marks or only one question found, check for connectors
    # Common patterns: "X and Y", "X also Y", "X what about Y", etc.
    connector_patterns = [
        r'\s+and\s+',           # "What is X and what is Y"
        r'\s+also\s+',          # "What is X also what is Y"
        r'\s+what about\s+',     # "What is X what about Y"
        r'\s+how about\s+',     # "What is X how about Y"
        r'\s+,\s+and\s+',       # "What is X, and what is Y"
        r'\s+;\s+',             # "What is X; what is Y"
        r'\s+then\s+',          # "What is X then what is Y"
    ]
    
    for pattern in connector_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            # Split on this connector
            parts = re.split(pattern, query, flags=re.IGNORECASE)
            parts = [p.strip() for p in parts if p.strip()]
            
            # Only split if we get at least 2 meaningful parts
            if len(parts) >= 2:
                # Check if parts look like separate questions
                # (e.g., both start with question words or are complete thoughts)
                question_words = ['what', 'who', 'when', 'where', 'why', 'how', 'which', 'can', 'should', 'is', 'are', 'does', 'do']
                valid_parts = []
                
                for part in parts:
                    part_lower = part.lower().strip()
                    # Check if it starts with a question word or looks like a question
                    is_question = any(part_lower.startswith(qw) for qw in question_words) or \
                                  part_lower.endswith('?') or \
                                  len(part.split()) >= 3  # At least 3 words (likely a complete thought)
                    
                    if is_question:
                        valid_parts.append(part)
                
                if len(valid_parts) >= 2:
                    logger.info(f"Detected {len(valid_parts)} questions via connector pattern: {pattern}")
                    return valid_parts
    
    # If no multiple questions detected, return single-item list
    logger.debug(f"Single question detected: {query[:50]}...")
    return [query]


def combine_multiple_answers(question_answers: List[dict]) -> str:
    """
    Combine answers from multiple questions into a coherent response.
    Uses markdown formatting for proper rendering in the frontend.
    
    Args:
        question_answers: List of dicts with 'question' and 'answer' keys
        
    Returns:
        Combined answer string with markdown formatting
    """
    if not question_answers:
        return "I apologize, but I couldn't generate a response."
    
    if len(question_answers) == 1:
        return question_answers[0].get("answer", "No answer provided")
    
    # Multiple questions - format them clearly with markdown
    combined_parts = []
    
    for i, qa in enumerate(question_answers, 1):
        question = qa.get("question", f"Question {i}")
        answer = qa.get("answer", "No answer provided")
        
        # Clean question - remove trailing question mark for header
        question_clean = question.strip()
        if question_clean.endswith('?'):
            question_clean = question_clean[:-1].strip()
        
        # Clean answer - ensure proper spacing
        answer_clean = answer.strip()
        
        # Format with markdown: Bold question header, then answer with proper spacing
        # Use double newlines for paragraph breaks
        combined_parts.append(f"**{question_clean}:**\n\n{answer_clean}")
    
    # Join with horizontal rule separator for clear visual separation
    return "\n\n---\n\n".join(combined_parts)

