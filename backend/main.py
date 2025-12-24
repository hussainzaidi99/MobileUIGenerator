# backend/main.py - Production-Ready with Image Enrichment + Credits System
# Version: 2.5.0
# - Keeps CRITICAL FIX: Image enrichment BEFORE preview generation
# - Adds Stripe-based credits system, token tracking, and usage reporting

from asyncio.log import logger
import os
import asyncio
import json 
from typing import Dict, List, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
import io
import zipfile
from Services.prompt_refiner import refine_prompt, refiner_stats
from LLM_Schema.llm_client import (
    extract_intent,
    componentize,
    generate_react_native_from_json,
    generate_preview_from_json,
    generate_asset_prompts,
    generate_backgrounds,
    send_chat,
)
from LLM_Schema.llm_client import _safe_json_loads  # ✅ ADD THIS TOO

from Services.component_model import create_component_model
from Services.style_enricher import enrich_styles
from Services.pexels_image_service import enrich_layout_with_pexels
from Services.image_url_generator import enrich_layout_with_images
from Services.background_jobs import setup_background_jobs, shutdown_background_jobs
from Services.tier_manager import TierManager

# 🆕 Credits / token tracking middleware
from middleware.credits_middleware import (
    token_tracker,
    check_user_credits,
    deduct_credits_after_generation,
    estimate_tokens,
)
from Services.session_manager import (
    session_manager,
    create_editing_session,
    get_editing_session
)

load_dotenv()

# ============================================================================ #
# CREATE FASTAPI APP
# ============================================================================ #

app = FastAPI(
    title="UI Pipeline Beta - React Native Edition (with Credits System)",
    version="2.5.0",
    description=(
        "Production-ready architecture with dynamic backgrounds, "
        "image enrichment, and Stripe-powered credits system."
    ),
)

# ============================================================================ #
# INCLUDE AUTH & PAYMENT ROUTES
# ============================================================================ #

from Auth.auth_routes import router as auth_router
from payments.payment_routes import router as payment_router, get_user_credits

app.include_router(auth_router)
app.include_router(payment_router)

# ============================================================================ #
# RATE LIMITING (using SlowAPI)
# ============================================================================ #

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================================================ #
# DATABASE IMPORTS
# ============================================================================ #

from db.database import connect_to_mongo, close_mongo_connection

# ============================================================================ #
# CORS MIDDLEWARE
# ============================================================================ #

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STEP_TIMEOUT = int(os.getenv("STEP_TIMEOUT", "30"))

# ============================================================================ #
# INTELLIGENT COMPONENT-TO-SCREEN ASSIGNMENT
# ============================================================================ #


def assign_component_to_screen(
    comp: Dict,
    screen_names: List[str],
    design_strategy: Dict,
    screen_component_count: Dict[str, int],
) -> str:
    """
    Intelligently assign component to most likely screen.

    Strategies:
      1. Explicit "screen" field
      2. ID matching with screen name
      3. Context hints based on screen_type + keywords
      4. Load balancing fallback
    """
    comp_type = comp.get("type", "").lower()
    comp_id = str(comp.get("id", "")).lower()
    props = comp.get("props", {})

    # STRATEGY 1: Explicit screen field (highest priority)
    explicit_screen = comp.get("screen")
    if explicit_screen and explicit_screen in screen_names:
        return explicit_screen

    # STRATEGY 2: Exact match in component ID
    for screen_name in screen_names:
        if screen_name.lower() in comp_id:
            return screen_name

    # STRATEGY 3: Component type + context hints
    screen_type = design_strategy.get("screen_type", "general")

    if screen_type == "auth":
        # Login screen keywords
        login_keywords = [
            "login",
            "signin",
            "sign-in",
            "sign_in",
            "forgot",
            "password",
            "email",
        ]
        if any(
            keyword in comp_id or keyword in str(props).lower()
            for keyword in login_keywords
        ):
            login_screen = next(
                (s for s in screen_names if "login" in s.lower() or "signin" in s.lower()),
                None,
            )
            if login_screen:
                return login_screen

        # Signup screen keywords
        signup_keywords = [
            "signup",
            "sign-up",
            "sign_up",
            "register",
            "create",
            "name",
        ]
        if any(
            keyword in comp_id or keyword in str(props).lower()
            for keyword in signup_keywords
        ):
            signup_screen = next(
                (s for s in screen_names if "signup" in s.lower() or "register" in s.lower()),
                None,
            )
            if signup_screen:
                return signup_screen

    elif screen_type == "ecommerce":
        # Cart/Checkout screen
        if any(keyword in comp_id for keyword in ["cart", "checkout", "payment", "order"]):
            cart_screen = next(
                (s for s in screen_names if any(k in s.lower() for k in ["cart", "checkout", "payment"])),
                None,
            )
            if cart_screen:
                return cart_screen

        # Product listing screen
        if any(keyword in comp_id for keyword in ["product", "search", "grid", "shop"]):
            return screen_names[0]  # Product listing is usually first

    elif screen_type == "social":
        # Profile screen
        if any(keyword in comp_id for keyword in ["profile", "user", "avatar", "followers"]):
            profile_screen = next(
                (s for s in screen_names if "profile" in s.lower()),
                None,
            )
            if profile_screen:
                return profile_screen

        # Feed screen
        if any(keyword in comp_id for keyword in ["feed", "post", "card"]):
            feed_screen = next(
                (s for s in screen_names if "feed" in s.lower()),
                None,
            )
            if feed_screen:
                return feed_screen

    elif screen_type == "dashboard":
        # Settings screen
        if any(keyword in comp_id for keyword in ["settings", "preferences", "config"]):
            settings_screen = next(
                (s for s in screen_names if "settings" in s.lower()),
                None,
            )
            if settings_screen:
                return settings_screen

        # Dashboard/Analytics screen
        if any(keyword in comp_id for keyword in ["stat", "chart", "analytics", "overview"]):
            return screen_names[0]  # Dashboard is usually first

    # STRATEGY 4: Load balancing fallback
    min_screen = min(screen_names, key=lambda s: screen_component_count.get(s, 0))
    return min_screen


# ============================================================================ #
# INTELLIGENT COMPONENT NESTING LOGIC
# ============================================================================ #


def _nest_auth_components(components: List[Dict]) -> List[Dict]:
    """
    Intelligently nest authentication screen components.
    Groups form inputs inside a Card container.
    """
    nested = []
    card_children: List[Dict] = []
    inside_card = False
    card_component = None

    for comp in components:
        comp_type = (comp.get("type") or "").lower()

        # Components that stay outside Card
        if comp_type in ("illustrationheader", "customillustrationheader"):
            nested.append(comp)

        # First spacer after illustration
        elif comp_type in ("spacer", "customspacer") and not inside_card and not card_component:
            nested.append(comp)

        # Card starts - begin collecting children
        elif comp_type in ("card", "customcard"):
            inside_card = True
            card_component = comp

        # Form elements go inside Card
        elif inside_card and comp_type in (
            "iconinput",
            "textinput",
            "passwordinput",
            "customtextinput",
            "spacer",
            "customspacer",
            "linkbutton",
            "customlinkbutton",
            "gradientbutton",
            "customgradientbutton",
            "button",
            "custombutton",
            "checkbox",
            "customcheckbox",
            "switch",
        ):
            card_children.append(comp)

            # Close card after primary CTA button
            if comp_type in ("gradientbutton", "customgradientbutton"):
                if card_component:
                    card_component["children"] = card_children
                    nested.append(card_component)
                    inside_card = False
                    card_component = None
                    card_children = []

        # Components after Card (Divider, Social buttons, etc.)
        elif not inside_card and comp_type in (
            "divider",
            "customdivider",
            "socialbutton",
            "customsocialbutton",
            "linkbutton",
            "customlinkbutton",
        ):
            nested.append(comp)

        # Fallback: add to current context
        else:
            if inside_card:
                card_children.append(comp)
            else:
                nested.append(comp)

    # Edge case: Card was never closed
    if card_component and card_children:
        card_component["children"] = card_children
        nested.append(card_component)

    return nested


