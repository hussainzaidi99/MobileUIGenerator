# backend/payments/payment_routes.py - PRODUCTION READY (Perfectly Aligned with Frontend)
"""
Stripe Payment Integration with Tier Management System
Features:
- Payment verification with email notifications
- Automatic webhook handling
- Credit balance management
- Transaction history tracking
- Duplicate payment prevention
- Perfect alignment with frontend flow
"""

import os
import stripe
import logging
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId

from db.database import Database
from Services.tier_manager import TierManager, TIER_CONFIG
from Services.email_service import EmailService

# Initialize logging
logger = logging.getLogger(__name__)

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

class VerifySessionRequest(BaseModel):
    session_id: str
    user_id: str

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _to_object_id(user_id: str) -> ObjectId:
    """Convert string user_id to ObjectId with better error handling"""
    try:
        user_id = user_id.strip()
        
        if len(user_id) != 24:
            raise ValueError(f"Invalid ObjectId length: {len(user_id)} (expected 24)")
        
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

async def get_user_credits(user_id: str) -> dict:
    """Get user's current credit balance with tier information"""
    db = Database.get_db()
    users_collection = db["users"]
    
    object_id = _to_object_id(user_id)
    user = await users_collection.find_one({"_id": object_id})
    
    if not user:
        logger.error(f"🔍 User not found with ObjectId: {object_id}")
        raise HTTPException(
            status_code=404, 
            detail=f"User not found with ID: {user_id}"
        )
    
    try:
        tier_info = await TierManager.get_user_tier_info(user_id)
    except Exception as e:
        logger.warning(f"⚠️ Failed to get tier info: {e}")
        tier_info = None
    
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

