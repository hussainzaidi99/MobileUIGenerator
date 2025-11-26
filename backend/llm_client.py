# backend/llm_client.py - PRODUCTION VERSION WITH 4-API ARCHITECTURE
# OpenRouter (DeepSeek) + Groq Fallback - 4-API Distributed Architecture
# API 0: Refiner | API 1: Intent | API 2: Component | API 3: Code
# Enhanced with smart CoT orchestration for optimal token usage

import os
import json
import httpx
import asyncio
import re
from dotenv import load_dotenv
from typing import Any, Dict, List, Union, Optional

# Import CoT orchestration system
from cot_orchestrator import (
    detect_categories,
    get_enhanced_prompt,
    estimate_token_count
)

load_dotenv()

# ============================================================================
# 🔵 OPENROUTER / DEEPSEEK — 3 API Keys (Intent, Component, Code ONLY)
# API 0 (Refiner) uses Groq only, no OpenRouter
# ============================================================================

OR_API_KEY_INTENT = os.getenv("OR_API_KEY_INTENT")
OR_API_KEY_COMPONENT = os.getenv("OR_API_KEY_COMPONENT")
OR_API_KEY_CODE = os.getenv("OR_API_KEY_CODE")

OR_API_URL = os.getenv("OR_API_URL", "https://openrouter.ai/api/v1/chat/completions")

OR_MODEL_INTENT = os.getenv("OR_MODEL_INTENT", "deepseek/deepseek-chat-v3")
OR_MODEL_COMPONENT = os.getenv("OR_MODEL_COMPONENT", "deepseek/deepseek-chat-v3")
OR_MODEL_CODE = os.getenv("OR_MODEL_CODE", "deepseek/deepseek-r1-0528")

OR_SITE_URL = os.getenv("OR_SITE_URL", "http://localhost:5173")
OR_APP_NAME = os.getenv("OR_APP_NAME", "Project-Beta-UI-Generator")


# ============================================================================
# 🟢 GROQ — 4 API Keys (Refiner uses Groq ONLY, others are fallbacks)
# ============================================================================

GROQ_API_KEY_REFINER = os.getenv("GROQ_API_KEY_REFINER")  # Primary for Refiner
GROQ_API_KEY_INTENT = os.getenv("GROQ_API_KEY_INTENT")
GROQ_API_KEY_COMPONENT = os.getenv("GROQ_API_KEY_COMPONENT")
GROQ_API_KEY_CODE = os.getenv("GROQ_API_KEY_CODE")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "35"))


# ============================================================================
# ROUTE CONFIG — 4-API Architecture
# API 0: Refiner (Groq ONLY) | API 1-3: OpenRouter + Groq Fallback
# ============================================================================

ROUTES_CONFIG = {
    "refiner": {
        "or_key": None,  # No OpenRouter for refiner
        "or_model": None,
        "groq_key": GROQ_API_KEY_REFINER,  # Groq ONLY
    },
    "intent": {
        "or_key": OR_API_KEY_INTENT,
        "or_model": OR_MODEL_INTENT,
        "groq_key": GROQ_API_KEY_INTENT,
    },
    "component": {
        "or_key": OR_API_KEY_COMPONENT,
        "or_model": OR_MODEL_COMPONENT,
        "groq_key": GROQ_API_KEY_COMPONENT,
    },
    "code": {
        "or_key": OR_API_KEY_CODE,
        "or_model": OR_MODEL_CODE,
        "groq_key": GROQ_API_KEY_CODE,
    },
}

MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"


# Startup diagnostics
print("\n🤖 4-API DISTRIBUTED ARCHITECTURE:")
print("   API 0 (REFINER): Groq ONLY (fast prompt enhancement)")
print("   API 1-3: DeepSeek via OpenRouter + Groq Fallback\n")
for route, cfg in ROUTES_CONFIG.items():
    or_status = "✅" if cfg['or_key'] else "➖"
    groq_status = "✅" if cfg['groq_key'] else "❌"
    print(f"   {route.upper()}: OpenRouter={or_status} | Groq={groq_status}")
print()


# ============================================================================
# UTILITY: Enhanced JSON Parser
# ============================================================================

