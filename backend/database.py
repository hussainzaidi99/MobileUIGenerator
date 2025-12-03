# backend/database.py - MongoDB Connection & Configuration
"""
Production-grade MongoDB configuration with:
- Connection pooling
- Retry logic
- Health checks
- Index management
"""

import os
from typing import Optional
from pymongo import MongoClient, ASCENDING, IndexModel
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")

# Connection pooling settings
MAX_POOL_SIZE = 50
MIN_POOL_SIZE = 10
MAX_IDLE_TIME_MS = 30000  # 30 seconds


class Database:
    """MongoDB Database Manager with connection pooling"""

    client: Optional[MongoClient] = None
    db = None

    @classmethod
    def connect(cls):
        """Establish MongoDB connection with retry logic"""
        try:
            cls.client = MongoClient(
                MONGODB_URL,
                maxPoolSize=MAX_POOL_SIZE,
                minPoolSize=MIN_POOL_SIZE,
                maxIdleTimeMS=MAX_IDLE_TIME_MS,
                serverSelectionTimeoutMS=5000,   # 5 second timeout
                connectTimeoutMS=10000,          # 10 second connection timeout
                retryWrites=True,
                retryReads=True,
            )

            # Test connection
            cls.client.admin.command("ping")

            cls.db = cls.client[MONGODB_DB_NAME]

            # Create indexes
            cls._create_indexes()

            logger.info(f"✅ Connected to MongoDB: {MONGODB_DB_NAME}")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            return False

    @classmethod
    def _create_indexes(cls):
        """Create database indexes for performance"""
        # ✅ FIXED: Check if db is None instead of using bool()
        if cls.db is None:
            return

        try:
            # =========================
            # Users collection indexes
            # =========================
            users_collection = cls.db.users

            # Unique email index
            users_collection.create_index(
                [("email", ASCENDING)],
                unique=True,
                name="email_unique_idx",
            )

            # Username index (for search)
            users_collection.create_index(
                [("username", ASCENDING)],
                name="username_idx",
            )

            # Created at index (for sorting)
            users_collection.create_index(
                [("created_at", ASCENDING)],
                name="created_at_idx",
            )

            # ============================
            # Sessions collection indexes
            # ============================
            sessions_collection = cls.db.sessions

            # User ID index
            sessions_collection.create_index(
                [("user_id", ASCENDING)],
                name="user_id_idx",
            )

            # Expires at index with TTL (auto-delete expired sessions)
            sessions_collection.create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,  # Delete when expires_at is reached
                name="expires_at_ttl_idx",
            )

            # Refresh token index
            sessions_collection.create_index(
                [("refresh_token", ASCENDING)],
                unique=True,
                sparse=True,
                name="refresh_token_idx",
            )

            # ======================================
            # Login attempts collection (rate limit)
            # ======================================
            login_attempts_collection = cls.db.login_attempts

            # Email index
            login_attempts_collection.create_index(
                [("email", ASCENDING)],
                name="login_email_idx",
            )

            # TTL index (auto-delete after 24 hours)
            login_attempts_collection.create_index(
                [("created_at", ASCENDING)],
                expireAfterSeconds=86400,  # 24 hours
                name="login_attempts_ttl_idx",
            )

            # ==========================================
            # 🆕 Email verifications collection indexes
            # ==========================================
            email_verifications_collection = cls.db.email_verifications

            # Email + type index (e.g. "signup", "password_reset")
            email_verifications_collection.create_index(
                [("email", ASCENDING), ("type", ASCENDING)],
                name="email_type_idx",
            )

            # User ID index (fast lookup per user)
            email_verifications_collection.create_index(
                [("user_id", ASCENDING)],
                name="user_id_idx",
            )

            # Code index (for quick lookups by verification code)
            email_verifications_collection.create_index(
                [("code", ASCENDING)],
                name="code_idx",
            )

            # TTL index (auto-delete expired codes after 1 hour)
            email_verifications_collection.create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=3600,  # 1 hour after expiration
                name="verifications_ttl_idx",
            )

            logger.info("✅ Database indexes created successfully")

        except Exception as e:
            logger.error(f"⚠️  Index creation warning: {e}")

    @classmethod
    def disconnect(cls):
        """Close MongoDB connection"""
        if cls.client is not None:
            cls.client.close()
            logger.info("🔌 MongoDB connection closed")

    @classmethod
    def get_collection(cls, name: str):
        """Get a collection by name"""
        # ✅ FIXED: Check if db is None instead of using bool()
        if cls.db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.db[name]

    @classmethod
    def health_check(cls) -> bool:
        """Check if database connection is healthy"""
        try:
            if cls.client is None:
                return False
            cls.client.admin.command("ping")
            return True
        except Exception:
            return False


# Collection getters (for convenience)
def get_users_collection():
    """Get users collection"""
    return Database.get_collection("users")


def get_sessions_collection():
    """Get sessions collection"""
    return Database.get_collection("sessions")


def get_login_attempts_collection():
    """Get login attempts collection"""
    return Database.get_collection("login_attempts")


def get_projects_collection():
    """Get projects collection (for future use)"""
    return Database.get_collection("projects")


def get_email_verifications_collection():
    """Get email verifications collection"""
    return Database.get_collection("email_verifications")


# Startup/Shutdown handlers
async def connect_to_mongo():
    """FastAPI startup handler"""
    Database.connect()


async def close_mongo_connection():
    """FastAPI shutdown handler"""
    Database.disconnect()
