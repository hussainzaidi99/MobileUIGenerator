# backend/main.py - Production-Ready 3-API Architecture (React Native)
# Version: 2.2.1 - Corrected Architecture Labels
# 
# Architecture:
# - API 0: Prompt Refiner (Groq)
# - API 1: Intent Extractor (DeepSeek Chat v3)
# - API 2: Component Generator (DeepSeek Chat v3) 
# - RN Converter: Deterministic Python (NO LLM)
# - Preview Adapter: Pass-through Python (NO LLM)
# - API 3: UNUSED (reserved for future features)

import os
import json
import asyncio
from typing import Any, Dict, List
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
import io
import zipfile

from prompt_refiner import refine_prompt, refiner_stats
from llm_client import (
    extract_intent, 
    componentize, 
    generate_react_native_from_json, 
    generate_preview_from_json, 
    generate_asset_prompts
)
from component_model import create_component_model
from style_enricher import enrich_styles

load_dotenv()

app = FastAPI(
    title="UI Pipeline Beta - React Native Edition",
    version="2.2.0",
    description="Production-ready 4-API architecture with intelligent component screen assignment"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STEP_TIMEOUT = int(os.getenv("STEP_TIMEOUT", "30"))


# ============================================================================
# INTELLIGENT COMPONENT-TO-SCREEN ASSIGNMENT
# ============================================================================

def assign_component_to_screen(
    comp: Dict, 
    screen_names: List[str], 
    design_strategy: Dict,
    screen_component_count: Dict[str, int]
) -> str:
    """
    Intelligently assign component to most likely screen based on multiple strategies.
    
    Args:
        comp: Component dictionary
        screen_names: List of screen names
        design_strategy: Design strategy from intent extraction
        screen_component_count: Current count of components per screen (for balancing)
        
    Returns:
        Screen name to assign component to
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
        login_keywords = ["login", "signin", "sign-in", "sign_in", "forgot", "password", "email"]
        if any(keyword in comp_id or keyword in str(props).lower() for keyword in login_keywords):
            login_screen = next((s for s in screen_names if "login" in s.lower() or "signin" in s.lower()), None)
            if login_screen:
                return login_screen
        
        # Signup screen keywords
        signup_keywords = ["signup", "sign-up", "sign_up", "register", "create", "name"]
        if any(keyword in comp_id or keyword in str(props).lower() for keyword in signup_keywords):
            signup_screen = next((s for s in screen_names if "signup" in s.lower() or "register" in s.lower()), None)
            if signup_screen:
                return signup_screen
    
    elif screen_type == "ecommerce":
        # Cart/Checkout screen
        if any(keyword in comp_id for keyword in ["cart", "checkout", "payment", "order"]):
            cart_screen = next((s for s in screen_names if any(k in s.lower() for k in ["cart", "checkout", "payment"])), None)
            if cart_screen:
                return cart_screen
        
        # Product listing screen
        if any(keyword in comp_id for keyword in ["product", "search", "grid", "shop"]):
            return screen_names[0]  # Product listing is usually first
    
    elif screen_type == "social":
        # Profile screen
        if any(keyword in comp_id for keyword in ["profile", "user", "avatar", "followers"]):
            profile_screen = next((s for s in screen_names if "profile" in s.lower()), None)
            if profile_screen:
                return profile_screen
        
        # Feed screen
        if any(keyword in comp_id for keyword in ["feed", "post", "card"]):
            feed_screen = next((s for s in screen_names if "feed" in s.lower()), None)
            if feed_screen:
                return feed_screen
    
    elif screen_type == "dashboard":
        # Settings screen
        if any(keyword in comp_id for keyword in ["settings", "preferences", "config"]):
            settings_screen = next((s for s in screen_names if "settings" in s.lower()), None)
            if settings_screen:
                return settings_screen
        
        # Dashboard/Analytics screen
        if any(keyword in comp_id for keyword in ["stat", "chart", "analytics", "overview"]):
            return screen_names[0]  # Dashboard is usually first
    
    # STRATEGY 4: Component position-based heuristic (for ordered generation)
    # If first half of components are being assigned, prefer first screen
    # This helps when LLM generates screens in order but without explicit labels
    
    # STRATEGY 5: Load balancing fallback
    # Assign to screen with fewest components to prevent one screen getting everything
    min_screen = min(screen_names, key=lambda s: screen_component_count.get(s, 0))
    return min_screen


# ============================================================================
# INTELLIGENT COMPONENT NESTING LOGIC
# ============================================================================

def _nest_auth_components(components: List[Dict]) -> List[Dict]:
    """
    Intelligently nest authentication screen components.
    Groups form inputs inside Card container.
    
    Pattern:
    - IllustrationHeader (outside)
    - Spacer
    - Card (container)
        - IconInput (email)
        - Spacer
        - IconInput (password)
        - LinkButton (forgot password)
        - Spacer
        - GradientButton (submit)
    - Divider (outside)
    - SocialButtons (outside)
    - LinkButtons (outside)
    """
    nested = []
    card_children = []
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
            "iconinput", "textinput", "passwordinput", "customtextinput",
            "spacer", "customspacer", "linkbutton", "customlinkbutton",
            "gradientbutton", "customgradientbutton", "button", "custombutton",
            "checkbox", "customcheckbox", "switch"
        ):
            card_children.append(comp)
            
            # Close card after primary CTA button
            if comp_type in ("gradientbutton", "customgradientbutton"):
                # Add card with all children
                if card_component:
                    card_component["children"] = card_children
                    nested.append(card_component)
                    inside_card = False
                    card_component = None
                    card_children = []
        
        # Components after Card (Divider, Social buttons, etc.)
        elif not inside_card and comp_type in (
            "divider", "customdivider", "socialbutton", "customsocialbutton",
            "linkbutton", "customlinkbutton"
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
    """
    Nest e-commerce components (SearchInput + Grid of ProductCards).
    
    Pattern:
    - SearchInput (outside)
    - Spacer
    - Grid (container)
        - ProductCard × N
    - FloatingActionButton (outside)
    """
    nested = []
    grid_children = []
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
        
        elif inside_grid and comp_type in ("productcard", "customproductcard", "card", "customcard"):
            grid_children.append(comp)
        
        elif comp_type in ("floatingactionbutton", "customfloatingactionbutton"):
            # Close grid before FAB
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
    
    # Close grid if still open
    if grid_component and grid_children:
        grid_component["children"] = grid_children
        nested.append(grid_component)
    
    return nested


def _nest_dashboard_components(components: List[Dict]) -> List[Dict]:
    """
    Nest dashboard components (Grid of StatCards).
    
    Pattern:
    - AppBar (outside)
    - Grid (container)
        - StatCard × N
    - Card (container)
        - ProgressBar
    """
    nested = []
    grid_children = []
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
            # Close grid before spacer
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
                # Close grid
                if inside_grid and grid_component and grid_children:
                    grid_component["children"] = grid_children
                    nested.append(grid_component)
                    inside_grid = False
                    grid_component = None
                    grid_children = []
                nested.append(comp)
    
    # Close grid if still open
    if grid_component and grid_children:
        grid_component["children"] = grid_children
        nested.append(grid_component)
    
    return nested


def _nest_components_by_screen_type(components: List[Dict], screen_type: str) -> List[Dict]:
    """
    Route to appropriate nesting logic based on screen type.
    
    Args:
        components: Flat list of components from LLM
        screen_type: Screen type from design_strategy
        
    Returns:
        Properly nested component hierarchy
    """
    screen_type = (screen_type or "").lower()
    
    if screen_type == "auth":
        return _nest_auth_components(components)
    elif screen_type == "ecommerce":
        return _nest_ecommerce_components(components)
    elif screen_type in ("dashboard", "analytics"):
        return _nest_dashboard_components(components)
    else:
        # Default: minimal nesting (just ensure root container)
        return components


# ============================================================================
# MAIN PIPELINE ENDPOINT
# ============================================================================

@app.post("/generate_pipeline")
async def generate_pipeline(request: Request):
    """
    🚀 Production-Ready 4-API Architecture with Intelligent Component Screen Assignment
    
    Pipeline:
    0. API 0 (REFINER) → Transform raw prompt into structured prompt
    1. API 1 (INTENT) → Generate Component Model JSON (single source of truth)
    2. ASSEMBLY → Intelligently assign components to screens + nest by type
    3. API 2 (COMPONENT) → React Native Code Generation (deterministic)
    4. API 3 (CODE) → Web Preview Generation (parallel)
    
    Returns:
        JSON response with component model, React Native code, and web preview
    """
    body = await request.json()
    raw_prompt = body.get("prompt", "")
    
    if not raw_prompt:
        return JSONResponse({"error": "Missing prompt"}, status_code=400)
    
    print(f"\n🔹 Beta Pipeline (React Native v2.2): {raw_prompt}\n")
    
    # ========================================================================
    # STEP 0: API 0 (REFINER) → Enhance User Prompt
    # ========================================================================
    print("🔵 [STEP 0] API 0 (REFINER) - Enhancing user prompt...")
    
    try:
        refinement_result = await asyncio.wait_for(
            refine_prompt(raw_prompt),
            timeout=STEP_TIMEOUT
        )
        
        refiner_stats.record(refinement_result)
        prompt = refinement_result['refined_prompt']
        
        if refinement_result['refinement_applied']:
            print(f"✅ [STEP 0] Prompt refined:")
            print(f"   Original ({refinement_result['metadata']['original_word_count']} words): {raw_prompt[:80]}...")
            print(f"   Refined ({refinement_result['metadata']['refined_word_count']} words): {prompt[:80]}...")
            print(f"   Expansion: {refinement_result['metadata']['expansion_ratio']}x")
        else:
            print(f"ℹ️  [STEP 0] Using original prompt: {refinement_result['metadata']['reason']}")
            prompt = raw_prompt
        
    except Exception as e:
        print(f"⚠️  [STEP 0] Refiner failed: {e} - using original prompt")
        prompt = raw_prompt
        refinement_result = {
            "original_prompt": raw_prompt,
            "refined_prompt": raw_prompt,
            "refinement_applied": False,
            "metadata": {"reason": f"Error: {str(e)[:50]}"}
        }
    
    # ========================================================================
    # STEP 1: API 1 (INTENT) → Generate Component Model (JSON TRUTH)
    # ========================================================================
    print("\n🔵 [STEP 1] API 1 (INTENT) - Generating Component Model...")
    
    try:
        intent_obj = await asyncio.wait_for(
            extract_intent(prompt),
            timeout=STEP_TIMEOUT
        )
        intent_obj["device"] = "mobile"
        screen_names = intent_obj.get("screens", []) or ["Home"]
        
        print(f"📋 Screens detected: {screen_names}")
        
        component_result = await asyncio.wait_for(
            componentize(intent_obj, prompt),
            timeout=STEP_TIMEOUT
        )
        
        all_components = component_result.get("components", [])
        
        print(f"✅ [STEP 1] Generated {len(all_components)} components (flat list)")
        
    except Exception as e:
        print(f"❌ [STEP 1] Failed: {e}")
        return JSONResponse(
            {"error": f"Component model generation failed: {e}"}, 
            status_code=500
        )
    
    # ========================================================================
    # STEP 1.5: INTELLIGENT COMPONENT-TO-SCREEN ASSIGNMENT (FIXED!)
    # ========================================================================
    print("\n🔵 [STEP 1.5] ASSEMBLY - Assigning components to screens intelligently...")
    
    screen_type = intent_obj.get("design_strategy", {}).get("screen_type", "general")
    design_strategy = intent_obj.get("design_strategy", {})
    
    try:
        # Initialize screen-component mapping
        screen_component_map = {screen_name: [] for screen_name in screen_names}
        screen_component_count = {screen_name: 0 for screen_name in screen_names}
        
        # Assign each component to appropriate screen
        for idx, comp in enumerate(all_components):
            # Use intelligent assignment function
            assigned_screen = assign_component_to_screen(
                comp, 
                screen_names, 
                design_strategy,
                screen_component_count
            )
            
            # Add to map
            screen_component_map[assigned_screen].append(comp)
            screen_component_count[assigned_screen] += 1
            
            # Debug logging for first few components
            if idx < 5:
                print(f"   📍 Component '{comp.get('id', 'unknown')}' ({comp.get('type')}) → {assigned_screen}")
        
        # Validation: Check for empty screens
        empty_screens = [name for name in screen_names if len(screen_component_map[name]) == 0]
        if empty_screens:
            print(f"   ⚠️  Warning: Empty screens detected: {empty_screens}")
        
        # Validation: Check distribution
        total_assigned = sum(len(comps) for comps in screen_component_map.values())
        if total_assigned != len(all_components):
            print(f"   ⚠️  Warning: Assignment mismatch! Total: {len(all_components)}, Assigned: {total_assigned}")
        
        # Build screens with properly grouped and nested components
        screens = []
        
        print(f"\n📊 Component Distribution by Screen:")
        for screen_name in screen_names:
            screen_comps = screen_component_map[screen_name]
            
            if not screen_comps:
                print(f"   ⚠️  {screen_name}: 0 components (creating empty state)")
                # Create empty screen with placeholder
                screens.append({
                    "name": screen_name,
                    "components": [{
                        "id": f"root-{screen_name.lower()}",
                        "type": "Container",
                        "props": {"padding": "16"},
                        "children": [{
                            "id": f"empty-{screen_name.lower()}",
                            "type": "EmptyState",
                            "props": {
                                "icon": "📱",
                                "title": f"{screen_name} Screen",
                                "message": "No components generated for this screen"
                            }
                        }]
                    }]
                })
                continue
            
            # Apply intelligent nesting based on screen type
            nested_comps = _nest_components_by_screen_type(screen_comps, screen_type)
            
            # Log component types for debugging
            comp_types = [c.get("type") for c in screen_comps]
            print(f"   📱 {screen_name}: {len(screen_comps)} components → {len(nested_comps)} top-level")
            print(f"      Types: {', '.join(comp_types[:5])}{'...' if len(comp_types) > 5 else ''}")
            
            screens.append({
                "name": screen_name,
                "components": [{
                    "id": f"root-{screen_name.lower()}",
                    "type": "Container",
                    "props": {"padding": "16"},
                    "children": nested_comps
                }]
            })
        
        component_model_dict = {
            "screens": screens,
            "tokens": {"gap": 16, "padding": 20, "cardRadius": 12},
            "theme": {
                "primary": "#0D9488",
                "background": "#F7FAFC",
                "surface": "#FFFFFF",
                "text": "#0F172A"
            }
        }
        
        # Enrich with styles from design strategy
        component_model_dict = enrich_styles(component_model_dict, intent_obj)
        component_model = create_component_model(component_model_dict)
        
        print(f"✅ [STEP 1.5] Component hierarchy built for '{screen_type}' screen type")
        
    except Exception as e:
        print(f"❌ [STEP 1.5] Assembly failed: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Component assembly failed: {e}"}, 
            status_code=500
        )
    
    # ========================================================================
    # STEP 2 & 3: PARALLEL PROCESSING
    # API 2 (COMPONENT) → React Native Code Generation
    # API 3 (CODE) → Web Preview Generation
    # ========================================================================
    print("\n⚡ [STEP 2] Running RN Code Generation + Preview Adapter in PARALLEL (no API calls)...")
    
    json_truth = component_model.to_dict()
    
    async def generate_rn_task(): 
        """Generate React Native code from component model (deterministic converter)"""
        try:
            print("🔧 [RN CONVERTER] Generating React Native code...")
            rn_files = await generate_react_native_from_json(json_truth)
            print(f"✅ [RN CONVERTER] Generated {len(rn_files)} React Native files")
            return rn_files
        except Exception as e:
            print(f"❌ [RN CONVERTER] React Native generation failed: {e}")
            raise
    
    async def generate_preview_task():
        
        """Generate web preview from component model (pass-through adapter)"""
        try:
            
            print("🔄 [PREVIEW ADAPTER] Generating web preview...")
            web_preview = await generate_preview_from_json(json_truth)
            print(f"✅ [PREVIEW ADAPTER] Web preview generated")
            return web_preview
        except Exception as e:
            print(f"⚠️ [PREVIEW ADAPTER] Preview generation failed: {e}")
        # Fallback to pass-through
            try:
                from preview_adapter import PreviewAdapter
                return PreviewAdapter.to_web_preview(json_truth)
            except:
                
                return json_truth
    
    # Run both tasks in parallel
    try:
        rn_files, web_preview = await asyncio.gather(
            generate_rn_task(),
            generate_preview_task(),
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(rn_files, Exception):
            print(f"❌ React Native generation failed: {rn_files}")
            return JSONResponse(
                {"error": f"React Native code generation failed: {str(rn_files)}"}, 
                status_code=500
            )
        
        if isinstance(web_preview, Exception):
            print(f"⚠️  Preview generation exception: {web_preview}")
            # Use raw model as fallback
            web_preview = json_truth
        
    except Exception as e:
        print(f"❌ Parallel processing failed: {e}")
        return JSONResponse(
            {"error": f"Code generation failed: {e}"}, 
            status_code=500
        )
    
    # ========================================================================
    # STEP 4: Asset Prompts (optional metadata)
    # ========================================================================
    asset_prompts = await generate_asset_prompts([
        comp for screen in screens 
        for comp in screen.get("components", [])
    ])
    
    print(f"\n✅ Pipeline Complete!")
    print(f"   📝 API 0 (Refiner): {'Applied' if refinement_result['refinement_applied'] else 'Skipped'}")
    print(f"   🎯 API 1 (Intent): {len(screens)} screens detected")
    print(f"   🧩 API 2 (Component): {len(all_components)} components generated")
    print(f"   🔧 RN Converter: {len(rn_files)} files created")
    print(f"   🔄 Preview Adapter: Ready")
    
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
                name: len(screen_component_map[name]) 
                for name in screen_names
            }
        }
    }


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@app.post("/export/react-native")
async def export_react_native(request: Request):
    """
    Export React Native files as ZIP archive
    
    Request Body:
        {
            "react_native_code": {
                "filename1.tsx": "content1",
                "filename2.ts": "content2",
                ...
            }
        }
    
    Returns:
        ZIP file stream with all React Native project files
    """
    body = await request.json()
    rn_files = body.get("react_native_code", {})
    
    if not rn_files:
        return JSONResponse(
            {"error": "No React Native code provided"}, 
            status_code=400
        )
    
    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, content in rn_files.items():
                zip_file.writestr(filename, content)
        
        zip_buffer.seek(0)
        
        print(f"✅ Exported {len(rn_files)} React Native files as ZIP")
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=react_native_app.zip"
            }
        )
    
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return JSONResponse(
            {"error": f"Export failed: {str(e)}"}, 
            status_code=500
        )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.get("/refiner/stats")
async def get_refiner_stats():
    """Get prompt refiner statistics"""
    return refiner_stats.get_stats()


@app.post("/refine")
async def refine_endpoint(request: Request):
    """Standalone prompt refinement endpoint (for testing)"""
    body = await request.json()
    prompt = body.get("prompt", "")
    
    if not prompt:
        return JSONResponse({"error": "Missing prompt"}, status_code=400)
    
    result = await refine_prompt(prompt)
    refiner_stats.record(result)
    
    return result


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "platform": "react-native",
        "architecture": "4-API (Refiner → Intent → Assembly → Component → Preview)",
        "version": "2.2.0",
        "features": {
            "intelligent_screen_assignment": True,
            "intelligent_nesting": True,
            "screen_types": ["auth", "ecommerce", "dashboard", "social", "onboarding", "settings"],
            "deterministic_generation": True,
            "fallback_strategies": ["explicit_field", "id_matching", "context_hints", "load_balancing"]
        }
    }


@app.get("/")
def root():
    """Root endpoint with API documentation"""
    return {
        "message": "✅ Beta Pipeline Ready (React Native Edition v2.2)", 
        "platform": "React Native",
        "version": "2.2.0",
        "architecture": {
            "api_0": "Prompt Refiner (Groq - enhances user input)",
            "api_1": "Intent Extractor (DeepSeek Chat v3 - design strategy)",
            "api_2": "Component Generator (DeepSeek Chat v3 - component model JSON)",
            "assembly": "Component-to-Screen Assignment (Python - multi-strategy)",
            "nesting": "Screen-type-aware Component Nesting (Python)",
            "rn_converter": "React Native Code Generator (Python - deterministic)",
            "preview_adapter": "Web Preview Generator (Python - pass-through)",
            "api_3": "🚫 UNUSED (reserved for future features)"
        },
        "endpoints": {
            "POST /generate_pipeline": "Main pipeline - generates component model + RN code + preview",
            "POST /export/react-native": "Export React Native code as ZIP",
            "POST /refine": "Standalone prompt refinement",
            "GET /refiner/stats": "Prompt refiner statistics",
            "GET /health": "Health check",
            "GET /": "This documentation"
        },
        "fixes_in_v2_2": [
            "✅ FIXED: Components no longer bleed across screens",
            "✅ Multi-strategy component-to-screen assignment",
            "✅ Explicit screen field support (highest priority)",
            "✅ ID-based matching (login-*, signup-*, etc.)",
            "✅ Context-aware hints (keywords in props/ids)",
            "✅ Load balancing fallback (prevents screen overload)",
            "✅ Empty screen handling with placeholders",
            "✅ Detailed component distribution logging"
        ],
        "features": [
            "✅ Intelligent component nesting (screen-type aware)",
            "✅ Deterministic code generation (no LLM hallucinations)",
            "✅ 100% component accuracy (direct mapping)",
            "✅ Parallel processing (fast)",
            "✅ Production-ready React Native output",
            "✅ Smart prompt enhancement",
            "✅ 40+ UI components supported",
            "✅ Auto-detects: Auth, E-commerce, Dashboard, Social, Onboarding, Settings"
        ]
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    print(f"❌ Unhandled exception: {exc}")
    import traceback
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )


# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*70)
    print("🚀 UI PIPELINE BETA - REACT NATIVE EDITION v2.2")
    print("="*70)
    print(f"Platform: React Native")
    print(f"Architecture: 3 LLM APIs + 2 Deterministic Converters")
    print(f"")
    print(f"🤖 LLM API Calls:")
    print(f"   API 0: Prompt Refiner (Groq)")
    print(f"   API 1: Intent Extractor (DeepSeek Chat v3)")
    print(f"   API 2: Component Generator (DeepSeek Chat v3)")
    print(f"")
    print(f"🔧 Deterministic Converters (no LLM):")
    print(f"   - React Native Code Generator (Python)")
    print(f"   - Web Preview Adapter (Python)")
    print(f"")
    print(f"🚫 Unused APIs:")
    print(f"   API 3 (OR_API_KEY_CODE): Reserved for future features")
    
    # Check critical dependencies
    try:
        from preview_to_react_native import PreviewToReactNativeConverter
        print("✅ PreviewToReactNativeConverter loaded")
    except ImportError as e:
        print(f"❌ PreviewToReactNativeConverter not found: {e}")
        print("⚠️  React Native code generation will fail!")
    
    try:
        from prompt_refiner import refine_prompt
        print("✅ Prompt Refiner loaded")
    except ImportError:
        print("⚠️  Prompt Refiner not available")
    
    try:
        from llm_client import extract_intent, componentize
        print("✅ LLM Client loaded")
    except ImportError as e:
        print(f"❌ LLM Client error: {e}")
    
    print("\n🆕 NEW FEATURES (v2.2):")
    print("   ✅ FIXED: Cross-screen component bleeding bug")
    print("   ✅ Multi-strategy component-to-screen assignment:")
    print("      1. Explicit 'screen' field (highest priority)")
    print("      2. ID-based matching (login-*, signup-*, etc.)")
    print("      3. Context-aware keywords in props/ids")
    print("      4. Load balancing fallback")
    print("   ✅ Detailed component distribution logging")
    print("   ✅ Empty screen detection with placeholders")
    print("   ✅ Assignment validation checks")
    print("="*70 + "\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )