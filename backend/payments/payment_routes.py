# backend/payments/payment_routes.py - FIXED with better error handling
"""
Stripe Payment Integration with Tier Management System
FIXED: Better ObjectId conversion and error handling
"""

import os
import stripe
from fastapi import APIRouter, Request, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId

from db.database import Database
from Services.tier_manager import TierManager, TIER_CONFIG

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/payment", tags=["payment"])

# ============================================================================
# CREDIT PACKAGES CONFIGURATION
# ============================================================================

CREDIT_PACKAGES = {
    "basic": {
        "credits": 142,
        "tokens": 10_000_000,
        "price": 499,
        "name": "Basic Plan",
        "description": "142 Credits - Perfect for small projects (30 days)",
        "duration_days": 30
    },
    "pro": {
        "credits": 284,
        "tokens": 20_000_000,
        "price": 999,
        "name": "Pro Plan",
        "description": "284 Credits - Great for regular use (30 days)",
        "duration_days": 30
    },
    "premium": {
        "credits": 568,
        "tokens": 40_000_000,
        "price": 1999,
        "name": "Premium Plan",
        "description": "568 Credits - Best value for power users (30 days)",
        "duration_days": 30
    }
}

TOKENS_PER_CREDIT = 70_000

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CheckoutRequest(BaseModel):
    user_id: str
    credits_package: str

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _to_object_id(user_id: str) -> ObjectId:
    """Convert string user_id to ObjectId with better error handling"""
    try:
        # Remove any whitespace
        user_id = user_id.strip()
        
        # Validate length (MongoDB ObjectIds are 24 hex characters)
        if len(user_id) != 24:
            raise ValueError(f"Invalid ObjectId length: {len(user_id)} (expected 24)")
        
        # Convert to ObjectId
        return ObjectId(user_id)
    except InvalidId as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid user_id format: '{user_id}' is not a valid MongoDB ObjectId"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to parse user_id: {str(e)}"
        )

def get_user_credits(user_id: str) -> dict:
    """Get user's current credit balance with tier information"""
    db = Database.get_db()
    users_collection = db["users"]
    
    # Convert to ObjectId with validation
    object_id = _to_object_id(user_id)
    
    # Query database
    user = users_collection.find_one({"_id": object_id})
    
    if not user:
        # Debug: Check if user exists with different query
        print(f"🔍 DEBUG: User not found with ObjectId: {object_id}")
        print(f"🔍 DEBUG: Original user_id string: '{user_id}'")
        
        # Try to find any user to verify collection is accessible
        sample_user = users_collection.find_one()
        if sample_user:
            print(f"🔍 DEBUG: Collection accessible. Sample user _id: {sample_user.get('_id')}")
        else:
            print(f"🔍 DEBUG: Users collection is empty or inaccessible")
        
        raise HTTPException(
            status_code=404, 
            detail=f"User not found with ID: {user_id}"
        )
    
    # Get tier info
    try:
        tier_info = TierManager.get_user_tier_info(user_id)
    except Exception as e:
        print(f"⚠️ Warning: Failed to get tier info: {e}")
        tier_info = None
    
    # Serialize datetime fields
    last_purchase = user.get("last_purchase")
    if last_purchase and hasattr(last_purchase, 'isoformat'):
        last_purchase = last_purchase.isoformat()
    
    return {
        "credits": user.get("credits", 0),
        "tokens_remaining": int(user.get("credits", 0) * TOKENS_PER_CREDIT),
        "last_purchase": last_purchase,
        "total_spent": user.get("total_spent", 0),
        "tier": user.get("tier", "limited"),
        "tier_info": tier_info
    }

def deduct_credits(user_id: str, tokens_used: int) -> bool:
    """Deduct credits based on token usage"""
    credits_to_deduct = tokens_used / TOKENS_PER_CREDIT
    
    db = Database.get_db()
    users_collection = db["users"]
    
    # Convert to ObjectId
    object_id = _to_object_id(user_id)
    
    # Check current balance
    user = users_collection.find_one({"_id": object_id})
    if not user:
        print(f"❌ Deduct credits failed: User {user_id} not found")
        return False
    
    if user.get("credits", 0) < credits_to_deduct:
        print(f"❌ Deduct credits failed: Insufficient balance")
        return False
    
    # Deduct credits
    result = users_collection.update_one(
        {"_id": object_id},
        {
            "$inc": {"credits": -credits_to_deduct},
            "$push": {
                "usage_history": {
                    "tokens": tokens_used,
                    "credits_deducted": credits_to_deduct,
                    "date": datetime.now(timezone.utc)
                }
            }
        }
    )
    
    return result.modified_count > 0

