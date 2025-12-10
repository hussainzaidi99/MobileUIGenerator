# backend/scripts/migrate_user_credits.py
"""
Migration script to add credits system fields to existing users.
Run this ONCE after setting up the credits system.

Usage:
    python scripts/migrate_user_credits.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")

def migrate_users():
    """Add credits system fields to all existing users."""
    
    print("\n" + "=" * 70)
    print("🔄 USER CREDITS MIGRATION")
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
        
        # Count users before migration
        total_users = users_collection.count_documents({})
        users_needing_update = users_collection.count_documents({"credits": {"$exists": False}})
        
        print(f"📊 Status:")
        print(f"   Total users: {total_users}")
        print(f"   Users needing credits field: {users_needing_update}")
        
        if users_needing_update == 0:
            print("\n✅ All users already have credits fields. No migration needed.")
            return
        
        print(f"\n🔧 Updating {users_needing_update} users...")
        
        # Update all users that don't have credits field
        result = users_collection.update_many(
            {"credits": {"$exists": False}},  # Only update users without credits
            {
                "$set": {
                    "credits": 0.0,                    # Start with 0 credits
                    "purchase_history": [],            # Empty purchase history
                    "usage_history": [],               # Empty usage history
                    "last_purchase": None,             # No purchases yet
                    "total_spent": 0.0,                # No money spent yet
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        print(f"\n✅ Migration complete!")
        print(f"   Modified {result.modified_count} users")
        print(f"   Matched {result.matched_count} users")
        
        # Verify migration
        print(f"\n🔍 Verification:")
        users_with_credits = users_collection.count_documents({"credits": {"$exists": True}})
        print(f"   Users with credits field: {users_with_credits}/{total_users}")
        
        if users_with_credits == total_users:
            print("   ✅ All users successfully migrated!")
        else:
            print(f"   ⚠️ Warning: {total_users - users_with_credits} users still missing credits field")
        
        # Show sample user
        sample_user = users_collection.find_one({"credits": {"$exists": True}})
        if sample_user:
            print(f"\n📋 Sample user schema:")
            print(f"   Email: {sample_user.get('email')}")
            print(f"   Credits: {sample_user.get('credits')}")
            print(f"   Purchase History: {len(sample_user.get('purchase_history', []))} items")
            print(f"   Usage History: {len(sample_user.get('usage_history', []))} items")
        
        client.close()
        print("\n" + "=" * 70)
        print("✅ MIGRATION COMPLETE")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def add_test_credits(email: str, credits: float = 142.0):
    """Add test credits to a specific user (useful for testing)."""
    
    print(f"\n🎁 Adding {credits} test credits to {email}...")
    
    try:
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        
        db = client[MONGODB_DB_NAME]
        users_collection = db["users"]
        
        result = users_collection.update_one(
            {"email": email.lower()},
            {
                "$inc": {"credits": credits},
                "$push": {
                    "purchase_history": {
                        "package": "test_grant",
                        "credits": credits,
                        "price": 0,
                        "date": datetime.now(timezone.utc),
                        "note": "Test credits granted by admin"
                    }
                }
            }
        )
        
        if result.modified_count > 0:
            user = users_collection.find_one({"email": email.lower()})
            print(f"✅ Credits added successfully!")
            print(f"   New balance: {user.get('credits')} credits")
            print(f"   Tokens available: {int(user.get('credits') * 70000):,}")
        else:
            print(f"❌ User not found: {email}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Failed to add credits: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate users to credits system")
    parser.add_argument(
        "--add-credits",
        type=str,
        help="Email of user to add test credits to"
    )
    parser.add_argument(
        "--amount",
        type=float,
        default=142.0,
        help="Amount of credits to add (default: 142)"
    )
    
    args = parser.parse_args()
    
    if args.add_credits:
        # Add test credits to specific user
        add_test_credits(args.add_credits, args.amount)
    else:
        # Run full migration
        migrate_users()