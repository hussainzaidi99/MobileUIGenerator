# backend/email_service.py - Production Email Verification & Password Reset Service
"""
Handles:
- Email verification codes (6-digit)
- Password reset codes (6-digit)
- Code generation, validation, and expiration
- Integration with Resend API via HTTPS
"""

import os
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging
import requests

from database import Database

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_API_URL = "https://api.resend.com/emails"

FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@support.vectorlabzfzellc.com")
APP_NAME = os.getenv("APP_NAME", "App Builder")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Code settings
CODE_LENGTH = 6
VERIFICATION_CODE_EXPIRY_MINUTES = 15  # signup / email verification
RESET_CODE_EXPIRY_MINUTES = 15        # password reset

# Safety limits
MAX_CODE_ATTEMPTS = 5
HTTP_TIMEOUT_SECONDS = 10


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_code(length: int = CODE_LENGTH) -> str:
    """Generate a secure numeric verification code of given length."""
    return "".join(random.choices(string.digits, k=length))


def _send_email_via_resend(
    to: str,
    subject: str,
    html: str,
    text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Low-level helper to send an email via Resend HTTP API.

    Returns a dict:
        { "success": bool, "message": str, "data": Optional[dict] }
    """
    if not RESEND_API_KEY:
        logger.error("❌ RESEND_API_KEY not configured; cannot send email.")
        return {
            "success": False,
            "message": "Email sending is not configured on the server.",
        }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "from": FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
    }

    if text:
        payload["text"] = text

    try:
        response = requests.post(
            RESEND_API_URL,
            headers=headers,
            json=payload,
            timeout=HTTP_TIMEOUT_SECONDS,
        )

        if response.status_code in (200, 201):
            logger.info(f"✅ Email sent successfully to: {to}")
            return {
                "success": True,
                "message": "Email sent successfully",
                "data": response.json(),
            }

        logger.error(
            "❌ Failed to send email to %s: %s %s",
            to,
            response.status_code,
            response.text,
        )
        return {
            "success": False,
            "message": f"Failed to send email: {response.text}",
        }

    except Exception as e:
        logger.exception("❌ Email service error")
        return {
            "success": False,
            "message": f"Email service error: {str(e)}",
        }


def _store_code(
    *,
    email: str,
    code: str,
    code_type: str,
    user_id: Optional[str] = None,
    expires_in_minutes: int = VERIFICATION_CODE_EXPIRY_MINUTES,
) -> bool:
    """
    Store a verification/reset code in the email_verifications collection.

    code_type:
      - "email_verification" for signup email verification
      - "password_reset"     for password reset
    """
    try:
        collection = Database.get_collection("email_verifications")
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=expires_in_minutes)

        # Invalidate any previous unused codes for this user/type
        query: Dict[str, Any] = {
            "email": email.lower(),
            "type": code_type,
            "is_used": False,
        }

        # If we have a user_id, narrow the invalidation to that user
        if user_id:
            query["user_id"] = str(user_id)

        collection.update_many(query, {"$set": {"is_used": True}})

        doc = {
            "user_id": str(user_id) if user_id is not None else None,
            "email": email.lower(),
            "code": code,
            "type": code_type,
            "created_at": now,
            "expires_at": expires_at,
            "is_used": False,
            "attempts": 0,
        }

        collection.insert_one(doc)
        logger.info(
            "✅ Stored %s code for %s (user_id=%s)",
            code_type,
            email,
            user_id,
        )
        return True

    except Exception as e:
        logger.exception("❌ Failed to store %s code for %s", code_type, email)
        return False


def _verify_code_common(
    *,
    email: str,
    code: str,
    code_type: str,
) -> Dict[str, Any]:
    """
    Common logic to verify a 6-digit code in email_verifications.

    Returns dict with:
        success: bool
        message: str
        verification: Optional[dict]  # raw Mongo doc, when success=True
    """
    collection = Database.get_collection("email_verifications")

    verification = collection.find_one(
        {
            "email": email.lower(),
            "code": code,
            "type": code_type,
            "is_used": False,
        }
    )

    if not verification:
        logger.warning("⚠️ Invalid %s code for email=%s", code_type, email)
        return {
            "success": False,
            "message": "Invalid code",
        }

    now = datetime.now(timezone.utc)
    expires_at = verification["expires_at"]

    # Normalize naive datetime to UTC if needed
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        logger.warning("⚠️ Expired %s code for email=%s", code_type, email)
        return {
            "success": False,
            "message": "Code has expired. Please request a new one.",
        }

    attempts = verification.get("attempts", 0) + 1
    if attempts > MAX_CODE_ATTEMPTS:
        logger.warning(
            "⚠️ Too many %s code attempts for email=%s", code_type, email
        )
        # Optionally mark as used/blocked here
        collection.update_one(
            {"_id": verification["_id"]},
            {"$set": {"attempts": attempts, "blocked_at": now}},
        )
        return {
            "success": False,
            "message": "Too many attempts. Please request a new code.",
        }

    # Update attempts (but not yet marking as used; caller can mark)
    collection.update_one(
        {"_id": verification["_id"]},
        {"$set": {"attempts": attempts}},
    )

    return {
        "success": True,
        "message": "Code is valid",
        "verification": verification,
    }


# ============================================================================
# EMAIL SERVICE
# ============================================================================

class EmailService:
    """Email service for verification and password reset flows."""

    # ----------------------------------------------------------------------
    # SIGNUP EMAIL VERIFICATION
    # ----------------------------------------------------------------------

    @staticmethod
    async def send_verification_email(
        email: str, username: str, user_id: str
    ) -> bool:
        """
        Send signup/email-verification code to user and store it in DB.

        type: "email_verification"
        """
        code = generate_code()

        stored = _store_code(
            email=email,
            code=code,
            code_type="email_verification",
            user_id=user_id,
            expires_in_minutes=VERIFICATION_CODE_EXPIRY_MINUTES,
        )
        if not stored:
            return False

        subject = f"Verify your {APP_NAME} account"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 16px;
                    padding: 40px;
                    color: white;
                }}
                .code-box {{
                    background: white;
                    color: #667eea;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(255,255,255,0.3);
                    font-size: 14px;
                    opacity: 0.9;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎉 Welcome to {APP_NAME}!</h1>
                <p>Hi <strong>{username}</strong>,</p>
                <p>Thank you for signing up! To complete your registration, please verify your email address using the code below:</p>
                
                <div class="code-box">
                    {code}
                </div>
                
                <p>This code will expire in <strong>{VERIFICATION_CODE_EXPIRY_MINUTES} minutes</strong>.</p>
                
                <p>If you didn't create an account with {APP_NAME}, you can safely ignore this email.</p>
                
                <div class="footer">
                    <p>Best regards,<br>The {APP_NAME} Team</p>
                    <p style="font-size: 12px; opacity: 0.8;">
                        This is an automated email, please do not reply.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        text = f"""
Welcome to {APP_NAME}!

Hi {username},

Thank you for signing up! To complete your registration, please verify your email address using the code below:

Verification Code: {code}

This code will expire in {VERIFICATION_CODE_EXPIRY_MINUTES} minutes.

If you didn't create an account with {APP_NAME}, you can safely ignore this email.

Best regards,
The {APP_NAME} Team
        """.strip()

        result = _send_email_via_resend(email, subject, html, text)

        if result["success"]:
            logger.info("✅ Verification email sent to %s", email)
            return True

        logger.error("❌ Failed to send verification email to %s", email)
        return False

    @staticmethod
    async def verify_email_code(email: str, code: str) -> Dict[str, Any]:
        """
        Verify a signup/email-verification code and mark user as verified.
        """
        result = _verify_code_common(
            email=email,
            code=code,
            code_type="email_verification",
        )

        if not result["success"]:
            return {
                "success": False,
                "message": result["message"],
            }

        verification = result["verification"]
        collection = Database.get_collection("email_verifications")
        users_collection = Database.get_collection("users")

        now = datetime.now(timezone.utc)

        # Mark code as used + verified_at
        collection.update_one(
            {"_id": verification["_id"]},
            {"$set": {"is_used": True, "verified_at": now}},
        )

        # Mark user as verified (if we have a user_id)
        user_id = verification.get("user_id")
        if user_id:
            from bson import ObjectId

            users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_verified": True, "updated_at": now}},
            )
            logger.info("✅ Email verified & user marked as verified: %s", email)
        else:
            logger.warning(
                "⚠️ Verification document for %s had no user_id; email verified but user not updated.",
                email,
            )

        return {
            "success": True,
            "message": "Email verified successfully!",
        }

    # ----------------------------------------------------------------------
    # PASSWORD RESET
    # ----------------------------------------------------------------------

    @staticmethod
    async def send_password_reset_email(email: str, username: str) -> bool:
        """
        Send password reset code if user exists.
        - Does not leak whether the email is registered (returns True either way).
        - For Google-only users, sends a Google-specific info email instead.
        """
        users_collection = Database.get_collection("users")

        user = users_collection.find_one({"email": email.lower()})
        if not user:
            # Do NOT reveal that the user doesn't exist for security reasons.
            logger.warning("⚠️ Password reset requested for non-existent email: %s", email)
            return True

        # Google-only account (no password)
        if user.get("auth_provider") == "google" and not user.get("hashed_password"):
            logger.warning(
                "⚠️ Password reset requested for Google-only user: %s", email
            )
            return await EmailService.send_google_user_notification(email, username)

        # Regular password reset
        code = generate_code()

        stored = _store_code(
            email=email,
            code=code,
            code_type="password_reset",
            user_id=str(user["_id"]),
            expires_in_minutes=RESET_CODE_EXPIRY_MINUTES,
        )
        if not stored:
            # To avoid leaking internal failures, return True but log error
            logger.error("❌ Failed to store password reset code for %s", email)
            return True

        subject = f"Reset your {APP_NAME} password"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    border-radius: 16px;
                    padding: 40px;
                    color: white;
                }}
                .code-box {{
                    background: white;
                    color: #f5576c;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .warning {{
                    background: rgba(255, 255, 255, 0.2);
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(255,255,255,0.3);
                    font-size: 14px;
                    opacity: 0.9;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔐 Password Reset Request</h1>
                <p>Hi <strong>{username}</strong>,</p>
                <p>We received a request to reset your password. Use the code below to reset it:</p>
                
                <div class="code-box">
                    {code}
                </div>
                
                <p>This code will expire in <strong>{RESET_CODE_EXPIRY_MINUTES} minutes</strong>.</p>
                
                <div class="warning">
                    <strong>⚠️ Security Alert:</strong>
                    <p>If you didn't request this password reset, please ignore this email and ensure your account is secure.</p>
                </div>
                
                <div class="footer">
                    <p>Best regards,<br>The {APP_NAME} Team</p>
                    <p style="font-size: 12px; opacity: 0.8;">
                        This is an automated email, please do not reply.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        text = f"""
Password Reset Request

Hi {username},

We received a request to reset your password. Use the code below to reset it:

Reset Code: {code}

This code will expire in {RESET_CODE_EXPIRY_MINUTES} minutes.

Security Alert: If you didn't request this password reset, please ignore this email and ensure your account is secure.

Best regards,
The {APP_NAME} Team
        """.strip()

        result = _send_email_via_resend(email, subject, html, text)

        if result["success"]:
            logger.info("✅ Password reset email sent to %s", email)
            return True

        logger.error("❌ Failed to send password reset email to %s", email)
        # Still return True to avoid leaking failures to client
        return True

    @staticmethod
    async def verify_reset_code(email: str, code: str) -> Dict[str, Any]:
        """
        Verify password reset code.

        Returns:
            {
                "success": bool,
                "message": str,
                "reset_token": Optional[str]  # verification _id as token
            }
        """
        result = _verify_code_common(
            email=email,
            code=code,
            code_type="password_reset",
        )

        if not result["success"]:
            return {
                "success": False,
                "message": result["message"],
            }

        verification = result["verification"]
        collection = Database.get_collection("email_verifications")
        now = datetime.now(timezone.utc)

        # Mark code as used
        collection.update_one(
            {"_id": verification["_id"]},
            {"$set": {"is_used": True, "used_at": now}},
        )

        logger.info("✅ Password reset code verified for %s", email)

        return {
            "success": True,
            "message": "Reset code verified",
            "reset_token": str(verification["_id"]),  # can be used to confirm reset
        }

    # ----------------------------------------------------------------------
    # GOOGLE-ONLY USER NOTIFICATION
    # ----------------------------------------------------------------------

    @staticmethod
    async def send_google_user_notification(email: str, username: str) -> bool:
        """
        Notify Google-only users that they must use Google Sign-In
        instead of password reset.
        """
        subject = f"{APP_NAME} - Account uses Google Sign-In"

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Hi {username},</h2>
            <p>You requested a password reset, but your account uses <strong>Google Sign-In</strong>.</p>
            <p>To access your account, please use the "Sign in with Google" button on our login page.</p>
            <p>If you'd like to set up password login as well, please contact our support team.</p>
            <p>Best regards,<br>The {APP_NAME} Team</p>
        </body>
        </html>
        """

        text = (
            f"Hi {username}, your account uses Google Sign-In. "
            f"Please use the Google Sign-In button to access your account."
        )

        result = _send_email_via_resend(email, subject, html, text)
        return bool(result.get("success"))
