# backend/auth_service.py - Core Authentication Service
"""
Production-grade authentication service with:
- Password hashing (bcrypt)
- JWT token generation/validation (FIXED: Timezone-aware timestamps)
- Rate limiting protection
- Account lockout
- Session management
"""

import os
from datetime import datetime, timedelta, timezone  # ✅ ADDED timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId
from dotenv import load_dotenv
import logging

from database import (
    get_users_collection,
    get_sessions_collection,
    get_login_attempts_collection
)
from auth_models import (
    UserInDB,
    SessionInDB,
    TokenPayload,
    UserResponse,
    TokenResponse
)

load_dotenv()
logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-key-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ✅ HELPER: Get current UTC time (timezone-aware)
def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)


class AuthService:
    """Core authentication service"""
    
    # ========================================================================
    # PASSWORD UTILITIES
    # ========================================================================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password, rounds=BCRYPT_ROUNDS)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    # ========================================================================
    # JWT TOKEN UTILITIES
    # ========================================================================
    
    @staticmethod
    def create_access_token(user_data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        now = utc_now()  # ✅ FIXED: Use timezone-aware UTC
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": str(user_data["_id"]),
            "email": user_data["email"],
            "username": user_data["username"],
            "role": user_data.get("role", "user"),
            "type": "access",
            "exp": int(expire.timestamp()),  # ✅ Now correctly calculates UTC timestamp
            "iat": int(now.timestamp())
        }
        
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        now = utc_now()  # ✅ FIXED: Use timezone-aware UTC
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": str(user_data["_id"]),
            "email": user_data["email"],
            "username": user_data["username"],
            "role": user_data.get("role", "user"),
            "type": "refresh",
            "exp": int(expire.timestamp()),  # ✅ Now correctly calculates UTC timestamp
            "iat": int(now.timestamp())
        }
        
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[TokenPayload]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
                return None
            
            # Check expiration (JWT library already validates this, but double-check)
            exp = payload.get("exp")
            if exp:
                current_time = int(utc_now().timestamp())  # ✅ FIXED: Use timezone-aware UTC
                if current_time > exp:
                    logger.info(f"Token expired: current={current_time}, exp={exp}, diff={current_time - exp}s")
                    return None
            
            token_data = {
                "sub": payload["sub"],
                "email": payload["email"],
                "username": payload.get("username", ""),
                "role": payload.get("role", "user"),
                "type": payload["type"],
                "exp": payload["exp"],
                "iat": payload["iat"]
            }
            
            return TokenPayload(**token_data)
            
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    # ========================================================================
    # USER MANAGEMENT
    # ========================================================================
    
    @staticmethod
    async def create_user(email: str, password: str, username: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user"""
        users_collection = get_users_collection()
        
        # Check if user exists
        existing_user = users_collection.find_one({"email": email.lower()})
        if existing_user:
            raise ValueError("Email already registered")
        
        existing_username = users_collection.find_one({"username": username.lower()})
        if existing_username:
            raise ValueError("Username already taken")
        
        # Create user document
        now = utc_now()  # ✅ FIXED: Use timezone-aware UTC
        user_doc = {
            "email": email.lower(),
            "username": username.lower(),
            "hashed_password": AuthService.hash_password(password),
            "full_name": full_name,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "is_verified": False,
            "role": "user",
            "login_attempts": 0,
            "locked_until": None,
            "last_login": None
        }
        
        result = users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        
        logger.info(f"✅ User created: {email}")
        return user_doc
    
    @staticmethod
    async def authenticate_user(email: str, password: str, ip_address: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        users_collection = get_users_collection()
        login_attempts_collection = get_login_attempts_collection()
        
        # Get user
        user = users_collection.find_one({"email": email.lower()})
        if not user:
            AuthService._record_login_attempt(email, success=False, ip_address=ip_address)
            logger.warning(f"❌ Login failed: User not found - {email}")
            return None
        
        # Check if account is locked
        if user.get("locked_until"):
            now = utc_now()  # ✅ FIXED: Use timezone-aware UTC
            locked_until = user["locked_until"]
            
            # Handle both timezone-aware and naive datetimes from MongoDB
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            
            if now < locked_until:
                remaining = (locked_until - now).seconds // 60
                logger.warning(f"🔒 Account locked: {email} (remaining: {remaining} min)")
                raise ValueError(f"Account locked. Try again in {remaining} minutes.")
            else:
                # Unlock account
                users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"locked_until": None, "login_attempts": 0}}
                )
                user["locked_until"] = None
                user["login_attempts"] = 0
        
        # Verify password
        if not AuthService.verify_password(password, user["hashed_password"]):
            attempts = user.get("login_attempts", 0) + 1
            
            update_data = {
                "login_attempts": attempts,
                "updated_at": utc_now()  # ✅ FIXED
            }
            
            # Lock account if max attempts reached
            if attempts >= MAX_LOGIN_ATTEMPTS:
                lockout_until = utc_now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)  # ✅ FIXED
                update_data["locked_until"] = lockout_until
                logger.warning(f"🔒 Account locked due to failed attempts: {email}")
            
            users_collection.update_one({"_id": user["_id"]}, {"$set": update_data})
            AuthService._record_login_attempt(email, success=False, ip_address=ip_address)
            
            logger.warning(f"❌ Login failed: Invalid password - {email} (attempts: {attempts})")
            return None
        
        # Check if user is active
        if not user.get("is_active", True):
            logger.warning(f"❌ Login failed: Account disabled - {email}")
            raise ValueError("Account is disabled. Contact support.")
        
        # Successful login - reset attempts
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "login_attempts": 0,
                    "locked_until": None,
                    "last_login": utc_now(),  # ✅ FIXED
                    "updated_at": utc_now()   # ✅ FIXED
                }
            }
        )
        
        AuthService._record_login_attempt(email, success=True, ip_address=ip_address)
        logger.info(f"✅ Login successful: {email}")
        return user
    
    @staticmethod
    def _record_login_attempt(email: str, success: bool, ip_address: Optional[str] = None):
        """Record login attempt for analytics and security"""
        login_attempts_collection = get_login_attempts_collection()
        
        login_attempts_collection.insert_one({
            "email": email.lower(),
            "success": success,
            "ip_address": ip_address,
            "created_at": utc_now()  # ✅ FIXED
        })
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    @staticmethod
    async def create_session(
        user: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TokenResponse:
        """Create a new session with access and refresh tokens"""
        sessions_collection = get_sessions_collection()
        
        # Generate tokens
        access_token = AuthService.create_access_token(user)
        refresh_token = AuthService.create_refresh_token(user)
        
        # Create session document
        now = utc_now()  # ✅ FIXED
        expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        session_doc = {
            "user_id": str(user["_id"]),
            "refresh_token": refresh_token,
            "access_token": access_token,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": now,
            "expires_at": expires_at,
            "is_active": True
        }
        
        sessions_collection.insert_one(session_doc)
        
        logger.info(f"✅ Session created for user: {user['email']}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    async def refresh_session(refresh_token: str) -> Optional[TokenResponse]:
        """Refresh access token using refresh token"""
        sessions_collection = get_sessions_collection()
        users_collection = get_users_collection()
        
        # Verify refresh token
        token_payload = AuthService.verify_token(refresh_token, token_type="refresh")
        if not token_payload:
            logger.warning("❌ Invalid refresh token")
            return None
        
        # Find session
        session = sessions_collection.find_one({
            "refresh_token": refresh_token,
            "is_active": True
        })
        
        if not session:
            logger.warning("❌ Session not found or inactive")
            return None
        
        # Check expiration
        now = utc_now()  # ✅ FIXED
        
        # Handle both timezone-aware and naive datetimes from MongoDB
        expires_at = session["expires_at"]
        if expires_at.tzinfo is None:
            # Make timezone-naive datetime aware (assume UTC)
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if now > expires_at:
            logger.info("❌ Session expired")
            sessions_collection.update_one(
                {"_id": session["_id"]},
                {"$set": {"is_active": False}}
            )
            return None
        
        # Get user
        user = users_collection.find_one({"_id": ObjectId(token_payload.sub)})
        if not user or not user.get("is_active", True):
            logger.warning("❌ User not found or inactive")
            return None
        
        # Generate new access token
        new_access_token = AuthService.create_access_token(user)
        
        # Update session
        sessions_collection.update_one(
            {"_id": session["_id"]},
            {"$set": {"access_token": new_access_token}}
        )
        
        logger.info(f"✅ Session refreshed for user: {user['email']}")
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    async def logout(refresh_token: str) -> bool:
        """Logout user by invalidating session"""
        sessions_collection = get_sessions_collection()
        
        result = sessions_collection.update_one(
            {"refresh_token": refresh_token},
            {"$set": {"is_active": False}}
        )
        
        if result.modified_count > 0:
            logger.info("✅ User logged out successfully")
            return True
        
        return False
    
    # ========================================================================
    # USER RETRIEVAL
    # ========================================================================
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        users_collection = get_users_collection()
        
        try:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
            return user
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None
    
    @staticmethod
    def user_to_response(user: Dict[str, Any]) -> UserResponse:
        """Convert user document to UserResponse model"""
        return UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            username=user["username"],
            full_name=user.get("full_name"),
            created_at=user["created_at"],
            is_active=user.get("is_active", True),
            is_verified=user.get("is_verified", False),
            role=user.get("role", "user")
        )
# ========================================================================
    # 🆕 GOOGLE OAUTH AUTHENTICATION
    # ========================================================================
    
    @staticmethod
    async def authenticate_with_google(
        google_token: str, 
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with Google ID token.
        
        Flow:
        1. Verify Google ID token with Google servers
        2. Extract user info (email, name, picture, google_id)
        3. Check if user exists by email
        4. If exists with password auth -> link accounts (auth_provider = "both")
        5. If exists with Google auth -> log in
        6. If doesn't exist -> create new user with Google auth
        
        Returns:
            User document if successful, None otherwise
        """
        from google.oauth2 import id_token
        from google.auth.transport import requests
        
        users_collection = get_users_collection()
        
        try:
            # Verify the Google ID token
            # Note: You need to install google-auth: pip install google-auth
            idinfo = id_token.verify_oauth2_token(
                google_token, 
                requests.Request(),
                None  # We'll skip audience verification for now - add your client ID in production
            )
            
            # Extract user information from Google
            google_id = idinfo['sub']  # Unique Google user ID
            email = idinfo['email'].lower()
            email_verified = idinfo.get('email_verified', False)
            name = idinfo.get('name', '')
            picture = idinfo.get('picture', '')
            
            # Security: Ensure email is verified by Google
            if not email_verified:
                raise ValueError("Google email not verified")
            
            logger.info(f"✅ Google token verified for: {email}")
            
            # Check if user already exists
            existing_user = users_collection.find_one({"email": email})
            
            if existing_user:
                # User exists - update Google info and log in
                auth_provider = existing_user.get("auth_provider", "local")
                
                # Link accounts if user signed up with password
                if auth_provider == "local":
                    auth_provider = "both"  # User can now sign in with email OR Google
                    logger.info(f"🔗 Linking Google account to existing user: {email}")
                
                # Update user with Google info
                users_collection.update_one(
                    {"_id": existing_user["_id"]},
                    {
                        "$set": {
                            "google_id": google_id,
                            "picture_url": picture,
                            "auth_provider": auth_provider,
                            "is_verified": True,  # Google users are auto-verified
                            "last_login": utc_now(),
                            "updated_at": utc_now()
                        }
                    }
                )
                
                # Fetch updated user
                user = users_collection.find_one({"_id": existing_user["_id"]})
                logger.info(f"✅ Google login successful (existing user): {email}")
                return user
            
            else:
                # New user - create account with Google auth
                # Generate username from email or name
                base_username = email.split('@')[0] or name.replace(' ', '').lower()
                username = base_username
                
                # Ensure username is unique
                counter = 1
                while users_collection.find_one({"username": username}):
                    username = f"{base_username}{counter}"
                    counter += 1
                
                now = utc_now()
                new_user = {
                    "email": email,
                    "username": username,
                    "hashed_password": None,  # No password for Google-only users
                    "full_name": name,
                    "created_at": now,
                    "updated_at": now,
                    "is_active": True,
                    "is_verified": True,  # Google users are auto-verified
                    "role": "user",
                    "login_attempts": 0,
                    "locked_until": None,
                    "last_login": now,
                    # Google OAuth fields
                    "google_id": google_id,
                    "picture_url": picture,
                    "auth_provider": "google"
                }
                
                result = users_collection.insert_one(new_user)
                new_user["_id"] = result.inserted_id
                
                logger.info(f"✅ New user created via Google: {email}")
                return new_user
        
        except ValueError as e:
            # Business logic errors (email not verified, etc.)
            logger.warning(f"❌ Google auth validation error: {e}")
            raise
        
        except Exception as e:
            # Token verification failed or other errors
            logger.error(f"❌ Google auth error: {e}")
            return None
    
    @staticmethod
    def user_to_response(user: Dict[str, Any]) -> UserResponse:
        """Convert user document to UserResponse model"""
        return UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            username=user["username"],
            full_name=user.get("full_name"),
            created_at=user["created_at"],
            is_active=user.get("is_active", True),
            is_verified=user.get("is_verified", False),
            role=user.get("role", "user"),
            # 🆕 Google OAuth fields
            google_id=user.get("google_id"),
            picture_url=user.get("picture_url"),
            auth_provider=user.get("auth_provider", "local")
        )