def _nest_ecommerce_components(components: List[Dict]) -> List[Dict]:
    """Nest e-commerce components (SearchInput + Grid of ProductCards)."""
    nested = []
    grid_children: List[Dict] = []
    inside_grid = False
    grid_component = None

    for comp in components:
        comp_type = (comp.get("type") or "").lower()

        if comp_type in ("searchinput", "customsearchinput"):
            nested.append(comp)

        elif comp_type in ("spacer", "customspacer") and not inside_grid:
            nested.append(comp)

        elif comp_type in ("grid", "customgrid"):
            inside_grid = True
            grid_component = comp

        elif inside_grid and comp_type in (
            "productcard",
            "customproductcard",
            "card",
            "customcard",
        ):
            grid_children.append(comp)

        elif comp_type in ("floatingactionbutton", "customfloatingactionbutton"):
            if grid_component and grid_children:
                grid_component["children"] = grid_children
                nested.append(grid_component)
                inside_grid = False
                grid_component = None
                grid_children = []
            nested.append(comp)

        else:
            if inside_grid:
                grid_children.append(comp)
            else:
                nested.append(comp)

    if grid_component and grid_children:
        grid_component["children"] = grid_children
        nested.append(grid_component)

    return nested


def _nest_dashboard_components(components: List[Dict]) -> List[Dict]:
    """Nest dashboard components (Grid of StatCards)."""
    nested = []
    grid_children: List[Dict] = []
    inside_grid = False
    grid_component = None

    for comp in components:
        comp_type = (comp.get("type") or "").lower()

        if comp_type in ("appbar", "customappbar", "header", "customheader"):
            nested.append(comp)

        elif comp_type in ("grid", "customgrid"):
            inside_grid = True
            grid_component = comp

        elif inside_grid and comp_type in ("statcard", "customstatcard"):
            grid_children.append(comp)

        elif comp_type in ("spacer", "customspacer") and inside_grid:
            if grid_component and grid_children:
                grid_component["children"] = grid_children
                nested.append(grid_component)
                inside_grid = False
                grid_component = None
                grid_children = []
            nested.append(comp)

        else:
            if inside_grid and comp_type in ("statcard", "customstatcard"):
                grid_children.append(comp)
            else:
                if inside_grid and grid_component and grid_children:
                    grid_component["children"] = grid_children
                    nested.append(grid_component)
                    inside_grid = False
                    grid_component = None
                    grid_children = []
                nested.append(comp)

    if grid_component and grid_children:
        grid_component["children"] = grid_children
        nested.append(grid_component)

    return nested


def _nest_components_by_screen_type(components: List[Dict], screen_type: str) -> List[Dict]:
    """Route to appropriate nesting logic based on screen type."""
    screen_type = (screen_type or "").lower()

    if screen_type == "auth":
        return _nest_auth_components(components)
    elif screen_type == "ecommerce":
        return _nest_ecommerce_components(components)
    elif screen_type in ("dashboard", "analytics"):
        return _nest_dashboard_components(components)
    else:
        return components


# ============================================================================ #
# 🎯 MAIN PIPELINE - IMAGE ENRICHMENT BEFORE PREVIEW + CREDITS SYSTEM
# ============================================================================ #


