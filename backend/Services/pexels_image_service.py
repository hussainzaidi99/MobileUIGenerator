# backend/Services/pexels_image_service.py
"""
🎨 PEXELS DYNAMIC IMAGE GENERATION SYSTEM
Production-ready image retrieval with context-aware search, caching, and fallbacks.

Features:
- Context-aware Pexels search based on screen type + component semantics
- Smart query construction from component props
- Redis caching for performance (optional)
- Rate limiting protection
- Deterministic selection for consistency
- Fallback strategies for edge cases
"""

import os
import hashlib
import asyncio
import httpx
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "iAlYABt2URtBTSkyhb7j7Ln3BEjpClzjXJj408IAw3XUXKgwDOTHV5x9")
PEXELS_BASE_URL = "https://api.pexels.com/v1"
PEXELS_TIMEOUT = int(os.getenv("PEXELS_TIMEOUT", "10"))

# Cache configuration (optional - works without Redis)
ENABLE_REDIS_CACHE = os.getenv("REDIS_ENABLED", "false").lower() == "true"
CACHE_TTL_HOURS = 24  # Cache search results for 24 hours

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 200  # Pexels free tier limit
REQUEST_DELAY = 0.3  # 300ms between requests

# ============================================================================
# IN-MEMORY CACHE (Fallback when Redis unavailable)
# ============================================================================

