# backend/Services/prompt_refiner.py - FIXED VERSION
"""
Prompt Refiner using Groq API (FREE)
Transforms raw user prompts into structured, detailed prompts.
"""

import os
import asyncio
import httpx
from typing import Dict, Any
from dotenv import load_dotenv

# Token tracking (for monitoring only - Groq is free)
from middleware.credits_middleware import token_tracker

load_dotenv()

# Groq API Configuration (FREE)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "15"))

# System prompt for refiner
PROMPT_REFINER_SYSTEM = """You are an expert UI/UX prompt engineer. Transform vague user prompts into detailed, structured specifications.

INPUT: Short, casual prompt (e.g. "login screen", "dashboard with charts")
OUTPUT: 3-4 line detailed prompt with:
- Screen type and purpose
- Key UI components needed
- Design style and aesthetic
- User interaction flow

Keep it concise but comprehensive. Focus on actionable UI elements."""

PROJECT_TITLER_SYSTEM = """You are a creative product manager. 
Your task is to generate a short, catchy, and professional project title (2-4 words) for a mobile app project based on the user's prompt.
Do NOT use special characters. Just the title text.
Example: "Modern E-commerce App", "Fitness Tracker Dashboard", "Social Media Feed"."""


class RefinerStats:
    """Track refiner statistics"""
    def __init__(self):
        self.total = 0
        self.successful = 0
        self.skipped = 0
    
    def record(self, result: Dict[str, Any]):
        self.total += 1
        if result.get("refinement_applied"):
            self.successful += 1
        else:
            self.skipped += 1
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total,
            "successful_refinements": self.successful,
            "skipped": self.skipped,
            "success_rate": round((self.successful / self.total * 100) if self.total > 0 else 0, 2)
        }


# Global stats tracker
refiner_stats = RefinerStats()


def _detect_keywords(text: str) -> list:
    """Detect UI-related keywords in text"""
    keywords = []
    keyword_map = {
        "auth": ["login", "signup", "register", "signin", "password", "authentication"],
        "ecommerce": ["cart", "product", "shop", "checkout", "payment", "store"],
        "dashboard": ["dashboard", "analytics", "stats", "chart", "graph", "metrics"],
        "social": ["feed", "post", "comment", "like", "follow", "profile"],
        "onboarding": ["onboard", "tutorial", "welcome", "intro", "guide"],
    }
    
    text_lower = text.lower()
    for category, words in keyword_map.items():
        if any(word in text_lower for word in words):
            keywords.append(category)
    
    return keywords


