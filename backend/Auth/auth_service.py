# backend/Auth/auth_service.py - UPDATED with Free Tier Integration
"""
Production-grade authentication service with:
- Password hashing (bcrypt)
- JWT token generation/validation
- Rate limiting protection
- Account lockout
- Session management
- 🆕 Free Tier Management Integration
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId
from dotenv import load_dotenv
import logging

from db.database import (
    get_users_collection,
    get_sessions_collection,
    get_login_attempts_collection
)
from Auth.auth_models import (
    UserInDB,
    SessionInDB,
    TokenPayload,
    UserResponse,
    TokenResponse
)
# 🆕 Import TierManager
from Services.tier_manager import TierManager

load_dotenv()
logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    # JWT TOKEN UTILITIES (unchanged)
    # ========================================================================
    
    @staticmethod
    def create_access_token(user_data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        now = utc_now()
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": str(user_data["_id"]),
            "email": user_data["email"],
            "username": user_data["username"],
            "role": user_data.get("role", "user"),
            "type": "access",
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp())
        }
        
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        now = utc_now()
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": str(user_data["_id"]),
            "email": user_data["email"],
            "username": user_data["username"],
            "role": user_data.get("role", "user"),
            "type": "refresh",
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp())
        }
        
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[TokenPayload]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            if payload.get("type") != token_type:
                logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
                return None
            
            exp = payload.get("exp")
            if exp:
                current_time = int(utc_now().timestamp())
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
    # USER MANAGEMENT - 🆕 WITH FREE TIER INTEGRATION
    # ========================================================================
    
    @staticmethod
    async def create_user(
        email: str, 
        password: str, 
        username: str, 
        full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new user with automatic tier assignment"""
        users_collection = get_users_collection()
        
        # Check if user exists
        existing_user = users_collection.find_one({"email": email.lower()})
        if existing_user:
            raise ValueError("Email already registered")
        
        existing_username = users_collection.find_one({"username": username.lower()})
        if existing_username:
            raise ValueError("Username already taken")
        
        # Create base user document
        now = utc_now()
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
            "last_login": None,
            # Payment fields (will be updated by TierManager)
            "total_spent": 0.0,
            "purchase_history": [],
            "usage_history": [],
            "last_purchase": None,
        }
        
        # Insert user first
        result = users_collection.insert_one(user_doc)
        user_id = result.inserted_id
        
        # 🆕 Initialize tier (free tier if available, limited otherwise)
        tier_result = await TierManager.initialize_user_tier(user_id)
        
        # Fetch updated user with tier info
        user_doc = users_collection.find_one({"_id": user_id})
        
        logger.info(
            f"✅ User created: {email} | "
            f"Tier: {tier_result['tier']} | "
            f"Credits: {tier_result['credits']}"
        )
        
        return user_doc
    
    @staticmethod
    async def authenticate_user(
        email: str, 
        password: str, 
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
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
            now = utc_now()
            locked_until = user["locked_until"]
            
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            
            if now < locked_until:
                remaining = (locked_until - now).seconds // 60
                logger.warning(f"🔒 Account locked: {email} (remaining: {remaining} min)")
                raise ValueError(f"Account locked. Try again in {remaining} minutes.")
            else:
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
                "updated_at": utc_now()
            }
            
            if attempts >= MAX_LOGIN_ATTEMPTS:
                lockout_until = utc_now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
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
                    "last_login": utc_now(),
                    "updated_at": utc_now()
                }
            }
        )
        
        AuthService._record_login_attempt(email, success=True, ip_address=ip_address)
        logger.info(f"✅ Login successful: {email}")
        return user
    
    # ========================================================================
    # 🆕 GOOGLE OAUTH WITH FREE TIER INTEGRATION
    # ========================================================================
    
    @staticmethod
    async def authenticate_with_google(
        google_token: str, 
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with Google ID token"""
        from google.oauth2 import id_token
        from google.auth.transport import requests
        
        users_collection = get_users_collection()
        
        try:
            # Verify the Google ID token
            idinfo = id_token.verify_oauth2_token(
                google_token, 
                requests.Request(),
                None
            )
            
            google_id = idinfo['sub']
            email = idinfo['email'].lower()
            email_verified = idinfo.get('email_verified', False)
            name = idinfo.get('name', '')
            picture = idinfo.get('picture', '')
            
            if not email_verified:
                raise ValueError("Google email not verified")
            
            logger.info(f"✅ Google token verified for: {email}")
            
            # Check if user exists
            existing_user = users_collection.find_one({"email": email})
            
            if existing_user:
                # Update Google info
                auth_provider = existing_user.get("auth_provider", "local")
                
                if auth_provider == "local":
                    auth_provider = "both"
                    logger.info(f"🔗 Linking Google account to existing user: {email}")
                
                users_collection.update_one(
                    {"_id": existing_user["_id"]},
                    {
                        "$set": {
                            "google_id": google_id,
                            "picture_url": picture,
                            "auth_provider": auth_provider,
                            "is_verified": True,
                            "last_login": utc_now(),
                            "updated_at": utc_now()
                        }
                    }
                )
                
                user = users_collection.find_one({"_id": existing_user["_id"]})
                logger.info(f"✅ Google login successful (existing user): {email}")
                return user
            
            else:
                # Create new user with Google
                base_username = email.split('@')[0] or name.replace(' ', '').lower()
                username = base_username
                
                counter = 1
                while users_collection.find_one({"username": username}):
                    username = f"{base_username}{counter}"
                    counter += 1
                
                now = utc_now()
                new_user = {
                    "email": email,
                    "username": username,
                    "hashed_password": None,
                    "full_name": name,
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
                
                result = users_collection.insert_one(new_user)
                user_id = result.inserted_id
                
                # 🆕 Initialize tier
                tier_result = await TierManager.initialize_user_tier(user_id)
                
                # Fetch updated user
                new_user = users_collection.find_one({"_id": user_id})
                
                logger.info(
                    f"✅ New Google user created: {email} | "
                    f"Tier: {tier_result['tier']} | "
                    f"Credits: {tier_result['credits']}"
                )
                
                return new_user
        
        except ValueError as e:
            logger.warning(f"❌ Google auth validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Google auth error: {e}")
            return None
    
    # ========================================================================
    # OTHER METHODS (unchanged - keeping for brevity)
    # ========================================================================
    
    @staticmethod
    def _record_login_attempt(email: str, success: bool, ip_address: Optional[str] = None):
        """Record login attempt"""
        login_attempts_collection = get_login_attempts_collection()
        login_attempts_collection.insert_one({
            "email": email.lower(),
            "success": success,
            "ip_address": ip_address,
            "created_at": utc_now()
        })
    
    @staticmethod
    async def create_session(
        user: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TokenResponse:
        """Create a new session"""
        sessions_collection = get_sessions_collection()
        
        access_token = AuthService.create_access_token(user)
        refresh_token = AuthService.create_refresh_token(user)
        
        now = utc_now()
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
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    async def refresh_session(refresh_token: str) -> Optional[TokenResponse]:
        """Refresh access token"""
        sessions_collection = get_sessions_collection()
        users_collection = get_users_collection()
        
        token_payload = AuthService.verify_token(refresh_token, token_type="refresh")
        if not token_payload:
            return None
        
        session = sessions_collection.find_one({
            "refresh_token": refresh_token,
            "is_active": True
        })
        
        if not session:
            return None
        
        now = utc_now()
        expires_at = session["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if now > expires_at:
            sessions_collection.update_one(
                {"_id": session["_id"]},
                {"$set": {"is_active": False}}
            )
            return None
        
        user = users_collection.find_one({"_id": ObjectId(token_payload.sub)})
        if not user or not user.get("is_active", True):
            return None
        
        new_access_token = AuthService.create_access_token(user)
        
        sessions_collection.update_one(
            {"_id": session["_id"]},
            {"$set": {"access_token": new_access_token}}
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    async def logout(refresh_token: str) -> bool:
        """Logout user"""
        sessions_collection = get_sessions_collection()
        result = sessions_collection.update_one(
            {"refresh_token": refresh_token},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        users_collection = get_users_collection()
        try:
            return users_collection.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None
    
    @staticmethod
    def user_to_response(user: Dict[str, Any]) -> UserResponse:
        """Convert user document to response"""
        return UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            username=user["username"],
            full_name=user.get("full_name"),
            created_at=user["created_at"],
            is_active=user.get("is_active", True),
            is_verified=user.get("is_verified", False),
            role=user.get("role", "user"),
            google_id=user.get("google_id"),
            picture_url=user.get("picture_url"),
            auth_provider=user.get("auth_provider", "local")
        )