# ============================================================================
# PAYMENT ROUTES
# ============================================================================

@router.post("/create-checkout")
async def create_checkout_session(request: CheckoutRequest):
    """Create Stripe checkout session for tier upgrade"""
    try:
        # Validate package
        if request.credits_package not in CREDIT_PACKAGES:
            raise HTTPException(status_code=400, detail="Invalid package type")
        
        # Validate user exists (this will raise 404 if not found)
        try:
            get_user_credits(request.user_id)
        except HTTPException as e:
            if e.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Cannot create checkout: {e.detail}"
                )
            raise
        
        package = CREDIT_PACKAGES[request.credits_package]
        
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": package["name"],
                        "description": package["description"],
                    },
                    "unit_amount": package["price"]
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/pricing?canceled=true",
            metadata={
                "user_id": request.user_id,
                "credits": str(package["credits"]),
                "package_type": request.credits_package,
                "duration_days": str(package["duration_days"])
            }
        )
        
        return JSONResponse({
            "session_id": session.id,
            "url": session.url
        })
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkout creation failed: {str(e)}")

@router.get("/confirm")
async def confirm_payment(session_id: str = Query(..., description="Stripe session ID")):
    """Confirm payment and upgrade user tier"""
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id")
        
        # Retrieve session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Verify payment was successful
        if session.payment_status != "paid":
            return JSONResponse({
                "success": False,
                "error": "Payment not completed",
                "payment_status": session.payment_status
            }, status_code=400)
        
        # Extract metadata
        user_id = session.metadata.get("user_id")
        credits = int(session.metadata.get("credits", "0"))
        package_type = session.metadata.get("package_type")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in session metadata")
        
        # Convert to ObjectId
        object_id = _to_object_id(user_id)
        
        # Check if this session was already processed
        db = Database.get_db()
        users_collection = db["users"]
        
        user = users_collection.find_one({"_id": object_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if session already processed (prevent double-crediting)
        purchase_history = user.get("purchase_history", [])
        for purchase in purchase_history:
            if purchase.get("stripe_session_id") == session_id:
                # Already processed
                return JSONResponse({
                    "success": True,
                    "already_processed": True,
                    "message": "Payment already confirmed",
                    "credits_added": credits,
                    "tier": user.get("tier"),
                    "total_credits": user.get("credits")
                })
        
        # Process payment: Upgrade user tier
        purchase_info = {
            "package": package_type,
            "credits": credits,
            "price": CREDIT_PACKAGES[package_type]["price"] / 100,
            "stripe_session_id": session_id,
            "date": datetime.now(timezone.utc)
        }
        
        upgrade_result = TierManager.upgrade_user_tier(
            user_id=user_id,
            new_tier=package_type,
            credits_to_add=credits,
            purchase_info=purchase_info
        )
        
        if not upgrade_result["success"]:
            raise HTTPException(status_code=500, detail=f"Tier upgrade failed: {upgrade_result.get('error')}")
        
        # Get updated balance
        balance = get_user_credits(user_id)
        
        print(f"✅ Payment confirmed: {user_id} -> {package_type} (+{credits} credits)")
        
        return JSONResponse({
            "success": True,
            "message": f"Successfully upgraded to {TIER_CONFIG[package_type]['name']}!",
            "credits_added": credits,
            "tier": package_type,
            "tier_name": TIER_CONFIG[package_type]["name"],
            "total_credits": balance["credits"],
            "tokens_remaining": balance["tokens_remaining"],
            "expires_at": upgrade_result.get("expires_at").isoformat() if upgrade_result.get("expires_at") else None,
            "features": TIER_CONFIG[package_type]["features"]
        })
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Payment confirmation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Payment confirmation failed: {str(e)}")

@router.get("/balance/{user_id}")
async def get_credit_balance(user_id: str):
    """Get user's credit balance with tier information"""
    try:
        balance = get_user_credits(user_id)
        return JSONResponse(balance)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Balance check error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {str(e)}")

@router.get("/free-tier/status")
async def get_free_tier_status():
    """Get free tier availability status"""
    try:
        current_count = TierManager.get_free_tier_count()
        can_add = TierManager.can_add_free_tier_user()
        
        return JSONResponse({
            "current_free_tier_users": current_count,
            "max_free_tier_users": 20,
            "available_slots": 20 - current_count,
            "can_add_new_user": can_add
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/packages")
async def get_packages():
    """Get available credit packages with tier information"""
    packages = []
    
    for key, pkg in CREDIT_PACKAGES.items():
        packages.append({
            "id": key,
            "name": pkg["name"],
            "description": pkg["description"],
            "credits": pkg["credits"],
            "tokens": pkg["tokens"],
            "price": pkg["price"] / 100,
            "price_per_credit": round(pkg["price"] / pkg["credits"] / 100, 4),
            "duration_days": pkg["duration_days"],
            "features": TIER_CONFIG[key]["features"]
        })
    
    return JSONResponse({"packages": packages})

@router.get("/tier/{user_id}")
async def get_user_tier(user_id: str):
    """Get detailed user tier information"""
    try:
        tier_info = TierManager.get_user_tier_info(user_id)
        
        if not tier_info:
            raise HTTPException(status_code=404, detail="User not found")
        
        # TierManager.get_user_tier_info() already returns serialized datetimes
        # No need to serialize again - they're already ISO strings
        return JSONResponse(tier_info)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Tier info error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get tier info: {str(e)}")

@router.post("/deduct")
async def deduct_credits_endpoint(request: Request):
    """Internal endpoint to deduct credits"""
    body = await request.json()
    user_id = body.get("user_id")
    tokens_used = body.get("tokens_used")
    
    if not user_id or not tokens_used:
        raise HTTPException(status_code=400, detail="Missing user_id or tokens_used")
    
    success = deduct_credits(user_id, tokens_used)
    
    if not success:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    # Get updated balance
    balance = get_user_credits(user_id)
    
    return JSONResponse({
        "success": True,
        "tokens_used": tokens_used,
        "credits_deducted": tokens_used / TOKENS_PER_CREDIT,
        "remaining_credits": balance["credits"],
        "remaining_tokens": balance["tokens_remaining"]
    })

# ============================================================================
# ADMIN ENDPOINTS (Background Jobs)
# ============================================================================

@router.post("/admin/reset-free-tier-credits")
async def reset_free_tier_credits_endpoint(request: Request):
    """Admin endpoint: Reset credits for free-tier users"""
    try:
        reset_results = TierManager.reset_free_tier_credits()
        
        return JSONResponse({
            "success": True,
            "users_reset": len(reset_results),
            "results": reset_results
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Credit reset failed: {str(e)}")

@router.post("/admin/downgrade-expired-tiers")
async def downgrade_expired_tiers_endpoint(request: Request):
    """Admin endpoint: Downgrade users with expired paid tiers"""
    try:
        downgrade_results = TierManager.downgrade_expired_tiers()
        
        return JSONResponse({
            "success": True,
            "users_downgraded": len(downgrade_results),
            "results": downgrade_results
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Downgrade failed: {str(e)}")

# ============================================================================
# DEBUG ENDPOINT (Remove in production)
# ============================================================================

@router.get("/debug/user/{user_id}")
async def debug_user_lookup(user_id: str):
    """Debug endpoint to check user lookup"""
    try:
        db = Database.get_db()
        users_collection = db["users"]
        
        # Try ObjectId conversion
        try:
            object_id = ObjectId(user_id)
            print(f"✅ ObjectId conversion successful: {object_id}")
        except Exception as e:
            return JSONResponse({
                "error": "Invalid ObjectId format",
                "user_id": user_id,
                "details": str(e)
            })
        
        # Try to find user
        user = users_collection.find_one({"_id": object_id})
        
        if user:
            # Convert ObjectId to string for JSON response
            user["_id"] = str(user["_id"])
            
            # Convert datetime objects
            for key in ["created_at", "updated_at", "last_login", "tier_start_date", "tier_end_date", "next_credit_reset", "last_credit_reset"]:
                if key in user and user[key]:
                    user[key] = user[key].isoformat() if hasattr(user[key], 'isoformat') else str(user[key])
            
            return JSONResponse({
                "found": True,
                "user": user
            })
        else:
            # User not found - check if collection has any users
            sample_user = users_collection.find_one()
            
            return JSONResponse({
                "found": False,
                "user_id": user_id,
                "object_id": str(object_id),
                "collection_accessible": sample_user is not None,
                "sample_user_id": str(sample_user["_id"]) if sample_user else None
            })
    
    except Exception as e:
        import traceback
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)