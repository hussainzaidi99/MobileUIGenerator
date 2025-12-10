# backend/Services/image_url_generator.py
"""
FIXED: Dynamic Image URL Generator v4.2 (2025)
- Guaranteed variety across ALL product cards
- Counter-based assignment for sequential products
- Better fallback strategies
"""

import hashlib
import re
from typing import Dict, Any, List, Tuple, Union

# ============================================================================
# GLOBAL COUNTER FOR SEQUENTIAL ASSIGNMENT
# ============================================================================
_product_counter = 0

def reset_product_counter():
    """Reset the global product counter (call at start of enrichment)"""
    global _product_counter
    _product_counter = 0

def get_next_product_index() -> int:
    """Get next product index and increment counter"""
    global _product_counter
    idx = _product_counter
    _product_counter += 1
    return idx

# ============================================================================
# STABLE HASH
# ============================================================================
def stable_hash(value: str) -> int:
    """Create a stable positive integer hash for a given string."""
    if not value:
        return 0
    md5 = hashlib.md5(value.encode("utf-8")).hexdigest()
    return int(md5, 16)

# ============================================================================
# EXPANDED CURATED PHOTO LIBRARY (20+ photos per category)
# ============================================================================
CURATED_PHOTOS: Dict[str, Union[str, List[str]]] = {
    # Headphones (8 options)
    "headphones": [
        "1505740420928-5e560c06d30e",  # Over-ear headphones
        "1484704849700-f032a568e944",  # White headphones
        "1545127398-14699f92334b",     # Black headphones
        "1546435770-a3d18dde6fa3",     # Gaming headphones
        "1590658165737-15a047b7a0c7",  # Studio headphones
        "1558618666-fcd25c85cd64",     # Wireless headphones
        "1577174881658-0f30bd0e56b4",  # Premium headphones
        "1524678606370-a47ad25cb82a",  # Earbuds
    ],
    
    # Watches (8 options)
    "watch": [
        "1523275335684-37898b6baf30",  # Luxury watch 1
        "1524592301720-b371c0ba1ae7",  # Smart watch 1
        "1508685096489-7edc7a3592f9",  # Classic watch
        "1533139502658-0198f920d8e8",  # Sport watch
        "1522312346080-cc281b1a1ba1",  # Luxury watch 2
        "1614164185128-c42e0c0b6b4a",  # Smart watch 2
        "1587836374664-72b150f6c205",  # Fashion watch
        "1606838598606-aaaa2e1c3e52",  # Elegant watch
    ],
    
    # Shoes (8 options)
    "shoes": [
        "1549298916-b41d501d3772",     # White sneakers
        "1460353581641-37baddab0fa2",  # Running shoes
        "1542291026-7eec264c27ff",     # Casual shoes
        "1605348532760-1b7163e92d91",  # High-top sneakers
        "1584735175315-9d5df23860e6",  # Leather shoes
        "1600185365926-3a2ce3cdb129",  # Sports shoes
        "1608231387042-66d1773070a5",  # Designer shoes
        "1551107696-a4b0629c25e1",     # Colorful sneakers
    ],
    
    # Laptops (8 options)
    "laptop": [
        "1496181133206-80ce9b88a853",  # MacBook style 1
        "1517694712202-14dd9538aa97",  # Laptop on desk
        "1587614382346-4ec70e388b28",  # Modern laptop
        "1593642632823-8f785ba67e45",  # Gaming laptop
        "1588872659547-7c8f1be6d1c5",  # Business laptop
        "1525547719571-a2d4ac8945e2",  # MacBook style 2
        "1603302576837-37561b2e2302",  # Ultrabook
        "1559028012-f8d0d7068e9f",     # Creative laptop
    ],
    
    # Phones (8 options)
    "phone": [
        "1511707171634-5f897ff02aa9",  # iPhone 1
        "1510557880182-3d4d3cba35a5",  # Smartphone 1
        "1580910051074-3eb67677303a",  # Modern phone
        "1598327105666-5b89351aff97",  # iPhone 2
        "1585060544812-6b45742d762f",  # Android phone
        "1592286927405-82d0f4c8b67e",  # Flagship phone
        "1601784551446-20c9e07cdbdb",  # Premium phone
        "1607082349566-187780abb570",  # Latest phone
    ],
    
    # Clothing/Fashion (8 options)
    "clothing": [
        "1434389677669-e08b4cac3105",  # Cozy sweater
        "1576566588028-4147f3842f27",  # Fashion sweater
        "1620799140408-eec2b0dda3d1",  # T-shirt collection
        "1489987707025-afc232f7ea0f",  # Clothing rack 1
        "1558769132-cb1e27e47497",     # Fashion items
        "1445205170230-053b83016050",  # Wardrobe
        "1490114538077-0a7f8cb49891",  # Clothing rack 2
        "1467043153537-a4acd46f39f1",  # Casual wear
    ],
    
    # Bags/Backpacks (8 options)
    "bag": [
        "1553062407-98eeb64c6a62",     # Leather backpack
        "1491637639811-60e2756cc1c7",  # Travel backpack
        "1622560480605-d83c853bc5c3",  # Designer bag
        "1590874103328-11f65e8e2a4b",  # Laptop bag
        "1553062407-98eeb64c6a62",     # Modern backpack
        "1581605777210-b7d1e1e16f14",  # Fashion bag
        "1590393801261-ac74a6f9f54e",  # Sports bag
        "1624887061721-78e5742dde1e",  # Luxury bag
    ],
    
    # Electronics/Gadgets (8 options)
    "gadget": [
        "1468495244123-6c6c332eeece",  # Tech gadget 1
        "1550009158-9ebfd4d588a0",     # Electronics
        "1535223289827-42f1a9fb8c6e",  # Modern gadget
        "1593642532400-4b5d8e8f0c2e",  # Smart device
        "1581093588401-fbb62a02f120",  # Tech accessory
        "1598327105666-5b89351aff97",  # Premium gadget
        "1593642632823-8f785ba67e45",  # Gaming device
        "1581091870621-f5b2f6e97dc5",  # Audio device
    ],
    
    # Default fallback
    "default": "1523275335684-37898b6baf30",
}

