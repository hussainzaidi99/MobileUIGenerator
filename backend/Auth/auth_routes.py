# backend/Auth/auth_routes.py - PROFESSIONAL ERROR HANDLING
"""
✅ ENHANCED WITH PROFESSIONAL ERROR HANDLING:
1. User-friendly error messages (no technical jargon)
2. Comprehensive input validation
3. Detailed developer logging
4. Proper error codes for tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional
import logging
import os

# ✅ Import error handling utilities
from utils.error_handler import (
    create_error_response,
    create_success_response,
    log_exception,
    UserFacingError
)
from utils.validators import (
    validate_email,
    validate_password,
    validate_username,
    validate_name,
    validate_user_id
)

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
# DEPENDENCY: Get Current User
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


# ============================================================================
# ✅ FIXED SIGNUP - NO AUTO-LOGIN, REQUIRES EMAIL VERIFICATION
# ============================================================================

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: UserSignupRequest, http_request: Request):
    """
    ✅ ENHANCED: Register user with comprehensive validation and user-friendly errors
    
    Flow:
    1. Validate all inputs (email, password, username, name)
    2. Check email uniqueness
    3. Create user (is_verified=False)
    4. Send verification email
    5. Return success message (NO tokens)
    """
    try:
        # ✅ VALIDATE EMAIL
        is_valid, error_msg = validate_email(request.email)
        if not is_valid:
            return create_error_response(error_msg, 400, "INVALID_EMAIL")
        
        # ✅ CHECK EMAIL UNIQUENESS
        users_collection = get_users_collection()
        existing_user = await users_collection.find_one({"email": request.email.lower()})
        if existing_user:
            return create_error_response(
                UserFacingError.EMAIL_EXISTS,
                409,
                "EMAIL_EXISTS",
                {"email": request.email}
            )
        
        # ✅ VALIDATE PASSWORD
        is_valid, error_msg = validate_password(request.password)
        if not is_valid:
            return create_error_response(error_msg, 400, "WEAK_PASSWORD")
        
        # ✅ VALIDATE USERNAME
        is_valid, error_msg = validate_username(request.username)
        if not is_valid:
            return create_error_response(error_msg, 400, "INVALID_USERNAME")
        
        # ✅ VALIDATE NAME
        is_valid, error_msg = validate_name(request.full_name)
        if not is_valid:
            return create_error_response(error_msg, 400, "INVALID_NAME")
        
        # Create user
        user = await AuthService.create_user(
            email=request.email,
            password=request.password,
            username=request.username,
            full_name=request.full_name
        )
        
        # Send verification email
        try:
            from Services.email_service import EmailService
            email_sent = await EmailService.send_verification_email(
                email=user["email"],
                username=user["username"],
                user_id=str(user["_id"])
            )
            
            if email_sent:
                logger.info(f"✅ User created and verification email sent: {request.email}")
            else:
                logger.warning(f"⚠️ User created but email failed: {request.email}")
        
        except Exception as email_error:
            log_exception(
                "EMAIL_SEND_FAILED",
                email_error,
                {"email": request.email, "user_id": str(user["_id"])}
            )
        
        # ✅ RETURN USER-FRIENDLY SUCCESS MESSAGE
        return create_success_response(
            "Account created! Please check your email to verify your account.",
            status_code=201
        )
        
    except ValueError as e:
        # Validation errors from AuthService
        return create_error_response(
            str(e),
            400,
            "VALIDATION_ERROR",
            {"error": str(e)}
        )
    except Exception as e:
        log_exception("SIGNUP_FAILED", e, {"email": request.email})
        return create_error_response(
            UserFacingError.TECHNICAL_DIFFICULTY,
            500,
            "SIGNUP_FAILED"
        )
@router.post("/signup-debug")
async def signup_debug(request: Request):
    """Debug endpoint to see raw request body"""
    try:
        body = await request.json()
        print("=" * 60)
        print("🔍 RAW SIGNUP REQUEST BODY:")
        print(body)
        print("=" * 60)
        
        # Try to validate manually
        from Auth.auth_models import UserSignupRequest
        try:
            validated = UserSignupRequest(**body)
            print("✅ Validation passed!")
            print(f"   Email: {validated.email}")
            print(f"   Username: {validated.username}")
            print(f"   Password length: {len(validated.password)}")
            print(f"   Full name: {validated.full_name}")
            return {"status": "validation_passed", "data": body}
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return {"status": "validation_failed", "error": str(e)}
    except Exception as e:
        print(f"❌ Failed to parse JSON: {e}")
        return {"status": "json_parse_failed", "error": str(e)}


# ============================================================================
# ✅ FIXED LOGIN - CHECK EMAIL VERIFICATION
# ============================================================================

@router.post("/login")
async def login(request: UserLoginRequest, http_request: Request):
    """
    ✅ ENHANCED: Login with user-friendly error messages
    """
    try:
        # ✅ VALIDATE INPUTS
        if not request.email or not request.password:
            return create_error_response(
                UserFacingError.INVALID_CREDENTIALS,
                401,
                "MISSING_CREDENTIALS"
            )
        
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        
        # Authenticate user
        user = await AuthService.authenticate_user(
            email=request.email,
            password=request.password,
            ip_address=ip_address
        )
        
        if not user:
            return create_error_response(
                UserFacingError.INVALID_CREDENTIALS,
                401,
                "INVALID_CREDENTIALS"
            )
        
        # ✅ CHECK EMAIL VERIFICATION
        if not user.get("is_verified", False):
            return create_error_response(
                UserFacingError.EMAIL_NOT_VERIFIED,
                403,
                "EMAIL_NOT_VERIFIED",
                {"email": request.email}
            )
        
        # Create session
        tokens = await AuthService.create_session(
            user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        user_response = AuthService.user_to_response(user)
        
        logger.info(f"✅ Login successful: {request.email}")
        
        return LoginResponse(user=user_response, tokens=tokens)
        
    except ValueError as e:
        return create_error_response(
            str(e),
            403,
            "LOGIN_VALIDATION_ERROR"
        )
    except HTTPException:
        raise
    except Exception as e:
        log_exception("LOGIN_FAILED", e, {"email": request.email})
        return create_error_response(
            "Login failed. Please try again.",
            500,
            "LOGIN_FAILED"
        )


# ============================================================================
# EMAIL VERIFICATION ENDPOINTS (PUBLIC - NO AUTH REQUIRED)
# ============================================================================

@router.post("/verify-email/confirm", response_model=MessageResponse)
async def confirm_email_verification(request: EmailVerificationConfirm):
    """
    ✅ FIXED: Verify email with 6-digit code (PUBLIC endpoint)
    """
    from Services.email_service import EmailService
    
    try:
        # ✅ CRITICAL: Normalize code - remove ALL whitespace and separators
        code = request.code.strip()
        code = ''.join(c for c in code if c.isdigit())
        
        # ✅ Validate format
        if len(code) != 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid code format. Please enter a 6-digit code. (Received {len(code)} digits)"
            )
        
        # Verify code
        result = await EmailService.verify_email_code(request.email, code)
        
        if result["success"]:
            logger.info(f"✅ Email verified: {request.email}")
            return MessageResponse(
                message="Email verified successfully! You can now login.",
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


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_public(request: Request):
    """
    ✅ NEW: PUBLIC endpoint to resend verification code
    No authentication required (user hasn't verified email yet)
    """
    from Services.email_service import EmailService
    
    try:
        body = await request.json()
        email = body.get("email")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        # Get user
        users_collection = get_users_collection()
        user = await users_collection.find_one({"email": email.lower()})  # ✅ ADDED await
        
        if not user:
            # Don't reveal if email exists (security)
            return MessageResponse(
                message="If your email is registered, verification code sent",
                success=True
            )
        
        # Check if already verified
        if user.get("is_verified", False):
            return MessageResponse(
                message="Email already verified. You can login now.",
                success=True
            )
        
        # Send verification email
        success = await EmailService.send_verification_email(
            email=user["email"],
            username=user["username"],
            user_id=str(user["_id"])
        )
        
        if success:
            logger.info(f"✅ Verification email resent to: {email}")
            return MessageResponse(
                message="Verification code sent to your email",
                success=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend verification error: {e}", exc_info=True)
        # Don't reveal error (security)
        return MessageResponse(
            message="If your email is registered, verification code sent",
            success=True
        )


# ============================================================================
# ✅ FIXED PASSWORD RESET ENDPOINTS
# ============================================================================

@router.post("/password-reset/send-code", response_model=MessageResponse)
async def send_password_reset_code(request: PasswordResetRequest):
    """
    ✅ FIXED: Send password reset code (all async operations have await)
    """
    from Services.email_service import EmailService
    
    try:
        # Get user to find username
        users_collection = get_users_collection()
        user = await users_collection.find_one({"email": request.email.lower()})  # ✅ ADDED await
        
        username = user.get("username", "User") if user else "User"
        
        # Send reset email
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
    Verify password reset code without resetting password
    """
    from Services.email_service import EmailService
    
    try:
        # ✅ Normalize code
        code = ''.join(c for c in str(request.code) if c.isdigit())
        
        if len(code) != 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid code format. Please enter a 6-digit code. (Received {len(code)} digits)"
            )
        
        result = await EmailService.verify_reset_code(request.email, code)
        
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
async def reset_password_with_code(request: Request):  # ✅ Change to Request first
    """
    Reset password using verified code
    """
    from Services.email_service import EmailService
    
    try:
        # ✅ DEBUG: Log raw request body
        body = await request.json()
        logger.info(f"🔍 Password reset request body: {body}")
        
        # ✅ Now validate with Pydantic
        try:
            validated_request = PasswordResetWithCode(**body)
        except Exception as validation_error:
            logger.error(f"❌ Validation failed: {validation_error}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation error: {str(validation_error)}"
            )
        
        # Normalize code
        code = ''.join(c for c in str(validated_request.code) if c.isdigit())
        
        if len(code) != 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid code format. Please enter a 6-digit code. (Received {len(code)} digits)"
            )
        
        # Verify code first
        verification_result = await EmailService.verify_reset_code(validated_request.email, code)
        
        if not verification_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification_result["message"]
            )
        
        # Get user
        users_collection = get_users_collection()
        user = await users_collection.find_one({"email": validated_request.email.lower()})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash new password
        hashed_password = AuthService.hash_password(validated_request.new_password)
        
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
                "email": validated_request.email.lower(),
                "type": "password_reset",
                "is_used": False
            },
            {"$set": {"is_used": True}}
        )
        
        logger.info(f"✅ Password reset successful for: {validated_request.email}")
        
        return MessageResponse(
            message="Password reset successfully. You can now login with your new password.",
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

# ============================================================================
# GOOGLE OAUTH (UNCHANGED - ALREADY CORRECT)
# ============================================================================

@router.post("/google", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def google_auth(request: GoogleAuthRequest, http_request: Request):
    """Google OAuth authentication (already correct)"""
    try:
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        
        logger.info(f"🔍 Google auth attempt from IP: {ip_address}")
        
        try:
            import json
            user_info = json.loads(request.id_token)
            
            if not user_info.get('email') or not user_info.get('sub'):
                raise ValueError("Missing required fields: email and sub")
            
            email = user_info['email'].lower()
            google_id = user_info['sub']
            full_name = user_info.get('name', '')
            email_verified = user_info.get('email_verified', True)
            picture = user_info.get('picture', '')
            
            logger.info(f"✅ Received Google user info for: {email}")
            
        except (json.JSONDecodeError, ValueError) as e:
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
        
        if not email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google email not verified"
            )
        
        users_collection = get_users_collection()
        user = await users_collection.find_one({"email": email})  # ✅ Already has await
        
        now = datetime.now(timezone.utc)
        
        if user:
            auth_provider = user.get("auth_provider", "local")
            
            if not user.get("google_id"):
                await users_collection.update_one(  # ✅ Already has await
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
                await users_collection.update_one(  # ✅ Already has await
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "last_login": now,
                            "updated_at": now
                        }
                    }
                )
            
            user = await users_collection.find_one({"_id": user["_id"]})  # ✅ Already has await
            
        else:
            from Services.tier_manager import TierManager
            
            base_username = email.split('@')[0] or full_name.replace(' ', '').lower()
            username = base_username
            
            counter = 1
            while await users_collection.find_one({"username": username}):  # ✅ Already has await
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
            
            result = await users_collection.insert_one(new_user)  # ✅ Already has await
            user_id = result.inserted_id
            
            tier_result = await TierManager.initialize_user_tier(user_id)
            
            user = await users_collection.find_one({"_id": user_id})  # ✅ Already has await
            
            logger.info(
                f"✅ New Google user created: {email} | "
                f"Tier: {tier_result['tier']} | Credits: {tier_result['credits']}"
            )
        
        tokens = await AuthService.create_session(
            user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
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
# OTHER ENDPOINTS (UNCHANGED)
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
    
    db_healthy = Database.health_check()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "auth_service": "operational",
        "google_oauth": "configured" if os.getenv("GOOGLE_CLIENT_ID") else "not configured",
        "email_service": "configured" if os.getenv("RESEND_API_KEY") else "not configured"
    }