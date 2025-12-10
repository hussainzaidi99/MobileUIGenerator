# backend/scripts/migrate_to_tier_system.py
"""
Migration script to upgrade existing users to the new tier system.
Run this ONCE after deploying the tier system.

Usage:
    python scripts/migrate_to_tier_system.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import asyncio

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")

FREE_TIER_LIMIT = 20
FREE_TIER_CREDITS = 5


async def migrate_users():
    """Migrate existing users to tier system"""
    
    print("\n" + "=" * 70)
    print("🔄 TIER SYSTEM MIGRATION")
    print("=" * 70)
    print(f"Database: {MONGODB_DB_NAME}")
    print(f"Connecting to MongoDB...\n")
    
    try:
        # Connect to MongoDB
        client = MongoClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=20000,
        )
        
        # Test connection
        client.admin.command("ping")
        print("✅ MongoDB connection successful\n")
        
        db = client[MONGODB_DB_NAME]
        users_collection = db["users"]
        
        # Count users
        total_users = users_collection.count_documents({})
        users_needing_migration = users_collection.count_documents({
            "tier": {"$exists": False}
        })
        
        print(f"📊 Status:")
        print(f"   Total users: {total_users}")
        print(f"   Users needing migration: {users_needing_migration}")
        
        if users_needing_migration == 0:
            print("\n✅ All users already migrated. No action needed.")
            return
        
        print(f"\n🔧 Migrating {users_needing_migration} users...")
        print(f"   Free tier slots: {FREE_TIER_LIMIT}")
        print(f"   Free tier credits: {FREE_TIER_CREDITS}\n")
        
        # Get all users without tier
        users_to_migrate = list(users_collection.find({
            "tier": {"$exists": False}
        }))
        
        now = datetime.now(timezone.utc)
        next_reset = now + timedelta(hours=24)
        
        migrated_count = 0
        free_tier_assigned = 0
        limited_assigned = 0
        
        for user in users_to_migrate:
            user_id = user["_id"]
            email = user.get("email", "unknown")
            current_credits = user.get("credits", 0)
            
            # Determine tier assignment
            if free_tier_assigned < FREE_TIER_LIMIT:
                # Assign free tier
                tier = "free"
                credits = max(current_credits, FREE_TIER_CREDITS)  # Keep existing if higher
                
                tier_data = {
                    "tier": "free",
                    "credits": credits,
                    "tier_start_date": now,
                    "tier_end_date": None,
                    "last_credit_reset": now,
                    "next_credit_reset": next_reset,
                    "tier_history": [{
                        "tier": "free",
                        "assigned_at": now,
                        "reason": "migration"
                    }],
                    "had_free_tier": True,
                    "credit_reset_history": []
                }
                
                free_tier_assigned += 1
                print(f"   ✅ {email}: FREE tier ({credits} credits)")
                
            else:
                # Assign limited tier (free tier full)
                tier = "limited"
                credits = current_credits  # Keep existing credits
                
                tier_data = {
                    "tier": "limited",
                    "credits": credits,
                    "tier_start_date": now,
                    "tier_end_date": None,
                    "last_credit_reset": None,
                    "next_credit_reset": None,
                    "tier_history": [{
                        "tier": "limited",
                        "assigned_at": now,
                        "reason": "migration_free_tier_full"
                    }],
                    "had_free_tier": False,
                    "credit_reset_history": []
                }
                
                limited_assigned += 1
                print(f"   ⚠️  {email}: LIMITED tier ({credits} credits) - free tier full")
            
            # Ensure payment fields exist
            if "purchase_history" not in user:
                tier_data["purchase_history"] = []
            if "usage_history" not in user:
                tier_data["usage_history"] = []
            if "last_purchase" not in user:
                tier_data["last_purchase"] = None
            if "total_spent" not in user:
                tier_data["total_spent"] = 0.0
            
            # Update user
            users_collection.update_one(
                {"_id": user_id},
                {"$set": tier_data}
            )
            
            migrated_count += 1
        
        print(f"\n✅ Migration complete!")
        print(f"   Migrated: {migrated_count} users")
        print(f"   Free tier: {free_tier_assigned} users")
        print(f"   Limited tier: {limited_assigned} users")
        
        # Verification
        print(f"\n🔍 Verification:")
        users_with_tier = users_collection.count_documents({"tier": {"$exists": True}})
        free_tier_count = users_collection.count_documents({"tier": "free"})
        limited_count = users_collection.count_documents({"tier": "limited"})
        paid_tiers = users_collection.count_documents({
            "tier": {"$in": ["basic", "pro", "premium"]}
        })
        
        print(f"   Users with tier: {users_with_tier}/{total_users}")
        print(f"   Free tier: {free_tier_count}")
        print(f"   Limited: {limited_count}")
        print(f"   Paid tiers: {paid_tiers}")
        
        if users_with_tier == total_users:
            print("   ✅ All users successfully migrated!")
        else:
            print(f"   ⚠️  Warning: {total_users - users_with_tier} users still missing tier")
        
        # Show sample users
        print(f"\n📋 Sample users:")
        sample_free = users_collection.find_one({"tier": "free"})
        if sample_free:
            print(f"   Free tier example:")
            print(f"      Email: {sample_free.get('email')}")
            print(f"      Credits: {sample_free.get('credits')}")
            print(f"      Next reset: {sample_free.get('next_credit_reset')}")
        
        sample_limited = users_collection.find_one({"tier": "limited"})
        if sample_limited:
            print(f"   Limited tier example:")
            print(f"      Email: {sample_limited.get('email')}")
            print(f"      Credits: {sample_limited.get('credits')}")
        
        client.close()
        print("\n" + "=" * 70)
        print("✅ MIGRATION COMPLETE")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def add_test_credits_to_user(email: str, tier: str = "pro"):
    """
    Add a test paid tier to a specific user (useful for testing).
    
    Args:
        email: User email
        tier: "basic", "pro", or "premium"
    """
    
    tier_config = {
        "basic": {"credits": 142, "price": 4.99, "duration_days": 30},
        "pro": {"credits": 284, "price": 9.99, "duration_days": 30},
        "premium": {"credits": 568, "price": 19.99, "duration_days": 30},
    }
    
    if tier not in tier_config:
        print(f"❌ Invalid tier: {tier}")
        return
    
    config = tier_config[tier]
    
    print(f"\n🎁 Adding {tier.upper()} tier to {email}...")
    
    try:
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        
        db = client[MONGODB_DB_NAME]
        users_collection = db["users"]
        
        user = users_collection.find_one({"email": email.lower()})
        if not user:
            print(f"❌ User not found: {email}")
            return
        
        now = datetime.now(timezone.utc)
        tier_end = now + timedelta(days=config["duration_days"])
        
        previous_tier = user.get("tier", "free")
        
        result = users_collection.update_one(
            {"email": email.lower()},
            {
                "$set": {
                    "tier": tier,
                    "tier_start_date": now,
                    "tier_end_date": tier_end,
                    "previous_tier": previous_tier,
                    "had_free_tier": user.get("tier") == "free",
                    "last_purchase": now,
                },
                "$inc": {
                    "credits": config["credits"],
                    "total_spent": config["price"]
                },
                "$push": {
                    "purchase_history": {
                        "package": tier,
                        "credits": config["credits"],
                        "price": config["price"],
                        "date": now,
                        "note": "Test purchase via migration script"
                    },
                    "tier_history": {
                        "tier": tier,
                        "assigned_at": now,
                        "expires_at": tier_end,
                        "reason": "test_purchase",
                        "previous_tier": previous_tier
                    }
                }
            }
        )
        
        if result.modified_count > 0:
            updated_user = users_collection.find_one({"email": email.lower()})
            print(f"✅ Tier added successfully!")
            print(f"   Tier: {tier.upper()}")
            print(f"   Credits: {updated_user.get('credits')}")
            print(f"   Expires: {tier_end}")
            print(f"   Tokens available: {int(updated_user.get('credits') * 70000):,}")
        else:
            print(f"❌ Update failed")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Failed to add tier: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate users to tier system")
    parser.add_argument(
        "--add-tier",
        type=str,
        help="Email of user to add test tier to"
    )
    parser.add_argument(
        "--tier",
        type=str,
        default="pro",
        choices=["basic", "pro", "premium"],
        help="Tier to add (default: pro)"
    )
    
    args = parser.parse_args()
    
    if args.add_tier:
        # Add test tier to specific user
        asyncio.run(add_test_credits_to_user(args.add_tier, args.tier))
    else:
        # Run full migration
        asyncio.run(migrate_users())