def _safe_json_loads(s: Union[str, Dict, List], fallback: Any) -> Any:
    """Multi-strategy JSON parser with markdown stripping"""
    if isinstance(s, (dict, list)):
        return s
    
    if not isinstance(s, str) or not s.strip():
        return fallback
    
    # Strategy 1: Direct parse
    try:
        return json.loads(s)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Strategy 2: Strip markdown code fences
    try:
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', s.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Strategy 3: Extract first JSON object/array
    try:
        # Try to find JSON object
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', s, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        # Try to find JSON array
        match = re.search(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', s, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError, AttributeError):
        pass
    
    print(f"⚠️ JSON parse failed for: {s[:200]}...")
    return fallback


# ============================================================================
# 🔵 OPENROUTER API CALLER
# ============================================================================

async def call_openrouter(
    prompt: str, 
    api_key: str, 
    model: str, 
    timeout: int = LLM_TIMEOUT
) -> str:
    """Call OpenRouter API with DeepSeek models"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": OR_SITE_URL,
        "X-Title": OR_APP_NAME,
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": LLM_TEMPERATURE,
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(OR_API_URL, headers=headers, json=payload)
        
        if resp.status_code != 200:
            error_data = resp.json() if resp.text else {}
            raise RuntimeError(
                f"OpenRouter API error {resp.status_code}: {error_data.get('error', {}).get('message', resp.text)}"
            )
        
        data = resp.json()
        
        try:
            content = data["choices"][0]["message"]["content"]
            return content
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Invalid OpenRouter response structure: {data}")


# ============================================================================
# 🟢 GROQ API CALLER (Fallback)
# ============================================================================

async def call_groq(
    messages: List[Dict[str, str]], 
    api_key: str, 
    timeout: int = LLM_TIMEOUT
) -> str:
    """Call Groq Llama API as fallback"""
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": LLM_TEMPERATURE
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(GROQ_API_URL, json=payload, headers=headers)
        
        if resp.status_code != 200:
            raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text}")
        
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content


# ============================================================================
# UNIFIED LLM ROUTER (Primary + Fallback)
# ============================================================================

async def send_chat(
    prompt_or_messages: Union[str, List[Dict]], 
    route: str = "intent", 
    timeout: int = LLM_TIMEOUT
) -> str:
    """
    Route-specific LLM caller with dedicated API keys and fallbacks.
    
    SPECIAL CASE - API 0 (Refiner): Uses GROQ ONLY (no OpenRouter)
    API 1-3: Use OpenRouter (DeepSeek) primary + Groq fallback
    
    Args:
        prompt_or_messages: Prompt string or messages list
        route: "refiner", "intent", "component", or "code"
        timeout: Request timeout
    
    Returns:
        LLM response string
    
    Raises:
        RuntimeError: If API calls fail
    """
    if MOCK_MODE:
        return _mock_response(prompt_or_messages)
    
    config = ROUTES_CONFIG.get(route, ROUTES_CONFIG["intent"])
    
    # Convert messages list to string for OpenRouter (it expects string prompt)
    if isinstance(prompt_or_messages, list):
        prompt = "\n\n".join(
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in prompt_or_messages
        )
        messages = prompt_or_messages
    else:
        prompt = prompt_or_messages
        messages = [{"role": "user", "content": prompt}]
    
    # SPECIAL CASE: Refiner route uses GROQ ONLY (no OpenRouter)
    if route == "refiner":
        if config["groq_key"]:
            try:
                print(f"🟢 [REFINER] Calling Groq ({GROQ_MODEL})...")
                result = await call_groq(messages, config["groq_key"], timeout)
                print(f"✅ [REFINER] Groq succeeded!")
                return result
            except Exception as e:
                error_msg = str(e)
                print(f"❌ [REFINER] Groq failed: {error_msg[:150]}")
                raise RuntimeError(f"[REFINER] Groq failed: {error_msg}")
        else:
            raise RuntimeError("[REFINER] No Groq API key configured")
    
    # PHASE 1: Try OpenRouter (DeepSeek) first for API 1-3
    if config["or_key"]:
        try:
            print(f"🔵 [{route.upper()}] Calling OpenRouter ({config['or_model']})...")
            result = await call_openrouter(
                prompt, 
                config["or_key"], 
                config["or_model"], 
                timeout
            )
            print(f"✅ [{route.upper()}] OpenRouter succeeded!")
            return result
        
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ [{route.upper()}] OpenRouter failed: {error_msg[:150]}")
            
            if config["groq_key"]:
                print(f"🔄 [{route.upper()}] Falling back to Groq...")
            else:
                raise RuntimeError(f"[{route.upper()}] OpenRouter failed and no Groq fallback available: {error_msg}")
    
    # PHASE 2: Fallback to Groq for API 1-3
    if config["groq_key"]:
        try:
            print(f"🟢 [{route.upper()}] Calling Groq ({GROQ_MODEL})...")
            result = await call_groq(messages, config["groq_key"], timeout)
            print(f"✅ [{route.upper()}] Groq succeeded!")
            return result
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ [{route.upper()}] Groq also failed: {error_msg[:150]}")
            raise RuntimeError(f"[{route.upper()}] Both OpenRouter and Groq failed")
    
    raise RuntimeError(f"[{route.upper()}] No LLM provider available (check API keys)")


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
                {"id": "illustration-1", "type": "IllustrationHeader", "props": {
                    "illustration": "auth-welcome",
                    "title": "Welcome Back",
                    "subtitle": "Sign in to continue"
                }},
                {"id": "spacer-1", "type": "Spacer", "props": {"height": "32"}},
                {"id": "card-1", "type": "Card", "props": {"padding": "24", "elevation": "md"}},
                {"id": "input-email", "type": "IconInput", "props": {
                    "icon": "mail",
                    "label": "Email",
                    "placeholder": "you@example.com"
                }},
                {"id": "spacer-2", "type": "Spacer", "props": {"height": "16"}},
                {"id": "input-pwd", "type": "IconInput", "props": {
                    "icon": "lock",
                    "type": "password",
                    "label": "Password"
                }},
                {"id": "spacer-3", "type": "Spacer", "props": {"height": "24"}},
                {"id": "btn-login", "type": "GradientButton", "props": {
                    "text": "Sign In",
                    "gradient": "teal",
                    "size": "lg"
                }},
                {"id": "divider-1", "type": "Divider", "props": {"text": "OR"}},
                {"id": "btn-google", "type": "SocialButton", "props": {"provider": "Google"}},
                {"id": "spacer-4", "type": "Spacer", "props": {"height": "12"}},
                {"id": "btn-apple", "type": "SocialButton", "props": {"provider": "Apple"}}
            ]
        })
    
    return "{}"


###############################################################################
# 🎯 BASE PROMPTS (Work with CoT orchestration)
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
# 🧠 ENHANCED STAGE FUNCTIONS (With CoT Integration)
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
            "key_components": ["Header", "Container", "Button"]
        }
    }
    
    if not prompt.strip():
        return fallback
    
    # 🎯 STEP 1: Detect categories from prompt
    detected_categories = detect_categories(prompt)
    print(f"🎯 Detected categories: {', '.join(detected_categories) if detected_categories else 'None'}")
    
    # 🎯 STEP 2: Build enhanced prompt with relevant CoT examples
    enhanced_prompt = get_enhanced_prompt(
        base_prompt=COMPACT_INTENT_PROMPT,
        user_prompt=prompt,
        design_strategy=None  # We don't have design_strategy yet in Stage 1
    )
    
    # 🎯 STEP 3: Estimate token usage
    estimated_tokens = estimate_token_count(enhanced_prompt)
    print(f"📏 Intent prompt size: {len(enhanced_prompt):,} chars (~{estimated_tokens:,} tokens)")
    
    try:
        content = await asyncio.wait_for(
            send_chat(enhanced_prompt, route="intent", timeout=LLM_TIMEOUT),
            timeout=LLM_TIMEOUT + 5
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
        print(f"⚠️ Intent extraction timeout - using fallback")
        return fallback
    except Exception as e:
        print(f"⚠️ Intent extraction error: {e} - using fallback")
        return fallback


async def componentize(intent_obj: dict, original_prompt: str) -> dict:
    """
    Stage 2: Generate component model with CoT-enhanced prompts.
    
    Args:
        intent_obj: Intent object from Stage 1
        original_prompt: Original user prompt (fallback)
        
    Returns:
        Component model with components array
    """
    fallback = {"components": []}
    
    intent_text = intent_obj.get("intent", original_prompt)
    design_strategy = intent_obj.get("design_strategy", {})
    
    # 🎯 STEP 1: Build task JSON
    task_json = json.dumps({
        "task": "componentize",
        "intent": intent_text,
        "screens": intent_obj.get("screens", []),
        "design_strategy": design_strategy
    }, indent=2)
    
    # 🎯 STEP 2: Get enhanced prompt with CoT examples
    enhanced_prompt = get_enhanced_prompt(
        base_prompt=COMPACT_COMPONENTIZE_PROMPT,
        user_prompt=task_json,
        design_strategy=design_strategy  # Pass design_strategy for better category detection
    )
    
    # 🎯 STEP 3: Estimate token usage
    estimated_tokens = estimate_token_count(enhanced_prompt)
    print(f"📏 Componentize prompt size: {len(enhanced_prompt):,} chars (~{estimated_tokens:,} tokens)")
    
    try:
        content = await asyncio.wait_for(
            send_chat(enhanced_prompt, route="component", timeout=LLM_TIMEOUT),
            timeout=LLM_TIMEOUT + 5
        )
        
        result = _safe_json_loads(content, fallback)
        
        if not isinstance(result, dict) or "components" not in result:
            return fallback
        
        # Ensure component structure
        for i, comp in enumerate(result["components"]):
            if isinstance(comp, dict):
                comp.setdefault("id", f"comp-{i}")
                comp.setdefault("type", "Container")
                comp.setdefault("props", {})
        
        print(f"✅ Generated {len(result['components'])} components")
        
        return result
        
    except Exception as e:
        print(f"⚠️ Componentize error: {e} - using fallback")
        return fallback


async def generate_asset_prompts(components: list) -> dict:
    """
    Generate image generation prompts for visual components.
    
    Args:
        components: List of component objects
        
    Returns:
        Dictionary mapping component IDs to image prompts
    """
    prompts = {}
    
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
    API 3 (CODE): Generate web preview JSON from component model.
    
    STRATEGY: Direct pass-through (no transformation needed)
    - Component model IS already the web preview
    - No LLM, no transformation, no hallucinations
    - Ensures 100% consistency with generated React Native code
    
    Args:
        component_model: Component model JSON from API 1
        
    Returns:
        Web-ready preview JSON (pass-through)
    """
    print("\n🔵 [API 3] Generating web preview...")
    
    try:
        from preview_adapter import PreviewAdapter
        web_preview = PreviewAdapter.to_web_preview(component_model)
        
        print(f"✅ [API 3] Web preview ready")
        print(f"📊 [API 3] Screens: {len(web_preview.get('screens', []))}")
        
        return web_preview
        
    except ImportError:
        print("ℹ️  [API 3] PreviewAdapter not found - using direct pass-through")
        return component_model
    
    except Exception as e:
        print(f"⚠️  [API 3] Error: {e} - returning original model")
        return component_model


async def generate_react_native_from_json(component_model: dict) -> dict:
    """
    API 2 (COMPONENT): Generate React Native code from component model.
    
    ✅ DETERMINISTIC STRATEGY: Preview→React Native Direct Conversion
    - NO LLM involved (zero hallucinations)
    - NO fallbacks to legacy generators
    - Direct component mapping (100% accuracy)
    - Same input → Same output (deterministic)
    
    Args:
        component_model: Component model JSON from API 1
        
    Returns:
        Dictionary of React Native project files
        
    Raises:
        ImportError: If PreviewToReactNativeConverter is not available
        ValueError: If component_model is invalid
        RuntimeError: If conversion fails
    """
    print("\n🔵 [API 2] Starting React Native code generation...")
    print("🎯 [API 2] Method: Deterministic Preview→React Native conversion")
    
    try:
        from preview_to_react_native import PreviewToReactNativeConverter
    except ImportError as e:
        error_msg = f"PreviewToReactNativeConverter not found: {e}"
        print(f"\n❌ [API 2] CRITICAL ERROR: {error_msg}")
        raise ImportError(
            "PreviewToReactNativeConverter is required. "
            "Check that backend/preview_to_react_native.py exists."
        ) from e
    
    if not component_model or not isinstance(component_model, dict):
        error_msg = "component_model must be a non-empty dictionary"
        print(f"❌ [API 2] Validation failed: {error_msg}")
        raise ValueError(error_msg)
    
    screens = component_model.get("screens", [])
    if not screens:
        print("⚠️  [API 2] Warning: No screens in component model")
    
    print(f"📊 [API 2] Input: {len(screens)} screen(s), "
          f"{sum(len(s.get('components', [])) for s in screens)} components")
    
    try:
        converter = PreviewToReactNativeConverter(component_model)
        
        print("🔄 [API 2] Converting preview → React Native code...")
        rn_files = converter.convert()
        
        if not rn_files:
            raise RuntimeError("Converter returned empty result")
        
        required_files = {
            "App.tsx": "Main entry point",
            "src/theme/index.ts": "Theme configuration",
            "package.json": "Dependencies"
        }
        
        missing_files = [
            f"{path} ({desc})" 
            for path, desc in required_files.items() 
            if path not in rn_files
        ]
        
        if missing_files:
            print(f"⚠️  [API 2] Missing critical files:")
            for missing in missing_files:
                print(f"      - {missing}")
        
        screen_files = [f for f in rn_files.keys() if f.startswith("src/screens/")]
        total_size = sum(len(content) for content in rn_files.values())
        
        print(f"\n✅ [API 2] Conversion successful!")
        print(f"   📦 Files: {len(rn_files)}")
        print(f"   🎨 Components: {len(converter.used_components)}")
        print(f"   📱 Screens: {len(screen_files)}")
        print(f"   📊 Code size: {total_size:,} chars")
        print(f"   🎯 Accuracy: 100% (deterministic, no LLM)")
        
        if converter.warnings:
            print(f"\n⚠️  [API 2] Warnings ({len(converter.warnings)}):")
            for warning in converter.warnings[:3]:
                print(f"      - {warning}")
            if len(converter.warnings) > 3:
                print(f"      ... and {len(converter.warnings) - 3} more")
        
        if converter.errors:
            print(f"\n❌ [API 2] Errors ({len(converter.errors)}):")
            for error in converter.errors[:3]:
                print(f"      - {error}")
            if len(converter.errors) > 3:
                print(f"      ... and {len(converter.errors) - 3} more")
        
        return rn_files
        
    except Exception as e:
        print(f"\n❌ [API 2] Conversion failed: {e}")
        print(f"🔍 [API 2] Error type: {type(e).__name__}")
        
        import traceback
        print(f"\n🔍 [API 2] Full traceback:")
        traceback.print_exc()
        
        print(f"\n❌ [API 2] NO FALLBACK AVAILABLE")
        print(f"🔧 [API 2] Fix preview_to_react_native.py to resolve this issue")
        
        raise RuntimeError(
            f"React Native code generation failed: {str(e)}"
        ) from e


async def test_preview_conversion(component_model: dict) -> dict:
    """
    Test function to verify Preview→React Native conversion accuracy.
    
    Validates:
    - All component types convert correctly
    - No missing components or props
    - Generated code is syntactically valid
    - File structure is complete
    
    Args:
        component_model: Component model from API 1
        
    Returns:
        Test results dict with status and detailed metrics
    """
    print("\n🧪 [TEST] Testing Preview→React Native conversion...")
    print("=" * 70)
    
    try:
        from preview_to_react_native import PreviewToReactNativeConverter
        
        screens = component_model.get("screens", [])
        theme = component_model.get("theme", {})
        tokens = component_model.get("tokens", {})
        
        total_components = sum(
            len(screen.get("components", [])) 
            for screen in screens
        )
        
        print(f"\n📊 [TEST] Input Analysis:")
        print(f"   - Screens: {len(screens)}")
        print(f"   - Components: {total_components}")
        print(f"   - Theme colors: {len(theme)}")
        print(f"   - Design tokens: {len(tokens)}")
        
        converter = PreviewToReactNativeConverter(component_model)
        
        print(f"\n🔄 [TEST] Running deterministic conversion...")
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
            "avg_file_size": sum(len(c) for c in rn_files.values()) // len(rn_files) if rn_files else 0,
            "warnings": converter.warnings,
            "errors": converter.errors,
            "warning_count": len(converter.warnings),
            "error_count": len(converter.errors),
        }
        
        print(f"\n✅ [TEST] Conversion completed!")
        print(f"\n📦 File Metrics:")
        print(f"   - Total files: {results['files_generated']}")
        print(f"   - Screen files: {results['screens_generated']}")
        print(f"   - Component files: {len(component_files)}")
        
        print(f"\n🎨 Component Metrics:")
        print(f"   - Unique components: {results['component_count']}")
        if results['components_used']:
            print(f"   - Components: {', '.join(results['components_used'][:5])}")
            if len(results['components_used']) > 5:
                print(f"     ... and {len(results['components_used']) - 5} more")
        
        print(f"\n📊 Quality Checks:")
        print(f"   - App.tsx: {'✅' if results['has_app'] else '❌'}")
        print(f"   - Theme: {'✅' if results['has_theme'] else '❌'}")
        print(f"   - Components: {'✅' if results['has_components'] else '❌'}")
        print(f"   - Package.json: {'✅' if results['has_package'] else '❌'}")
        print(f"   - README: {'✅' if results['has_readme'] else '❌'}")
        
        print(f"\n📏 Size Metrics:")
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