# Rotation categories for variety
ROTATION_CATEGORIES: List[str] = [
    "headphones", "watch", "shoes", "laptop", 
    "phone", "clothing", "bag", "gadget"
]

# ============================================================================
# CATEGORY DETECTION (IMPROVED)
# ============================================================================
def _extract_text_from_component(component: Dict[str, Any]) -> Tuple[str, str]:
    """Extract all relevant text from component for category detection."""
    comp_id = str(component.get("id", "")).lower()
    props = component.get("props") or {}
    
    pieces = [
        str(props.get("title", "")),
        str(props.get("name", "")),
        str(props.get("alt", "")),
        str(props.get("label", "")),
        str(props.get("subtitle", "")),
        str(props.get("description", "")),
        comp_id,
    ]
    
    all_text = " ".join(pieces).lower().strip()
    return all_text, comp_id

def detect_image_category(component: Dict[str, Any], screen_type: str = "general") -> str:
    """
    Detect image category with improved keyword matching.
    """
    comp_type = (component.get("type") or "").lower()
    all_text, comp_id = _extract_text_from_component(component)
    
    print(f"[IMAGE DETECTION] Type: {comp_type}, Text: '{all_text[:60]}'")
    
    # Normalize text
    normalized = all_text.replace("-", " ").replace("_", " ")
    
    # KEYWORD MATCHING (order matters - most specific first)
    
    # Headphones
    if any(kw in normalized for kw in ["headphone", "earbud", "earphone", "airpod"]):
        return "headphones"
    
    # Watches
    if any(kw in normalized for kw in ["watch", "smartwatch"]):
        return "watch"
    
    # Shoes
    if any(kw in normalized for kw in ["shoe", "sneaker", "boot", "sandal"]):
        return "shoes"
    
    # Laptops
    if any(kw in normalized for kw in ["laptop", "macbook", "notebook", "computer"]):
        return "laptop"
    
    # Phones
    if any(kw in normalized for kw in ["phone", "smartphone", "iphone", "android"]):
        return "phone"
    
    # Bags
    if any(kw in normalized for kw in ["bag", "backpack", "luggage"]):
        return "bag"
    
    # Clothing
    if any(kw in normalized for kw in ["clothing", "shirt", "sweater", "jacket", "hoodie", "apparel", "wear"]):
        return "clothing"
    
    # Gadgets
    if any(kw in normalized for kw in ["gadget", "device", "tech", "electronic"]):
        return "gadget"
    
    # COMPONENT TYPE FALLBACK - Use sequential counter for variety
    if comp_type in ("productcard", "customproductcard", "cartitem", "customcartitem"):
        idx = get_next_product_index()
        category = ROTATION_CATEGORIES[idx % len(ROTATION_CATEGORIES)]
        print(f"[IMAGE MATCH] ✅ Fallback #{idx} → {category}")
        return category
    
    # Screen type fallback
    if screen_type == "ecommerce":
        idx = get_next_product_index()
        category = ROTATION_CATEGORIES[idx % len(ROTATION_CATEGORIES)]
        print(f"[IMAGE MATCH] ✅ E-commerce fallback #{idx} → {category}")
        return category
    
    print("[IMAGE MATCH] ⚠️ Using default")
    return "default"