@app.post("/generate_pipeline")
async def generate_pipeline(request: Request):
    """
    Pipeline with:
      - Prompt refinement
      - Intent & component generation
      - Intelligent screen assignment + nesting
      - Style enrichment
      - 🖼️ Image enrichment BEFORE preview generation
      - 🎨 Background generation
      - React Native code + preview in parallel
      - 💳 Credits system (pre-check + post-deduction + usage stats)
    """
    body = await request.json()
    raw_prompt = body.get("prompt", "")
    user_id = body.get("user_id")  # required for credits system

    if not raw_prompt:
        return JSONResponse({"error": "Missing prompt"}, status_code=400)

    if not user_id:
        return JSONResponse(
            {"error": "Missing user_id - authentication required"},
            status_code=401,
        )

    print(f"\n🔹 Beta Pipeline v2.5 (React Native) - User: {user_id}")
    print(f"   Prompt: {raw_prompt[:80]}...\n")

    # --------------------------------------------------------------------- #
    # 🆕 STEP -1: CHECK CREDITS BEFORE STARTING
    # --------------------------------------------------------------------- #

    estimated_tokens = estimate_tokens(raw_prompt)
    print(f"📊 Estimated tokens for request: {estimated_tokens:,}")

    has_credits = await check_user_credits(user_id, estimated_tokens)

    if not has_credits:
        # Try to fetch current balance for better error message
        try:
            balance = await get_user_credits(user_id)
            current_credits = balance.get("credits")
        except Exception:
            current_credits = None

        details = {
            "required_credits": estimated_tokens / 70_000,
            "message": "Please purchase more credits to continue.",
        }
        if current_credits is not None:
            details["current_credits"] = current_credits

        return JSONResponse(
            {
                "error": "Insufficient credits",
                "details": details,
            },
            status_code=402,  # Payment Required
        )

    # Reset token tracker for this request
    token_tracker.reset()

    # --------------------------------------------------------------------- #
    # STEP 0: PROMPT REFINER
    # --------------------------------------------------------------------- #

    print("🔵 [STEP 0] API 0 (REFINER) - Enhancing user prompt...")

    try:
        refinement_result = await asyncio.wait_for(
            refine_prompt(raw_prompt),
            timeout=STEP_TIMEOUT,
        )

        refiner_stats.record(refinement_result)
        prompt = refinement_result["refined_prompt"]

        if refinement_result["refinement_applied"]:
            print("✅ [STEP 0] Prompt refined:")
            print(
                f"   Original ({refinement_result['metadata']['original_word_count']} words): "
                f"{raw_prompt[:80]}..."
            )
            print(
                f"   Refined ({refinement_result['metadata']['refined_word_count']} words): "
                f"{prompt[:80]}..."
            )
        else:
            print(
                f"ℹ️ [STEP 0] Using original prompt: {refinement_result['metadata']['reason']}"
            )
            prompt = raw_prompt

    except Exception as e:
        print(f"⚠️ [STEP 0] Refiner failed: {e} - using original prompt")
        prompt = raw_prompt
        refinement_result = {
            "original_prompt": raw_prompt,
            "refined_prompt": raw_prompt,
            "refinement_applied": False,
            "metadata": {"reason": f"Error: {str(e)[:50]}"},
        }

    # --------------------------------------------------------------------- #
    # STEP 1: INTENT + COMPONENT MODEL
    # --------------------------------------------------------------------- #

    print("\n🔵 [STEP 1] API 1 (INTENT) - Generating Component Model...")

    try:
        intent_obj = await asyncio.wait_for(
            extract_intent(prompt),
            timeout=STEP_TIMEOUT,
        )
        intent_obj["device"] = "mobile"
        screen_names = intent_obj.get("screens", []) or ["Home"]

        print(f"📋 Screens detected: {screen_names}")

        component_result = await asyncio.wait_for(
            componentize(intent_obj, prompt),
            timeout=STEP_TIMEOUT,
        )

        all_components = component_result.get("components", [])
        print(f"✅ [STEP 1] Generated {len(all_components)} components (flat list)")

    except Exception as e:
        print(f"❌ [STEP 1] Failed: {e}")
        return JSONResponse(
            {"error": f"Component model generation failed: {e}"},
            status_code=500,
        )

    # --------------------------------------------------------------------- #
    # STEP 2: ASSEMBLY (SCREEN ASSIGNMENT + NESTING)
    # --------------------------------------------------------------------- #

    print("\n🔵 [STEP 2] ASSEMBLY - Assigning components to screens intelligently...")

    screen_type = intent_obj.get("design_strategy", {}).get("screen_type", "general")
    design_strategy = intent_obj.get("design_strategy", {})

    try:
        screen_component_map: Dict[str, List[Dict]] = {
            screen_name: [] for screen_name in screen_names
        }
        screen_component_count: Dict[str, int] = {
            screen_name: 0 for screen_name in screen_names
        }

        for idx, comp in enumerate(all_components):
            assigned_screen = assign_component_to_screen(
                comp,
                screen_names,
                design_strategy,
                screen_component_count,
            )

            screen_component_map[assigned_screen].append(comp)
            screen_component_count[assigned_screen] += 1

            if idx < 5:
                print(
                    f"   🔎 Component '{comp.get('id', 'unknown')}' ({comp.get('type')}) → {assigned_screen}"
                )

        # Build screens with nesting
        screens: List[Dict] = []

        print(f"\n📊 Component Distribution by Screen:")
        for screen_name in screen_names:
            screen_comps = screen_component_map[screen_name]

            if not screen_comps:
                print(f"   ⚠️ {screen_name}: 0 components (creating empty state)")
                screens.append(
                    {
                        "name": screen_name,
                        "components": [
                            {
                                "id": f"root-{screen_name.lower()}",
                                "type": "Container",
                                "props": {"padding": "16"},
                                "children": [
                                    {
                                        "id": f"empty-{screen_name.lower()}",
                                        "type": "EmptyState",
                                        "props": {
                                            "icon": "📱",
                                            "title": f"{screen_name} Screen",
                                            "message": "No components generated for this screen",
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                )
                continue

            nested_comps = _nest_components_by_screen_type(screen_comps, screen_type)

            comp_types = [c.get("type") for c in screen_comps]
            print(
                f"   📱 {screen_name}: {len(screen_comps)} components → {len(nested_comps)} top-level"
            )
            print(
                f"      Types: {', '.join(comp_types[:5])}"
                f"{'...' if len(comp_types) > 5 else ''}"
            )

            screens.append(
                {
                    "name": screen_name,
                    "components": [
                        {
                            "id": f"root-{screen_name.lower()}",
                            "type": "Container",
                            "props": {"padding": "16"},
                            "children": nested_comps,
                        }
                    ],
                }
            )

        component_model_dict = {
            "screens": screens,
            "tokens": {"gap": 16, "padding": 20, "cardRadius": 12},
            "theme": {
                "primary": "#0D9488",
                "background": "#F7FAFC",
                "surface": "#FFFFFF",
                "text": "#0F172A",
            },
        }

        print(f"✅ [STEP 2] Component hierarchy built for '{screen_type}' screen type")

    except Exception as e:
        print(f"❌ [STEP 2] Assembly failed: {e}")
        import traceback

        traceback.print_exc()
        return JSONResponse(
            {"error": f"Component assembly failed: {e}"},
            status_code=500,
        )

    # --------------------------------------------------------------------- #
    # STEP 3: STYLE ENRICHMENT
    # --------------------------------------------------------------------- #

    print("\n🔵 [STEP 3] STYLE ENRICHMENT - Applying design system...")
    
    try:
        component_model_dict = enrich_styles(component_model_dict, intent_obj)
        print("✅ [STEP 3] Styles enriched")
    except Exception as e:
        print(f"⚠️ [STEP 3] Style enrichment failed: {e} - proceeding without")

    # STEP 4: 🖼️ IMAGE ENRICHMENT (with Pexels + Unsplash fallback)
    print("\n🖼️  [STEP 4] IMAGE ENRICHMENT - Attempting Pexels, fallback to Unsplash...")
    
    try:
        # Try Pexels first with user prompt context
        component_model_dict = await enrich_layout_with_pexels(
            component_model_dict,
            user_prompt=prompt  # ✅ Pass user prompt for context-aware queries
        )
        
        # ✅ COUNT ENRICHED IMAGES (check if Pexels actually worked)
        image_count = 0
        def count_images(comp):
            count = 0
            props = comp.get("props", {})
            # Check if image URL is from Pexels
            image_url = props.get("image") or props.get("src") or props.get("illustration")
            if image_url and "pexels.com" in str(image_url):
                count += 1
            for child in comp.get("children", []):
                count += count_images(child)
            return count
        
        for screen in component_model_dict.get("screens", []):
            for comp in screen.get("components", []):
                image_count += count_images(comp)
        
        if image_count == 0:
            # Pexels returned no images - use Unsplash fallback
            print("⚠️  [IMAGE] Pexels returned 0 images - falling back to Unsplash")
            component_model_dict = enrich_layout_with_images(component_model_dict)
        else:
            print(f"✅ [STEP 4] Pexels enriched {image_count} components")
    
    except Exception as e:
        print(f"⚠️  [IMAGE] Pexels error: {e} - falling back to Unsplash")
        component_model_dict = enrich_layout_with_images(component_model_dict)
        import traceback
        traceback.print_exc()
    # --------------------------------------------------------------------- #
    # STEP 5: BACKGROUND GENERATION
    # --------------------------------------------------------------------- #

    print("\n🎨 [STEP 5] BACKGROUND GENERATION - Creating dynamic backgrounds...")
    try:
        component_model_dict["screens"] = await asyncio.wait_for(
            generate_backgrounds(
                component_model_dict["screens"],
                component_model_dict["theme"],
                design_strategy,
            ),
            timeout=STEP_TIMEOUT,
        )

        print(f"✅ [STEP 5] Backgrounds generated for {len(screens)} screens")

    except Exception as e:
        print(
            f"⚠️ [STEP 5] Background generation failed: {e} - proceeding without"
        )

    # Create component model AFTER enrichment (styles + images + backgrounds)
    component_model = create_component_model(component_model_dict)

    # --------------------------------------------------------------------- #
    # STEP 6: PARALLEL GENERATION (RN CODE + PREVIEW)
    # --------------------------------------------------------------------- #

    print("\n⚡ [STEP 6] Running RN Code + Preview Generation in PARALLEL...")

    json_truth = component_model.to_dict()

    async def generate_rn_task():
        try:
            print("🔧 [RN CONVERTER] Generating React Native code...")
            rn_files_inner = await generate_react_native_from_json(json_truth)
            print(
                f"✅ [RN CONVERTER] Generated {len(rn_files_inner)} React Native files"
            )
            return rn_files_inner
        except Exception as e:
            print(f"❌ [RN CONVERTER] React Native generation failed: {e}")
            raise

    async def generate_preview_task():
        try:
            print("🎨 [PREVIEW GENERATOR] Generating enhanced preview...")
            web_preview_inner = await generate_preview_from_json(json_truth)
            print("✅ [PREVIEW GENERATOR] Enhanced preview generated")
            return web_preview_inner
        except Exception as e:
            print(
                f"⚠️ [PREVIEW GENERATOR] Enhancement failed: {e} - using baseline"
            )
            try:
                from Services.preview_adapter import PreviewAdapter

                return PreviewAdapter.to_web_preview(json_truth)
            except Exception:
                return json_truth

    try:
        rn_files, web_preview = await asyncio.gather(
            generate_rn_task(),
            generate_preview_task(),
            return_exceptions=True,
        )

        if isinstance(rn_files, Exception):
            return JSONResponse(
                {
                    "error": f"React Native code generation failed: {str(rn_files)}"
                },
                status_code=500,
            )

        if isinstance(web_preview, Exception):
            print(f"⚠️ [PREVIEW] Using fallback preview due to: {web_preview}")
            web_preview = json_truth

    except Exception as e:
        print(f"❌ Parallel processing failed: {e}")
        return JSONResponse(
            {"error": f"Code generation failed: {e}"},
            status_code=500,
        )

    # --------------------------------------------------------------------- #
    # STEP 7: ASSET PROMPTS
    # --------------------------------------------------------------------- #

    asset_prompts = await generate_asset_prompts(
        [comp for screen in screens for comp in screen.get("components", [])]
    )

    # --------------------------------------------------------------------- #
    # 🆕 STEP 8: DEDUCT CREDITS AFTER GENERATION
    # --------------------------------------------------------------------- #

    print("\n💳 [STEP 8] Deducting credits...")
    deduction_result = await deduct_credits_after_generation(user_id)

    if not deduction_result.get("success", False):
        print(f"⚠️ Credit deduction warning: {deduction_result.get('error')}")

    # --------------------------------------------------------------------- #
    # 🆕 STEP 9: TOKEN / CREDIT USAGE SUMMARY
    # --------------------------------------------------------------------- #

    usage_summary = token_tracker.get_summary()

    print("\n✅ Pipeline Complete!")
    print(
        f"   📝 API 0 (Refiner): "
        f"{'Applied' if refinement_result['refinement_applied'] else
                'Skipped'}"
    )
    print(f"   🎯 API 1 (Intent): {len(screens)} screens detected")
    print(f"   🧩 API 2 (Component): {len(all_components)} components generated")
    print("   🖼️  IMAGE ENRICHMENT: ✅ Dynamic Unsplash URLs added")
    print("   🎨 API 3 (Background): Dynamic backgrounds added")
    print("   🎨 Preview: Enhanced with enriched images ✅")
    print(f"   🔧 RN Converter: {len(rn_files)} files created")
    print(f"   📊 Total tokens: {usage_summary['total_tokens']:,}")
    print(f"   💳 Credits used: {usage_summary['credits_used']:.4f}")
    print(f"   💰 Estimated cost: ${usage_summary['estimated_cost']:.6f}")

    return {
        "refinement": refinement_result,
        "component_model": json_truth,
        "react_native_code": rn_files,
        "web_preview": web_preview,
        "platform": "react-native",
        "asset_prompts": asset_prompts,
        "intent": intent_obj,
        "stats": {
            "screens": len(screens),
            "components": len(all_components),
            "screen_type": screen_type,
            "files_generated": len(rn_files),
            "total_code_size": sum(len(content) for content in rn_files.values()),
            "component_distribution": {
                name: len(screen_component_map[name]) for name in screen_names
            },
            "backgrounds_generated": True,
            "images_enriched": True,
            "preview_enhanced": True,
        },
        # 🆕 Credit & token usage stats
        "usage": {
            "tokens": usage_summary,
            "credits": deduction_result,
            "estimated_tokens": estimated_tokens,
        },
    }


# ============================================================================ #
# EXPORT ENDPOINTS
# ============================================================================ #


@app.post("/export/react-native")
async def export_react_native(request: Request):
    """Export React Native files as ZIP archive."""
    body = await request.json()
    rn_files = body.get("react_native_code", {})

    if not rn_files:
        return JSONResponse(
            {"error": "No React Native code provided"},
            status_code=400,
        )

    try:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filename, content in rn_files.items():
                zip_file.writestr(filename, content)

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=react_native_app.zip"
            },
        )

    except Exception as e:
        return JSONResponse(
            {"error": f"Export failed: {str(e)}"},
            status_code=500,
        )

@app.get("/tier/status")
async def tier_system_status():
    """Get tier system status and statistics"""
    try:
        free_tier_count = await TierManager.get_free_tier_count()
        can_add = await TierManager.can_add_free_tier_user()
        
        # Get tier distribution
        from db.database import Database
        db = Database.get_db()
        users_collection = db["users"]
        
        tier_distribution = {}
        for tier in ["free", "limited", "basic", "pro", "premium"]:
            count = await users_collection.count_documents({"tier": tier})
            tier_distribution[tier] = count
        
        return {
            "status": "operational",
            "free_tier": {
                "current_users": free_tier_count,
                "max_users": 20,
                "available_slots": 20 - free_tier_count,
                "can_add_new": can_add
            },
            "tier_distribution": tier_distribution,
            "total_users": sum(tier_distribution.values())
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get tier status: {str(e)}"},
            status_code=500
        )


@app.post("/admin/run-background-jobs")
async def run_background_jobs_manually():
    """
    Admin endpoint: Manually trigger background jobs.
    Useful for testing or manual runs.
    
    TODO: Add API key authentication in production!
    """
    try:
        from Services.background_jobs import run_all_jobs_now
        
        results = await run_all_jobs_now()
        
        return {
            "success": True,
            "results": results,
            "message": "Background jobs executed successfully"
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Background jobs failed: {str(e)}"},
            status_code=500
        )



# ============================================================================ #
# UTILITY ENDPOINTS
# ============================================================================ #


@app.get("/refiner/stats")
async def get_refiner_stats():
    """Get prompt refiner statistics."""
    return refiner_stats.get_stats()


@app.post("/refine")
async def refine_endpoint(request: Request):
    """Standalone prompt refinement endpoint."""
    body = await request.json()
    prompt = body.get("prompt", "")

    if not prompt:
        return JSONResponse({"error": "Missing prompt"}, status_code=400)

    result = await refine_prompt(prompt)
    refiner_stats.record(result)
    return result


@app.post("/test/backgrounds")
async def test_backgrounds(request: Request):
    """Test background generation."""
    body = await request.json()

    screen_type = body.get("screen_type", "auth")
    design_style = body.get("design_style", "modern")
    theme = body.get("theme", {"primary": "#0D9488", "background": "#F7FAFC"})

    test_screens = [
        {"name": "Screen1", "components": []},
        {"name": "Screen2", "components": []},
    ]

    design_strategy = {
        "screen_type": screen_type,
        "design_style": design_style,
    }

    try:
        enriched_screens = await generate_backgrounds(
            test_screens,
            theme,
            design_strategy,
        )

        return {
            "success": True,
            "screens": enriched_screens,
            "config": {
                "screen_type": screen_type,
                "design_style": design_style,
                "api_used": "deepseek-v3",
            },
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Background generation failed: {str(e)}"},
            status_code=500,
        )
# ============================================================================ #
# 🖼️ DIRECT IMAGE UPDATE HELPERS (for fast image-only edits)
# ============================================================================ #

def is_image_only_edit(edit_prompt: str) -> bool:
    """Detect if edit request is only about images."""
    prompt_lower = edit_prompt.lower()
    
    # Image keywords
    image_keywords = ['image', 'images', 'picture', 'pictures', 'photo', 'photos', 'illustration', 'illustrations']
    has_image_keyword = any(kw in prompt_lower for kw in image_keywords)
    
    # Structural keywords (indicates NOT image-only)
    structural_keywords = ['add screen', 'remove screen', 'new screen', 'delete screen', 'add component', 'add button', 'change color', 'change button']
    has_structural = any(kw in prompt_lower for kw in structural_keywords)
    
    return has_image_keyword and not has_structural

def extract_image_context(edit_prompt: str) -> str:
    """Extract business/theme context from edit prompt."""
    from Services.pexels_image_service import PexelsQueryBuilder
    return PexelsQueryBuilder._extract_context_from_prompt(edit_prompt)

async def update_images_directly(component_model: Dict[str, Any], user_context: str) -> Dict[str, Any]:
    """Update all images in component model using Pexels."""
    updated_model = await enrich_layout_with_pexels(component_model, user_prompt=user_context)
    return updated_model

# ============================================================================ #
# EDIT ENDPOINT
# ============================================================================ #

# backend/main.py - Enhanced Edit Endpoint with Debugging
# Add this updated version of the edit endpoint to your main.py

@app.post("/edit-component-model")
async def edit_component_model(request: Request):
    """
    Apply conversational edits to component model.
    ✅ ENHANCED: Better debugging and response validation
    """
    
    body = await request.json()
    
    session_id = body.get("session_id")
    edit_prompt = body.get("prompt", "").strip()
    user_id = body.get("user_id")
    
    # Validation
    if not session_id:
        return JSONResponse(
            {"error": "Missing session_id"},
            status_code=400
        )
    
    if not edit_prompt:
        return JSONResponse(
            {"error": "Missing edit prompt"},
            status_code=400
        )
    
    if not user_id:
        return JSONResponse(
            {"error": "Missing user_id - authentication required"},
            status_code=401
        )
    
    # Get session using helper function
    session = await get_editing_session(session_id)
    
    if not session:
        return JSONResponse(
            {"error": "Session not found or expired"},
            status_code=404
        )
    
    # Verify ownership
    if session["user_id"] != user_id:
        return JSONResponse(
            {"error": "Unauthorized - session belongs to different user"},
            status_code=403
        )
    
    print(f"\n🔄 [EDIT] Session: {session_id}")
    print(f"   User: {user_id}")
    print(f"   Edit #{session['edit_count'] + 1}: {edit_prompt[:80]}...")
    
    # -------------------------------------------------------------------- #
    # STEP 1: CHECK CREDITS
    # -------------------------------------------------------------------- #
    
    estimated_edit_tokens = 3000
    has_credits = await check_user_credits(user_id, estimated_edit_tokens)
    
    if not has_credits:
        return JSONResponse(
            {
                "error": "Insufficient credits for edit",
                "details": {
                    "required_credits": estimated_edit_tokens / 70_000,
                    "message": "Edits require minimal credits. Please top up."
                }
            },
            status_code=402
        )
    
    # Reset token tracker
    token_tracker.reset()
    
    # -------------------------------------------------------------------- #
    # 🆕 STEP 1.5: CHECK IF IMAGE-ONLY EDIT (FAST PATH)
    # -------------------------------------------------------------------- #
    
    if is_image_only_edit(edit_prompt):
        print("🖼️  [EDIT] Detected image-only edit - using direct Pexels update")
        
        # Extract context from edit prompt
        context = extract_image_context(edit_prompt)
        print(f"   Context extracted: '{context}'")
        
        try:
            current_model = session["component_model"]
            
            # Update images directly using Pexels (FAST!)
            print("   🔄 Updating images with Pexels...")
            updated_model = await update_images_directly(current_model, context)
            
            # Regenerate preview
            print("   🎨 Regenerating preview...")
            from Services.preview_adapter import PreviewAdapter
            web_preview = PreviewAdapter.to_web_preview(updated_model)
            
            # Update session with correct parameters
            await session_manager.update_session(
                session_id=session_id,
                new_component_model=updated_model,
                user_message=edit_prompt,
                assistant_response=f"Updated all images to {context} theme using Pexels",
                tokens_used=0,  # No LLM tokens used for direct update
                web_preview=web_preview
            )
            
            print(f"✅ [EDIT] Images updated in ~2 seconds (bypassed Gemini)")
            print(f"   Edit count: {session['edit_count']}")
            
            # ✅ ENSURE HISTORY IS UPDATED EVEN FOR DIRECT UPDATES
            # Regenerate RN code even for direct image updates to keep consistency
            from Services.preview_to_react_native import PreviewToReactNativeConverter
            converter = PreviewToReactNativeConverter(updated_model)
            react_native_code = converter.convert()

            await session_manager.update_session(
                session_id=session_id,
                new_component_model=updated_model,
                user_message=edit_prompt,
                assistant_response=f"Images updated to {context} theme (Direct Update)",
                tokens_used=0,
                web_preview=web_preview,
                react_native_code=react_native_code
            )

            return {
                "component_model": updated_model,
                "web_preview": web_preview,
                "react_native_code": react_native_code,
                "message": f"Images updated to {context} theme",
                "edit_type": "image_only",
                "bypassed_llm": True
            }
            
        except Exception as e:
            print(f"❌ [EDIT] Direct image update failed: {e}")
            import traceback
            traceback.print_exc()
            # Fall through to normal Gemini flow
            print("   ⚠️  Falling back to Gemini flow...")
    
    # -------------------------------------------------------------------- #
    # STEP 2: BUILD CONTEXT-AWARE PROMPT (for non-image edits)
    # -------------------------------------------------------------------- #
    
    current_model = session["component_model"]
    
    print(f"📊 [EDIT] Current model stats:")
    print(f"   Screens: {len(current_model.get('screens', []))}")
    print(f"   Theme: {current_model.get('theme', {}).get('primary', 'N/A')}")
    
    # Get recent conversation history
    conversation_history = await session_manager.get_conversation_history(
        session_id,
        last_n_exchanges=3
    )
    
    system_prompt = """You are a professional UI component editor for mobile apps.

TASK: Modify the provided component model based on user's edit request.

RULES:
1. PRESERVE structure - only change what's requested
2. Maintain component IDs and screen assignments
3. Keep all existing props unless explicitly changing them
4. Return COMPLETE component model, not just changes
5. Output ONLY valid JSON, no markdown, no explanations

INPUT FORMAT:
{
  "screens": [...],
  "theme": {...},
  "tokens": {...}
}

OUTPUT FORMAT:
Same structure as input, with requested modifications applied.

EXAMPLES OF EDITS:
- "Change login button to green" → Update button's gradient/color prop
- "Add forgot password link" → Insert LinkButton component
- "Make header larger" → Increase title size in props
- "Change screen background to blue" → Update theme.background
- "Remove the subtitle" → Remove subtitle prop or component

CRITICAL: Return the FULL component model JSON, not a diff."""

    # Build context
    context_messages = []
    
    # Add conversation history
    for msg in conversation_history:
        context_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current edit request with full model
    edit_context = f"""Current Component Model:
{json.dumps(current_model, indent=2)}

User Edit Request:
{edit_prompt}

Return the complete updated component model as JSON."""
    
    # -------------------------------------------------------------------- #
    # STEP 3: CALL GEMINI API
    # -------------------------------------------------------------------- #
    
    try:
        print("🤖 [EDIT] Calling Gemini for component modification...")
        
        response_text = await asyncio.wait_for(
            send_chat(
                edit_context,
                route="component",
                timeout=25
            ),
            timeout=30
        )
        
        print(f"✅ [EDIT] Gemini response received ({len(response_text)} chars)")
        print(f"📝 [EDIT] First 200 chars: {response_text[:200]}...")
        
        # Parse response
        updated_model = _safe_json_loads(response_text, current_model)
        
        if not isinstance(updated_model, dict):
            print("⚠️ [EDIT] Invalid response format, using fallback")
            updated_model = current_model
        
        # Validate structure
        if "screens" not in updated_model:
            print("⚠️ [EDIT] Missing screens in response")
            updated_model = current_model
        
        print(f"✅ [EDIT] Updated model validated:")
        print(f"   Screens: {len(updated_model.get('screens', []))}")
        print(f"   Theme: {updated_model.get('theme', {}).get('primary', 'N/A')}")
        
    except asyncio.TimeoutError:
        print("⏰ [EDIT] Gemini timeout - using original model")
        return JSONResponse(
            {"error": "Edit request timed out. Please try again."},
            status_code=504
        )
    
    except Exception as e:
        print(f"❌ [EDIT] Error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Edit failed: {str(e)}"},
            status_code=500
        )
    
    # -------------------------------------------------------------------- #
    # STEP 4: REGENERATE PREVIEW
    # -------------------------------------------------------------------- #
    
    print("🎨 [EDIT] Regenerating preview...")
    
    try:
        from Services.preview_adapter import PreviewAdapter
        web_preview = PreviewAdapter.to_web_preview(updated_model)
        
        print(f"✅ [EDIT] Preview generated:")
        print(f"   Screens: {len(web_preview.get('screens', []))}")
        
    except Exception as e:
        print(f"⚠️ [EDIT] Preview generation failed: {e}")
        import traceback
        traceback.print_exc()
        web_preview = updated_model
    
    # -------------------------------------------------------------------- #
    # STEP 4.5: REGENERATE REACT NATIVE CODE
    # -------------------------------------------------------------------- #
    
    print("🔧 [EDIT] Regenerating React Native code...")
    try:
        from Services.preview_to_react_native import PreviewToReactNativeConverter
        converter = PreviewToReactNativeConverter(updated_model)
        react_native_code = converter.convert()
        print(f"✅ [EDIT] RN code regenerated ({len(react_native_code)} files)")
    except Exception as e:
        print(f"⚠️ [EDIT] RN conversion failed during edit: {e}")
        import traceback
        traceback.print_exc()
        react_native_code = {}

    # -------------------------------------------------------------------- #
    # STEP 5: UPDATE SESSION & DEDUCT CREDITS
    # -------------------------------------------------------------------- #
    
    # Get token usage
    usage_summary = token_tracker.get_summary()
    tokens_used = usage_summary.get("total_tokens", 0)
    
    # Update session
    await session_manager.update_session(
        session_id,
        updated_model,
        edit_prompt,
        "Applied changes successfully",
        tokens_used=tokens_used,
        web_preview=web_preview,
        react_native_code=react_native_code
    )
    
    # Deduct credits
    deduction_result = await deduct_credits_after_generation(user_id)
    
    print(f"✅ [EDIT] Complete!")
    print(f"   Tokens used: {usage_summary['total_tokens']:,}")
    print(f"   Credits: {usage_summary['credits_used']:.4f}")
    print(f"   Edit count: {session['edit_count'] + 1}")
    
    # -------------------------------------------------------------------- #
    # STEP 6: RETURN RESPONSE WITH DEBUGGING INFO
    # -------------------------------------------------------------------- #
    
    response_data = {
        "success": True,
        "session_id": session_id,
        "component_model": updated_model,
        "web_preview": web_preview,
        "react_native_code": react_native_code,
        "edit_count": session["edit_count"] + 1,
        "usage": {
            "tokens": usage_summary,
            "credits": deduction_result
        },
        "message": "Changes applied successfully",
        # ✅ DEBUG INFO
        "debug": {
            "screens_count": len(updated_model.get("screens", [])),
            "theme_primary": updated_model.get("theme", {}).get("primary"),
            "preview_screens_count": len(web_preview.get("screens", [])),
            "model_has_screens": "screens" in updated_model,
            "preview_has_screens": "screens" in web_preview
        }
    }
    
    print(f"📤 [EDIT] Sending response:")
    print(f"   Component model screens: {response_data['debug']['screens_count']}")
    print(f"   Preview screens: {response_data['debug']['preview_screens_count']}")
    
    return response_data


# ============================================================================ #
# ✅ SESSION CREATION ENDPOINT
# ============================================================================ #

@app.post("/create-edit-session")
async def create_edit_session_endpoint(request: Request):
    """
    Create a new editing session from generated component model.
    Called automatically after successful generation.
    """
    
    body = await request.json()
    
    component_model = body.get("component_model")
    web_preview = body.get("web_preview")
    react_native_code = body.get("react_native_code")
    user_id = body.get("user_id")
    
    if not component_model:
        return JSONResponse(
            {"error": "Missing component_model"},
            status_code=400
        )
    
    if not user_id:
        return JSONResponse(
            {"error": "Missing user_id"},
            status_code=401
        )
    
    # Use helper function
    session_id = await create_editing_session(
        component_model, 
        user_id, 
        web_preview=web_preview, 
        react_native_code=react_native_code
    )
    
    return {
        "session_id": session_id,
        "message": "Edit session created. You can now make conversational edits.",
        "expires_in": "2 hours"
    }


# ============================================================================ #
# ✅ SESSION STATUS ENDPOINT
# ============================================================================ #

@app.get("/edit-session/{session_id}")
async def get_edit_session_status(session_id: str):
    """Get current session status and statistics"""
    
    session = await get_editing_session(session_id)
    
    if not session:
        return JSONResponse(
            {"error": "Session not found or expired"},
            status_code=404
        )
    
    return {
        "session_id": session_id,
        "user_id": session["user_id"],
        "edit_count": session["edit_count"],
        "total_tokens_used": session["total_tokens_used"],
        "created_at": session["created_at"].isoformat(),
        "last_activity": session["last_activity"].isoformat(),
        "conversation_history": session.get("conversation_history", []),
        "component_model": session.get("component_model"),
        "web_preview": session.get("web_preview"),
        "react_native_code": session.get("react_native_code"),
        "metadata": session["metadata"]
    }

@app.get("/conversations/list/{user_id}")
async def list_user_conversations(user_id: str):
    """List all persistent conversations for a user."""
    conversations = await session_manager.get_user_sessions(user_id)
    return {"conversations": conversations}

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: str):
    """Delete a conversation history."""
    # Verify ownership (simplified for now)
    session = await session_manager.get_session(conversation_id)
    if not session or session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized or not found")
        
    await session_manager.delete_session(conversation_id)
    return {"success": True}


# ============================================================================ #
# ✅ GET USER'S SESSIONS
# ============================================================================ #

@app.get("/edit-sessions/user/{user_id}")
async def get_user_edit_sessions(user_id: str):
    """Get all active editing sessions for a user"""
    
    sessions = session_manager.get_user_sessions(user_id)
    
    return {
        "user_id": user_id,
        "active_sessions": len(sessions),
        "sessions": sessions
    }


# ============================================================================ #
# ✅ DELETE SESSION ENDPOINT
# ============================================================================ #

@app.delete("/edit-session/{session_id}")
async def delete_edit_session(session_id: str, request: Request):
    """Manually delete an editing session"""
    
    body = await request.json()
    user_id = body.get("user_id")
    
    if not user_id:
        return JSONResponse(
            {"error": "Missing user_id"},
            status_code=401
        )
    
    # Verify ownership before deletion
    session = await get_editing_session(session_id)
    
    if not session:
        return JSONResponse(
            {"error": "Session not found"},
            status_code=404
        )
    
    if session["user_id"] != user_id:
        return JSONResponse(
            {"error": "Unauthorized"},
            status_code=403
        )
    
    success = await session_manager.delete_session(session_id)
    
    if success:
        return {
            "success": True,
            "message": "Session deleted successfully"
        }
    else:
        return JSONResponse(
            {"error": "Failed to delete session"},
            status_code=500
        )


# ============================================================================ #
# ✅ SESSION MANAGER STATS ENDPOINT
# ============================================================================ #

@app.get("/edit-sessions/stats")
async def get_session_manager_stats():
    """Get overall session manager statistics"""
    
    stats = session_manager.get_stats()
    
    return {
        "status": "operational",
        "statistics": stats,
        "active_sessions": len(session_manager)
    }

@app.get("/health")
async def health_check():
    """Health check with session manager status"""
    
    # Health check for the database
    from db.database import Database
    
    db_healthy = await Database.health_check()
    
    try:
        free_tier_count = await TierManager.get_free_tier_count()
        tier_system_healthy = True
    except:
        free_tier_count = "unknown"
        tier_system_healthy = False

    # Add session manager stats
    active_sessions = len(session_manager)
    session_stats = session_manager.get_stats()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "platform": "react-native",
        "architecture": "5-API + Deterministic Converters + Tier System",
        "version": "2.7.0",
        "database": "connected" if db_healthy else "disconnected",
        "tier_system": "operational" if tier_system_healthy else "degraded",
        "free_tier_status": f"{free_tier_count}/20 slots",
        "features": {
            "intelligent_screen_assignment": True,
            "intelligent_nesting": True,
            "dynamic_backgrounds": True,
            "dynamic_images": True,
            "gemini_enhanced_preview": True,
            "tier_system": True,
            "free_tier_management": True,
            "automatic_credit_resets": True,
            "stripe_payments": True,
            "token_tracking": True,
            "background_jobs": True,
            "screen_types": [
                "auth",
                "ecommerce",
                "dashboard",
                "social",
                "onboarding",
                "settings",
            ],
            "tiers": ["free", "limited", "basic", "pro", "premium"],
            "deterministic_generation": True,
        },
        "edit_sessions": {
            "active": active_sessions,
            "total_edits": session_stats.get("total_edits", 0),
            "timeout": f"{session_stats.get('timeout_hours', 2)}h",
            "avg_edits_per_session": session_stats.get("avg_edits_per_session", 0)
        },
    }