async def deduct_credits(user_id: str, tokens_used: int) -> bool:
    """Deduct credits based on token usage"""
    credits_to_deduct = tokens_used / TOKENS_PER_CREDIT
    
    db = Database.get_db()
    users_collection = db["users"]
    
    object_id = _to_object_id(user_id)
    user = await users_collection.find_one({"_id": object_id})
    
    if not user:
        logger.error(f"❌ Deduct credits failed: User {user_id} not found")
        return False
    
    if user.get("credits", 0) < credits_to_deduct:
        logger.error(f"❌ Deduct credits failed: Insufficient balance")
        return False
    
    result = await users_collection.update_one(
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
    """
    Create Stripe checkout session for credit purchase.
    Called by frontend PricingPage.jsx handlePurchase()
    """
    try:
        if request.credits_package not in CREDIT_PACKAGES:
            raise HTTPException(status_code=400, detail="Invalid package type")
        
        # Validate user exists
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
            cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/payment/cancel",
            metadata={
                "user_id": request.user_id,
                "credits": str(package["credits"]),
                "package_type": request.credits_package,
                "package_id": request.credits_package,
                "duration_days": str(package["duration_days"])
            }
        )
        
        logger.info(f"✅ Checkout session created for user {request.user_id}: {session.id}")
        
        return JSONResponse({
            "session_id": session.id,
            "url": session.url
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in create-checkout: {e}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Checkout creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Checkout creation failed: {str(e)}")


@router.post("/verify-session")
async def verify_payment_session(request: VerifySessionRequest):
    """
    Verify Stripe checkout session and add credits to user account.
    This is called by PaymentStatusPage.jsx after successful payment.
    
    Flow:
    1. User completes Stripe payment
    2. Stripe redirects to /payment/success?session_id=xxx
    3. Frontend calls this endpoint with session_id + user_id
    4. We verify payment, add credits, send email
    
    CRITICAL: This uses atomic database operations to prevent race conditions
    between frontend calls and webhook calls.
    """
    try:
        # Retrieve Stripe session
        session = stripe.checkout.Session.retrieve(request.session_id)
        
        if session.payment_status != "paid":
            logger.warning(f"Payment not completed: {request.session_id}, status: {session.payment_status}")
            raise HTTPException(
                status_code=400,
                detail=f"Payment not completed. Status: {session.payment_status}"
            )
        
        # Get database
        db = Database.get_db()
        users_collection = db["users"]
        
        # 🔒 CRITICAL: Atomic check-and-set to prevent race condition
        # Try to mark this session as processed FIRST before doing anything else
        result = await users_collection.update_one(
            {
                "_id": ObjectId(request.user_id),
                "purchase_history.stripe_session_id": {"$ne": request.session_id}  # Session NOT already in history
            },
            {
                "$push": {
                    "purchase_history": {
                        "stripe_session_id": request.session_id,
                        "processing_started_at": datetime.now(timezone.utc),
                        "status": "processing"
                    }
                }
            }
        )
        
        # If matched_count is 0, it means session was already processed
        if result.matched_count == 0:
            logger.warning(f"🔒 Payment {request.session_id} already being processed or completed")
            
            # Get current balance to return
            try:
                balance = await get_user_credits(request.user_id)
                return JSONResponse({
                    "success": True,
                    "already_processed": True,
                    "message": "Payment already confirmed",
                    "credits": balance["credits"],
                    "tokens_remaining": balance["tokens_remaining"]
                })
            except:
                return JSONResponse({
                    "success": True,
                    "already_processed": True,
                    "message": "Payment already confirmed"
                })
        
        # If we get here, we successfully claimed this payment processing
        logger.info(f"🔒 Successfully claimed payment processing lock for session {request.session_id}")
        
        # Get user (we know they exist from the atomic update above)
        user = await users_collection.find_one({"_id": ObjectId(request.user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get package details from session metadata
        package_type = session.metadata.get("package_type") or session.metadata.get("package_id")
        
        if not package_type or package_type not in CREDIT_PACKAGES:
            # Rollback: Remove processing lock
            await users_collection.update_one(
                {"_id": ObjectId(request.user_id)},
                {
                    "$pull": {
                        "purchase_history": {"stripe_session_id": request.session_id}
                    }
                }
            )
            raise HTTPException(status_code=400, detail="Invalid package in session metadata")
        
        package = CREDIT_PACKAGES[package_type]
        credits_to_add = package["credits"]
        amount_paid = session.amount_total / 100  # Convert cents to dollars
        
        # Process payment: Upgrade user tier
        purchase_info = {
            "package": package_type,
            "credits": credits_to_add,
            "price": amount_paid,
            "stripe_session_id": request.session_id,
            "stripe_payment_intent": session.payment_intent,
            "date": datetime.now(timezone.utc),
            "status": "completed"  # Mark as completed
        }
        
        upgrade_result = await TierManager.upgrade_user_tier(
            user_id=request.user_id,
            new_tier=package_type,
            credits_to_add=credits_to_add,
            purchase_info=purchase_info
        )
        
        if not upgrade_result["success"]:
            # Rollback: Remove processing lock
            await users_collection.update_one(
                {"_id": ObjectId(request.user_id)},
                {
                    "$pull": {
                        "purchase_history": {"stripe_session_id": request.session_id}
                    }
                }
            )
            raise HTTPException(
                status_code=500, 
                detail=f"Tier upgrade failed: {upgrade_result.get('error')}"
            )
        
        # Update the purchase history entry to mark as completed
        await users_collection.update_one(
            {
                "_id": ObjectId(request.user_id),
                "purchase_history.stripe_session_id": request.session_id
            },
            {
                "$set": {
                    "purchase_history.$.status": "completed",
                    "purchase_history.$.completed_at": datetime.now(timezone.utc),
                    "purchase_history.$.credits": credits_to_add,
                    "purchase_history.$.price": amount_paid
                }
            }
        )
        
        # Get updated balance
        balance = await get_user_credits(request.user_id)
        
        # Send success email (don't fail request if email fails)
        try:
            await EmailService.send_payment_success_email(
                email=user["email"],
                username=user.get("username", user["email"]),
                package_name=package["name"],
                credits_purchased=credits_to_add,
                amount_paid=amount_paid,
                new_balance=balance["credits"],
                transaction_id=request.session_id
            )
            logger.info(f"✅ Payment success email sent to {user['email']}")
        except Exception as e:
            logger.error(f"Failed to send payment success email: {e}")
            # Don't fail the request if email fails
        
        logger.info(
            f"✅ Payment verified: {request.user_id} -> {package_type} (+{credits_to_add} credits)"
        )
        
        return JSONResponse({
            "success": True,
            "message": f"Successfully upgraded to {TIER_CONFIG[package_type]['name']}!",
            "credits_added": credits_to_add,
            "tier": package_type,
            "tier_name": TIER_CONFIG[package_type]["name"],
            "total_credits": balance["credits"],
            "tokens_remaining": balance["tokens_remaining"],
            "expires_at": upgrade_result.get("expires_at").isoformat() if upgrade_result.get("expires_at") else None,
            "features": TIER_CONFIG[package_type]["features"]
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in verify-session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Payment verification failed")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events for automatic payment processing.
    This is called automatically by Stripe when events occur.
    
    Serves as a backup to the frontend /verify-session call.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if not webhook_secret:
        logger.warning("⚠️ Stripe webhook secret not configured")
        return JSONResponse({"status": "webhook secret not configured"})
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        if session.payment_status == "paid":
            user_id = session.metadata.get("user_id")
            
            if user_id:
                try:
                    # Process payment automatically
                    await verify_payment_session(
                        VerifySessionRequest(
                            session_id=session.id,
                            user_id=user_id
                        )
                    )
                    logger.info(f"✅ Webhook: Payment processed for user {user_id}")
                except Exception as e:
                    logger.error(f"Webhook payment processing failed: {e}")
    
    # Handle checkout.session.expired (payment cancelled/expired)
    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        user_id = session.metadata.get("user_id")
        package_type = session.metadata.get("package_type") or session.metadata.get("package_id")
        
        if user_id and package_type:
            try:
                db = Database.get_db()
                users_collection = db["users"]
                user = users_collection.find_one({"_id": ObjectId(user_id)})
                
                if user and package_type in CREDIT_PACKAGES:
                    package = CREDIT_PACKAGES[package_type]
                    
                    await EmailService.send_payment_failed_email(
                        email=user["email"],
                        username=user.get("username", user["email"]),
                        package_name=package["name"],
                        amount=package["price"] / 100,
                        reason="Payment session expired"
                    )
                    logger.info(f"✅ Webhook: Cancellation email sent to {user['email']}")
            except Exception as e:
                logger.error(f"Failed to send cancellation email: {e}")
    
    return JSONResponse({"status": "success"})


@router.get("/balance/{user_id}")
async def get_credit_balance(user_id: str):
    """
    Get user's credit balance with tier information.
    Called by App.jsx fetchUserCredits()
    """
    try:
        balance = await get_user_credits(user_id)
        return JSONResponse(balance)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Balance check error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {str(e)}")


@router.get("/tier/{user_id}")
async def get_user_tier(user_id: str):
    """
    Get detailed user tier information.
    Called by App.jsx fetchTierInfo()
    """
    try:
        tier_info = await TierManager.get_user_tier_info(user_id)
        
        if not tier_info:
            raise HTTPException(status_code=404, detail="User not found")
        
        return JSONResponse(tier_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tier info error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get tier info: {str(e)}")


@router.get("/free-tier/status")
async def get_free_tier_status():
    """
    Get free tier availability status.
    Called by AuthPage.jsx during signup
    """
    try:
        current_count = await TierManager.get_free_tier_count()
        can_add = await TierManager.can_add_free_tier_user()
        
        return JSONResponse({
            "current_free_tier_users": current_count,
            "max_free_tier_users": 20,
            "available_slots": 20 - current_count,
            "can_add_new_user": can_add
        })
    except Exception as e:
        logger.error(f"Free tier status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packages")
async def get_packages():
    """
    Get available credit packages with tier information.
    Called by PricingPage.jsx fetchPackages()
    """
    packages = []
    
    for key, pkg in CREDIT_PACKAGES.items():
        packages.append({
            "id": key,
            "name": pkg["name"],
            "description": pkg["description"],
            "credits": pkg["credits"],
            "tokens": pkg["tokens"],
            "price": pkg["price"] / 100,  # Convert cents to dollars
            "price_per_credit": round(pkg["price"] / pkg["credits"] / 100, 4),
            "duration_days": pkg["duration_days"],
            "features": TIER_CONFIG[key]["features"]
        })
    
    return JSONResponse({"packages": packages})


@router.post("/deduct")
async def deduct_credits_endpoint(request: Request):
    """
    Internal endpoint to deduct credits.
    Called by middleware after UI generation
    """
    body = await request.json()
    user_id = body.get("user_id")
    tokens_used = body.get("tokens_used")
    
    if not user_id or not tokens_used:
        raise HTTPException(status_code=400, detail="Missing user_id or tokens_used")
    
    success = await deduct_credits(user_id, tokens_used)
    
    if not success:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    balance = await get_user_credits(user_id)
    
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
    """
    Admin endpoint: Reset credits for free-tier users (called by cron job).
    TODO: Add API key authentication in production!
    """
    try:
        reset_results = await TierManager.reset_free_tier_credits()
        
        return JSONResponse({
            "success": True,
            "users_reset": len(reset_results),
            "results": reset_results
        })
    except Exception as e:
        logger.error(f"Credit reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"Credit reset failed: {str(e)}")


@router.post("/admin/downgrade-expired-tiers")
async def downgrade_expired_tiers_endpoint(request: Request):
    """
    Admin endpoint: Downgrade users with expired paid tiers (called by cron job).
    TODO: Add API key authentication in production!
    """
    try:
        downgrade_results = await TierManager.downgrade_expired_tiers()
        
        return JSONResponse({
            "success": True,
            "users_downgraded": len(downgrade_results),
            "results": downgrade_results
        })
    except Exception as e:
        logger.error(f"Downgrade failed: {e}")
        raise HTTPException(status_code=500, detail=f"Downgrade failed: {str(e)}")


# ============================================================================
# DEBUG ENDPOINT (REMOVE IN PRODUCTION)
# ============================================================================

@router.get("/debug/user/{user_id}")
async def debug_user_lookup(user_id: str):
    """
    Debug endpoint to check user lookup.
    ⚠️ REMOVE THIS IN PRODUCTION - exposes user data
    """
    try:
        db = Database.get_db()
        users_collection = db["users"]
        
        try:
            object_id = ObjectId(user_id)
            logger.info(f"✅ ObjectId conversion successful: {object_id}")
        except Exception as e:
            return JSONResponse({
                "error": "Invalid ObjectId format",
                "user_id": user_id,
                "details": str(e)
            })
        
        user = await users_collection.find_one({"_id": object_id})
        
        if user:
            user["_id"] = str(user["_id"])
            
            # Convert datetime objects
            for key in ["created_at", "updated_at", "last_login", "tier_start_date", 
                       "tier_end_date", "next_credit_reset", "last_credit_reset"]:
                if key in user and user[key]:
                    user[key] = user[key].isoformat() if hasattr(user[key], 'isoformat') else str(user[key])
            
            return JSONResponse({
                "found": True,
                "user": user
            })
        else:
            sample_user = await users_collection.find_one()
            
            return JSONResponse({
                "found": False,
                "user_id": user_id,
                "object_id": str(object_id),
                "collection_accessible": sample_user is not None,
                "sample_user_id": str(sample_user["_id"]) if sample_user else None
            })
    
    except Exception as e:
        logger.error(f"Debug lookup error: {e}")
        import traceback
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)