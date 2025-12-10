# backend/services/background_jobs.py
"""
Background Jobs for Tier Management System
- Daily credit reset for free-tier users
- Daily tier expiration check and downgrade
- Can be run as cron jobs or with APScheduler
"""

import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from Services.tier_manager import TierManager

logger = logging.getLogger(__name__)

# ============================================================================
# JOB FUNCTIONS
# ============================================================================

async def job_reset_free_tier_credits():
    """
    Job: Reset credits for free-tier users whose monthly cycle has completed.
    Runs daily to check which users are due for their monthly reset.
    """
    try:
        logger.info("🔄 Starting free-tier credit reset job...")
        start_time = datetime.now(timezone.utc)
        
        results = await TierManager.reset_free_tier_credits()
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"✅ Credit reset job completed in {duration:.2f}s | "
            f"Users reset: {len(results)}"
        )
        
        return {
            "success": True,
            "users_reset": len(results),
            "duration_seconds": duration,
            "timestamp": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        logger.error(f"❌ Credit reset job failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc)
        }


async def job_downgrade_expired_tiers():
    """
    Job: Downgrade users with expired paid tiers (runs daily)
    """
    try:
        logger.info("⬇️ Starting tier expiration check job...")
        start_time = datetime.now(timezone.utc)
        
        results = await TierManager.downgrade_expired_tiers()
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"✅ Tier downgrade job completed in {duration:.2f}s | "
            f"Users downgraded: {len(results)}"
        )
        
        return {
            "success": True,
            "users_downgraded": len(results),
            "duration_seconds": duration,
            "timestamp": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        logger.error(f"❌ Tier downgrade job failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc)
        }


# ============================================================================
# SCHEDULER SETUP
# ============================================================================

scheduler = AsyncIOScheduler()

def setup_background_jobs():
    """
    Setup background jobs with APScheduler.
    Call this in your FastAPI startup event.
    """
    
    # Job 1: Check and reset free-tier credits every day at 00:00 UTC
    # (Only resets users whose 30-day cycle has completed)
    scheduler.add_job(
        job_reset_free_tier_credits,
        trigger=CronTrigger(hour=0, minute=0),  # Daily at midnight UTC
        id="reset_free_tier_credits",
        name="Check & Reset Free Tier Credits (Monthly)",
        replace_existing=True,
        misfire_grace_time=3600  # 1 hour grace period
    )
    logger.info("📅 Scheduled: Check free-tier credit resets (daily check for monthly resets)")
    
    # Job 2: Check and downgrade expired tiers every day at 01:00 UTC
    scheduler.add_job(
        job_downgrade_expired_tiers,
        trigger=CronTrigger(hour=1, minute=0),  # Daily at 1 AM UTC
        id="downgrade_expired_tiers",
        name="Downgrade Expired Tiers",
        replace_existing=True,
        misfire_grace_time=3600
    )
    logger.info("📅 Scheduled: Downgrade expired tiers (daily at 01:00 UTC)")
    
    # Start the scheduler
    scheduler.start()
    logger.info("✅ Background job scheduler started")


def shutdown_background_jobs():
    """
    Shutdown the scheduler.
    Call this in your FastAPI shutdown event.
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("🛑 Background job scheduler stopped")


# ============================================================================
# MANUAL JOB TRIGGERS (for testing)
# ============================================================================

async def run_all_jobs_now():
    """
    Manually run all jobs immediately (for testing).
    Usage: await run_all_jobs_now()
    """
    logger.info("▶️ Running all background jobs manually...")
    
    results = {
        "credit_reset": await job_reset_free_tier_credits(),
        "tier_downgrade": await job_downgrade_expired_tiers()
    }
    
    logger.info("✅ All jobs completed")
    return results


# ============================================================================
# ALTERNATIVE: SIMPLE CRON SCRIPT (without APScheduler)
# ============================================================================

async def run_cron_jobs():
    """
    Simple function to run all jobs sequentially.
    Use this if you want to call it from an external cron job instead of APScheduler.
    
    Example crontab entry:
    0 0 * * * cd /path/to/backend && python -c "import asyncio; from services.background_jobs import run_cron_jobs; asyncio.run(run_cron_jobs())"
    """
    logger.info("🔄 Starting scheduled maintenance jobs...")
    
    # Run jobs
    credit_reset_result = await job_reset_free_tier_credits()
    tier_downgrade_result = await job_downgrade_expired_tiers()
    
    # Summary
    total_users_affected = (
        credit_reset_result.get("users_reset", 0) +
        tier_downgrade_result.get("users_downgraded", 0)
    )
    
    logger.info(
        f"✅ Maintenance complete | "
        f"Total users affected: {total_users_affected}"
    )
    
    return {
        "credit_reset": credit_reset_result,
        "tier_downgrade": tier_downgrade_result,
        "total_users_affected": total_users_affected
    }


# ============================================================================
# STANDALONE SCRIPT EXECUTION
# ============================================================================

if __name__ == "__main__":
    """
    Run this script directly for manual job execution:
    python backend/services/background_jobs.py
    """
    import sys
    sys.path.append(".")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Connect to MongoDB
    from db.database import Database
    Database.connect()
    
    # Run jobs
    print("\n" + "="*70)
    print("🔄 RUNNING BACKGROUND JOBS MANUALLY")
    print("="*70 + "\n")
    
    results = asyncio.run(run_cron_jobs())
    
    print("\n" + "="*70)
    print("✅ JOBS COMPLETED")
    print("="*70)
    print(f"Credit Resets: {results['credit_reset'].get('users_reset', 0)}")
    print(f"Tier Downgrades: {results['tier_downgrade'].get('users_downgraded', 0)}")
    print(f"Total Users Affected: {results['total_users_affected']}")
    print("="*70 + "\n")
    
    # Cleanup
    Database.disconnect()