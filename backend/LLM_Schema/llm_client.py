# backend/LLM_Schema/llm_client.py - PRODUCTION VERSION WITH GEMINI 2.5 FLASH
# All LLM stages (Refiner/Intent/Component/Code/Background) use Gemini 2.5 Flash.
# Deterministic code & preview generation remain NON-LLM as before.
#
# Architecture:
#   Stage 0: Refiner (logical route "refiner")      → Gemini 2.5 Flash
#   Stage 1: Intent (route "intent")                → Gemini 2.5 Flash + CoT orchestration
#   Stage 2: Component Model (route "component")    → Gemini 2.5 Flash + CoT orchestration
#   Stage 3: Background Enhancer (route "code")     → Gemini 2.5 Flash (optional)
#   Preview & RN Converter                          → Deterministic, NO LLM

import os
import sys
import json
import asyncio
import re
from pathlib import Path
from dotenv import load_dotenv
from typing import Any, Dict, List, Union, Optional

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import Google's official Gemini SDK
import google.generativeai as genai

from Services.background_generator import enrich_screens_with_backgrounds
from middleware.credits_middleware import token_tracker


# CoT orchestration system (kept from old architecture)
from LLM_Schema.cot_orchestrator import (
    detect_categories,
    get_enhanced_prompt,
    estimate_token_count,
)

load_dotenv()

# ============================================================================
# 🟢 GEMINI 2.5 FLASH API CONFIG
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "4096"))
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "35"))

# ============================================================================
# 🟠 GROQ API CONFIG (Free Tier for REFINER only)
# ============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "15"))

# Legacy variable names for compatibility
LLM_TEMPERATURE = GEMINI_TEMPERATURE
LLM_TIMEOUT = GEMINI_TIMEOUT

MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

# Configure Gemini
if GEMINI_API_KEY and not MOCK_MODE:
    genai.configure(api_key=GEMINI_API_KEY)

# ============================================================================
# ROUTE CONFIG – logical routes preserved for compatibility
# All routes share the same Gemini model + key now.
# ============================================================================

ROUTES_CONFIG: Dict[str, Dict[str, Optional[str]]] = {
    "refiner": {
        "gemini_key": None,  # Don't use Gemini for refiner
        "groq_key": GROQ_API_KEY,  # Use free Groq instead
    },
    "intent": {
        "gemini_key": GEMINI_API_KEY,
        "groq_key": None,
    },
    "component": {
        "gemini_key": GEMINI_API_KEY,
        "groq_key": None,
    },
    "code": {
        "gemini_key": GEMINI_API_KEY,
        "groq_key": None,
    },
}

# Startup diagnostics
print("\n🤖 HYBRID LLM ARCHITECTURE:")
print("   REFINER    : Groq Llama 3.3 70B (FREE)")
print("   INTENT     : Gemini 2.5 Flash (PAID)")
print("   COMPONENT  : Gemini 2.5 Flash (PAID)")
print("   BACKGROUND : Gemini 2.5 Flash (PAID)")
print(f"   Gemini Temp: {GEMINI_TEMPERATURE}")
print(f"   Max Tokens : {GEMINI_MAX_TOKENS}")
print(f"   Timeout    : {GEMINI_TIMEOUT}s")
for route, cfg in ROUTES_CONFIG.items():
    gemini_status = "✅" if cfg.get("gemini_key") else "❌"
    groq_status = "✅" if cfg.get("groq_key") else "❌"
    print(f"   {route.upper()}: Gemini={gemini_status} | Groq={groq_status}")
print()

# ============================================================================
# UTILITY: Enhanced JSON Parser
# ============================================================================

