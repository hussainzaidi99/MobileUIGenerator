# backend/Auth/auth_models.py - Pydantic Models for Authentication
# (UPDATED with Google OAuth, Email Verification & Reset Code models)
"""
Type-safe authentication models with validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

# ============================================================================
# REQUEST MODELS
# ============================================================================


class UserSignupRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    username: str = Field(..., min_length=3, max_length=30)
    full_name: Optional[str] = Field(None, max_length=100)

    @validator("password")
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @validator("username")
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()


class UserLoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


# ============================================================================
# 🆕 GOOGLE OAUTH MODELS
# ============================================================================


class GoogleAuthRequest(BaseModel):
    """Google OAuth authentication request"""
    id_token: str = Field(..., description="Google ID token from OAuth flow")

    @validator("id_token")
    def validate_id_token(cls, v: str) -> str:
        """Basic validation for ID token format"""
        if not v or len(v) < 50:
            raise ValueError("Invalid Google ID token format")
        return v


class GoogleUserInfo(BaseModel):
    """Google user information extracted from ID token"""
    sub: str  # Google user ID (unique identifier)
    email: str
    email_verified: bool = True
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None


# ============================================================================
# 🆕 EMAIL VERIFICATION MODELS
# ============================================================================


class EmailVerificationRequest(BaseModel):
    """
    Request to send a verification email.
    type: "signup", "password_reset", "change_email", etc.
    """
    email: EmailStr
    type: Optional[str] = "signup"


class EmailVerificationConfirm(BaseModel):
    """
    Request to confirm a verification code sent by email.
    Used by /auth/verify-email or similar routes.
    """
    email: EmailStr
    code: str
    type: Optional[str] = "signup"


# ============================================================================
# TOKEN & PASSWORD MODELS
# ============================================================================


class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """
    Start password reset flow (send reset email/code).
    Usually used by: POST /auth/password/reset/request
    """
    email: EmailStr


class PasswordResetCodeRequest(BaseModel):
    """
    Verify a password reset code (if using code-based reset).
    Usually used by: POST /auth/password/reset/verify
    """
    email: EmailStr
    code: str


class PasswordResetCodeVerify(PasswordResetCodeRequest):
    """
    Alias for PasswordResetCodeRequest, kept for backward compatibility.
    Some routes may import PasswordResetCodeVerify explicitly.
    """
    pass


class PasswordResetWithCode(BaseModel):
    """
    Reset password directly with email + code + new password.
    Likely used by something like: POST /auth/password/reset/with-code
    """
    email: EmailStr
    code: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordResetConfirm(BaseModel):
    """
    Confirm password reset with a token/code and set new password.
    Usually used by: POST /auth/password/reset/confirm
    """
    reset_token: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ============================================================================
# RESPONSE MODELS
# ============================================================================


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User data response (without sensitive info)"""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    created_at: datetime
    is_active: bool
    is_verified: bool
    role: str = "user"
    # 🆕 Google OAuth fields
    google_id: Optional[str] = None
    picture_url: Optional[str] = None
    auth_provider: str = "local"  # "local" or "google"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class LoginResponse(BaseModel):
    """Complete login response"""
    user: UserResponse
    tokens: TokenResponse


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


# ============================================================================
# INTERNAL MODELS (Database)
# ============================================================================


class UserInDB(BaseModel):
    """User model as stored in database"""
    email: str
    username: str
    hashed_password: Optional[str] = None  # Optional for Google users
    full_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    is_verified: bool = False
    role: str = "user"
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
    last_login: Optional[datetime] = None
    # 🆕 Google OAuth fields
    google_id: Optional[str] = None  # Google "sub" field
    picture_url: Optional[str] = None
    auth_provider: str = "local"  # "local", "google", or "both"


class SessionInDB(BaseModel):
    """Session model as stored in database"""
    user_id: str
    refresh_token: str
    access_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    is_active: bool = True


class EmailVerificationInDB(BaseModel):
    """
    Email verification record as stored in database.
    Mirrors the indexes you set up in database.py (email, type, user_id, code, expires_at).
    """
    email: EmailStr
    type: str = "signup"  # "signup", "password_reset", etc.
    user_id: Optional[str] = None
    code: str
    created_at: datetime
    expires_at: datetime
    consumed_at: Optional[datetime] = None


# ============================================================================
# TOKEN PAYLOAD
# ============================================================================


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user_id
    email: str
    username: Optional[str] = None
    role: Optional[str] = "user"
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    type: str  # "access" or "refresh"
