# backend/db/database.py - MOTOR (ASYNC) VERSION
"""
Production-grade MongoDB configuration with:
- Async connection pooling (Motor)
- Retry logic
- Health checks
- Index management
- get_db() method for accessing database instance
"""

import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient  
from pymongo import ASCENDING 
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError  
from dotenv import load_dotenv
import logging
import asyncio  # ✅ NEW - needed for async sleep

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

    client: Optional[AsyncIOMotorClient] = None
    db = None
    _connection_attempts = 0
    _max_retries = 3

    @classmethod
    async def connect(cls):
        """Establish MongoDB connection with retry logic"""
        
        for attempt in range(1, cls._max_retries + 1):
            try:
                logger.info(f"🔄 MongoDB connection attempt {attempt}/{cls._max_retries}...")
                
                cls.client = AsyncIOMotorClient(
                    MONGODB_URL,
                    maxPoolSize=MAX_POOL_SIZE,
                    minPoolSize=MIN_POOL_SIZE,
                    maxIdleTimeMS=MAX_IDLE_TIME_MS,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=20000,
                    socketTimeoutMS=20000,
                    retryWrites=True,
                    retryReads=True,
                )

                # Test connection with admin command
                await cls.client.admin.command("ping")
                
                # Get database reference
                cls.db = cls.client[MONGODB_DB_NAME]
                
                # Verify we can actually access the database
                await cls.db.list_collection_names()

                # Create indexes AFTER successful connection
                await cls._create_indexes()

                logger.info(f"✅ Connected to MongoDB: {MONGODB_DB_NAME}")
                cls._connection_attempts = attempt
                return True

            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"❌ MongoDB connection failed (attempt {attempt}/{cls._max_retries}): {e}")
                
                # Clean up failed connection
                if cls.client:
                    try:
                        cls.client.close()
                    except:
                        pass
                    cls.client = None
                    cls.db = None
                
                # Wait before retry
                if attempt < cls._max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("❌ All MongoDB connection attempts failed!")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Unexpected MongoDB error: {e}")
                cls.client = None
                cls.db = None
                return False
        
        return False

    @classmethod
    def get_db(cls):
        """
        Get database instance.
        This method is required by TierManager and payment routes.
        """
        if cls.db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.db

    @classmethod
    async def _create_indexes(cls):
        """Create database indexes for performance"""
        if cls.db is None:
            logger.warning("⚠️ Cannot create indexes - database not connected")
            return

        try:
            # =========================
            # Users collection indexes
            # =========================
            users_collection = cls.db.users

            # Unique email index
            await users_collection.create_index(
                [("email", ASCENDING)],
                unique=True,
                name="email_unique_idx",
            )

            # Username index (for search)
            await users_collection.create_index(
                [("username", ASCENDING)],
                name="username_idx",
            )

            # Created at index (for sorting)
            await users_collection.create_index(
                [("created_at", ASCENDING)],
                name="created_at_idx",
            )

            # Tier index (for tier management)
            await users_collection.create_index(
                [("tier", ASCENDING)],
                name="tier_idx",
            )

            # Next credit reset index (for background jobs)
            await users_collection.create_index(
                [("next_credit_reset", ASCENDING)],
                sparse=True,
                name="next_credit_reset_idx",
            )

            # Tier end date index (for expiration checks)
            await users_collection.create_index(
                [("tier_end_date", ASCENDING)],
                sparse=True,
                name="tier_end_date_idx",
            )

            # ============================
            # Sessions collection indexes
            # ============================
            sessions_collection = cls.db.sessions

            # User ID index
            await sessions_collection.create_index(
                [("user_id", ASCENDING)],
                name="user_id_idx",
            )

            # Expires at index with TTL (auto-delete expired sessions)
            await sessions_collection.create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="expires_at_ttl_idx",
            )

            # Refresh token index
            await sessions_collection.create_index(
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
            await login_attempts_collection.create_index(
                [("email", ASCENDING)],
                name="login_email_idx",
            )

            # TTL index (auto-delete after 24 hours)
            await login_attempts_collection.create_index(
                [("created_at", ASCENDING)],
                expireAfterSeconds=86400,
                name="login_attempts_ttl_idx",
            )

            # ==========================================
            # Email verifications collection indexes
            # ==========================================
            email_verifications_collection = cls.db.email_verifications

            # Email + type index
            await email_verifications_collection.create_index(
                [("email", ASCENDING), ("type", ASCENDING)],
                name="email_type_idx",
            )

            # User ID index
            await email_verifications_collection.create_index(
                [("user_id", ASCENDING)],
                name="user_id_idx",
            )

            # Code index
            await email_verifications_collection.create_index(
                [("code", ASCENDING)],
                name="code_idx",
            )

            # TTL index (auto-delete expired codes after 1 hour)
            await email_verifications_collection.create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=3600,
                name="verifications_ttl_idx",
            )

            logger.info("✅ Database indexes created successfully")

        except Exception as e:
            logger.error(f"⚠️ Index creation warning: {e}")

    @classmethod
    def disconnect(cls):
        """Close MongoDB connection"""
        if cls.client is not None:
            try:
                cls.client.close()
                logger.info("🔌 MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")
            finally:
                cls.client = None
                cls.db = None

    @classmethod
    def get_collection(cls, name: str):
        """Get a collection by name"""
        if cls.db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.db[name]

    @classmethod
    async def health_check(cls) -> bool:
        """Check if database connection is healthy"""
        try:
            # Check if client exists
            if cls.client is None:
                logger.warning("Health check failed: No client")
                return False
            
            # Check if db exists
            if cls.db is None:
                logger.warning("Health check failed: No database")
                return False
                
            # Ping the database
            await cls.client.admin.command("ping")
            
            # Try to list collections
            await cls.db.list_collection_names()
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
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
    success = await Database.connect()
    if not success:
        logger.error("⚠️ WARNING: MongoDB connection failed! Auth features will not work.")
    return success


async def close_mongo_connection():
    """FastAPI shutdown handler"""
    Database.disconnect()