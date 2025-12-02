"""
Validation Utilities
Input validation and sanitization functions.
"""

from typing import Optional
from pathlib import Path
from app.config import settings
from fastapi import HTTPException, status


def validate_file_extension(filename: str) -> bool:
    """
    Validate that the file has an allowed extension.
    
    Args:
        filename: Name of the file to validate
        
    Returns:
        True if extension is allowed
        
    Raises:
        HTTPException: If extension is not allowed
    """
    file_path = Path(filename)
    extension = file_path.suffix.lower()
    
    allowed_extensions = settings.allowed_extensions_list
    
    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{extension}' not allowed. "
                   f"Allowed extensions: {', '.join(allowed_extensions)}"
        )
    
    return True


def validate_file_size(file_size: int, max_size_mb: Optional[int] = None) -> bool:
    """
    Validate that the file size is within limits.
    
    Args:
        file_size: Size of the file in bytes
        max_size_mb: Maximum allowed size in MB (uses config default if None)
        
    Returns:
        True if size is valid
        
    Raises:
        HTTPException: If file size exceeds limit
    """
    if max_size_mb is None:
        max_size_mb = settings.max_upload_size_mb
    
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds "
                   f"maximum allowed size ({max_size_mb} MB)"
        )
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and other issues.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components, keep only the filename
    path = Path(filename)
    clean_name = path.name
    
    # Replace potentially dangerous characters
    dangerous_chars = ['..', '/', '\\', '\x00']
    for char in dangerous_chars:
        clean_name = clean_name.replace(char, '_')
    
    return clean_name


def validate_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
        
    Raises:
        HTTPException: If email format is invalid
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    return True


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength.
    
    Requirements:
    - At least 8 characters
    - Contains uppercase and lowercase letters
    - Contains at least one digit
    - Contains at least one special character
    
    Args:
        password: Password to validate
        
    Returns:
        True if password meets requirements
        
    Raises:
        HTTPException: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    if not any(char.isupper() for char in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )
    
    if not any(char.islower() for char in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )
    
    if not any(char.isdigit() for char in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one digit"
        )
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(char in special_chars for char in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one special character"
        )
    
    return True

