# backend/middleware/credits_middleware.py
"""
Credits & Token Tracking Middleware
Tracks token usage across API calls and manages credit deductions

PRICING MODEL:
- 1 Credit = 70,000 tokens
- 10M tokens = 142 credits ($2.50 cost: $0.50 input + $2.00 output)
- Based on Gemini 2.0 Flash pricing
"""

from typing import Dict
from payments.payment_routes import get_user_credits, deduct_credits, TOKENS_PER_CREDIT


class TokenTracker:
    """Track token usage across API calls"""
    
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        
    def add_usage(self, input_tokens: int, output_tokens: int):
        """Add token usage from an API call"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += (input_tokens + output_tokens)
    
    def reset(self):
        """Reset tracker for new request"""
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
    
    def get_summary(self) -> Dict:
        """Get usage summary with cost estimation"""
        credits_used = self.total_tokens / TOKENS_PER_CREDIT
        
        # Cost estimation based on Gemini 2.0 Flash pricing
        # Input: $0.075 per 1M tokens | Output: $0.30 per 1M tokens
        input_cost = (self.input_tokens / 1_000_000) * 0.075
        output_cost = (self.output_tokens / 1_000_000) * 0.30
        estimated_cost = input_cost + output_cost
        
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "credits_used": round(credits_used, 4),
            "estimated_cost": round(estimated_cost, 6)
        }


# Global token tracker instance
token_tracker = TokenTracker()


def estimate_tokens(prompt: str) -> int:
    """
    Estimate token usage for a complete UI generation request.
    
    Based on empirical data:
    - Your pricing: 10M tokens = 142 credits = $2.50 cost
    - Average per generation: ~70,000 tokens (1 credit)
    - Complex generations can use 100k-200k tokens
    
    This accounts for:
    1. Prompt Refiner API (Groq - free, not counted)
    2. Intent Extraction API (Gemini 2.0 Flash)
    3. Component Generation API (Gemini 2.0 Flash) 
    4. Background Generation API (Gemini 2.0 Flash)
    5. System prompts overhead (~2000 tokens per API)
    6. Output generation (usually 2-4x input tokens)
    """
    
    # Base token estimation from prompt
    word_count = len(prompt.split())
    char_count = len(prompt)
    
    # More accurate: ~1.3 tokens per word for English
    prompt_tokens = int(word_count * 1.3)
    
    # Estimate complexity based on prompt characteristics
    has_multiple_screens = any(keyword in prompt.lower() for keyword in 
        ['screens', 'pages', 'login and signup', 'dashboard', 'multiple', 'and'])
    has_rich_components = any(keyword in prompt.lower() for keyword in
        ['chart', 'graph', 'cards', 'grid', 'list', 'form', 'animation'])
    is_detailed_prompt = word_count > 30 or char_count > 200
    
    # Calculate complexity multiplier
    complexity_score = 1.0
    if has_multiple_screens:
        complexity_score += 0.5
    if has_rich_components:
        complexity_score += 0.3
    if is_detailed_prompt:
        complexity_score += 0.2
    
    # Estimation breakdown:
    
    # 1. Input tokens across 3 Gemini API calls
    #    (Refiner uses Groq - free, not counted)
    api_calls = 3  # Intent, Component, Background
    system_prompt_overhead = 2000 * api_calls  # ~2k tokens per system prompt
    user_prompt_repeated = prompt_tokens * api_calls
    total_input = system_prompt_overhead + user_prompt_repeated
    
    # 2. Output tokens (typically 2-4x input for UI generation)
    #    - Intent extraction: ~1000 tokens
    #    - Component generation: ~15000-40000 tokens (main cost)
    #    - Background generation: ~3000-8000 tokens
    base_output = 20000  # Conservative baseline
    complexity_adjusted_output = int(base_output * complexity_score)
    
    # 3. Total estimation
    total_estimated = total_input + complexity_adjusted_output
    
    # Map to expected ranges:
    # - Simple (1 screen, basic components): ~50k-70k tokens (0.7-1.0 credits)
    # - Medium (2-3 screens, rich components): ~80k-120k tokens (1.1-1.7 credits)  
    # - Complex (multiple screens, charts, grids): ~130k-200k tokens (1.9-2.9 credits)
    
    if word_count < 15 and not has_multiple_screens:
        # Simple generation
        estimated = 25000
    elif word_count < 30 and complexity_score < 1.5:
        # Medium generation
        estimated = 45000
    else:
        # Complex generation
        estimated = max(total_estimated, 70000)
    
    # Apply complexity multiplier (reduced impact)
    estimated = int(estimated * (1 + (complexity_score - 1) * 0.5))
    
    # Cap at reasonable maximum (prevent extreme estimates)
    estimated = min(estimated, 150000)
    
    # Add 5% safety margin (lowered from 15%)
    estimated = int(estimated * 1.05)
    
    print(f"📊 Token Estimation Breakdown:")
    print(f"   Prompt: {word_count} words, {char_count} chars")
    print(f"   Complexity Score: {complexity_score:.2f}")
    print(f"   Estimated Total: {estimated:,} tokens")
    print(f"   Estimated Credits: {estimated / TOKENS_PER_CREDIT:.4f}")
    
    return estimated


async def check_user_credits(user_id: str, estimated_tokens: int) -> bool:
    
    """
    Check if user has sufficient credits before generation.
    Returns True if user has enough credits, False otherwise.
    """
    try:
        balance = await get_user_credits(user_id)
        current_credits = balance.get("credits", 0)
        
        required_credits = estimated_tokens / TOKENS_PER_CREDIT
        
        print(f"💳 Credit Check:")
        print(f"   User ID: {user_id}")
        print(f"   Current Balance: {current_credits:.4f} credits")
        print(f"   Required: {required_credits:.4f} credits ({estimated_tokens:,} tokens)")
        print(f"   Status: {'✅ Sufficient' if current_credits >= required_credits else '❌ Insufficient'}")
        
        return current_credits >= required_credits
        
    except Exception as e:
        print(f"⚠️ Credit check failed: {e}")
        return False


async def deduct_credits_after_generation(user_id: str) -> Dict:
    """
    Deduct credits after successful generation based on actual token usage.
    Returns deduction result with updated balance.
    """
    try:
        actual_tokens = token_tracker.total_tokens
        
        if actual_tokens == 0:
            print("⚠️ Warning: No tokens tracked - generation may have failed")
            return {
                "success": False,
                "error": "No tokens tracked - generation may have failed"
            }
        
        # Deduct credits
        success = await deduct_credits(user_id, actual_tokens)
        
        if not success:
            print("❌ Credit deduction failed - insufficient balance")
            return {
                "success": False,
                "error": "Credit deduction failed - insufficient balance"
            }
        
        # Get updated balance
        balance = await get_user_credits(user_id)
        
        credits_deducted = actual_tokens / TOKENS_PER_CREDIT
        
        result = {
            "success": True,
            "tokens_used": actual_tokens,
            "credits_deducted": round(credits_deducted, 4),
            "remaining_credits": balance["credits"],
            "remaining_tokens": balance["tokens_remaining"]
        }
        
        print(f"✅ Credits Deducted Successfully:")
        print(f"   Tokens Used: {actual_tokens:,}")
        print(f"   Input: {token_tracker.input_tokens:,} | Output: {token_tracker.output_tokens:,}")
        print(f"   Credits Deducted: {credits_deducted:.4f}")
        print(f"   Remaining Balance: {balance['credits']:.4f} credits ({balance['tokens_remaining']:,} tokens)")
        
        return result
        
    except Exception as e:
        print(f"❌ Credit deduction error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }