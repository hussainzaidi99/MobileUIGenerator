// frontend/src/utils/errorMessages.js
/**
 * Map HTTP status codes and error codes to user-friendly messages
 */

export const ERROR_MESSAGES = {
    // ============================================================================
    // AUTHENTICATION ERRORS
    // ============================================================================
    INVALID_EMAIL: {
        title: "Invalid email",
        description: "Please enter a valid email address (e.g., user@example.com)"
    },
    EMAIL_EXISTS: {
        title: "Email already registered",
        description: "This email is already in use. Try logging in instead."
    },
    WEAK_PASSWORD: {
        title: "Weak password",
        description: "Password must be at least 8 characters with uppercase, lowercase, numbers, and special characters"
    },
    INVALID_USERNAME: {
        title: "Invalid username",
        description: "Username must be 3-20 characters (letters, numbers, and underscores only)"
    },
    INVALID_NAME: {
        title: "Invalid name",
        description: "Name must be at least 2 characters long"
    },
    INVALID_CREDENTIALS: {
        title: "Login failed",
        description: "Email or password is incorrect. Please try again."
    },
    EMAIL_NOT_VERIFIED: {
        title: "Email not verified",
        description: "Please check your inbox and verify your email before logging in."
    },
    ACCOUNT_LOCKED: {
        title: "Account locked",
        description: "Your account has been temporarily locked. Try again in 15 minutes."
    },

    // ============================================================================
    // PAYMENT ERRORS
    // ============================================================================
    INSUFFICIENT_CREDITS: {
        title: "Insufficient credits",
        description: "You don't have enough credits. Purchase more to continue."
    },
    INVALID_PACKAGE: {
        title: "Invalid package",
        description: "Selected package is not available. Please choose a valid plan."
    },
    PAYMENT_UNAVAILABLE: {
        title: "Payment unavailable",
        description: "Payment processing is temporarily unavailable. Please try again later."
    },
    STRIPE_ERROR: {
        title: "Payment failed",
        description: "Unable to process payment. Please try again or contact support."
    },

    // ============================================================================
    // GENERATION ERRORS
    // ============================================================================
    EMPTY_PROMPT: {
        title: "Empty prompt",
        description: "Please describe the app you want to create"
    },
    PROMPT_TOO_SHORT: {
        title: "Prompt too short",
        description: "Please provide more details about your app (at least 10 characters)"
    },
    PROMPT_TOO_LONG: {
        title: "Prompt too long",
        description: "Your description is too long. Please keep it under 1000 characters."
    },
    INVALID_PROMPT: {
        title: "Invalid prompt",
        description: "Please describe your app in more detail"
    },
    GENERATION_FAILED: {
        title: "Generation failed",
        description: "Unable to generate your app. Please try rephrasing your request."
    },
    LLM_TIMEOUT: {
        title: "Request timeout",
        description: "This is taking too long. Try simplifying your request."
    },
    LLM_RATE_LIMIT: {
        title: "Too many requests",
        description: "We're experiencing high demand. Please try again in a few moments."
    },

    // ============================================================================
    // SESSION ERRORS
    // ============================================================================
    INVALID_SESSION: {
        title: "Session expired",
        description: "Your editing session has expired. Please generate a new app."
    },
    SESSION_NOT_FOUND: {
        title: "Project not found",
        description: "This project no longer exists or has been deleted."
    },
    SESSION_EXPIRED: {
        title: "Session expired",
        description: "This editing session has expired. Please start a new project."
    },
    UNAUTHORIZED_EDIT: {
        title: "Access denied",
        description: "You don't have permission to edit this project."
    },

    // ============================================================================
    // EXPORT ERRORS
    // ============================================================================
    NO_CODE_PROVIDED: {
        title: "No code available",
        description: "No code available to export. Please generate an app first."
    },
    EXPORT_FAILED: {
        title: "Export failed",
        description: "Unable to create export file. Please try again."
    },

    // ============================================================================
    // NETWORK ERRORS
    // ============================================================================
    NETWORK_ERROR: {
        title: "Connection error",
        description: "Unable to reach server. Check your internet connection."
    },

    // ============================================================================
    // GENERIC ERRORS
    // ============================================================================
    TECHNICAL_DIFFICULTY: {
        title: "Something went wrong",
        description: "We're experiencing technical difficulties. Please try again."
    },
    UNAUTHORIZED: {
        title: "Not logged in",
        description: "Please log in to continue."
    },

    // ============================================================================
    // HTTP STATUS CODES
    // ============================================================================
    400: {
        title: "Invalid input",
        description: "Please check your information and try again"
    },
    401: {
        title: "Incorrect password",
        description: "The password you entered is incorrect"
    },
    402: {
        title: "Insufficient credits",
        description: "You need more credits to continue"
    },
    403: {
        title: "Access denied",
        description: "You don't have permission for this action"
    },
    404: {
        title: "Account not found",
        description: "No account exists with this email"
    },
    409: {
        title: "Already exists",
        description: "This resource already exists"
    },
    422: {
        title: "Invalid data",
        description: "Some information is incorrect or missing"
    },
    429: {
        title: "Too many requests",
        description: "Please wait a moment before trying again"
    },
    500: {
        title: "Something went wrong",
        description: "An unexpected error occurred. We've been notified"
    },
    503: {
        title: "Service unavailable",
        description: "Our servers are temporarily unavailable"
    },
    504: {
        title: "Request timeout",
        description: "This took too long. Try simplifying your request"
    }
};

/**
 * Get user-friendly error message from error response
 * @param {Object} error - Error object from API or catch block
 * @returns {Object} { title, description }
 */
export function getErrorMessage(error) {
    // Check for error_code from backend
    if (error?.error_code && ERROR_MESSAGES[error.error_code]) {
        return ERROR_MESSAGES[error.error_code];
    }

    // Check for HTTP status code
    if (error?.status && ERROR_MESSAGES[error.status]) {
        return ERROR_MESSAGES[error.status];
    }

    // Check for network error
    if (error?.message === 'Failed to fetch' || error?.message === 'Network Error') {
        return ERROR_MESSAGES.NETWORK_ERROR;
    }

    // Check for error message in response
    if (error?.error && typeof error.error === 'string') {
        // Try to match error message to known errors
        const errorText = error.error.toLowerCase();

        if (errorText.includes('email') && errorText.includes('invalid')) {
            return ERROR_MESSAGES.INVALID_EMAIL;
        }
        if (errorText.includes('password') && errorText.includes('incorrect')) {
            return ERROR_MESSAGES.INVALID_CREDENTIALS;
        }
        if (errorText.includes('verify') && errorText.includes('email')) {
            return ERROR_MESSAGES.EMAIL_NOT_VERIFIED;
        }

        // Return custom message if available
        return {
            title: "Error",
            description: error.error
        };
    }

    // Default fallback
    return ERROR_MESSAGES.TECHNICAL_DIFFICULTY;
}

/**
 * Handle API error and show toast
 * @param {Object} error - Error object
 * @param {Function} toastFn - Toast function to call
 */
export function handleApiError(error, toastFn) {
    const errorMsg = getErrorMessage(error);
    toastFn(errorMsg.title, errorMsg.description);
}