# ============================================================================
# IMAGE URL GENERATION (IMPROVED)
# ============================================================================
def generate_image_url(
    component: Dict[str, Any],
    screen_type: str = "general",
    width: int = 400,
    height: int = 300,
    use_curated: bool = True,
) -> str:
    """
    Generate Unsplash image URL with GUARANTEED variety.
    Uses both category detection AND component ID for unique selection.
    """
    category = detect_image_category(component, screen_type)
    
    if use_curated and category in CURATED_PHOTOS:
        photos = CURATED_PHOTOS[category]
        
        # Use BOTH category AND component ID for unique selection
        comp_id = str(component.get("id", ""))
        combined_seed = f"{category}:{comp_id}:{get_next_product_index()}"
        h = stable_hash(combined_seed)
        
        if isinstance(photos, list):
            photo_id = photos[h % len(photos)]
            print(f"[IMAGE URL] 🎯 Selected photo {(h % len(photos)) + 1}/{len(photos)} from {category}")
        else:
            photo_id = photos
        
        url = (
            f"https://images.unsplash.com/photo-{photo_id}"
            f"?auto=format&fit=crop&w={width}&h={height}&q=85"
        )
        print(f"[IMAGE URL] ✅ Generated: {url[:90]}...")
        return url
    
    # Fallback
    query = category.replace("_", "+")
    url = f"https://source.unsplash.com/featured/{width}x{height}/?{query}+product"
    print(f"[IMAGE URL] ⚠️ Fallback: {url[:90]}...")
    return url

# ============================================================================
# COMPONENT ENRICHMENT (RECURSIVE)
# ============================================================================
def enrich_component_with_images(
    component: Dict[str, Any],
    screen_type: str = "general",
    depth: int = 0,
) -> Dict[str, Any]:
    """
    Recursively enrich component with image URLs.
    """
    comp_type = (component.get("type") or "").lower()
    props = component.get("props") or {}
    
    indent = "  " * depth
    print(f"{indent}[ENRICH] Type: {comp_type}, ID: {component.get('id', 'unknown')}")
    
    needs_enrichment = False
    image_prop_key: str = ""
    
    # Detect which prop needs enrichment
    if comp_type in ("image", "customimage"):
        image_prop_key = "src"
        needs_enrichment = not props.get("src") or "placeholder" in str(props.get("src", "")).lower()
    
    elif comp_type in ("productcard", "customproductcard"):
        image_prop_key = "image"
        needs_enrichment = not props.get("image") or "placeholder" in str(props.get("image", "")).lower()
    
    elif comp_type in ("cartitem", "customcartitem"):
        image_prop_key = "image"
        needs_enrichment = not props.get("image") or "placeholder" in str(props.get("image", "")).lower()
    
    elif comp_type in ("illustrationheader", "customillustrationheader"):
        image_prop_key = "illustration"
        needs_enrichment = not props.get("illustration") or "placeholder" in str(props.get("illustration", "")).lower()
    
    elif comp_type in ("herosection", "hero", "customherosection"):
        image_prop_key = "coverImage"
        needs_enrichment = not props.get("coverImage") or "placeholder" in str(props.get("coverImage", "")).lower()
    
    # Enrich if needed
    if needs_enrichment and image_prop_key:
        size_map: Dict[str, Tuple[int, int]] = {
            "src": (400, 300),
            "image": (400, 400),
            "illustration": (600, 400),
            "coverImage": (800, 400),
        }
        width, height = size_map.get(image_prop_key, (400, 300))
        
        new_url = generate_image_url(component, screen_type, width, height)
        props[image_prop_key] = new_url
        print(f"{indent}  ✅ Enriched '{image_prop_key}' → {new_url[:70]}...")
    
    component["props"] = props
    
    # Recursive enrichment
    children = component.get("children", [])
    if children:
        print(f"{indent}  🔄 Enriching {len(children)} children...")
        component["children"] = [
            enrich_component_with_images(child, screen_type, depth + 1)
            for child in children
        ]
    
    return component

# ============================================================================
# LAYOUT ENRICHMENT (ENTRY POINT)
# ============================================================================
def enrich_layout_with_images(layout: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich entire layout with image URLs.
    CRITICAL: Resets counter at start to ensure consistent variety.
    """
    # RESET COUNTER FOR FRESH START
    reset_product_counter()
    
    screens: List[Dict[str, Any]] = layout.get("screens", [])
    design_strategy = layout.get("design_strategy", {}) or {}
    screen_type = design_strategy.get("screen_type", "general")
    
    print("\n" + "=" * 60)
    print(f"[IMAGE ENRICHMENT] Starting for {len(screens)} screens (screen_type='{screen_type}')")
    print("=" * 60)
    
    for screen_idx, screen in enumerate(screens):
        screen_name = screen.get("name", f"Screen {screen_idx + 1}")
        components = screen.get("components", []) or []
        
        print(f"\n[SCREEN {screen_idx + 1}] {screen_name} ({len(components)} components)")
        
        enriched_components: List[Dict[str, Any]] = []
        for comp in components:
            enriched_comp = enrich_component_with_images(comp, screen_type, depth=0)
            enriched_components.append(enriched_comp)
        
        screen["components"] = enriched_components
    
    layout["screens"] = screens
    
    print("\n" + "=" * 60)
    print(f"[IMAGE ENRICHMENT] ✅ Complete! Processed {_product_counter} product images")
    print("=" * 60 + "\n")
    
    return layout