async def refine_prompt(raw_prompt: str, timeout: int = 15) -> Dict[str, Any]:
    """
    API 0: Transform raw user prompt into structured, detailed prompt.
    
    Uses Groq API (FREE) - tokens are logged but NOT counted toward credits.
    
    Args:
        raw_prompt: User's original input (can be vague, short, casual)
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary containing:
        - original_prompt: User's raw input
        - refined_prompt: Enhanced 3-4 line structured prompt
        - refinement_applied: Boolean indicating if refinement was successful
        - metadata: Additional info (word count, detected keywords, token usage, etc.)
    """
    
    # Fallback in case of API failure
    fallback_result = {
        "original_prompt": raw_prompt,
        "refined_prompt": raw_prompt,  # Pass through unchanged
        "refinement_applied": False,
        "metadata": {
            "reason": "API call failed or skipped",
            "original_word_count": len(raw_prompt.split()),
            "refined_word_count": len(raw_prompt.split()),
            "tokens_used": 0,
            "free_api": "groq"
        }
    }
    
    # Skip refinement for empty prompts
    if not raw_prompt or not raw_prompt.strip():
        fallback_result["metadata"]["reason"] = "Empty prompt"
        return fallback_result
    
    # Skip refinement if prompt is already detailed (>50 words)
    word_count = len(raw_prompt.split())
    if word_count > 50:
        print(f"ℹ️  [REFINER] Prompt already detailed ({word_count} words), skipping refinement")
        fallback_result["refinement_applied"] = False
        fallback_result["metadata"]["reason"] = "Already detailed"
        return fallback_result
    
    # Check if Groq API key is configured
    if not GROQ_API_KEY:
        print("⚠️  [REFINER] Groq API key not configured - skipping refinement")
        fallback_result["metadata"]["reason"] = "API key not configured"
        return fallback_result
    
    try:
        print(f"🔄 [API 0 - REFINER] Refining prompt: '{raw_prompt[:100]}...'")
        
        # Prepare Groq API request
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": PROMPT_REFINER_SYSTEM},
                {"role": "user", "content": f"USER PROMPT: {raw_prompt}\n\nREFINED PROMPT:"}
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        # Call Groq API with timeout
        async with httpx.AsyncClient() as client:
            response = await asyncio.wait_for(
                client.post(GROQ_API_URL, headers=headers, json=payload),
                timeout=timeout
            )
            
            response.raise_for_status()
            data = response.json()
        
        # Extract refined prompt
        refined_text = data["choices"][0]["message"]["content"].strip()
        
        # 🆕 TOKEN TRACKING (Groq API - FREE, just for monitoring)
        tokens_used = 0
        if "usage" in data:
            input_tokens = data["usage"].get("prompt_tokens", 0)
            output_tokens = data["usage"].get("completion_tokens", 0)
            tokens_used = data["usage"].get("total_tokens", 0)
            
            print(f"📊 Groq API (FREE) - Input: {input_tokens:,} | Output: {output_tokens:,} | Total: {tokens_used:,}")
            
            # NOTE: We DON'T add to token_tracker since Groq is free
            # token_tracker.add_usage(input_tokens, output_tokens)  # ❌ Don't do this
        
        # Clean up the response
        refined_text = refined_text.replace("REFINED PROMPT:", "").strip()
        refined_text = refined_text.replace("OUTPUT:", "").strip()
        
        # Remove markdown code blocks if present
        if refined_text.startswith("```"):
            refined_text = refined_text.split("```")[1].strip()
        
        # Validate refinement quality
        refined_word_count = len(refined_text.split())
        
        # If refined prompt is too short or too similar to original, use fallback
        if refined_word_count < word_count + 5:
            print(f"⚠️  [REFINER] Refinement too short, using original")
            fallback_result["metadata"]["tokens_used"] = tokens_used
            return fallback_result
        
        print(f"✅ [API 0 - REFINER] Successfully refined prompt")
        print(f"   Original: {word_count} words → Refined: {refined_word_count} words")
        
        # Detect keywords for metadata
        detected_keywords = _detect_keywords(refined_text)
        
        return {
            "original_prompt": raw_prompt,
            "refined_prompt": refined_text,
            "refinement_applied": True,
            "metadata": {
                "original_word_count": word_count,
                "refined_word_count": refined_word_count,
                "expansion_ratio": round(refined_word_count / word_count, 2),
                "detected_keywords": detected_keywords,
                "tokens_used": tokens_used,
                "free_api": "groq",
                "reason": "Successfully refined"
            }
        }
        
    except asyncio.TimeoutError:
        print(f"⚠️  [REFINER] Timeout - using original prompt")
        fallback_result["metadata"]["reason"] = "Timeout"
        return fallback_result
        
    except httpx.HTTPStatusError as e:
        print(f"⚠️  [REFINER] HTTP Error {e.response.status_code} - using original prompt")
        fallback_result["metadata"]["reason"] = f"HTTP {e.response.status_code}"
        return fallback_result
        
    except Exception as e:
        print(f"⚠️  [REFINER] Error: {e} - using original prompt")
        fallback_result["metadata"]["reason"] = f"Error: {str(e)[:50]}"
        return fallback_result

async def generate_project_title(raw_prompt: str, timeout: int = 10) -> str:
    """
    Generate a short 2-4 word project title from the prompt.
    """
    if not raw_prompt or not raw_prompt.strip():
        return "Untitled Project"
    
    # Check if Groq API key is configured
    if not GROQ_API_KEY:
        return "New Project"
    
    try:
        # Prepare Groq API request
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": PROJECT_TITLER_SYSTEM},
                {"role": "user", "content": f"USER PROMPT: {raw_prompt}\n\nPROJECT TITLE:"}
            ],
            "temperature": 0.5,
            "max_tokens": 20
        }
        
        # Call Groq API with timeout
        async with httpx.AsyncClient() as client:
            response = await asyncio.wait_for(
                client.post(GROQ_API_URL, headers=headers, json=payload),
                timeout=timeout
            )
            
            if response.status_code != 200:
                print(f"⚠️ [TITLER] API Error: {response.status_code}")
                return "New Project"
                
            data = response.json()
        
        title = data["choices"][0]["message"]["content"].strip()
        
        # Clean up quotes if present
        title = title.replace('"', '').replace("'", "").replace("*", "").strip()
        
        # Limit to 30 chars
        if len(title) > 30:
            title = title[:27] + "..."
            
        print(f"🏷️ [TITLER] Generated title: {title}")
        return title
        
    except Exception as e:
        print(f"⚠️ [TITLER] Failed to generate title: {e}")
        return "New Project"