class SimpleCache:
    """In-memory cache with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_hours: int = 24):
        """Set cached value with TTL"""
        expiry = datetime.now() + timedelta(hours=ttl_hours)
        self._cache[key] = (value, expiry)
    
    def clear_expired(self):
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = [k for k, (_, exp) in self._cache.items() if now >= exp]
        for key in expired_keys:
            del self._cache[key]

# Global cache instance
_memory_cache = SimpleCache()

# ============================================================================
# REDIS CACHE (Optional)
# ============================================================================

_redis_client = None

def get_redis_client():
    """Get Redis client if enabled"""
    global _redis_client
    
    if not ENABLE_REDIS_CACHE:
        return None
    
    if _redis_client is None:
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            _redis_client.ping()
            print("✅ Redis cache connected")
        except Exception as e:
            print(f"⚠️  Redis unavailable: {e} - using memory cache")
            _redis_client = False
    
    return _redis_client if _redis_client is not False else None

# ============================================================================
# CACHE OPERATIONS
# ============================================================================

def cache_get(key: str) -> Optional[str]:
    """Get from cache (Redis or memory)"""
    redis = get_redis_client()
    
    if redis:
        try:
            return redis.get(key)
        except Exception:
            pass
    
    return _memory_cache.get(key)

def cache_set(key: str, value: str, ttl_hours: int = CACHE_TTL_HOURS):
    """Set in cache (Redis or memory)"""
    redis = get_redis_client()
    
    if redis:
        try:
            redis.setex(key, ttl_hours * 3600, value)
            return
        except Exception:
            pass
    
    _memory_cache.set(key, value, ttl_hours)

# ============================================================================
# SEMANTIC QUERY BUILDER
# ============================================================================

class PexelsQueryBuilder:
    """Build intelligent Pexels search queries from component context"""
    
    # Category-specific keywords for better results
    CATEGORY_KEYWORDS = {
        "auth": {
            "login": ["security", "padlock", "login", "authentication", "mobile login"],
            "signup": ["welcome", "registration", "onboarding", "user registration"],
            "welcome": ["welcome screen", "greeting", "hello", "welcome banner"],
            "verification": ["verification", "security code", "authentication", "two factor"],
            "success": ["success", "checkmark", "completion", "achievement"],
        },
        "ecommerce": {
            "product": ["product photography", "commercial product", "e-commerce product"],
            "headphones": ["wireless headphones", "premium headphones", "audio headphones"],
            "laptop": ["modern laptop", "macbook", "computer technology"],
            "phone": ["smartphone", "mobile phone", "iphone", "android phone"],
            "watch": ["smartwatch", "luxury watch", "wristwatch", "apple watch"],
            "shoes": ["sneakers", "running shoes", "fashion shoes", "athletic footwear"],
            "clothing": ["fashion clothing", "apparel", "stylish outfit", "wardrobe"],
            "bag": ["leather bag", "backpack", "fashion bag", "travel luggage"],
            "cart": ["shopping cart", "e-commerce cart", "online shopping"],
        },
        "social": {
            "avatar": ["person portrait", "professional headshot", "profile picture"],
            "post": ["social media", "lifestyle photo", "casual moment"],
            "cover": ["abstract background", "gradient background", "modern pattern"],
            "profile": ["user profile", "person", "portrait photography"],
        },
        "dashboard": {
            "analytics": ["data visualization", "charts graphs", "business analytics"],
            "stats": ["statistics", "infographic", "data display"],
            "hero": ["business dashboard", "modern workspace", "technology screen"],
        },
        "food": {
            "burger": ["gourmet burger", "hamburger", "food photography burger"],
            "pizza": ["pizza slice", "italian pizza", "food photography pizza"],
            "sushi": ["sushi rolls", "japanese food", "sushi platter"],
            "salad": ["fresh salad", "healthy salad", "green salad bowl"],
            "coffee": ["coffee cup", "latte art", "espresso coffee"],
            "dessert": ["dessert plate", "sweet dessert", "pastry"],
        },
        "travel": {
            "destination": ["travel destination", "scenic landscape", "vacation spot"],
            "hotel": ["luxury hotel", "hotel room", "accommodation"],
            "beach": ["tropical beach", "ocean beach", "seaside"],
        },
    }
    
    @classmethod
    def build_query(
        cls,
        component: Dict[str, Any],
        screen_type: str = "general",
        fallback_keyword: str = "modern minimal",
        user_context: str = ""  # ✅ NEW: User prompt context
    ) -> str:
        """
        Build optimal Pexels search query from component context.
        
        Strategy:
        1. Extract context from user prompt (e.g., "barber shop")
        2. Extract semantic hints from component props
        3. Match to category-specific keywords
        4. Build query with modifiers for quality
        """
        comp_type = (component.get("type") or "").lower()
        props = component.get("props") or {}
        
        # ✅ NEW: Extract business/domain context from user prompt
        context_keywords = cls._extract_context_from_prompt(user_context)
        
        # Extract text content
        text_parts = [
            str(props.get("title", "")),
            str(props.get("name", "")),
            str(props.get("alt", "")),
            str(props.get("label", "")),
            str(props.get("description", "")),
            str(component.get("id", "")),
        ]
        
        all_text = " ".join(text_parts).lower().strip()
        
        # ✅ PRIORITY 1: If user context exists, use it!
        if context_keywords:
            # For auth screens with business context: "barber shop login"
            if screen_type == "auth":
                return f"{context_keywords} professional"
            # For other screens: use context directly
            return context_keywords
        
        # Detect specific item type
        detected_type = cls._detect_item_type(all_text, screen_type)
        
        # Get category-specific keywords
        if screen_type in cls.CATEGORY_KEYWORDS:
            category_keywords = cls.CATEGORY_KEYWORDS[screen_type]
            
            if detected_type in category_keywords:
                base_keywords = category_keywords[detected_type]
                # Rotate through keywords for variety
                keyword_index = abs(hash(component.get("id", ""))) % len(base_keywords)
                return base_keywords[keyword_index]
        
        # Fallback: construct from component type + text
        if all_text:
            # Clean and format
            clean_text = all_text.replace("-", " ").replace("_", " ")
            words = [w for w in clean_text.split() if len(w) > 2][:3]
            
            if words:
                return " ".join(words)
        
        # Final fallback
        return f"{screen_type} {fallback_keyword}" if screen_type != "general" else fallback_keyword
    
    @classmethod
    def _extract_context_from_prompt(cls, user_prompt: str) -> str:
        """
        Extract business/domain context from user prompt.
        
        Examples:
        - "barber shop app" → "barber shop"
        - "coffee shop mobile UI" → "coffee shop"
        - "fitness gym authentication" → "fitness gym"
        """
        if not user_prompt:
            return ""
        
        prompt_lower = user_prompt.lower()
        
        # Remove common UI/tech words
        noise_words = [
            "app", "mobile", "ui", "screen", "authentication", "auth",
            "login", "signup", "modern", "design", "interface", "with",
            "email", "password", "social", "google", "apple", "facebook",
            "create", "build", "generate", "make", "for", "and", "the"
        ]
        
        words = prompt_lower.split()
        context_words = []
        
        for word in words:
            # Keep meaningful business/domain words
            if word not in noise_words and len(word) > 2:
                context_words.append(word)
        
        # Take first 2-3 meaningful words
        if context_words:
            return " ".join(context_words[:2])
        
        return ""
    
    @classmethod
    def _detect_item_type(cls, text: str, screen_type: str) -> str:
        """Detect specific item type from text"""
        
        # Product detection
        product_map = {
            "headphone": "headphones",
            "earbud": "headphones",
            "airpod": "headphones",
            "laptop": "laptop",
            "macbook": "laptop",
            "computer": "laptop",
            "phone": "phone",
            "smartphone": "phone",
            "iphone": "phone",
            "watch": "watch",
            "smartwatch": "watch",
            "shoe": "shoes",
            "sneaker": "shoes",
            "boot": "shoes",
            "bag": "bag",
            "backpack": "bag",
            "shirt": "clothing",
            "jacket": "clothing",
            "sweater": "clothing",
        }
        
        # Food detection
        food_map = {
            "burger": "burger",
            "pizza": "pizza",
            "sushi": "sushi",
            "salad": "salad",
            "coffee": "coffee",
            "dessert": "dessert",
        }
        
        # Auth detection
        auth_map = {
            "login": "login",
            "signin": "login",
            "signup": "signup",
            "register": "signup",
            "welcome": "welcome",
            "verify": "verification",
            "otp": "verification",
        }
        
        # Combine all maps
        all_maps = {**product_map, **food_map, **auth_map}
        
        for keyword, item_type in all_maps.items():
            if keyword in text:
                return item_type
        
        # Default based on screen type
        if screen_type == "ecommerce":
            return "product"
        elif screen_type == "food":
            return "burger"
        elif screen_type == "auth":
            return "login"
        
        return "general"

# ============================================================================
# PEXELS API CLIENT
# ============================================================================

class PexelsImageService:
    """Production-ready Pexels image retrieval service"""
    
    def __init__(self):
        self.api_key = PEXELS_API_KEY
        self.base_url = PEXELS_BASE_URL
        self.timeout = PEXELS_TIMEOUT
        self._last_request_time = 0
        self.query_builder = PexelsQueryBuilder()
    
    async def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < REQUEST_DELAY:
            await asyncio.sleep(REQUEST_DELAY - time_since_last)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    def _generate_cache_key(self, query: str, orientation: str = "landscape") -> str:
        """Generate cache key for query"""
        key_string = f"pexels:{query}:{orientation}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def search_photos(
        self,
        query: str,
        per_page: int = 15,
        orientation: str = "landscape"
    ) -> List[Dict[str, Any]]:
        """
        Search Pexels for photos.
        
        Args:
            query: Search query
            per_page: Number of results (max 80)
            orientation: landscape, portrait, or square
            
        Returns:
            List of photo objects
        """
        # Check cache first
        cache_key = self._generate_cache_key(query, orientation)
        cached = cache_get(cache_key)
        
        if cached:
            print(f"✅ [PEXELS CACHE] Hit for '{query}'")
            import json
            return json.loads(cached)
        
        # Rate limiting
        await self._rate_limit()
        
        print(f"🔍 [PEXELS API] Searching: '{query}' (orientation={orientation})")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    headers={"Authorization": self.api_key},
                    params={
                        "query": query,
                        "per_page": per_page,
                        "orientation": orientation,
                    }
                )
                
                if response.status_code != 200:
                    print(f"⚠️  [PEXELS API] Error {response.status_code}: {response.text[:200]}")
                    return []
                
                data = response.json()
                photos = data.get("photos", [])
                
                # Cache results
                if photos:
                    import json
                    cache_set(cache_key, json.dumps(photos), CACHE_TTL_HOURS)
                    print(f"✅ [PEXELS API] Found {len(photos)} photos for '{query}'")
                else:
                    print(f"⚠️  [PEXELS API] No photos found for '{query}'")
                
                return photos
        
        except Exception as e:
            print(f"❌ [PEXELS API] Error: {e}")
            return []
    
    async def get_image_url(
        self,
        component: Dict[str, Any],
        screen_type: str = "general",
        width: int = 400,
        height: int = 300,
        use_cache: bool = True,
        user_context: str = "",  # ✅ NEW: User prompt context
        used_ids: set = None      # ✅ NEW: Tracking used image IDs
    ) -> str:
        """
        Get optimal image URL for component.
        
        Args:
            component: Component dict with type, props, id
            screen_type: Screen category (auth, ecommerce, social, etc.)
            width: Desired width
            height: Desired height
            use_cache: Whether to use cached results
            user_context: User's original prompt for context-aware queries
            used_ids: Set of photo IDs already used in this generation
            
        Returns:
            Pexels image URL
        """
        try:
            # Build query with user context
            query = self.query_builder.build_query(
                component, 
                screen_type,
                user_context=user_context
            )

            # Determine orientation
            aspect_ratio = width / height if height > 0 else 1.0
            if aspect_ratio > 1.3:
                orientation = "landscape"
            elif aspect_ratio < 0.8:
                orientation = "portrait"
            else:
                orientation = "square"

            # Search Pexels
            photos = await self.search_photos(query, per_page=15, orientation=orientation)

            if not photos:
                # Fallback: try broader query
                fallback_query = self.query_builder.build_query(
                    component, 
                    screen_type,
                    fallback_keyword="modern"
                )

                if fallback_query != query:
                    print(f"🔄 [PEXELS FALLBACK] Trying broader query: '{fallback_query}'")
                    photos = await self.search_photos(fallback_query, per_page=15, orientation=orientation)

            # Filter out already used photos if possible
            selected_photo = None
            photo_index = 0
            
            if photos:
                # Deterministic selection based on component ID
                comp_id = component.get("id", "")
                base_index = abs(hash(comp_id)) % len(photos)
                
                # Try to find a photo that hasn't been used yet
                for i in range(len(photos)):
                    current_index = (base_index + i) % len(photos)
                    candidate = photos[current_index]
                    candidate_id = candidate.get("id")
                    
                    if used_ids is None or candidate_id not in used_ids:
                        selected_photo = candidate
                        photo_index = current_index
                        if used_ids is not None:
                            used_ids.add(candidate_id)
                        break
                
                # Fallback to base_index if all appear used (unlikely with per_page=15)
                if not selected_photo:
                    selected_photo = photos[base_index]
                    photo_index = base_index

            if not selected_photo:
                fallback_url = self._get_fallback_url(width, height)
                print(f"⚠️  [PEXELS] No photos found - using fallback: {fallback_url[:80]}")
                return fallback_url

            # Get optimal size URL
            url = self._get_optimal_size_url(selected_photo, width, height)

            print(f"✅ [PEXELS] Selected photo {photo_index + 1}/{len(photos)}: {url[:80]}...")
            return url

        except Exception as e:
            print(f"❌ [PEXELS ERROR] {e}")
            import traceback
            traceback.print_exc()

            # Return Unsplash fallback on any error
            fallback_url = self._get_fallback_url(width, height)
            print(f"🔄 [PEXELS] Using fallback: {fallback_url}")
            return fallback_url
    
    
    def _get_optimal_size_url(
        self,
        photo: Dict[str, Any],
        target_width: int,
        target_height: int
    ) -> str:
        """Get best size URL from Pexels photo object"""
        src = photo.get("src", {})
        
        # Pexels provides these sizes:
        # - original: full resolution
        # - large2x: 1880x1200
        # - large: 940x650
        # - medium: 350x233
        # - small: 130x86
        # - portrait: 800x1200
        # - landscape: 1200x627
        # - tiny: 280x200
        
        # Choose based on target dimensions
        if target_width >= 800 or target_height >= 800:
            return src.get("large2x") or src.get("large") or src.get("original")
        elif target_width >= 400 or target_height >= 400:
            return src.get("large") or src.get("medium") or src.get("original")
        else:
            return src.get("medium") or src.get("small") or src.get("original")
    
    def _get_fallback_url(self, width: int, height: int) -> str:
        """Generate fallback URL (Unsplash as backup)"""
        return f"https://source.unsplash.com/random/{width}x{height}/?minimal,modern"

# ============================================================================
# GLOBAL SERVICE INSTANCE
# ============================================================================

_pexels_service: Optional[PexelsImageService] = None

def get_pexels_service() -> PexelsImageService:
    """Get global Pexels service instance (singleton)"""
    global _pexels_service
    
    if _pexels_service is None:
        _pexels_service = PexelsImageService()
    
    return _pexels_service

# ============================================================================
# MAIN ENRICHMENT FUNCTION (Drop-in replacement for image_url_generator.py)
# ============================================================================

async def enrich_component_with_pexels(
    component: Dict[str, Any],
    screen_type: str = "general",
    depth: int = 0,
    user_context: str = "",  # ✅ NEW: User prompt context
    used_ids: set = None      # ✅ NEW: Tracking used image IDs
) -> Dict[str, Any]:
    """
    Recursively enrich component with Pexels image URLs.
    
    Args:
        component: Component to enrich
        screen_type: Screen category
        depth: Recursion depth
        user_context: Context from user prompt
        used_ids: Set of already used image IDs
    """
    comp_type = (component.get("type") or "").lower()
    props = component.get("props") or {}
    
    indent = "  " * depth
    print(f"{indent}[PEXELS ENRICH] Type: {comp_type}, ID: {component.get('id', 'unknown')}")
    
    needs_enrichment = False
    image_prop_key: str = ""
    
    # Detect which prop needs enrichment
    # ✅ ALWAYS enrich image components (force Pexels over LLM placeholders)
    if comp_type in ("image", "customimage"):
        image_prop_key = "src"
        needs_enrichment = True  # Always enrich
    
    elif comp_type in ("productcard", "customproductcard"):
        image_prop_key = "image"
        needs_enrichment = True  # Always enrich
    
    elif comp_type in ("cartitem", "customcartitem"):
        image_prop_key = "image"
        needs_enrichment = True  # Always enrich
    
    elif comp_type in ("illustrationheader", "customillustrationheader"):
        image_prop_key = "illustration"
        needs_enrichment = True  # Always enrich
    
    elif comp_type in ("herosection", "hero", "customherosection"):
        image_prop_key = "coverImage"
        needs_enrichment = True  # Always enrich
    
    # Enrich if needed
    if needs_enrichment and image_prop_key:
        size_map: Dict[str, Tuple[int, int]] = {
            "src": (400, 300),
            "image": (400, 400),
            "illustration": (600, 400),
            "coverImage": (800, 400),
        }
        width, height = size_map.get(image_prop_key, (400, 300))
        
        service = get_pexels_service()
        new_url = await service.get_image_url(
            component, 
            screen_type, 
            width, 
            height,
            user_context=user_context,
            used_ids=used_ids
        )
        
        props[image_prop_key] = new_url
        print(f"{indent}  ✅ Enriched '{image_prop_key}' → {new_url[:70]}...")
    
    component["props"] = props
    
    # Recursive enrichment
    children = component.get("children", [])
    if children:
        print(f"{indent}  🔄 Enriching {len(children)} children...")
        enriched_children = []
        for child in children:
            enriched_child = await enrich_component_with_pexels(
                child, 
                screen_type, 
                depth + 1,
                user_context=user_context,
                used_ids=used_ids
            )
            enriched_children.append(enriched_child)
        component["children"] = enriched_children
    
    return component

async def enrich_layout_with_pexels(
    layout: Dict[str, Any],
    user_prompt: str = ""  # ✅ NEW: User's original prompt
) -> Dict[str, Any]:
    """
    Enrich entire layout with Pexels image URLs.
    
    Drop-in replacement for enrich_layout_with_images()
    
    Args:
        layout: Component model layout
        user_prompt: User's original prompt for context-aware image selection
    """
    screens: List[Dict[str, Any]] = layout.get("screens", [])
    design_strategy = layout.get("design_strategy", {}) or {}
    screen_type = design_strategy.get("screen_type", "general")
    
    # ✅ Extract context from user prompt
    user_context = PexelsQueryBuilder._extract_context_from_prompt(user_prompt)
    
    print("\n" + "=" * 60)
    print(f"[PEXELS ENRICHMENT] Starting for {len(screens)} screens")
    print(f"   Screen Type: '{screen_type}'")
    if user_context:
        print(f"   User Context: '{user_context}' (from prompt: '{user_prompt[:50]}...')")
    print("=" * 60)
    
    image_count = 0
    used_ids = set() # ✅ Track IDs for entire layout
    
    for screen_idx, screen in enumerate(screens):
        screen_name = screen.get("name", f"Screen {screen_idx + 1}")
        components = screen.get("components", []) or []
        
        print(f"\n[SCREEN {screen_idx + 1}] {screen_name} ({len(components)} components)")
        
        enriched_components: List[Dict[str, Any]] = []
        for comp in components:
            enriched_comp = await enrich_component_with_pexels(
                comp, 
                screen_type, 
                depth=0,
                user_context=user_context,
                used_ids=used_ids
            )
            enriched_components.append(enriched_comp)
            
            # Count images
            def count_images(c):
                count = 0
                props = c.get("props", {})
                if props.get("image") or props.get("src") or props.get("illustration") or props.get("coverImage"):
                    count += 1
                for child in c.get("children", []):
                    count += count_images(child)
                return count
            
            image_count += count_images(enriched_comp)
        
        screen["components"] = enriched_components
    
    layout["screens"] = screens
    
    print("\n" + "=" * 60)
    print(f"[PEXELS ENRICHMENT] ✅ Complete! Processed {image_count} images")
    print("=" * 60 + "\n")
    
    return layout

# ============================================================================
# CLI TESTING
# ============================================================================

async def test_pexels_service():
    """Test Pexels service with various queries"""
    print("\n" + "=" * 70)
    print("🧪 TESTING PEXELS IMAGE SERVICE")
    print("=" * 70)
    
    service = get_pexels_service()
    
    # Test cases
    test_components = [
        {
            "id": "product-1",
            "type": "ProductCard",
            "props": {"title": "Wireless Headphones", "price": "$99.99"}
        },
        {
            "id": "product-2",
            "type": "ProductCard",
            "props": {"title": "MacBook Pro", "price": "$1999"}
        },
        {
            "id": "food-1",
            "type": "ProductCard",
            "props": {"title": "Classic Burger", "price": "$12.99"}
        },
        {
            "id": "auth-1",
            "type": "IllustrationHeader",
            "props": {"title": "Welcome Back"}
        }
    ]
    
    screen_types = ["ecommerce", "ecommerce", "food", "auth"]
    
    for comp, screen_type in zip(test_components, screen_types):
        print(f"\n📦 Testing: {comp['props'].get('title')} ({screen_type})")
        url = await service.get_image_url(comp, screen_type, 400, 400)
        print(f"   URL: {url}")
        print(f"   ✅ Success")

if __name__ == "__main__":
    asyncio.run(test_pexels_service())