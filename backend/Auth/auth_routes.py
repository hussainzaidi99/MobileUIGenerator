# backend/Auth/auth_routes.py - Authentication API Routes (UPDATED with Google OAuth)
"""
FastAPI authentication endpoints with:
- Rate limiting
- Request validation
- Security headers
- Proper error handling
- 🆕 Google OAuth endpoint
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone  # ✅ ADD THIS LINE AT TOP
from bson import ObjectId  # ✅ ADD THIS IF NOT PRESENT
from typing import Optional
import logging
import os

from Auth.auth_models import (
    UserSignupRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    GoogleAuthRequest,
    EmailVerificationConfirm,
    PasswordResetRequest, 
    PasswordResetCodeRequest,
    PasswordResetCodeVerify,
    PasswordResetWithCode,
    LoginResponse,
    MessageResponse,
    TokenResponse,
    UserResponse
)
from Auth.auth_service import AuthService
from db.database import get_users_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# ============================================================================
# DEPENDENCY: Get Current User (unchanged)
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    
    token_payload = AuthService.verify_token(token, token_type="access")
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = await AuthService.get_user_by_id(token_payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Optional authentication - returns None if not authenticated"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# ============================================================================
# PUBLIC ENDPOINTS (existing - unchanged)
# ============================================================================

@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: UserSignupRequest, http_request: Request):
    """Register a new user with email/password"""
    try:
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        
        user = await AuthService.create_user(
            email=request.email,
            password=request.password,
            username=request.username,
            full_name=request.full_name
        )
        
        tokens = await AuthService.create_session(
            user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        user_response = AuthService.user_to_response(user)
        
        # 🆕 Send verification email asynchronously
        try:
            from Services.email_service import EmailService
            await EmailService.send_verification_email(
                email=user["email"],
                username=user["username"],
                user_id=str(user["_id"])
            )
            logger.info(f"📧 Verification email sent to: {request.email}")
        except Exception as e:
            logger.error(f"⚠️ Failed to send verification email: {e}")
            # Don't fail signup if email fails
        
        logger.info(f"✅ User signup successful: {request.email}")
        
        return LoginResponse(user=user_response, tokens=tokens)
        
    except ValueError as e:
        logger.warning(f"Signup validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: UserLoginRequest, http_request: Request):
    """Login with email and password"""
    try:
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        
        user = await AuthService.authenticate_user(
            email=request.email,
            password=request.password,
            ip_address=ip_address
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        tokens = await AuthService.create_session(
            user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        user_response = AuthService.user_to_response(user)
        
        logger.info(f"✅ Login successful: {request.email}")
        
        return LoginResponse(user=user_response, tokens=tokens)
        
    except ValueError as e:
        logger.warning(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


# backend/Auth/auth_routes.py - Updated google_auth function
# Replace your existing google_auth function with this:

@router.post("/google", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def google_auth(request: GoogleAuthRequest, http_request: Request):
    """
    Authenticate with Google OAuth.
    
    - **id_token**: Google user info (JSON string) OR Google ID token (JWT)
    
    This endpoint:
    1. Accepts user info from Google (via access token flow)
    2. Creates new user if doesn't exist, or logs in existing user
    3. Awards free tier credits to new users (if slots available)
    4. Returns JWT tokens for your app (same as /login)
    
    **Account Linking:**
    - If email exists with password auth → links Google account (auth_provider = "both")
    - If email exists with Google auth → logs in
    - If email doesn't exist → creates new user with Google auth
    
    **Security:**
    - Accepts verified user info from Google's userinfo endpoint
    - Records IP and user agent for security audit
    - Only accepts verified Google emails
    """
    try:
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        
        logger.info(f"🔐 Google auth attempt from IP: {ip_address}")
        
        # Try to parse as JSON (user info from frontend)
        try:
            import json
            user_info = json.loads(request.id_token)
            
            # Validate required fields
            if not user_info.get('email') or not user_info.get('sub'):
                raise ValueError("Missing required fields: email and sub")
            
            email = user_info['email'].lower()
            google_id = user_info['sub']
            full_name = user_info.get('name', '')
            email_verified = user_info.get('email_verified', True)
            picture = user_info.get('picture', '')
            
            logger.info(f"✅ Received Google user info for: {email}")
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: Try as Google ID token (JWT) - original flow
            logger.info(f"Attempting to verify as Google ID token...")
            user = await AuthService.authenticate_with_google(
                google_token=request.id_token,
                ip_address=ip_address
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google authentication failed. Invalid token."
                )
            
            # Create session and return (original flow)
            tokens = await AuthService.create_session(
                user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            user_response = AuthService.user_to_response(user)
            
            tier = user.get("tier", "unknown")
            credits = user.get("credits", 0)
            logger.info(
                f"✅ Google auth successful (ID token flow): {user['email']} | "
                f"Tier: {tier} | Credits: {credits}"
            )
            
            return LoginResponse(user=user_response, tokens=tokens)
        
        # Process user info (new popup flow)
        if not email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google email not verified"
            )
        
        # Get user collection
        users_collection = get_users_collection()
        
        # Check if user exists
        user = await users_collection.find_one({"email": email})
        
        now = datetime.now(timezone.utc)  # ✅ Define now HERE at the top
        
        if user:
            # Existing user - update Google info
            auth_provider = user.get("auth_provider", "local")
            
            if not user.get("google_id"):
                # Link Google account
                await users_collection.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "google_id": google_id,
                            "picture_url": picture,
                            "is_verified": True,
                            "auth_provider": "both" if auth_provider == "local" else "google",
                            "last_login": now,
                            "updated_at": now
                        }
                    }
                )
                logger.info(f"🔗 Linked Google account to existing user: {email}")
            else:
                # Just update last login
                await users_collection.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "last_login": now,
                            "updated_at": now
                        }
                    }
                )
            
            # Fetch updated user
            user = await users_collection.find_one({"_id": user["_id"]})
            
        else:
            # New user - create with Google
            from Services.tier_manager import TierManager
            
            base_username = email.split('@')[0] or full_name.replace(' ', '').lower()
            username = base_username
            
            counter = 1
            while await users_collection.find_one({"username": username}):
                username = f"{base_username}{counter}"
                counter += 1
            
            new_user = {
                "email": email,
                "username": username,
                "hashed_password": None,
                "full_name": full_name,
                "created_at": now,
                "updated_at": now,
                "is_active": True,
                "is_verified": True,
                "role": "user",
                "login_attempts": 0,
                "locked_until": None,
                "last_login": now,
                "google_id": google_id,
                "picture_url": picture,
                "auth_provider": "google",
                "total_spent": 0.0,
                "purchase_history": [],
                "usage_history": [],
                "last_purchase": None,
            }
            
            result = await users_collection.insert_one(new_user)
            user_id = result.inserted_id
            
            # Initialize tier
            tier_result = await TierManager.initialize_user_tier(user_id)
            
            # Fetch complete user
            user = await users_collection.find_one({"_id": user_id})
            
            logger.info(
                f"✅ New Google user created: {email} | "
                f"Tier: {tier_result['tier']} | Credits: {tier_result['credits']}"
            )
        
        # Create session
        tokens = await AuthService.create_session(
            user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Prepare response
        user_response = AuthService.user_to_response(user)
        
        tier = user.get("tier", "unknown")
        credits = user.get("credits", 0)
        logger.info(
            f"✅ Google auth successful: {email} | "
            f"Tier: {tier} | Credits: {credits}"
        )
        
        return LoginResponse(user=user_response, tokens=tokens)
        
    except ValueError as e:
        logger.warning(f"⚠️ Google auth validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Google auth unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed. Please try again or contact support."
        )

# ============================================================================
# OTHER ENDPOINTS (unchanged)
# ============================================================================

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: TokenRefreshRequest):
    """Refresh access token using refresh token"""
    try:
        tokens = await AuthService.refresh_session(request.refresh_token)
        
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        logger.info("✅ Token refreshed successfully")
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(request: TokenRefreshRequest):
    """Logout user by invalidating refresh token"""
    try:
        success = await AuthService.logout(request.refresh_token)
        
        if not success:
            logger.warning("Logout attempt with invalid token")
        
        return MessageResponse(
            message="Logged out successfully",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        return MessageResponse(
            message="Logged out",
            success=True
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return AuthService.user_to_response(user)


@router.get("/verify", response_model=MessageResponse)
async def verify_token_endpoint(user: dict = Depends(get_current_user)):
    """Verify if access token is valid"""
    return MessageResponse(
        message="Token is valid",
        success=True
    )


@router.get("/health")
async def auth_health_check():
    """Check if auth system is operational"""
    from db.database import Database
    
    db_healthy = await Database.health_check()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "auth_service": "operational",
        "google_oauth": "configured" if AuthService.hash_password else "not configured",
        "email_service": "configured" if os.getenv("RESEND_API_KEY") else "not configured"
    }

# backend/auth_routes.py - FIXED: Email verification endpoints
# Replace lines 265-315 with this:

# ============================================================================
# 🆕 EMAIL VERIFICATION ENDPOINTS (PUBLIC - NO AUTH REQUIRED)
# ============================================================================

@router.post("/verify-email/send", response_model=MessageResponse)
async def send_verification_email(user: dict = Depends(get_current_user)):
    """
    Send verification email to current user.
    Only works for unverified users.
    REQUIRES AUTH: User must be logged in.
    """
    from Services.email_service import EmailService
    
    try:
        # Check if already verified
        if user.get("is_verified", False):
            return MessageResponse(
                message="Email already verified",
                success=True
            )
        
        # Send verification email
        success = await EmailService.send_verification_email(
            email=user["email"],
            username=user["username"],
            user_id=str(user["_id"])
        )
        
        if success:
            logger.info(f"✅ Verification email sent to: {user['email']}")
            return MessageResponse(
                message="Verification code sent to your email",
                success=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
    
    except Exception as e:
        logger.error(f"Send verification email error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.post("/verify-email/confirm", response_model=MessageResponse)
async def confirm_email_verification(request: EmailVerificationConfirm):
    """
    Verify email with 6-digit code.
    PUBLIC ENDPOINT - No authentication required.
    
    This is intentionally public because:
    1. User hasn't logged in yet during signup flow
    2. They just created account and received code via email
    3. The 6-digit code provides sufficient security:
       - Expires in 15 minutes
       - Max 5 attempts
       - One-time use
       - Rate limited per email
    """
    from Services.email_service import EmailService
    
    try:
        # Verify code
        result = await EmailService.verify_email_code(request.email, request.code)
        
        if result["success"]:
            logger.info(f"✅ Email verified (public endpoint): {request.email}")
            return MessageResponse(
                message=result["message"],
                success=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


# ============================================================================
# 🆕 PASSWORD RESET WITH EMAIL CODE (PUBLIC - NO AUTH REQUIRED)
# ============================================================================

@router.post("/password-reset/send-code", response_model=MessageResponse)
async def send_password_reset_code(request: PasswordResetRequest):
    """
    Send password reset code to user's email.
    PUBLIC ENDPOINT - No authentication required.
    Works for both verified and unverified users.
    Returns success even if email doesn't exist (security best practice).
    """
    from Services.email_service import EmailService
    
    try:
        # Get user to find username
        users_collection = get_users_collection()
        user = await users_collection.find_one({"email": request.email.lower()})
        
        username = user.get("username", "User") if user else "User"
        
        # Send reset email (returns True even if user doesn't exist for security)
        await EmailService.send_password_reset_email(request.email, username)
        
        logger.info(f"📧 Password reset code requested for: {request.email}")
        
        return MessageResponse(
            message="If your email is registered, you'll receive a reset code shortly",
            success=True
        )
    
    except Exception as e:
        logger.error(f"Send reset code error: {e}", exc_info=True)
        # Don't reveal error to user (security)
        return MessageResponse(
            message="If your email is registered, you'll receive a reset code shortly",
            success=True
        )


@router.post("/password-reset/verify-code", response_model=MessageResponse)
async def verify_password_reset_code(request: PasswordResetCodeVerify):
    """
    Verify password reset code without resetting password.
    PUBLIC ENDPOINT - No authentication required.
    Returns success if code is valid.
    """
    from Services.email_service import EmailService
    
    try:
        result = await EmailService.verify_reset_code(request.email, request.code)
        
        if result["success"]:
            return MessageResponse(
                message="Code verified successfully",
                success=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verify reset code error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Code verification failed"
        )


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def reset_password_with_code(request: PasswordResetWithCode):
    """
    Reset password using verified code.
    PUBLIC ENDPOINT - No authentication required.
    Code must be valid and not expired.
    """
    from Services.email_service import EmailService
    
    try:
        # Verify code first
        verification_result = await EmailService.verify_reset_code(request.email, request.code)
        
        if not verification_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification_result["message"]
            )
        
        # Get user
        users_collection = get_users_collection()
        user = await users_collection.find_one({"email": request.email.lower()})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash new password
        from datetime import datetime, timezone
        hashed_password = AuthService.hash_password(request.new_password)
        
        # Update password
        await users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "updated_at": datetime.now(timezone.utc),
                    "login_attempts": 0,
                    "locked_until": None
                }
            }
        )
        
        # Mark code as used
        from db.database import Database
        verification_collection = Database.get_collection("email_verifications")
        await verification_collection.update_many(
            {
                "email": request.email.lower(),
                "type": "password_reset",
                "is_used": False
            },
            {"$set": {"is_used": True}}
        )
        
        logger.info(f"✅ Password reset successful for: {request.email}")
        
        return MessageResponse(
            message="Password reset successfully",
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )