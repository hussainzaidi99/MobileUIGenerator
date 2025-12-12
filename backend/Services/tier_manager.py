# backend/Services/tier_manager.py - FIXED with timezone awareness
"""
Free Tier Management System
FIXED: Properly handles timezone-aware and naive datetime objects
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
import logging
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from db.database import Database

logger = logging.getLogger(__name__)

# ============================================================================
# TIER CONFIGURATION
# ============================================================================

FREE_TIER_LIMIT = 20
FREE_TIER_CREDITS = 5
FREE_TIER_RESET_INTERVAL_DAYS = 30

TIER_CONFIG = {
    "free": {
        "name": "Free Tier",
        "credits": FREE_TIER_CREDITS,
        "price": 0,
        "duration_days": None,
        "features": ["5 credits/month", "Basic UI generation", "Community support"]
    },
    "basic": {
        "name": "Basic Plan",
        "credits": 142,
        "price": 4.99,
        "duration_days": 30,
        "features": ["142 credits/month", "10M tokens", "Email support", "Priority generation"]
    },
    "pro": {
        "name": "Pro Plan",
        "credits": 284,
        "price": 9.99,
        "duration_days": 30,
        "features": ["284 credits/month", "20M tokens", "Email support", "Priority generation", "Advanced components"]
    },
    "premium": {
        "name": "Premium Plan",
        "credits": 568,
        "price": 19.99,
        "duration_days": 30,
        "features": ["568 credits/month", "40M tokens", "Priority support", "Advanced features", "Custom components"]
    }
}


# ============================================================================
# 🔧 HELPER FUNCTION - TIMEZONE FIX
# ============================================================================

def make_aware(dt):
    """
    Convert naive datetime to timezone-aware (UTC).
    If already aware, return as-is.
    """
    if dt is None:
        return None
    
    # Check if datetime is naive (no timezone info)
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        # Make it UTC-aware
        return dt.replace(tzinfo=timezone.utc)
    
    # Already aware, return as-is
    return dt


# ============================================================================
# TIER MANAGER CLASS
# ============================================================================

class TierManager:
    """Manages user tiers and credit allocations"""
    
    @staticmethod
    def _to_object_id(user_id: str) -> ObjectId:
        """Convert string user_id to ObjectId"""
        try:
            return ObjectId(user_id)
        except Exception as e:
            raise ValueError(f"Invalid user_id format: {user_id}")
    
    @staticmethod
    def _serialize_datetime(dt) -> Optional[str]:
        """Convert datetime to ISO string, return None if invalid"""
        if dt is None:
            return None
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()
        return None
    
    @staticmethod
    async def get_free_tier_count() -> int:
        """Get current number of free-tier users"""
        db = Database.get_db()
        users_collection = db["users"]
        
        count = await users_collection.count_documents({
            "tier": "free",
            "is_active": True
        })
        
        return count
    
    @staticmethod
    async def can_add_free_tier_user() -> bool:
        """Check if we can add a new free-tier user"""
        current_count = await TierManager.get_free_tier_count()
        return current_count < FREE_TIER_LIMIT
    
    @staticmethod
    async def initialize_user_tier(user_id: str) -> Dict:
        """Initialize tier for a new user"""
        db = Database.get_db()
        users_collection = db["users"]
        
        # Convert to ObjectId
        object_id = TierManager._to_object_id(user_id)
        
        # Check if we can assign free tier
        can_assign_free = await TierManager.can_add_free_tier_user()
        
        now = datetime.now(timezone.utc)
        
        if can_assign_free:
            # Assign free tier
            tier_data = {
                "tier": "free",
                "credits": FREE_TIER_CREDITS,
                "tier_start_date": now,
                "tier_end_date": None,
                "last_credit_reset": now,
                "next_credit_reset": now + timedelta(days=FREE_TIER_RESET_INTERVAL_DAYS),
                "tier_history": [{
                    "tier": "free",
                    "assigned_at": now,
                    "reason": "initial_signup"
                }]
            }
            
            await users_collection.update_one(
                {"_id": object_id},
                {"$set": tier_data}
            )
            
            logger.info(f"✅ Free tier assigned to user: {user_id} ({TierManager.get_free_tier_count()}/{FREE_TIER_LIMIT})")
            
            return {
                "success": True,
                "tier": "free",
                "credits": FREE_TIER_CREDITS,
                "message": "Welcome! You've been assigned to our Free Tier with 5 credits (resets monthly)"
            }
        else:
            # Free tier full - assign limited access
            tier_data = {
                "tier": "limited",
                "credits": 0,
                "tier_start_date": now,
                "tier_end_date": None,
                "last_credit_reset": None,
                "next_credit_reset": None,
                "tier_history": [{
                    "tier": "limited",
                    "assigned_at": now,
                    "reason": "free_tier_full"
                }]
            }
            
            await users_collection.update_one(
                {"_id": object_id},
                {"$set": tier_data}
            )
            
            logger.warning(f"⚠️ Free tier full - user assigned 'limited': {user_id}")
            
            return {
                "success": True,
                "tier": "limited",
                "credits": 0,
                "message": "Free tier is currently full. Purchase a plan to get started!",
                "requires_payment": True
            }
    
    @staticmethod
    async def upgrade_user_tier(
        user_id: str,
        new_tier: str,
        credits_to_add: int,
        purchase_info: Dict
    ) -> Dict:
        """Upgrade user to a paid tier"""
        db = Database.get_db()
        users_collection = db["users"]
        
        # Convert to ObjectId
        object_id = TierManager._to_object_id(user_id)
        
        if new_tier not in ["basic", "pro", "premium"]:
            return {
                "success": False,
                "error": "Invalid tier"
            }
        
        user = await users_collection.find_one({"_id": object_id})
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        now = datetime.now(timezone.utc)
        duration_days = TIER_CONFIG[new_tier]["duration_days"]
        tier_end_date = now + timedelta(days=duration_days)
        
        # Determine if user had free tier before
        previous_tier = user.get("tier", "limited")
        was_free_tier = previous_tier == "free"
        
        update_data = {
            "tier": new_tier,
            "credits": user.get("credits", 0) + credits_to_add,
            "tier_start_date": now,
            "tier_end_date": tier_end_date,
            "previous_tier": previous_tier,
            "had_free_tier": was_free_tier,
            "last_purchase": now,
            "total_spent": user.get("total_spent", 0) + purchase_info.get("price", 0),
        }
        
        await users_collection.update_one(
            {"_id": object_id},
            {
                "$set": update_data,
                "$push": {
                    "tier_history": {
                        "tier": new_tier,
                        "assigned_at": now,
                        "expires_at": tier_end_date,
                        "reason": "purchase",
                        "purchase_info": purchase_info
                    }
                }
            }
        )
        
        logger.info(f"✅ User upgraded: {user_id} -> {new_tier} (expires: {tier_end_date})")
        
        return {
            "success": True,
            "tier": new_tier,
            "credits": update_data["credits"],
            "expires_at": tier_end_date,
            "message": f"Successfully upgraded to {TIER_CONFIG[new_tier]['name']}!"
        }
    
    @staticmethod
    async def downgrade_expired_tiers() -> List[Dict]:
        """Background job: Check and downgrade expired paid tiers"""
        db = Database.get_db()
        users_collection = db["users"]
        
        now = datetime.now(timezone.utc)
        
        # Find users with expired paid tiers
        expired_users = await list(users_collection.find({
            "tier": {"$in": ["basic", "pro", "premium"]},
            "tier_end_date": {"$lt": now}
        }))
        
        downgraded = []
        
        for user in expired_users:
            user_id = user["_id"]  # Already ObjectId from MongoDB
            previous_tier = user.get("tier")
            had_free_tier = user.get("had_free_tier", False)
            
            # Determine downgrade target
            if had_free_tier:
                new_tier = "free"
                new_credits = FREE_TIER_CREDITS
                logger.info(f"⬇️ Restoring free tier for expired user: {user_id}")
            else:
                can_get_free = TierManager.can_add_free_tier_user()
                
                if can_get_free:
                    new_tier = "free"
                    new_credits = FREE_TIER_CREDITS
                    logger.info(f"⬇️ Assigning free tier to expired user: {user_id}")
                else:
                    new_tier = "limited"
                    new_credits = 0
                    logger.info(f"⬇️ Downgrading to limited (free tier full): {user_id}")
            
            # Update user
            reset_time = now + timedelta(days=FREE_TIER_RESET_INTERVAL_DAYS) if new_tier == "free" else None
            
            await users_collection.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "tier": new_tier,
                        "credits": new_credits,
                        "tier_start_date": now,
                        "tier_end_date": None,
                        "last_credit_reset": now if new_tier == "free" else None,
                        "next_credit_reset": reset_time,
                        "previous_tier": previous_tier
                    },
                    "$push": {
                        "tier_history": {
                            "tier": new_tier,
                            "assigned_at": now,
                            "reason": "plan_expired",
                            "previous_tier": previous_tier
                        }
                    }
                }
            )
            
            downgraded.append({
                "user_id": str(user_id),
                "email": user.get("email"),
                "from_tier": previous_tier,
                "to_tier": new_tier,
                "new_credits": new_credits
            })
        
        logger.info(f"✅ Downgraded {len(downgraded)} expired users")
        return downgraded
    
    @staticmethod
    async def reset_free_tier_credits() -> List[Dict]:
        """Background job: Reset credits for free-tier users"""
        db = Database.get_db()
        users_collection = db["users"]
        
        now = datetime.now(timezone.utc)
        
        # Find free-tier users due for credit reset
        users_to_reset = await list(users_collection.find({
            "tier": "free",
            "is_active": True,
            "next_credit_reset": {"$lte": now}
        }))
        
        reset_results = []
        
        for user in users_to_reset:
            user_id = user["_id"]  # Already ObjectId from MongoDB
            
            # Reset credits to 5
            next_reset = now + timedelta(days=FREE_TIER_RESET_INTERVAL_DAYS)
            
            await users_collection.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "credits": FREE_TIER_CREDITS,
                        "last_credit_reset": now,
                        "next_credit_reset": next_reset
                    },
                    "$push": {
                        "credit_reset_history": {
                            "reset_at": now,
                            "credits_set": FREE_TIER_CREDITS
                        }
                    }
                }
            )
            
            reset_results.append({
                "user_id": str(user_id),
                "email": user.get("email"),
                "credits_reset_to": FREE_TIER_CREDITS,
                "next_reset": next_reset.isoformat()  # Serialize datetime
            })
            
            logger.info(f"🔄 Credits reset for free-tier user: {user.get('email')}")
        
        if reset_results:
            logger.info(f"✅ Reset credits for {len(reset_results)} free-tier users")
        
        return reset_results
    
    @staticmethod
    async def get_user_tier_info(user_id: str) -> Optional[Dict]:
        """Get detailed tier information for a user - FIXED timezone issue"""
        db = Database.get_db()
        users_collection = db["users"]
        
        # Convert to ObjectId
        try:
            object_id = TierManager._to_object_id(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            return None
        
        user = await users_collection.find_one({"_id": object_id})
        if not user:
            logger.warning(f"User not found: {user_id}")
            return None
        
        tier = user.get("tier", "limited")
        tier_config = TIER_CONFIG.get(tier, {})
        
        # 🔧 FIX: Make sure tier_end_date is timezone-aware before calculation
        tier_end_date = user.get("tier_end_date")
        days_remaining = None
        
        if tier_end_date:
            try:
                # Make both datetimes timezone-aware
                tier_end_date_aware = make_aware(tier_end_date)
                now_aware = datetime.now(timezone.utc)
                
                # Now we can safely subtract them
                delta = tier_end_date_aware - now_aware
                days_remaining = max(0, delta.days)
            except Exception as e:
                logger.error(f"Failed to calculate days_remaining: {e}")
                days_remaining = None
        
        # Return with all datetime fields serialized
        return {
            "tier": tier,
            "tier_name": tier_config.get("name", "Unknown"),
            "credits": user.get("credits", 0),
            "tokens_remaining": int(user.get("credits", 0) * 70000),
            "tier_start_date": TierManager._serialize_datetime(user.get("tier_start_date")),
            "tier_end_date": TierManager._serialize_datetime(tier_end_date),
            "next_credit_reset": TierManager._serialize_datetime(user.get("next_credit_reset")),
            "features": tier_config.get("features", []),
            "is_paid_tier": tier in ["basic", "pro", "premium"],
            "can_upgrade": tier in ["free", "limited"],
            "days_remaining": days_remaining
        }