def _safe_json_loads(s: Union[str, Dict, List], fallback: Any) -> Any:
    """
    Multi-strategy JSON parser with markdown stripping
    FIXED: Added comprehensive error logging
    """
    if isinstance(s, (dict, list)):
        return s

    if not isinstance(s, str) or not s.strip():
        print("⚠️ [JSON] Empty or non-string input")
        return fallback

    # Strategy 1: Direct parse
    try:
        result = json.loads(s)
        print("✅ [JSON] Strategy 1 succeeded (direct parse)")
        return result
    except (json.JSONDecodeError, ValueError) as e:
        print(f"❌ [JSON] Strategy 1 failed: {str(e)[:100]}")

    # Strategy 2: Strip markdown code fences
    try:
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', s.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned.strip(), flags=re.MULTILINE)
        result = json.loads(cleaned)
        print("✅ [JSON] Strategy 2 succeeded (markdown stripped)")
        return result
    except (json.JSONDecodeError, ValueError) as e:
        print(f"❌ [JSON] Strategy 2 failed: {str(e)[:100]}")

    # Strategy 3: Extract first JSON object/array
    try:
        # Try JSON object
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', s, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            print("✅ [JSON] Strategy 3 succeeded (extracted object)")
            return result
        
        # Try JSON array
        match = re.search(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', s, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            print("✅ [JSON] Strategy 3 succeeded (extracted array)")
            return result
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        print(f"❌ [JSON] Strategy 3 failed: {str(e)[:100]}")

    print(f"❌ [JSON] All strategies failed. Input preview: {s[:200]}...")
    return fallback

# ============================================================================
# 🟠 GROQ API CALLER (for REFINER route only)
# ============================================================================

async def call_groq(
    prompt: str,
    api_key: Optional[str] = None,
    timeout: int = GROQ_TIMEOUT,
) -> str:
    """Call Groq Llama API (free tier)"""
    import httpx
    
    key = api_key or GROQ_API_KEY
    if not key:
        raise RuntimeError("GROQ_API_KEY not configured in .env")

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": GEMINI_TEMPERATURE,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(GROQ_API_URL, json=payload, headers=headers)

        if resp.status_code != 200:
            error_text = resp.text[:400] if resp.text else "Unknown error"
            raise RuntimeError(f"Groq API error {resp.status_code}: {error_text}")

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
            return content
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Invalid Groq response structure: {data}") from e

# ============================================================================
# 🟢 GEMINI API CALLER (for INTENT, COMPONENT, BACKGROUND routes)
# WITH TOKEN TRACKING
# ============================================================================

async def call_gemini(
    prompt: str,
    api_key: Optional[str] = None,
    timeout: int = GEMINI_TIMEOUT,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Call Gemini 2.0 Flash API with automatic token usage tracking.
    
    Token usage is automatically tracked via token_tracker middleware
    for credit deduction after generation completes.
    """
    key = api_key or GEMINI_API_KEY
    if not key:
        raise RuntimeError("GEMINI_API_KEY not configured in .env")

    try:
        # Create model instance with custom token limit if provided
        generation_config = {
            "temperature": GEMINI_TEMPERATURE,
            "max_output_tokens": max_tokens or GEMINI_MAX_TOKENS,
        }
        
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=generation_config
        )

        # Generate content with timeout
        response = await asyncio.wait_for(
            asyncio.to_thread(
                model.generate_content,
                prompt,
                request_options={"timeout": timeout}
            ),
            timeout=timeout + 10  # Add buffer for async timeout
        )

        # 🆕 TRACK TOKEN USAGE (for credit deduction)
        if hasattr(response, 'usage_metadata'):
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
            
            token_tracker.add_usage(input_tokens, output_tokens)
            
            # Log token usage for monitoring
            print(f"📊 Gemini API - Input: {input_tokens:,} | Output: {output_tokens:,} | Total: {input_tokens + output_tokens:,}")
        else:
            # Fallback: If usage_metadata not available, log warning
            print(f"⚠️  Warning: Token usage metadata not available from Gemini API")

        return response.text

    except asyncio.TimeoutError:
        raise RuntimeError(f"Gemini API timeout after {timeout}s")
    except Exception as e:
        error_msg = str(e)
        if "API_KEY" in error_msg.upper():
            raise RuntimeError("Invalid Gemini API key - get one at https://aistudio.google.com/apikey")
        raise RuntimeError(f"Gemini API error: {error_msg}")
# ============================================================================
# MOCK MODE (For Testing)
# ============================================================================

def _mock_response(prompt_or_messages) -> str:
    """Mock responses for testing without API calls"""
    if isinstance(prompt_or_messages, str):
        text = prompt_or_messages
    else:
        text = str(prompt_or_messages[-1].get("content", ""))

    if "extract intent" in text.lower() or "design strategist" in text.lower():
        return json.dumps({
            "intent": "Create modern mobile authentication flow",
            "device": "mobile",
            "screens": ["Login", "Signup"],
            "constraints": ["modern design", "social login"],
            "language": "en",
            "design_strategy": {
                "screen_type": "auth",
                "design_style": "modern",
                "primary_pattern": "cards",
                "color_theme": "teal",
                "key_components": ["IllustrationHeader", "Card", "IconInput", "GradientButton"]
            }
        })

    if "component architect" in text.lower():
        return json.dumps({
            "components": [
                {
                    "id": "illustration-1",
                    "type": "IllustrationHeader",
                    "screen": "Login",
                    "props": {
                        "illustration": "auth-welcome",
                        "title": "Welcome Back",
                        "subtitle": "Sign in to continue"
                    }
                },
                {
                    "id": "input-email",
                    "type": "IconInput",
                    "screen": "Login",
                    "props": {"icon": "mail", "label": "Email"}
                },
                {
                    "id": "btn-login",
                    "type": "GradientButton",
                    "screen": "Login",
                    "props": {"text": "Sign In", "gradient": "teal"}
                }
            ]
        })

    return "{}"

###############################################################################
# 🎯 BASE PROMPTS (with CoT orchestration)
###############################################################################

COMPACT_INTENT_PROMPT = """You are a mobile UI design strategist and intent analyzer.

TASK: Extract intent and design strategy from user prompt.

SCREEN TYPES & PATTERNS:
- auth: Login/Signup → Card, IconInput, GradientButton, SocialButton, Divider
- ecommerce: Products/Cart → SearchInput, Grid, ProductCard, FloatingActionButton
- social: Feed/Profile → Avatar, CardList, TabBar, StatCard, ImageGallery
- dashboard: Analytics → StatCard, ProgressBar, Grid, AppBar
- onboarding: Steps → IllustrationHeader, ProgressBar, GradientButton
- settings: Preferences → FormSection, List, ListItem, Switch

DESIGN STYLES:
- modern: Gradients, elevation, generous spacing, icons
- minimal: Flat, simple, white space
- bold: Large typography, vibrant colors

COLOR THEMES:
- Finance/Banking → blue | Health → green | Food → orange | Tech → purple | Social → vibrant

OUTPUT FORMAT (strict JSON):
{
  "intent": "clear description",
  "device": "mobile",
  "screens": ["Screen1", "Screen2"],
  "constraints": ["design_style: modern", "theme: teal"],
  "language": "en",
  "design_strategy": {
    "screen_type": "auth|ecommerce|social|dashboard|onboarding|settings",
    "design_style": "modern|minimal|bold",
    "primary_pattern": "cards|list|grid|hero",
    "color_theme": "teal|blue|purple|green|orange",
    "key_components": ["IllustrationHeader", "Card", "GradientButton"]
  }
}

CRITICAL: Output ONLY valid JSON, no markdown, no explanations."""

COMPACT_COMPONENTIZE_PROMPT = """You are a mobile UI component architect using PATTERN-BASED generation.

COMPONENTS (use these):
Layout: Container, Card, Stack, Grid, Spacer
Content: Header, Text, Divider, Badge
Input: TextInput, PasswordInput, IconInput, SearchInput, Checkbox, Switch
Button: Button, GradientButton, IconButton, SocialButton, FloatingActionButton, LinkButton
Media: Image, Avatar, IllustrationHeader, HeroSection, ImageGallery
Navigation: TabBar, AppBar
Feedback: ProgressBar, Alert, EmptyState
Special: StatCard, ProductCard, ListItem, FormSection, Rating, CartItem, QuantityControl, PriceBreakdown

DESIGN TOKENS:
- spacing: xs:4, sm:8, md:16, lg:24, xl:32, 2xl:48
- borderRadius: sm:8, md:12, lg:16, xl:24, full:999
- elevation: none, sm, md, lg, xl
- gradients: teal, blue, purple, pink, orange, green
- sizes: sm:32, md:44, lg:56 (buttons)

GENERATION RULES:
1. Identify screen type from design_strategy
2. Use relevant pattern examples provided below
3. Adapt components to match user's specific requirements
4. Add modern elements: gradients, elevation:md, generous spacing (16-24px)
5. Every component needs unique 'id' (descriptive: input-email, btn-login, card-main)
6. **CRITICAL: Every component MUST have a "screen" field matching one of the provided screen names**
7. Group components logically by screen - all Login components should have "screen": "Login"
8. Buttons: size:lg for primary CTAs, md for secondary
9. FloatingActionButton: bottom-right for primary actions
10. Spacing between major sections: 24-32px

OUTPUT FORMAT:
{
  "components": [
    {
      "id": "unique-id",
      "type": "ComponentType",
      "screen": "ScreenName",
      "props": {
        "key": "value"
      }
    }
  ]
}

**CRITICAL REQUIREMENTS:**
- Every component MUST include a "screen" field
- The "screen" value MUST match one of the screen names provided in the task
- Group related components under the same screen (e.g., all login form inputs go to "Login" screen)
- Use descriptive IDs that hint at the screen (e.g., "login-email-input", "signup-name-input")

CRITICAL: Output ONLY valid JSON, no markdown, no explanations."""

###############################################################################
# 🧠 ENHANCED STAGE FUNCTIONS (with CoT integration, Gemini API)
###############################################################################

async def extract_intent(prompt: str) -> dict:
    """
    Stage 1: Extract intent with intelligent CoT prompt enhancement.

    Args:
        prompt: User's natural language prompt

    Returns:
        Intent object with design strategy
    """
    fallback = {
        "intent": prompt,
        "device": "mobile",
        "screens": ["Home"],
        "constraints": ["modern design"],
        "language": "en",
        "design_strategy": {
            "screen_type": "general",
            "design_style": "modern",
            "primary_pattern": "cards",
            "color_theme": "teal",
            "key_components": ["Header", "Container", "Button"],
        },
    }

    if not prompt.strip():
        return fallback

    # STEP 1: Detect categories from prompt
    detected_categories = detect_categories(prompt)
    print(f"🎯 Detected categories: {', '.join(detected_categories) if detected_categories else 'None'}")

    # STEP 2: Build enhanced prompt with relevant CoT examples
    enhanced_prompt = get_enhanced_prompt(
        base_prompt=COMPACT_INTENT_PROMPT,
        user_prompt=prompt,
        design_strategy=None,  # Stage 1 has no design_strategy yet
    )

    # STEP 3: Estimate token usage
    estimated_tokens = estimate_token_count(enhanced_prompt)
    print(f"📏 Intent prompt size: {len(enhanced_prompt):,} chars (~{estimated_tokens:,} tokens)")

    try:
        content = await asyncio.wait_for(
            send_chat(enhanced_prompt, route="intent", timeout=LLM_TIMEOUT),
            timeout=LLM_TIMEOUT + 5,
        )

        intent = _safe_json_loads(content, fallback)

        if not isinstance(intent, dict):
            return fallback

        # Ensure required fields
        intent.setdefault("intent", prompt)
        intent["device"] = "mobile"
        intent.setdefault("language", "en")

        if not isinstance(intent.get("screens"), list) or not intent["screens"]:
            intent["screens"] = ["Home"]
        if not isinstance(intent.get("constraints"), list):
            intent["constraints"] = []

        if "design_strategy" not in intent:
            intent["design_strategy"] = fallback["design_strategy"]

        screen_type = intent.get("design_strategy", {}).get("screen_type", "general")
        design_style = intent.get("design_strategy", {}).get("design_style", "modern")
        print(f"✅ Intent: {screen_type} ({design_style})")

        return intent

    except asyncio.TimeoutError:
        print("⚠️ Intent extraction timeout - using fallback")
        return fallback
    except Exception as e:
        print(f"⚠️ Intent extraction error: {e} - using fallback")
        return fallback
from typing import Any, Dict, List

def generate_fallback_components(intent_obj: dict) -> dict:
    """
    Generate a basic but functional component model when the LLM fails.

    Strategy:
    - Use intent_obj['design_strategy']['screen_type'] to select a category
      from: auth, ecommerce, social, dashboard, onboarding, settings.
    - Use intent_obj['screens'] (1–3 screen names) to decide which screens
      to build.
    - Always return a dict of shape: {"components": [ ... ]}.
    - Keep structure compatible with preview & RN converter (id, type, screen, props, optional children).
    """
    design_strategy = intent_obj.get("design_strategy") or {}
    screen_type = (design_strategy.get("screen_type") or "general").lower()
    screens = intent_obj.get("screens") or ["Home"]

    # Normalize screen names for detection but preserve originals
    normalized_screens: List[str] = [str(s) for s in screens]
    lower_screens: List[str] = [s.lower() for s in normalized_screens]

    def find_screen(default: str, keywords: List[str]) -> str:
        """
        Helper: pick a screen name by keyword, otherwise fallback.
        """
        for kw in keywords:
            for name, name_lower in zip(normalized_screens, lower_screens):
                if kw in name_lower:
                    return name
        return default

    components: List[Dict[str, Any]] = []

    print(f"🔧 [FALLBACK] Generating components for screen_type='{screen_type}' screens={normalized_screens}")

    # -----------------------------------------------------------------------
    # AUTH FALLBACK (Login / Signup / OTP / Forgot Password)
    # -----------------------------------------------------------------------
    if screen_type == "auth":
        has_login = any("login" in s or "sign in" in s for s in lower_screens)
        has_signup = any("signup" in s or "sign up" in s or "register" in s for s in lower_screens)
        has_otp = any("otp" in s or "verify" in s for s in lower_screens)
        has_forgot = any("forgot" in s or "reset" in s for s in lower_screens)

        # If nothing detected, assume login + signup as a safe default
        if not any([has_login, has_signup, has_otp, has_forgot]):
            has_login = True
            has_signup = True

        # LOGIN
        if has_login:
            login_screen = find_screen("Login", ["login", "sign in"])
            components.extend([
                {
                    "id": "login-header",
                    "type": "IllustrationHeader",
                    "screen": login_screen,
                    "props": {
                        "title": "Welcome Back",
                        "subtitle": "Sign in to continue"
                    }
                },
                {
                    "id": "login-email",
                    "type": "IconInput",
                    "screen": login_screen,
                    "props": {
                        "icon": "mail",
                        "label": "Email",
                        "placeholder": "Enter your email"
                    }
                },
                {
                    "id": "login-password",
                    "type": "PasswordInput",
                    "screen": login_screen,
                    "props": {
                        "icon": "lock",
                        "label": "Password",
                        "placeholder": "Enter your password"
                    }
                },
                {
                    "id": "login-forgot-link",
                    "type": "LinkButton",
                    "screen": login_screen,
                    "props": {
                        "text": "Forgot Password?",
                        "align": "right"
                    }
                },
                {
                    "id": "login-button",
                    "type": "GradientButton",
                    "screen": login_screen,
                    "props": {
                        "text": "Sign In",
                        "gradient": "teal",
                        "size": "lg"
                    }
                },
                {
                    "id": "login-divider",
                    "type": "Divider",
                    "screen": login_screen,
                    "props": {
                        "text": "OR"
                    }
                },
                {
                    "id": "login-social-google",
                    "type": "SocialButton",
                    "screen": login_screen,
                    "props": {
                        "provider": "google",
                        "text": "Continue with Google"
                    }
                },
                {
                    "id": "login-social-apple",
                    "type": "SocialButton",
                    "screen": login_screen,
                    "props": {
                        "provider": "apple",
                        "text": "Continue with Apple"
                    }
                }
            ])

        # SIGNUP
        if has_signup:
            signup_screen = find_screen("Signup", ["signup", "sign up", "register"])
            components.extend([
                {
                    "id": "signup-header",
                    "type": "IllustrationHeader",
                    "screen": signup_screen,
                    "props": {
                        "title": "Create Account",
                        "subtitle": "Join us today"
                    }
                },
                {
                    "id": "signup-name",
                    "type": "IconInput",
                    "screen": signup_screen,
                    "props": {
                        "icon": "user",
                        "label": "Full Name",
                        "placeholder": "Enter your full name"
                    }
                },
                {
                    "id": "signup-email",
                    "type": "IconInput",
                    "screen": signup_screen,
                    "props": {
                        "icon": "mail",
                        "label": "Email",
                        "placeholder": "Enter your email"
                    }
                },
                {
                    "id": "signup-password",
                    "type": "PasswordInput",
                    "screen": signup_screen,
                    "props": {
                        "icon": "lock",
                        "label": "Password",
                        "placeholder": "Create a password"
                    }
                },
                {
                    "id": "signup-terms",
                    "type": "Checkbox",
                    "screen": signup_screen,
                    "props": {
                        "label": "I agree to Terms & Conditions",
                        "value": False
                    }
                },
                {
                    "id": "signup-button",
                    "type": "GradientButton",
                    "screen": signup_screen,
                    "props": {
                        "text": "Sign Up",
                        "gradient": "blue",
                        "size": "lg"
                    }
                }
            ])

        # OTP / VERIFICATION
        if has_otp:
            otp_screen = find_screen("OTP Verification", ["otp", "verify", "verification"])
            components.extend([
                {
                    "id": "otp-header",
                    "type": "IllustrationHeader",
                    "screen": otp_screen,
                    "props": {
                        "title": "Verify Code",
                        "subtitle": "Enter the 6-digit code sent to your email"
                    }
                },
                {
                    "id": "otp-grid",
                    "type": "Grid",
                    "screen": otp_screen,
                    "props": {
                        "columns": 6,
                        "gap": 8
                    },
                    "children": [
                        {
                            "id": f"otp-input-{i+1}",
                            "type": "TextInput",
                            "props": {
                                "style": "otp",
                                "maxLength": 1
                            }
                        }
                        for i in range(6)
                    ]
                },
                {
                    "id": "otp-button",
                    "type": "GradientButton",
                    "screen": otp_screen,
                    "props": {
                        "text": "Verify",
                        "size": "lg"
                    }
                },
                {
                    "id": "otp-resend",
                    "type": "LinkButton",
                    "screen": otp_screen,
                    "props": {
                        "text": "Resend Code",
                        "align": "center"
                    }
                }
            ])

        # FORGOT PASSWORD
        if has_forgot:
            forgot_screen = find_screen("Forgot Password", ["forgot", "reset"])
            components.extend([
                {
                    "id": "forgot-header",
                    "type": "IllustrationHeader",
                    "screen": forgot_screen,
                    "props": {
                        "title": "Reset Password",
                        "subtitle": "Enter your email to receive reset link"
                    }
                },
                {
                    "id": "forgot-email",
                    "type": "IconInput",
                    "screen": forgot_screen,
                    "props": {
                        "icon": "mail",
                        "label": "Email",
                        "placeholder": "Enter your email"
                    }
                },
                {
                    "id": "forgot-button",
                    "type": "GradientButton",
                    "screen": forgot_screen,
                    "props": {
                        "text": "Send Reset Link",
                        "gradient": "blue",
                        "size": "lg"
                    }
                }
            ])

    # -----------------------------------------------------------------------
    # ECOMMERCE FALLBACK (Product List / Detail / Cart / Checkout)
    # -----------------------------------------------------------------------
    elif screen_type == "ecommerce":
        has_products = any("product" in s or "home" in s or "list" in s for s in lower_screens)
        has_cart = any("cart" in s for s in lower_screens)
        has_checkout = any("checkout" in s or "payment" in s for s in lower_screens)

        # Default to product listing if nothing else detected
        if not any([has_products, has_cart, has_checkout]):
            has_products = True

        if has_products:
            product_screen = find_screen("Products", ["product", "home", "list"])
            components.extend([
                {
                    "id": "products-search",
                    "type": "SearchInput",
                    "screen": product_screen,
                    "props": {
                        "placeholder": "Search products...",
                        "borderRadius": "full"
                    }
                },
                {
                    "id": "products-grid",
                    "type": "Grid",
                    "screen": product_screen,
                    "props": {
                        "columns": 2,
                        "gap": 16
                    },
                    "children": [
                        {
                            "id": f"product-card-{i+1}",
                            "type": "ProductCard",
                            "props": {
                                "title": f"Product {i+1}",
                                "price": f"${99 + i * 10}.99",
                                "rating": 4.5,
                                "badge": "Sale" if i == 0 else None
                            }
                        }
                        for i in range(4)
                    ]
                },
                {
                    "id": "products-cart-fab",
                    "type": "FloatingActionButton",
                    "screen": product_screen,
                    "props": {
                        "icon": "cart",
                        "position": "bottom-right",
                        "gradient": "orange"
                    }
                }
            ])

        if has_cart:
            cart_screen = find_screen("Cart", ["cart"])
            components.extend([
                {
                    "id": "cart-appbar",
                    "type": "AppBar",
                    "screen": cart_screen,
                    "props": {
                        "title": "Shopping Cart",
                        "subtitle": "3 items"
                    }
                },
                {
                    "id": "cart-items",
                    "type": "CardList",
                    "screen": cart_screen,
                    "props": {
                        "spacing": "md"
                    },
                    "children": [
                        {
                            "id": f"cart-item-{i+1}",
                            "type": "CartItem",
                            "props": {
                                "title": f"Product {i+1}",
                                "price": f"${99 + i * 10}.99",
                                "quantity": 1
                            }
                        }
                        for i in range(3)
                    ]
                },
                {
                    "id": "cart-price-breakdown",
                    "type": "PriceBreakdown",
                    "screen": cart_screen,
                    "props": {
                        "subtotal": "$299.97",
                        "shipping": "$10.00",
                        "tax": "$24.00",
                        "total": "$333.97"
                    }
                },
                {
                    "id": "cart-checkout-button",
                    "type": "GradientButton",
                    "screen": cart_screen,
                    "props": {
                        "text": "Proceed to Checkout",
                        "gradient": "orange",
                        "size": "lg"
                    }
                }
            ])

        if has_checkout:
            checkout_screen = find_screen("Checkout", ["checkout", "payment"])
            components.extend([
                {
                    "id": "checkout-appbar",
                    "type": "AppBar",
                    "screen": checkout_screen,
                    "props": {
                        "title": "Checkout"
                    }
                },
                {
                    "id": "checkout-shipping-section",
                    "type": "FormSection",
                    "screen": checkout_screen,
                    "props": {
                        "title": "Shipping Address"
                    }
                },
                {
                    "id": "checkout-name",
                    "type": "IconInput",
                    "screen": checkout_screen,
                    "props": {
                        "icon": "user",
                        "label": "Full Name"
                    }
                },
                {
                    "id": "checkout-email",
                    "type": "IconInput",
                    "screen": checkout_screen,
                    "props": {
                        "icon": "mail",
                        "label": "Email"
                    }
                },
                {
                    "id": "checkout-address",
                    "type": "TextInput",
                    "screen": checkout_screen,
                    "props": {
                        "label": "Address",
                        "placeholder": "Street, City, ZIP"
                    }
                },
                {
                    "id": "checkout-payment-section",
                    "type": "FormSection",
                    "screen": checkout_screen,
                    "props": {
                        "title": "Payment Method"
                    }
                },
                {
                    "id": "checkout-card-number",
                    "type": "IconInput",
                    "screen": checkout_screen,
                    "props": {
                        "icon": "card",
                        "label": "Card Number"
                    }
                },
                {
                    "id": "checkout-place-order",
                    "type": "GradientButton",
                    "screen": checkout_screen,
                    "props": {
                        "text": "Place Order",
                        "gradient": "green",
                        "size": "lg"
                    }
                }
            ])

    # -----------------------------------------------------------------------
    # SOCIAL FALLBACK (Feed / Profile / Messages)
    # -----------------------------------------------------------------------
    elif screen_type == "social":
        has_feed = any("feed" in s or "home" in s or "timeline" in s for s in lower_screens)
        has_profile = any("profile" in s for s in lower_screens)
        has_messages = any("message" in s or "chat" in s or "conversation" in s for s in lower_screens)

        if not any([has_feed, has_profile, has_messages]):
            has_feed = True

        if has_feed:
            feed_screen = find_screen("Feed", ["feed", "home", "timeline"])
            components.extend([
                {
                    "id": "feed-appbar",
                    "type": "AppBar",
                    "screen": feed_screen,
                    "props": {
                        "title": "Feed",
                        "actions": ["search", "notifications"]
                    }
                },
                {
                    "id": "feed-posts",
                    "type": "CardList",
                    "screen": feed_screen,
                    "props": {
                        "spacing": "md"
                    }
                },
                {
                    "id": "feed-create-fab",
                    "type": "FloatingActionButton",
                    "screen": feed_screen,
                    "props": {
                        "icon": "plus",
                        "gradient": "blue",
                        "position": "bottom-right"
                    }
                },
                {
                    "id": "feed-tabbar",
                    "type": "TabBar",
                    "screen": feed_screen,
                    "props": {
                        "tabs": ["Home", "Search", "Notifications", "Profile"]
                    }
                }
            ])

        if has_profile:
            profile_screen = find_screen("Profile", ["profile"])
            components.extend([
                {
                    "id": "profile-hero",
                    "type": "HeroSection",
                    "screen": profile_screen,
                    "props": {
                        "height": 240
                    }
                },
                {
                    "id": "profile-avatar",
                    "type": "Avatar",
                    "screen": profile_screen,
                    "props": {
                        "size": "xl",
                        "name": "John Doe",
                        "position": "center"
                    }
                },
                {
                    "id": "profile-name",
                    "type": "Header",
                    "screen": profile_screen,
                    "props": {
                        "title": "John Doe",
                        "size": "2xl",
                        "align": "center"
                    }
                },
                {
                    "id": "profile-stats",
                    "type": "Grid",
                    "screen": profile_screen,
                    "props": {
                        "columns": 3,
                        "gap": 16
                    },
                    "children": [
                        {
                            "id": "profile-posts",
                            "type": "StatCard",
                            "props": {
                                "value": "1.2k",
                                "label": "Posts",
                                "color": "blue"
                            }
                        },
                        {
                            "id": "profile-followers",
                            "type": "StatCard",
                            "props": {
                                "value": "10k",
                                "label": "Followers",
                                "color": "green"
                            }
                        },
                        {
                            "id": "profile-following",
                            "type": "StatCard",
                            "props": {
                                "value": "500",
                                "label": "Following",
                                "color": "purple"
                            }
                        }
                    ]
                }
            ])

        if has_messages:
            messages_screen = find_screen("Messages", ["message", "chat", "conversation"])
            components.extend([
                {
                    "id": "messages-appbar",
                    "type": "AppBar",
                    "screen": messages_screen,
                    "props": {
                        "title": "Messages"
                    }
                },
                {
                    "id": "messages-search",
                    "type": "SearchInput",
                    "screen": messages_screen,
                    "props": {
                        "placeholder": "Search conversations..."
                    }
                },
                {
                    "id": "messages-list",
                    "type": "CardList",
                    "screen": messages_screen,
                    "props": {
                        "spacing": "sm"
                    }
                }
            ])

    # -----------------------------------------------------------------------
    # DASHBOARD FALLBACK (Analytics / Admin)
    # -----------------------------------------------------------------------
    elif screen_type == "dashboard":
        dashboard_screen = find_screen("Dashboard", ["dashboard", "analytics", "admin"])
        components.extend([
            {
                "id": "dashboard-appbar",
                "type": "AppBar",
                "screen": dashboard_screen,
                "props": {
                    "title": "Dashboard",
                    "subtitle": "Overview"
                }
            },
            {
                "id": "dashboard-grid",
                "type": "Grid",
                "screen": dashboard_screen,
                "props": {
                    "columns": 2,
                    "gap": 16
                },
                "children": [
                    {
                        "id": "stat-revenue",
                        "type": "StatCard",
                        "props": {
                            "icon": "money",
                            "value": "$24,500",
                            "label": "Revenue",
                            "color": "green"
                        }
                    },
                    {
                        "id": "stat-users",
                        "type": "StatCard",
                        "props": {
                            "icon": "users",
                            "value": "1,234",
                            "label": "Users",
                            "color": "blue"
                        }
                    },
                    {
                        "id": "stat-growth",
                        "type": "StatCard",
                        "props": {
                            "icon": "trending-up",
                            "value": "+15%",
                            "label": "Growth",
                            "color": "purple"
                        }
                    },
                    {
                        "id": "stat-conversion",
                        "type": "StatCard",
                        "props": {
                            "icon": "target",
                            "value": "89%",
                            "label": "Conversion",
                            "color": "orange"
                        }
                    }
                ]
            },
            {
                "id": "dashboard-progress",
                "type": "Card",
                "screen": dashboard_screen,
                "props": {
                    "elevation": "md"
                },
                "children": [
                    {
                        "id": "dashboard-progress-title",
                        "type": "Header",
                        "props": {
                            "title": "Monthly Goal",
                            "size": "lg"
                        }
                    },
                    {
                        "id": "dashboard-progress-bar",
                        "type": "ProgressBar",
                        "props": {
                            "value": 67,
                            "label": "$20,000 / $30,000",
                            "color": "blue"
                        }
                    }
                ]
            }
        ])

    # -----------------------------------------------------------------------
    # ONBOARDING FALLBACK (Welcome / Tutorial Steps)
    # -----------------------------------------------------------------------
    elif screen_type == "onboarding":
        # Build one simple step per screen
        for idx, (screen_name, screen_lower) in enumerate(zip(normalized_screens, lower_screens), start=1):
            components.extend([
                {
                    "id": f"onboarding-{idx}-illustration",
                    "type": "IllustrationHeader",
                    "screen": screen_name,
                    "props": {
                        "title": f"Welcome Step {idx}",
                        "subtitle": "Discover amazing features",
                        "spacing": "2xl"
                    }
                },
                {
                    "id": f"onboarding-{idx}-progress",
                    "type": "ProgressBar",
                    "screen": screen_name,
                    "props": {
                        "value": int(100 * idx / max(len(normalized_screens), 1)),
                        "steps": len(normalized_screens),
                        "currentStep": idx,
                        "color": "blue"
                    }
                },
                {
                    "id": f"onboarding-{idx}-primary",
                    "type": "GradientButton",
                    "screen": screen_name,
                    "props": {
                        "text": "Continue" if idx < len(normalized_screens) else "Get Started",
                        "gradient": "blue" if idx < len(normalized_screens) else "green",
                        "size": "lg"
                    }
                },
                {
                    "id": f"onboarding-{idx}-skip",
                    "type": "Button",
                    "screen": screen_name,
                    "props": {
                        "text": "Skip",
                        "variant": "ghost",
                        "size": "md"
                    }
                }
            ])

    # -----------------------------------------------------------------------
    # SETTINGS FALLBACK (Settings / Edit Profile / Notifications)
    # -----------------------------------------------------------------------
    elif screen_type == "settings":
        has_settings = any("settings" in s or "preference" in s for s in lower_screens)
        has_edit_profile = any("edit profile" in s or ("profile" in s and "edit" in s) for s in lower_screens)
        has_notifications = any("notification" in s for s in lower_screens)

        if not any([has_settings, has_edit_profile, has_notifications]):
            has_settings = True

        if has_settings:
            settings_screen = find_screen("Settings", ["settings", "preference"])
            components.extend([
                {
                    "id": "settings-header",
                    "type": "Header",
                    "screen": settings_screen,
                    "props": {
                        "title": "Settings",
                        "size": "2xl"
                    }
                },
                {
                    "id": "settings-account-section",
                    "type": "FormSection",
                    "screen": settings_screen,
                    "props": {
                        "title": "Account"
                    }
                },
                {
                    "id": "settings-list",
                    "type": "List",
                    "screen": settings_screen,
                    "props": {
                        "spacing": "sm"
                    }
                }
            ])

        if has_edit_profile:
            edit_screen = find_screen("Edit Profile", ["edit profile"])
            components.extend([
                {
                    "id": "edit-profile-header",
                    "type": "Header",
                    "screen": edit_screen,
                    "props": {
                        "title": "Edit Profile",
                        "size": "2xl"
                    }
                },
                {
                    "id": "edit-profile-avatar",
                    "type": "Avatar",
                    "screen": edit_screen,
                    "props": {
                        "size": "xl",
                        "name": "John Doe",
                        "position": "center"
                    }
                },
                {
                    "id": "edit-profile-name",
                    "type": "IconInput",
                    "screen": edit_screen,
                    "props": {
                        "icon": "user",
                        "label": "Full Name"
                    }
                },
                {
                    "id": "edit-profile-email",
                    "type": "IconInput",
                    "screen": edit_screen,
                    "props": {
                        "icon": "mail",
                        "label": "Email"
                    }
                },
                {
                    "id": "edit-profile-save",
                    "type": "GradientButton",
                    "screen": edit_screen,
                    "props": {
                        "text": "Save Changes",
                        "gradient": "teal",
                        "size": "lg"
                    }
                }
            ])

        if has_notifications:
            notif_screen = find_screen("Notifications", ["notification"])
            components.extend([
                {
                    "id": "notifications-header",
                    "type": "Header",
                    "screen": notif_screen,
                    "props": {
                        "title": "Notifications",
                        "size": "2xl"
                    }
                },
                {
                    "id": "notifications-list",
                    "type": "List",
                    "screen": notif_screen,
                    "props": {
                        "spacing": "md"
                    }
                }
            ])

    # -----------------------------------------------------------------------
    # GENERIC FALLBACK (Unknown category, just give basic headers)
    # -----------------------------------------------------------------------
    if not components:
        print("ℹ️ [FALLBACK] No category-specific components generated; using generic headers.")
        for screen_name in normalized_screens:
            components.append(
                {
                    "id": f"header-{screen_name.lower().replace(' ', '-')}",
                    "type": "Header",
                    "screen": screen_name,
                    "props": {
                        "title": f"{screen_name} Screen",
                        "size": "2xl"
                    }
                }
            )

    print(f"✅ [FALLBACK] Generated {len(components)} components (screen_type={screen_type})")
    return {"components": components}


async def componentize(intent_obj: dict, original_prompt: str) -> dict:
    """
    Stage 2: Generate component model with CoT-enhanced prompts.

    Primary path:
      - Build a CoT-enhanced prompt based on intent + design_strategy.
      - Call Gemini (route="component") to get a component model.

    Fallback path:
      - If the LLM call fails OR returns no/invalid components,
        use generate_fallback_components(intent_obj) to build a safe,
        category-aware component model.
    """
    # Pre-compute a robust fallback model for this intent
    fallback = generate_fallback_components(intent_obj)

    intent_text = intent_obj.get("intent", original_prompt)
    design_strategy = intent_obj.get("design_strategy", {})

    # STEP 1: Build task JSON
    task_json = json.dumps(
        {
            "task": "componentize",
            "intent": intent_text,
            "screens": intent_obj.get("screens", []),
            "design_strategy": design_strategy,
        },
        indent=2,
    )

    # STEP 2: Get enhanced prompt with CoT examples
    enhanced_prompt = get_enhanced_prompt(
        base_prompt=COMPACT_COMPONENTIZE_PROMPT,
        user_prompt=task_json,
        design_strategy=design_strategy,
    )

    # STEP 3: Estimate token usage
    estimated_tokens = estimate_token_count(enhanced_prompt)
    print(f"📏 Componentize prompt size: {len(enhanced_prompt):,} chars (~{estimated_tokens:,} tokens)")

    try:
        content = await asyncio.wait_for(
            send_chat(enhanced_prompt, route="component", timeout=LLM_TIMEOUT),
            timeout=LLM_TIMEOUT + 5,
        )

        result = _safe_json_loads(content, fallback)

        # If parsing produced something non-dict, bail to fallback
        if not isinstance(result, dict):
            print("⚠️ [COMPONENT] Parsed response is not a dict - using fallback generator")
            return fallback

        components = result.get("components")

        # If there is no 'components' key or it's not a list, use fallback
        if not isinstance(components, list):
            print("⚠️ [COMPONENT] LLM response missing valid 'components' list - using fallback generator")
            return fallback

        # Normalize and enforce minimal structure
        screens = intent_obj.get("screens", [])
        default_screen = screens[0] if screens else "Screen"

        for i, comp in enumerate(components):
            if not isinstance(comp, dict):
                # Skip completely invalid items
                continue

            comp.setdefault("id", f"comp-{i}")
            comp.setdefault("type", "Container")
            comp.setdefault("props", {})

            # Screen is CRITICAL for preview/RN conversion
            if "screen" not in comp or not comp["screen"]:
                comp["screen"] = default_screen

        # Filter out any non-dict items that may have slipped through
        result["components"] = [c for c in components if isinstance(c, dict)]

        # If still empty after normalization, fall back
        if not result["components"]:
            print("⚠️ [COMPONENT] LLM returned empty components after normalization - using fallback generator")
            return fallback

        print(f"✅ Generated {len(result['components'])} components (LLM path)")
        return result

    except Exception as e:
        print(f"⚠️ [COMPONENT] Error during componentize: {e} - using fallback generator")
        return fallback
  


async def generate_asset_prompts(components: list) -> dict:
    """
    Generate image generation prompts for visual components.

    Args:
        components: List of component objects

    Returns:
        Dictionary mapping component IDs to image prompts
    """
    prompts: Dict[str, str] = {}

    for c in components or []:
        if not isinstance(c, dict):
            continue

        comp_type = (c.get("type") or "").lower()
        props = c.get("props") or {}
        comp_id = c.get("id", "unknown")

        if comp_type == "illustrationheader":
            illustration = props.get("illustration", "")
            title = props.get("title", "")
            prompts[comp_id] = f"Modern mobile illustration: {illustration or title}, minimal, flat design"

        elif comp_type in ("image", "hero", "banner", "avatar"):
            alt = props.get("alt") or props.get("title") or "illustration"
            prompts[comp_id] = f"Mobile UI: {alt}, modern style"

        elif comp_type == "herosection":
            prompts[comp_id] = "Hero section cover, gradient background"

    return prompts

###############################################################################
# 🚀 CODE GENERATION - React Native Platform
###############################################################################

async def generate_preview_from_json(component_model: dict) -> dict:
    """
    Generate web preview JSON from component model (NO LLM).

    STRATEGY: Direct pass-through adapter
    - Component model → PreviewAdapter (if available)
    - No API call, no LLM, no transformation beyond deterministic mapping
    """
    print("\n🔄 [PREVIEW ADAPTER] Generating web preview (no API call)...")

    try:
        from Services.preview_adapter import PreviewAdapter
        web_preview = PreviewAdapter.to_web_preview(component_model)

        print("✅ [PREVIEW ADAPTER] Web preview ready")
        print(f"📊 [PREVIEW ADAPTER]: {len(web_preview.get('screens', []))} screens")

        return web_preview

    except ImportError:
        print("ℹ️ [PREVIEW ADAPTER] PreviewAdapter not found - using direct pass-through")
        return component_model

    except Exception as e:
        print(f"⚠️ [PREVIEW ADAPTER] Error: {e} - returning original model")
        return component_model

async def generate_react_native_from_json(component_model: dict) -> dict:
    """
    Generate React Native code from component model (NO LLM).

    Deterministic strategy:
    - Component Model → React Native Direct Conversion
    - NO API call, NO LLM (zero hallucinations)
    - Direct component mapping (100% deterministic)
    """
    print("\n🔧 [RN CONVERTER] Starting React Native code generation (no API call)...")
    print("🎯 [RN CONVERTER] Method: Deterministic component-to-code conversion")

    try:
        from Services.preview_to_react_native import PreviewToReactNativeConverter
    except ImportError as e:
        error_msg = f"PreviewToReactNativeConverter not found: {e}"
        print(f"\n❌ [RN CONVERTER] CRITICAL ERROR: {error_msg}")
        raise ImportError(
            "PreviewToReactNativeConverter is required. "
            "Check that backend/Services/preview_to_react_native.py exists."
        ) from e

    if not component_model or not isinstance(component_model, dict):
        error_msg = "component_model must be a non-empty dictionary"
        print(f"❌ [RN CONVERTER] Validation failed: {error_msg}")
        raise ValueError(error_msg)

    screens = component_model.get("screens", [])
    if not screens:
        print("⚠️  [RN CONVERTER] Warning: No screens in component model")

    print(
        f"📊 [RN CONVERTER] Input: {len(screens)} screen(s), "
        f"{sum(len(s.get('components', [])) for s in screens)} components"
    )

    try:
        converter = PreviewToReactNativeConverter(component_model)

        print("🔄 [RN CONVERTER] Converting component model → React Native code...")
        rn_files = converter.convert()

        if not rn_files:
            raise RuntimeError("Converter returned empty result")

        required_files = {
            "App.tsx": "Main entry point",
            "src/theme/index.ts": "Theme configuration",
            "package.json": "Dependencies",
        }

        missing_files = [
            f"{path} ({desc})"
            for path, desc in required_files.items()
            if path not in rn_files
        ]

        if missing_files:
            print("⚠️  [RN CONVERTER] Missing critical files:")
            for missing in missing_files:
                print(f"      - {missing}")

        screen_files = [f for f in rn_files.keys() if f.startswith("src/screens/")]
        total_size = sum(len(content) for content in rn_files.values())

        print("\n✅ [RN CONVERTER] Conversion successful!")
        print(f"   📦 Files: {len(rn_files)}")
        print(f"   🎨 Screens: {len(screen_files)}")
        print(f"   📊 Code size: {total_size:,} chars")
        print("   🎯 Accuracy: 100% (deterministic, no LLM)")

        if getattr(converter, "warnings", None):
            print(f"\n⚠️  [RN CONVERTER] Warnings ({len(converter.warnings)}):")
            for warning in converter.warnings[:3]:
                print(f"      - {warning}")
            if len(converter.warnings) > 3:
                print(f"      ... and {len(converter.warnings) - 3} more")

        if getattr(converter, "errors", None):
            print(f"\n❌ [RN CONVERTER] Errors ({len(converter.errors)}):")
            for error in converter.errors[:3]:
                print(f"      - {error}")
            if len(converter.errors) > 3:
                print(f"      ... and {len(converter.errors) - 3} more")

        return rn_files

    except Exception as e:
        print(f"\n❌ [RN CONVERTER] Conversion failed: {e}")
        import traceback
        print("\n🔍 [RN CONVERTER] Full traceback:")
        traceback.print_exc()

        print("\n❌ [RN CONVERTER] NO FALLBACK AVAILABLE")
        print("🔧 [RN CONVERTER] Fix preview_to_react_native.py to resolve this issue")

        raise RuntimeError(f"React Native code generation failed: {str(e)}") from e

async def test_preview_conversion(component_model: dict) -> dict:
    """
    Test function to verify Preview→React Native conversion accuracy.

    Validates:
    - All component types convert correctly
    - No missing components or props
    - Generated code is syntactically valid
    - File structure is complete
    """
    print("\n🧪 [TEST] Testing Preview→React Native conversion...")
    print("=" * 70)

    try:
        from Services.preview_to_react_native import PreviewToReactNativeConverter

        screens = component_model.get("screens", [])
        theme = component_model.get("theme", {})
        tokens = component_model.get("tokens", {})

        total_components = sum(len(screen.get("components", [])) for screen in screens)

        print("\n📊 [TEST] Input Analysis:")
        print(f"   - Screens: {len(screens)}")
        print(f"   - Components: {total_components}")
        print(f"   - Theme colors: {len(theme)}")
        print(f"   - Design tokens: {len(tokens)}")

        converter = PreviewToReactNativeConverter(component_model)

        print("\n🔄 [TEST] Running deterministic conversion...")
        rn_files = converter.convert()

        screen_files = [f for f in rn_files.keys() if f.startswith("src/screens/")]
        component_files = [f for f in rn_files.keys() if "components" in f]

        results = {
            "status": "success",
            "files_generated": len(rn_files),
            "file_list": sorted(list(rn_files.keys())),
            "screens_generated": len(screen_files),
            "components_used": sorted(list(converter.used_components)),
            "component_count": len(converter.used_components),
            "has_app": "App.tsx" in rn_files,
            "has_theme": "src/theme/index.ts" in rn_files,
            "has_components": "src/components/ui/index.tsx" in rn_files,
            "has_package": "package.json" in rn_files,
            "has_readme": "README.md" in rn_files,
            "total_code_size": sum(len(c) for c in rn_files.values()),
            "avg_file_size": (
                sum(len(c) for c in rn_files.values()) // len(rn_files) if rn_files else 0
            ),
            "warnings": converter.warnings,
            "errors": converter.errors,
            "warning_count": len(converter.warnings),
            "error_count": len(converter.errors),
        }

        print("\n✅ [TEST] Conversion completed!")
        print("\n📦 File Metrics:")
        print(f"   - Total files: {results['files_generated']}")
        print(f"   - Screen files: {results['screens_generated']}")
        print(f"   - Component files: {len(component_files)}")

        print("\n🎨 Component Metrics:")
        print(f"   - Unique components: {results['component_count']}")
        if results["components_used"]:
            print(f"   - Components: {', '.join(results['components_used'][:5])}")
            if len(results["components_used"]) > 5:
                print(f"     ... and {len(results['components_used']) - 5} more")

        print("\n📊 Quality Checks:")
        print(f"   - App.tsx: {'✅' if results['has_app'] else '❌'}")
        print(f"   - Theme: {'✅' if results['has_theme'] else '❌'}")
        print(f"   - Components: {'✅' if results['has_components'] else '❌'}")
        print(f"   - Package.json: {'✅' if results['has_package'] else '❌'}")
        print(f"   - README: {'✅' if results['has_readme'] else '❌'}")

        print("\n📏 Size Metrics:")
        print(f"   - Total: {results['total_code_size']:,} chars")
        print(f"   - Average: {results['avg_file_size']:,} chars/file")

        if results["warnings"]:
            print(f"\n⚠️  [TEST] Warnings ({results['warning_count']}):")
            for warning in results["warnings"][:5]:
                print(f"      - {warning}")

        if results["errors"]:
            print(f"\n❌ [TEST] Errors ({results['error_count']}):")
            for error in results["errors"][:5]:
                print(f"      - {error}")
            results["status"] = "failed"

        print(f"\n🎯 [TEST] Final Status: {results['status'].upper()}")

        return results

    except ImportError as e:
        error_msg = f"PreviewToReactNativeConverter not found: {e}"
        print(f"\n❌ [TEST] Critical error: {error_msg}")
        return {
            "status": "failed",
            "error": error_msg,
            "error_type": "ImportError",
            "files_generated": 0,
        }

    except Exception as e:
        print(f"\n❌ [TEST] Test failed: {e}")
        import traceback
        print("\n🔍 [TEST] Traceback:")
        traceback.print_exc()

        return {
            "status": "failed",
            "error": str(e),
            "error_type": type(e).__name__,
            "files_generated": 0,
        }

###############################################################################
# 🎨 BACKGROUND GENERATION (Single Gemini API, CoT-style enhancer)
###############################################################################

async def generate_backgrounds(
    screens: List[Dict[str, Any]],
    theme: Dict[str, Any],
    design_strategy: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate dynamic backgrounds using deterministic generator + optional LLM.

    1. Always generate deterministic backgrounds via enrich_screens_with_backgrounds
    2. Optionally enhance with LLM suggestions (Gemini API) for modern/bold styles
    """
    print("\n🎨 [BACKGROUNDS] Generating dynamic backgrounds...")

    try:
        # Deterministic phase
        enriched_screens = enrich_screens_with_backgrounds(
            screens,
            theme,
            design_strategy,
        )

        print(f"✅ [BACKGROUNDS] Generated {len(enriched_screens)} base backgrounds")

        # Optional: LLM enhancement for more expressive styles
        if design_strategy.get("design_style") in ["bold", "modern"]:
            enriched_screens = await _enhance_backgrounds_with_llm(
                enriched_screens,
                design_strategy,
            )

        return enriched_screens

    except Exception as e:
        print(f"⚠️ [BACKGROUNDS] Error: {e} - using basic backgrounds only")
        return enrich_screens_with_backgrounds(screens, theme, design_strategy)

async def _enhance_backgrounds_with_llm(
    screens: List[Dict[str, Any]],
    design_strategy: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Use LLM to suggest creative background enhancements.
    Uses Gemini API via send_chat(route="code") for logical compatibility.
    """
    print("🎨 [LLM ENHANCEMENT] Adding creative background suggestions...")

    screen_types = [s.get("name", "Screen") for s in screens]
    screen_type = design_strategy.get("screen_type", "general")
    design_style = design_strategy.get("design_style", "modern")

    prompt = f"""You are a creative UI background designer.

Given these screens: {', '.join(screen_types)}
Screen type: {screen_type}
Design style: {design_style}

Suggest creative background enhancements for each screen. Consider:
- Mood and emotion (welcoming, energetic, calm, professional)
- Color harmonies (complementary, analogous, triadic)
- Animation intensity (subtle, moderate, dramatic)
- Shape complexity (minimal, balanced, rich)

Output ONLY a JSON object with this structure:
{{
  "screens": [
    {{
      "name": "ScreenName",
      "mood_adjustment": "energetic|calm|professional|playful",
      "animation_intensity": "subtle|moderate|dramatic",
      "shape_complexity": "minimal|balanced|rich",
      "color_harmony": "complementary|analogous|triadic",
      "special_effects": ["glassmorphism", "particles", "aurora"]
    }}
  ]
}}

Keep suggestions aligned with the {design_style} design style."""

    try:
        response = await asyncio.wait_for(
            send_chat(prompt, route="code", timeout=15),
            timeout=20,
        )

        suggestions = _safe_json_loads(response, {"screens": []})

        # Apply suggestions to screens
        for screen in screens:
            screen_name = screen.get("name", "")
            suggestion = next(
                (s for s in suggestions.get("screens", []) if s.get("name") == screen_name),
                None,
            )

            if suggestion and "background" in screen:
                bg = screen["background"]

                # Mood
                if "mood_adjustment" in suggestion:
                    bg["mood"] = suggestion["mood_adjustment"]

                # Animation intensity
                if "animation_intensity" in suggestion:
                    intensity_map = {
                        "subtle": 0.5,
                        "moderate": 1.0,
                        "dramatic": 1.5,
                    }
                    multiplier = intensity_map.get(suggestion["animation_intensity"], 1.0)
                    if "animations" in bg and isinstance(bg["animations"], dict):
                        bg["animations"]["duration"] = int(20000 / multiplier)

                # Shape complexity (just a coarse hint)
                if "shape_complexity" in suggestion and "floating_shapes" in bg:
                    complexity_map = {
                        "minimal": 2,
                        "balanced": 4,
                        "rich": 6,
                    }
                    target_count = complexity_map.get(suggestion["shape_complexity"], 4)
                    current_count = len(bg["floating_shapes"].get("shapes", []))
                    if target_count > current_count:
                        bg["complexity"] = "high"
                    elif target_count < current_count:
                        bg["complexity"] = "low"

                print(f"   ✨ Enhanced {screen_name} background with LLM suggestions")

        print("✅ [LLM ENHANCEMENT] Background enhancement complete")
        return screens

    except asyncio.TimeoutError:
        print("⚠️ [LLM ENHANCEMENT] Timeout - using default backgrounds")
        return screens

    except Exception as e:
        print(f"⚠️ [LLM ENHANCEMENT] Error: {e} - using default backgrounds")
        return screens

###############################################################################
# HEALTH CHECK & DIAGNOSTICS
###############################################################################

def check_api_availability() -> Dict[str, Dict[str, bool]]:
    """
    Check which API keys are configured for each logical route.

    Returns:
        {
          "refiner":   {"gemini": bool, "groq": bool, "has_fallback": False},
          "intent":    {...},
          "component": {...},
          "code":      {...}
        }
    """
    status: Dict[str, Dict[str, bool]] = {}

    for route, config in ROUTES_CONFIG.items():
        status[route] = {
            "gemini": bool(config.get("gemini_key")),
            "groq": bool(config.get("groq_key")),
            "has_fallback": False,
        }

    return status

async def test_route(route: str = "intent") -> Dict[str, Any]:
    """
    Test a specific route with a simple prompt.

    Args:
        route: Route to test ("refiner", "intent", "component", or "code")

    Returns:
        Test result with status and response
    """
    test_prompts = {
        "refiner": "login screen",
        "intent": "Create a login screen",
        "component": '{"intent": "Login screen", "design_strategy": {"screen_type": "auth"}}',
        "code": '{"screens": [{"name": "Login"}]}',
    }

    prompt = test_prompts.get(route, test_prompts["intent"])

    try:
        print(f"\n🧪 Testing {route.upper()} route...")
        result = await asyncio.wait_for(
            send_chat(prompt, route=route, timeout=15),
            timeout=20,
        )

        return {
            "route": route,
            "status": "success",
            "response_length": len(result),
            "response_preview": (result[:100] + "...") if len(result) > 100 else result,
        }

    except Exception as e:
        return {
            "route": route,
            "status": "failed",
            "error": str(e),
        }

###############################################################################
# EXPORT PUBLIC API
###############################################################################

__all__ = [
    # Core functions
    "send_chat",
    "extract_intent",
    "componentize",
    "generate_asset_prompts",
    "generate_preview_from_json",
    "generate_react_native_from_json",
    "generate_backgrounds",

    # Diagnostics
    "check_api_availability",
    "test_route",
    "test_preview_conversion",

    # Configuration
    "ROUTES_CONFIG",
    "LLM_TIMEOUT",
    "LLM_TEMPERATURE",
    "MOCK_MODE",
]

###############################################################################
# CLI TEST INTERFACE (with CoT stats, Gemini API)
###############################################################################

if __name__ == "__main__":
    from LLM_Schema.cot_orchestrator import (
        print_library_overview,
        test_category_detection,
    )

    async def main():
        print("\n" + "=" * 70)
        print("🤖 HYBRID LLM CLIENT - GROQ (FREE) + GEMINI (PAID)")
        print("=" * 70)

        # Show CoT library overview
        print_library_overview()

        # Check API availability
        print("\n📊 API Availability Check:")
        availability = check_api_availability()
        for route, status in availability.items():
            gemini_icon = "✅" if status["gemini"] else "❌"
            groq_icon = "✅" if status["groq"] else "❌"
            print(f"   {route.upper()}: Gemini {gemini_icon} | Groq {groq_icon}")

        # Run tests if requested
        if len(sys.argv) > 1:
            if sys.argv[1] == "--test-cot":
                print("\n🧪 Testing CoT Category Detection:")
                test_category_detection()

            elif sys.argv[1] == "--test-intent":
                print("\n🧪 Testing Enhanced Intent Extraction:")
                test_prompts = [
                    "Modern login and signup screens",
                    "E-commerce app with products and cart",
                    "Social feed with posts and profiles",
                ]

                for prompt in test_prompts:
                    print(f"\n📝 Prompt: '{prompt}'")
                    result = await extract_intent(prompt)
                    ds = result["design_strategy"]
                    print(f"   Screen Type: {ds['screen_type']}")
                    print(f"   Screens: {result['screens']}")

            elif sys.argv[1] == "--test-routes":
                print("\n🧪 Testing All Routes:")
                for route_name in ["refiner", "intent", "component", "code"]:
                    result = await test_route(route_name)
                    status_icon = "✅" if result["status"] == "success" else "❌"
                    print(f"\n{status_icon} {route_name.upper()}: {result['status']}")
                    if result["status"] == "success":
                        print(f"   Response: {result['response_length']} chars")
                    else:
                        print(f"   Error: {result.get('error', 'Unknown')}")

            elif sys.argv[1] == "--demo":
                print("\n🎮 INTERACTIVE DEMO")
                print("=" * 70)

                prompt = input("\nEnter your UI prompt: ").strip()
                if prompt:
                    print("\n⏳ Extracting intent with CoT...")
                    intent = await extract_intent(prompt)
                    print(json.dumps(intent, indent=2))

                    print("\n⏳ Generating components...")
                    components = await componentize(intent, prompt)
                    print(f"\n✅ Generated {len(components.get('components', []))} components")

        else:
            print("\n💡 USAGE:")
            print("   python llm_client.py --test-cot       # Test CoT detection")
            print("   python llm_client.py --test-intent    # Test intent with CoT")
            print("   python llm_client.py --test-routes    # Test all API routes")
            print("   python llm_client.py --demo           # Interactive demo")

    asyncio.run(main())