@app.get("/")
def root():
    """Root endpoint with API documentation"""
    return {
        "message": "✅ UI Pipeline v2.6 - React Native Edition with Tier System",
        "platform": "React Native",
        "version": "2.6.0",
        "architecture": {
            "api_0": "Prompt Refiner (Groq)",
            "api_1": "Intent Extractor (DeepSeek v3)",
            "api_2": "Component Generator (DeepSeek v3)",
            "api_3": "Background Generator (DeepSeek v3)",
            "assembly": "Component-to-Screen Assignment (Python)",
            "nesting": "Screen-type-aware Nesting (Python)",
            "image_enrichment": "Dynamic Image URL Generator (Python)",
            "rn_converter": "React Native Code Generator (Python)",
            "preview_adapter": "Web Preview Generator (Python)",
            "tier_system": "Free tier + paid plans with auto-management",
            "background_jobs": "Automated credit resets & tier downgrades",
        },
        "endpoints": {
            "POST /generate_pipeline": "Main pipeline (requires user_id & tier with credits)",
            "POST /export/react-native": "Export React Native code as ZIP",
            "POST /refine": "Standalone prompt refinement",
            "POST /test/backgrounds": "Test background generation",
            "GET /refiner/stats": "Prompt refiner statistics",
            
            "# Payment & Tier Endpoints": "",
            "GET /payment/balance/{user_id}": "Get user credit balance",
            "GET /payment/tier/{user_id}": "Get user tier information",
            "GET /payment/packages": "Get available credit packages",
            "GET /payment/free-tier/status": "Check free tier availability",
            "POST /payment/create-checkout": "Create Stripe checkout session",
            "POST /payment/webhook": "Stripe webhook handler",
            
            "# Admin Endpoints (Background Jobs)": "",
            "POST /payment/admin/reset-free-tier-credits": "Reset free tier credits (cron)",
            "POST /payment/admin/downgrade-expired-tiers": "Downgrade expired tiers (cron)",
            "POST /admin/run-background-jobs": "Manually run all background jobs",
            
            "# Status Endpoints": "",
            "GET /tier/status": "Tier system status and statistics",
            "GET /health": "Health check with tier info",
            "GET /": "This documentation",
        },
        "tier_system": {
            "free": {
                "credits": 5,
                "price": 0,
                "duration": "30 days (monthly reset)",
                "limit": "20 users max",
                "features": ["5 credits/month", "Basic generation", "Community support"]
            },
            "basic": {
                "credits": 142,
                "price": 4.99,
                "duration": "30 days",
                "features": ["142 credits", "10M tokens", "Email support"]
            },
            "pro": {
                "credits": 284,
                "price": 9.99,
                "duration": "30 days",
                "features": ["284 credits", "20M tokens", "Priority generation"]
            },
            "premium": {
                "credits": 568,
                "price": 19.99,
                "duration": "30 days",
                "features": ["568 credits", "40M tokens", "Advanced features"]
            }
        },
        "new_in_v2_6": [
            "🎯 Free tier system (max 20 users)",
            "🔄 Monthly credit resets for free tier (5 credits every 30 days)",
            "⏰ Automatic tier downgrades after plan expiration",
            "📊 Comprehensive tier management",
            "🎁 New users auto-assigned to free tier (if available)",
            "🔧 Background jobs for automated maintenance",
            "📈 Tier status and distribution tracking"
        ],
        "background_jobs": {
            "credit_reset": "Daily at 00:00 UTC - Check and reset free tier credits (if 30 days passed)",
            "tier_downgrade": "Daily at 01:00 UTC - Downgrade expired paid tiers"
        },
        "features": [
            "✅ Intelligent component nesting (screen-type aware)",
            "✅ Deterministic code generation (no LLM hallucinations)",
            "✅ 100% component accuracy (direct mapping)",
            "✅ Parallel processing (fast)",
            "✅ Production-ready React Native output",
            "✅ Smart prompt enhancement",
            "✅ 40+ UI components supported",
            "✅ Auto-detects: Auth, E-commerce, Dashboard, Social, Onboarding, Settings",
            "✅ 🎨 Dynamic backgrounds per screen",
            "✅ 🖼️  Dynamic image enrichment per layout",
            "✅ 🎯 Complete tier management system",
            "✅ 🔄 Automated credit & tier management"
        ],
    }


