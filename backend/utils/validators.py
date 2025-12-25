# backend/utils/validators.py
"""
Input Validation Helpers
Comprehensive validation functions with user-friendly error messages
"""

import re
from typing import Tuple, Optional


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format
    
    Args:
        email: Email address to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Please enter a valid email address (e.g., user@example.com)"
    
    # RFC 5322 simplified pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email.strip()):
        return False, "Please enter a valid email address (e.g., user@example.com)"
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength
    
    Requirements:
    - At least 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 number (0-9)
    - At least 1 special character (@#$%^&*()_+-=[]{}|;:,.<>?)
    
    Args:
        password: Password to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password must be at least 8 characters with uppercase, lowercase, numbers, and special characters"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters with uppercase, lowercase, numbers, and special characters"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
    
    if not (has_upper and has_lower and has_digit and has_special):
        return False, "Password must be at least 8 characters with uppercase, lowercase, numbers, and special characters"
    
    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username format
    
    Requirements:
    - 3-20 characters
    - Alphanumeric + underscores only
    
    Args:
        username: Username to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Username must be 3-20 characters (letters, numbers, and underscores only)"
    
    username = username.strip()
    
    if len(username) < 3 or len(username) > 20:
        return False, "Username must be 3-20 characters (letters, numbers, and underscores only)"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username must be 3-20 characters (letters, numbers, and underscores only)"
    
    return True, ""


def validate_name(name: str) -> Tuple[bool, str]:
    """
    Validate name
    
    Requirements:
    - At least 2 characters
    
    Args:
        name: Name to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not name or not isinstance(name, str):
        return False, "Name must be at least 2 characters long"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters long"
    
    return True, ""


def validate_prompt(prompt: str) -> Tuple[bool, str]:
    """
    Validate generation prompt
    
    Requirements:
    - Not empty
    - At least 10 characters
    - Maximum 1000 characters
    
    Args:
        prompt: Generation prompt to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not prompt or not isinstance(prompt, str):
        return False, "Please describe the app you want to create (e.g., 'E-commerce app with product listings')"
    
    prompt = prompt.strip()
    
    if not prompt:
        return False, "Please describe the app you want to create (e.g., 'E-commerce app with product listings')"
    
    if len(prompt) < 10:
        return False, "Please provide more details about your app (at least 10 characters)"
    
    if len(prompt) > 1000:
        return False, "Your description is too long. Please keep it under 1000 characters."
    
    return True, ""


def validate_edit_prompt(prompt: str) -> Tuple[bool, str]:
    """
    Validate edit prompt
    
    Requirements:
    - Not empty
    - At least 3 characters
    
    Args:
        prompt: Edit prompt to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not prompt or not isinstance(prompt, str):
        return False, "Please describe what you'd like to change (e.g., 'change button color to blue')"
    
    prompt = prompt.strip()
    
    if not prompt or len(prompt) < 3:
        return False, "Please describe what you'd like to change (e.g., 'change button color to blue')"
    
    return True, ""


def validate_user_id(user_id: str) -> Tuple[bool, str]:
    """
    Validate user ID
    
    Args:
        user_id: User ID to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not user_id or not isinstance(user_id, str):
        return False, "Please log in to continue."
    
    user_id = user_id.strip()
    
    if not user_id:
        return False, "Please log in to continue."
    
    return True, ""


def validate_session_id(session_id: str) -> Tuple[bool, str]:
    """
    Validate session ID
    
    Args:
        session_id: Session ID to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not session_id or not isinstance(session_id, str):
        return False, "Invalid session. Please generate a new app."
    
    session_id = session_id.strip()
    
    if not session_id:
        return False, "Invalid session. Please generate a new app."
    
    return True, ""


def validate_package_id(package_id: str, valid_packages: list) -> Tuple[bool, str]:
    """
    Validate payment package ID
    
    Args:
        package_id: Package ID to validate
        valid_packages: List of valid package IDs
    
    Returns:
        (is_valid, error_message)
    """
    if not package_id or package_id not in valid_packages:
        return False, "Selected package is not available. Please choose a valid plan."
    
    return True, ""


def validate_required_field(value: any, field_name: str) -> Tuple[bool, str]:
    """
    Validate required field
    
    Args:
        value: Field value
        field_name: Name of the field
    
    Returns:
        (is_valid, error_message)
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return False, f"Required field '{field_name}' is missing."
    
    return True, ""
