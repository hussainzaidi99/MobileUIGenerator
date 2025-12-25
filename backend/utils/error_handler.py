# backend/utils/error_handler.py
"""
Professional Error Handling Utility
Provides user-friendly error messages while maintaining detailed developer logs
"""

from typing import Dict, Any, Optional
from fastapi.responses import JSONResponse
import logging
import traceback
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class UserFacingError:
    """User-friendly error messages - NO technical jargon!"""
    
    # ============================================================================
    # AUTHENTICATION ERRORS
    # ============================================================================
    INVALID_EMAIL = "Please enter a valid email address (e.g., user@example.com)"
    EMAIL_EXISTS = "This email is already registered. Try logging in instead."
    WEAK_PASSWORD = "Password must be at least 8 characters with uppercase, lowercase, numbers, and special characters"
    INVALID_USERNAME = "Username must be 3-20 characters (letters, numbers, and underscores only)"
    INVALID_NAME = "Name must be at least 2 characters long"
    INVALID_CREDENTIALS = "Email or password is incorrect. Please try again."
    ACCOUNT_LOCKED = "Your account has been temporarily locked due to multiple failed login attempts. Try again in 15 minutes."
    EMAIL_NOT_VERIFIED = "Please verify your email address before logging in. Check your inbox for the verification link."
    
    # ============================================================================
    # PAYMENT ERRORS
    # ============================================================================
    INVALID_PACKAGE = "Selected package is not available. Please choose a valid plan."
    PAYMENT_UNAVAILABLE = "Payment processing is temporarily unavailable. Please try again later."
    INSUFFICIENT_CREDITS = "You need {required} credits but have {current}. Purchase more credits to continue."
    STRIPE_ERROR = "Unable to process payment. Please try again or contact support."
    
    # ============================================================================
    # GENERATION ERRORS
    # ============================================================================
    EMPTY_PROMPT = "Please describe the app you want to create (e.g., 'E-commerce app with product listings')"
    PROMPT_TOO_SHORT = "Please provide more details about your app (at least 10 characters)"
    PROMPT_TOO_LONG = "Your description is too long. Please keep it under 1000 characters."
    LLM_TIMEOUT = "Generation is taking longer than expected. Please try again with a simpler prompt."
    LLM_RATE_LIMIT = "We're experiencing high demand. Please try again in a few moments."
    GENERATION_FAILED = "Unable to generate your app. Please try rephrasing your request."
    IMAGE_ENRICHMENT_FAILED = "App generated successfully, but some images couldn't be loaded. You can update them later."
    
    # ============================================================================
    # EDIT ERRORS
    # ============================================================================
    INVALID_SESSION = "Your editing session has expired. Please generate a new app."
    UNAUTHORIZED_EDIT = "You don't have permission to edit this project."
    EMPTY_EDIT_PROMPT = "Please describe what you'd like to change (e.g., 'change button color to blue')"
    TOO_MANY_EDITS = "You've reached the maximum number of edits for this session. Please generate a new app."
    EDIT_FAILED = "Unable to apply changes. Please try again or generate a new version."
    PREVIEW_FAILED = "Changes saved but preview couldn't update. Try refreshing the page."
    
    # ============================================================================
    # SESSION ERRORS
    # ============================================================================
    SESSION_NOT_FOUND = "This project no longer exists or has been deleted."
    SESSION_EXPIRED = "This editing session has expired (sessions last 2 hours). Please start a new project."
    CONVERSATION_NOT_FOUND = "This conversation has already been deleted."
    DELETE_FAILED = "Unable to delete project. Please try again."
    
    # ============================================================================
    # EXPORT ERRORS
    # ============================================================================
    NO_CODE_PROVIDED = "No code available to export. Please generate an app first."
    EMPTY_CODE = "Generated code is empty. Please regenerate your app."
    EXPORT_FAILED = "Unable to create export file. Please try again."
    FILE_TOO_LARGE = "Export file is too large. Please contact support for assistance."
    
    # ============================================================================
    # GENERIC ERRORS
    # ============================================================================
    TECHNICAL_DIFFICULTY = "We're experiencing technical difficulties. Please try again in a few moments."
    UNAUTHORIZED = "Please log in to continue."
    MISSING_FIELD = "Required field '{field}' is missing."
    RATE_LIMITED = "Too many requests. Please try again in {minutes} minutes."
    SERVER_ERROR = "Something went wrong on our end. Our team has been notified."


def create_error_response(
    user_message: str,
    status_code: int = 400,
    error_code: str = None,
    developer_details: Optional[Dict[str, Any]] = None,
    log_error: bool = True,
    log_level: str = "error"
) -> JSONResponse:
    """
    Create standardized error response with user-friendly message
    
    Args:
        user_message: Clear, actionable message for users (NO technical jargon!)
        status_code: HTTP status code (400, 401, 403, 404, 500, etc.)
        error_code: Internal error code for tracking (e.g., "INVALID_EMAIL")
        developer_details: Technical details (logged but NOT sent to user)
        log_error: Whether to log the error
        log_level: Logging level ("info", "warning", "error", "critical")
    
    Returns:
        JSONResponse with user-friendly error message
    """
    # Log error with full context (for developers)
    if log_error:
        log_message = (
            f"[{error_code or 'UNKNOWN'}] "
            f"Status: {status_code} | "
            f"User Message: {user_message}"
        )
        
        if developer_details:
            log_message += f" | Details: {developer_details}"
        
        # Log at appropriate level
        if log_level == "critical":
            logger.critical(log_message)
        elif log_level == "error":
            logger.error(log_message)
        elif log_level == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    # Return user-friendly response (NO technical details!)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": user_message,
            "error_code": error_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def log_exception(
    error_code: str,
    exception: Exception,
    context: Optional[Dict[str, Any]] = None
):
    """
    Log exception with full stack trace (for developers)
    
    Args:
        error_code: Internal error code
        exception: The exception that occurred
        context: Additional context (user_id, endpoint, payload, etc.)
    """
    logger.error(
        f"[{error_code}] Exception: {str(exception)}\n"
        f"Context: {context}\n"
        f"Stack Trace:\n{traceback.format_exc()}"
    )


def create_success_response(
    message: str,
    data: Optional[Dict[str, Any]] = None,
    status_code: int = 200
) -> JSONResponse:
    """
    Create standardized success response
    
    Args:
        message: Success message
        data: Response data
        status_code: HTTP status code (default 200)
    
    Returns:
        JSONResponse with success message and data
    """
    response_content = {
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data:
        response_content["data"] = data
    
    return JSONResponse(
        status_code=status_code,
        content=response_content
    )