# ============================================================================ #
# ERROR HANDLERS
# ============================================================================ #


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    print(f"❌ Unhandled exception: {exc}")
    import traceback

    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__,
        },
    )


# ============================================================================ #
# STARTUP/SHUTDOWN EVENTS
# ============================================================================ #
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db.database import Database

@app.on_event("startup")
async def startup_with_session_cleanup():
    """Startup event - includes session cleanup scheduler"""

    # Connect to MongoDB
    print("\n🔵 Connecting to MongoDB...")
    connection_success = await connect_to_mongo()

    # Verify connection
    if connection_success and await Database.health_check():  # ✅ ADD await
        print("✅ MongoDB Connected Successfully!")
        print(f"   Database: {os.getenv('MONGODB_DB_NAME')}")
        print(f"   Cluster: {os.getenv('MONGODB_CLUSTER', 'Unknown')}")
    else:
        print("❌ MongoDB Connection FAILED!")
        print("   ⚠️  Authentication & payment endpoints may not work!")
        print("   Check your MONGODB_URL in .env file")
        print("   The application will continue but those features are disabled.")
    
    # 🆕 Setup background jobs for tier management
    if connection_success:
        try:
            setup_background_jobs()
            print("✅ Background jobs scheduler started")
            
            # Show free tier status
            free_tier_count = await TierManager.get_free_tier_count()
            print(f"📊 Free tier: {free_tier_count}/20 slots used")
        except Exception as e:
            print(f"⚠️  Warning: Background jobs setup failed: {e}")

    print()

    # ✅ START SESSION CLEANUP SCHEDULER
    try:
        scheduler = AsyncIOScheduler()
        
        # Cleanup expired sessions every hour
        scheduler.add_job(
            session_manager.cleanup_expired_sessions,
            'interval',
            hours=1,
            id='session_cleanup'
        )
        
        scheduler.start()
        
        print("✅ Session cleanup scheduler started (runs every hour)")
        print(f"   Timeout: {session_manager.session_timeout.total_seconds() / 3600}h")
        
    except Exception as e:
        print(f"⚠️  Warning: Session cleanup scheduler failed: {e}")
    
    # Print session manager info
    print(f"📊 SessionManager ready - Active sessions: {len(session_manager)}")

    # Print general application info
    print("\n" + "=" * 70)
    print("🚀 UI PIPELINE v2.6 - REACT NATIVE EDITION (WITH TIER SYSTEM)")
    print("=" * 70)
    print("Platform: React Native")
    print("Architecture: 4 LLM APIs + Deterministic Converters + Tier System")
    print("")
    print("🤖 LLM API Calls:")
    print("   API 0: Prompt Refiner (Groq)")
    print("   API 1: Intent Extractor (Gemini-2.0-Flash)")
    print("   API 2: Component Generator (Gemini-2.0-Flash)")
    print("   API 3: Background Generator (Gemini-2.0-Flash)")
    print("")
    print("🔧 Deterministic Converters (no LLM):")
    print("   - React Native Code Generator (Python)")
    print("   - Web Preview Adapter (Python)")
    print("   - Dynamic Image URL Generator (Python)  🖼️")
    print("")
    print("🎯 TIER SYSTEM:")
    print("   FREE TIER:")
    print("      • 5 credits (resets every 30 days)")
    print("      • Limited to 20 users max")
    print("      • Basic UI generation")
    print("")
    print("   BASIC PLAN ($4.99/month):")
    print("      • 142 credits (30 days)")
    print("      • 10M tokens")
    print("      • Email support")
    print("")
    print("   PRO PLAN ($9.99/month):")
    print("      • 284 credits (30 days)")
    print("      • 20M tokens")
    print("      • Priority generation")
    print("")
    print("   PREMIUM PLAN ($19.99/month):")
    print("      • 568 credits (30 days)")
    print("      • 40M tokens")
    print("      • Advanced features")
    print("")
    print("🔄 BACKGROUND JOBS:")
    print("   • Daily check (00:00 UTC) - Reset free tier credits if 30 days passed")
    print("   • Daily tier expiration check (01:00 UTC) - Paid tier downgrades")
    print("")
    print("🆕 NEW FEATURES (v2.6):")
    print("   🎯 Free tier system (20 user limit)")
    print("   🔄 Automatic credit resets (daily)")
    print("   ⏰ Automatic tier downgrades after expiration")
    print("   📊 Comprehensive tier management")
    print("   🎁 New users start with free tier (if available)")
    print("")
    print("💳 PAYMENT FEATURES (v2.5):")
    print("   • Stripe payment integration")
    print("   • Token usage tracking")
    print("   • Pre-generation credit checks")
    print("   • Automatic credit deduction")
    print("")
    print("🎨 PREVIOUS FEATURES:")
    print("   • Dynamic background generation")
    print("   • Image enrichment")
    print("   • Multi-screen intelligent routing")
    print("   • Component-to-screen assignment")
    print("=" * 70 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event - close MongoDB connection and stop background jobs"""
    # 🆕 Stop background jobs
    try:
        shutdown_background_jobs()
        print("✅ Background jobs stopped")
    except Exception as e:
        print(f"⚠️  Warning: Background jobs shutdown failed: {e}")
    
    # Close MongoDB
    await close_mongo_connection()
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    errors = exc.errors()
    logger.error(f"❌ Validation Error: {errors}")
    
    # Format errors nicely
    error_messages = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": error_messages,
            "errors": errors,
            "message": "Validation failed. Please check your request."
        }
    )



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