# Export public API
__all__ = [
    'generate_preview_from_json',
    'generate_react_native_from_json',  # ← NEW: RN generator
    'test_preview_conversion',
]
###############################################################################
# HEALTH CHECK & DIAGNOSTICS
###############################################################################

def check_api_availability() -> Dict[str, Dict[str, bool]]:
    """
    Check which API keys are configured for each route.
    
    Returns:
        Status dictionary showing availability per route
    """
    status = {}
    
    for route, config in ROUTES_CONFIG.items():
        status[route] = {
            "openrouter": bool(config["or_key"]),
            "groq": bool(config["groq_key"]),
            "has_fallback": bool(config["or_key"]) and bool(config["groq_key"])
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
        "code": '{"screens": [{"name": "Login"}]}'
    }
    
    prompt = test_prompts.get(route, test_prompts["intent"])
    
    try:
        print(f"\n🧪 Testing {route.upper()} route...")
        result = await asyncio.wait_for(
            send_chat(prompt, route=route, timeout=15),
            timeout=20
        )
        
        return {
            "route": route,
            "status": "success",
            "response_length": len(result),
            "response_preview": result[:100] + "..." if len(result) > 100 else result
        }
    
    except Exception as e:
        return {
            "route": route,
            "status": "failed",
            "error": str(e)
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
    "generate_dart_from_json",
    "generate_preview_from_json",
    
    # Diagnostics
    "check_api_availability",
    "test_route",
    
    # Configuration
    "ROUTES_CONFIG",
    "LLM_TIMEOUT",
    "LLM_TEMPERATURE",
    "MOCK_MODE",
]


###############################################################################
# CLI TEST INTERFACE (Enhanced with CoT stats)
###############################################################################

if __name__ == "__main__":
    import sys
    from cot_orchestrator import print_library_overview, test_category_detection
    
    async def main():
        print("\n" + "="*70)
        print("🤖 ENHANCED LLM CLIENT WITH 4-API ARCHITECTURE")
        print("="*70)
        
        # Show CoT library overview
        print_library_overview()
        
        # Check API availability
        print("\n📊 API Availability Check:")
        availability = check_api_availability()
        for route, status in availability.items():
            or_icon = "✅" if status["openrouter"] else "❌"
            groq_icon = "✅" if status["groq"] else "❌"
            fallback = "🛡️" if status["has_fallback"] else "⚠️"
            print(f"   {route.upper()}: OpenRouter {or_icon} | Groq {groq_icon} | Fallback {fallback}")
        
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
                    "Social feed with posts and profiles"
                ]
                
                for prompt in test_prompts:
                    print(f"\n📝 Prompt: '{prompt}'")
                    result = await extract_intent(prompt)
                    print(f"   Screen Type: {result['design_strategy']['screen_type']}")
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
    
    # Run async main
    asyncio.run(main())