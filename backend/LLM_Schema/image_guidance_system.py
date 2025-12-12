# backend/LLM_Schema/image_guidance_system.py
"""
🖼️ INTELLIGENT IMAGE SELECTION SYSTEM
Guides LLM to select contextually appropriate Unsplash images based on:
- Screen category (auth, ecommerce, social, dashboard, etc.)
- Component type (ProductCard, Avatar, Hero, etc.)
- Semantic context (product name, screen purpose, user intent)
"""

from typing import Dict, List, Any, Set

###############################################################################
# 🎨 CURATED UNSPLASH IMAGE LIBRARY BY CATEGORY
###############################################################################

UNSPLASH_IMAGE_LIBRARY = {
    # ========================================================================
    # 🛒 ECOMMERCE CATEGORY
    # ========================================================================
    "ecommerce": {
        "electronics": {
            "headphones": [
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop",  # Premium over-ear
                "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=400&h=400&fit=crop",  # White wireless
                "https://images.unsplash.com/photo-1545127398-14699f92334b?w=400&h=400&fit=crop",  # Black studio
                "https://images.unsplash.com/photo-1546435770-a3d18dde6fa3?w=400&h=400&fit=crop",  # Gaming RGB
            ],
            "laptops": [
                "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=400&fit=crop",  # MacBook Air
                "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400&h=400&fit=crop",  # Laptop on desk
                "https://images.unsplash.com/photo-1587614382346-4ec70e388b28?w=400&h=400&fit=crop",  # Modern ultrabook
                "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=400&h=400&fit=crop",  # Gaming laptop
            ],
            "phones": [
                "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=400&fit=crop",  # iPhone 14 Pro
                "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=400&h=400&fit=crop",  # Android flagship
                "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=400&h=400&fit=crop",  # Latest iPhone
                "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=400&h=400&fit=crop",  # Premium smartphone
            ],
            "watches": [
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",  # Luxury watch
                "https://images.unsplash.com/photo-1524592301720-b371c0ba1ae7?w=400&h=400&fit=crop",  # Apple Watch
                "https://images.unsplash.com/photo-1522312346080-cc281b1a1ba1?w=400&h=400&fit=crop",  # Classic timepiece
                "https://images.unsplash.com/photo-1614164185128-c42e0c0b6b4a?w=400&h=400&fit=crop",  # Smart watch
            ],
            "cameras": [
                "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=400&h=400&fit=crop",  # DSLR camera
                "https://images.unsplash.com/photo-1606800052052-a08af7148866?w=400&h=400&fit=crop",  # Mirrorless
                "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=400&h=400&fit=crop",  # Vintage camera
            ],
        },
        "fashion": {
            "shoes": [
                "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop",  # White sneakers
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop",  # Running shoes
                "https://images.unsplash.com/photo-1605348532760-1b7163e92d91?w=400&h=400&fit=crop",  # High-top sneakers
                "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400&h=400&fit=crop",  # Designer shoes
            ],
            "clothing": [
                "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&h=400&fit=crop",  # Cozy sweater
                "https://images.unsplash.com/photo-1620799140408-eec2b0dda3d1?w=400&h=400&fit=crop",  # T-shirt collection
                "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=400&h=400&fit=crop",  # Fashion rack
                "https://images.unsplash.com/photo-1558769132-cb1e27e47497?w=400&h=400&fit=crop",  # Wardrobe items
            ],
            "bags": [
                "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop",  # Leather backpack
                "https://images.unsplash.com/photo-1491637639811-60e2756cc1c7?w=400&h=400&fit=crop",  # Travel bag
                "https://images.unsplash.com/photo-1590393801261-ac74a6f9f54e?w=400&h=400&fit=crop",  # Designer handbag
            ],
            "accessories": [
                "https://images.unsplash.com/photo-1556306535-0f09a537f0a3?w=400&h=400&fit=crop",  # Sunglasses
                "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=400&h=400&fit=crop",  # Jewelry
            ],
        },
        "home_garden": {
            "furniture": [
                "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=400&fit=crop",  # Sofa
                "https://images.unsplash.com/photo-1538688525198-9b88f6f53126?w=400&h=400&fit=crop",  # Chair
                "https://images.unsplash.com/photo-1519710164239-da123dc03ef4?w=400&h=400&fit=crop",  # Dining table
            ],
            "decor": [
                "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=400&h=400&fit=crop",  # Home decor
                "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?w=400&h=400&fit=crop",  # Plant pot
            ],
        },
        "sports": {
            "fitness": [
                "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=400&h=400&fit=crop",  # Gym equipment
                "https://images.unsplash.com/photo-1592632789004-57d4354f2499?w=400&h=400&fit=crop",  # Yoga mat
                "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=400&fit=crop",  # Dumbbells
            ],
        },
        "generic_products": [
            "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",  # Product 1
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop",  # Product 2
            "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop",  # Product 3
            "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop",  # Product 4
        ],
    },
    
    # ========================================================================
    # 🍔 FOOD & RESTAURANT CATEGORY
    # ========================================================================
    "food": {
        "meals": {
            "burgers": [
                "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=400&fit=crop",  # Classic burger
                "https://images.unsplash.com/photo-1550547660-d9450f859349?w=400&h=400&fit=crop",  # Gourmet burger
            ],
            "pizza": [
                "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400&h=400&fit=crop",  # Margherita
                "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=400&fit=crop",  # Pepperoni
            ],
            "pasta": [
                "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=400&h=400&fit=crop",  # Spaghetti
                "https://images.unsplash.com/photo-1556761175-4b46a572b786?w=400&h=400&fit=crop",  # Fettuccine
            ],
            "sushi": [
                "https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?w=400&h=400&fit=crop",  # Sushi rolls
                "https://images.unsplash.com/photo-1583623025817-d180a2221d0a?w=400&h=400&fit=crop",  # Sashimi
            ],
            "salads": [
                "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=400&fit=crop",  # Fresh salad
                "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=400&fit=crop",  # Caesar salad
            ],
        },
        "beverages": {
            "coffee": [
                "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&h=400&fit=crop",  # Latte art
                "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&h=400&fit=crop",  # Espresso
            ],
            "juices": [
                "https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=400&h=400&fit=crop",  # Fresh juice
            ],
        },
        "desserts": [
            "https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&h=400&fit=crop",  # Cake
            "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=400&h=400&fit=crop",  # Ice cream
        ],
    },
    
    # ========================================================================
    # 👥 SOCIAL MEDIA CATEGORY
    # ========================================================================
    "social": {
        "profiles": {
            "avatars": [
                "https://i.pravatar.cc/150?img=1",
                "https://i.pravatar.cc/150?img=12",
                "https://i.pravatar.cc/150?img=25",
                "https://i.pravatar.cc/150?img=33",
                "https://i.pravatar.cc/150?img=45",
            ],
        },
        "posts": {
            "lifestyle": [
                "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=400&fit=crop",  # Nature
                "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=600&h=400&fit=crop",  # City life
                "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=600&h=400&fit=crop",  # Photography
            ],
            "travel": [
                "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&h=400&fit=crop",  # Beach
                "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=600&h=400&fit=crop",  # City skyline
            ],
        },
        "cover_photos": [
            "https://images.unsplash.com/photo-1557683316-973673baf926?w=800&h=300&fit=crop",  # Gradient abstract
            "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=800&h=300&fit=crop",  # Geometric
        ],
    },
    
    # ========================================================================
    # 🔐 AUTH CATEGORY
    # ========================================================================
    "auth": {
        "illustrations": {
            "welcome": [
                "https://images.unsplash.com/photo-1551434678-e076c223a692?w=600&h=400&fit=crop",  # Team collaboration
                "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=600&h=400&fit=crop",  # Business team
            ],
            "security": [
                "https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?w=600&h=400&fit=crop",  # Padlock security
                "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=600&h=400&fit=crop",  # Cyber security
            ],
            "success": [
                "https://images.unsplash.com/photo-1513151233558-d860c5398176?w=600&h=400&fit=crop",  # Success celebration
            ],
        },
    },
    
    # ========================================================================
    # 📊 DASHBOARD CATEGORY
    # ========================================================================
    "dashboard": {
        "hero_images": [
            "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=400&fit=crop",  # Data visualization
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=400&fit=crop",  # Analytics screen
        ],
    },
    
    # ========================================================================
    # 🏨 TRAVEL & REAL ESTATE CATEGORY
    # ========================================================================
    "travel": {
        "destinations": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&h=400&fit=crop",  # Beach resort
            "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=400&fit=crop",  # Mountain landscape
            "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=600&h=400&fit=crop",  # City skyline
        ],
        "hotels": [
            "https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=600&h=400&fit=crop",  # Hotel room
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600&h=400&fit=crop",  # Luxury suite
        ],
    },
    "realestate": {
        "properties": [
            "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=600&h=400&fit=crop",  # Modern house
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=600&h=400&fit=crop",  # Apartment interior
        ],
    },
}

###############################################################################
# 🎯 IMAGE SELECTION GUIDANCE FOR LLM
###############################################################################

IMAGE_SELECTION_PROMPT = """
# 🖼️ INTELLIGENT IMAGE SELECTION GUIDELINES

**CRITICAL: Every component that displays visual content MUST have a contextually appropriate Unsplash image URL.**

## 📋 COMPONENT-SPECIFIC IMAGE REQUIREMENTS:

### 1. ProductCard / CartItem (E-commerce)
**Decision Tree:**
- Check product title/name for keywords
- Match to specific subcategory (electronics → headphones/laptops/phones)
- Select from curated library based on semantic match
- Use sequential selection within category to ensure variety

**Example:**
```json
{
  "id": "product-1",
  "type": "ProductCard",
  "props": {
    "title": "Wireless Headphones",
    "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop",
    "price": "$99.99"
  }
}
```

**Keyword Matching:**
- "headphone", "earbuds", "airpods" → Electronics > Headphones
- "laptop", "macbook", "notebook" → Electronics > Laptops
- "phone", "iphone", "smartphone" → Electronics > Phones
- "watch", "smartwatch" → Electronics > Watches
- "shoe", "sneaker", "boot" → Fashion > Shoes
- "shirt", "sweater", "jacket" → Fashion > Clothing
- "bag", "backpack" → Fashion > Bags

### 2. IllustrationHeader (Auth/Onboarding)
**Context-based selection:**
- Login screen → "welcome" or "security" illustrations
- Signup screen → "welcome" or "team" illustrations
- Success screen → "success" illustrations
- Onboarding → Relevant to app purpose (fitness, productivity, etc.)

**Example:**
```json
{
  "id": "auth-header",
  "type": "IllustrationHeader",
  "props": {
    "title": "Welcome Back",
    "illustration": "https://images.unsplash.com/photo-1551434678-e076c223a692?w=600&h=400&fit=crop"
  }
}
```

### 3. Avatar (Social/Profile)
**Rules:**
- Use pravatar.cc or ui-avatars.com
- Vary img parameter (1-70) for diversity
- Example: `https://i.pravatar.cc/150?img={random_1_to_70}`

### 4. HeroSection / Cover Images
**Selection criteria:**
- Social apps → Abstract/geometric patterns
- E-commerce → Product showcases
- Dashboard → Data visualization themes
- Travel → Destination images
- Real estate → Property photos

**Example:**
```json
{
  "id": "hero-1",
  "type": "HeroSection",
  "props": {
    "coverImage": "https://images.unsplash.com/photo-1557683316-973673baf926?w=800&h=300&fit=crop",
    "height": 300
  }
}
```

### 5. Food Delivery / Restaurant Apps
**Meal-specific selection:**
- Menu items → Match exact dish type (burger, pizza, sushi)
- Category headers → Use generic food category images
- Restaurant hero → Use ambiance/dining images

**Example:**
```json
{
  "id": "food-item-1",
  "type": "ProductCard",
  "props": {
    "title": "Classic Burger",
    "image": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=400&fit=crop",
    "price": "$12.99"
  }
}
```

## 🎨 IMAGE URL FORMAT RULES:

1. **Always include sizing parameters:**
   - ProductCard: `?w=400&h=400&fit=crop`
   - Hero/Cover: `?w=800&h=400&fit=crop` or `?w=800&h=300&fit=crop`
   - Illustration: `?w=600&h=400&fit=crop`
   - Thumbnail: `?w=150&h=150&fit=crop`

2. **Use `fit=crop` for consistent aspect ratios**

3. **Never use placeholder text URLs like:**
   ❌ `https://via.placeholder.com/400x300`
   ❌ `https://placehold.co/400x300?text=Product`
   ✅ Use actual Unsplash photo IDs

## 🔄 VARIETY STRATEGIES:

### For Product Grids (4-8+ items):
**Rotate through subcategories systematically:**

```json
{
  "components": [
    {
      "id": "product-1",
      "type": "ProductCard",
      "props": {
        "title": "Wireless Headphones",
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop"
      }
    },
    {
      "id": "product-2",
      "type": "ProductCard",
      "props": {
        "title": "Smart Watch",
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop"
      }
    },
    {
      "id": "product-3",
      "type": "ProductCard",
      "props": {
        "title": "Running Shoes",
        "image": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop"
      }
    },
    {
      "id": "product-4",
      "type": "ProductCard",
      "props": {
        "title": "Laptop",
        "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=400&fit=crop"
      }
    }
  ]
}
```

**Rotation Pattern:** Headphones → Watch → Shoes → Laptop → Phone → Bag → Clothing → Camera (repeat)

### For Social Posts:
**Vary between lifestyle, travel, photography themes**

### For Food Menus:
**Mix meal types:** Burger → Pizza → Salad → Pasta → Sushi (repeat)

## 🚨 CRITICAL RULES:

1. **NEVER leave image/src props empty or with placeholder text**
2. **ALWAYS match image to semantic context** (don't put a burger image on a "Laptop" product)
3. **Use consistent dimensions** within the same component type
4. **Ensure variety** in product grids (no repeated images)
5. **Consider screen type:**
   - E-commerce → Product photos
   - Food → Meal photos
   - Social → Lifestyle/travel photos
   - Auth → Team/security illustrations
   - Dashboard → Data viz themes

## 📚 QUICK REFERENCE BY SCREEN TYPE:

### E-commerce Product Listing:
- SearchInput (no image)
- Grid of 4-8 ProductCards → Use rotation strategy (headphones, watch, shoes, laptop, phone, bag, clothing, camera)
- FloatingActionButton (no image)

### Food Delivery Menu:
- SearchInput (no image)
- Category sections → Use meal-specific images (burgers, pizza, sushi, salads)
- CartItem → Match food type

### Social Feed:
- Avatar → pravatar.cc
- Post images → Lifestyle/travel rotation
- Cover photos → Abstract/geometric

### Auth Screens:
- IllustrationHeader → Welcome/security themes
- No product images needed

### Dashboard:
- StatCards (icons only, no images)
- Hero section → Data visualization theme
- Charts (no images)

## 🎯 YOUR TASK:

When generating components:
1. **Identify the screen category** (ecommerce, food, social, auth, dashboard)
2. **For each visual component**, determine the semantic context
3. **Select the most appropriate image** from the curated library above
4. **Ensure variety** by rotating through subcategories
5. **Use proper URL formatting** with sizing parameters

**Remember:** High-quality, contextually relevant images significantly improve the user experience. Take time to match images intelligently!
"""

###############################################################################
# 🧠 INTEGRATION WITH CoT ORCHESTRATOR
###############################################################################

def get_image_library_for_category(category: str) -> str:
    """
    Get curated image library for a specific screen category.
    
    Args:
        category: Screen category (auth, ecommerce, social, etc.)
        
    Returns:
        Formatted string with relevant image URLs
    """
    if category not in UNSPLASH_IMAGE_LIBRARY:
        return ""
    
    library = UNSPLASH_IMAGE_LIBRARY[category]
    
    output = [f"\n## 🖼️ CURATED IMAGE LIBRARY FOR {category.upper()}\n"]
    
    def format_subcategory(name: str, items: Any, indent: int = 0) -> List[str]:
        """Recursively format nested image library"""
        lines = []
        spaces = "  " * indent
        
        if isinstance(items, dict):
            lines.append(f"{spaces}**{name.upper()}:**")
            for key, value in items.items():
                lines.extend(format_subcategory(key, value, indent + 1))
        elif isinstance(items, list):
            lines.append(f"{spaces}**{name}:**")
            for idx, url in enumerate(items, 1):
                lines.append(f"{spaces}  {idx}. `{url}`")
        else:
            lines.append(f"{spaces}- {name}: `{items}`")
        
        return lines
    
    for key, value in library.items():
        output.extend(format_subcategory(key, value))
    
    return "\n".join(output)


def enhance_prompt_with_images(
    base_prompt: str,
    categories: Set[str]
) -> str:
    """
    Enhance prompt with image selection guidance and relevant image libraries.
    
    Args:
        base_prompt: Original prompt (intent/component generation)
        categories: Detected screen categories
        
    Returns:
        Enhanced prompt with image guidance
    """
    # Always include the general image selection guidelines
    enhanced = f"{base_prompt}\n\n{IMAGE_SELECTION_PROMPT}"
    
    # Add category-specific image libraries
    if categories:
        enhanced += "\n\n# 📚 AVAILABLE IMAGE LIBRARIES FOR YOUR SCREENS:\n"
        for category in categories:
            library_section = get_image_library_for_category(category)
            if library_section:
                enhanced += library_section + "\n"
    
    return enhanced


###############################################################################
# 🔧 HELPER FUNCTIONS
###############################################################################

def get_random_image_from_category(
    category: str,
    subcategory: str = None,
    index: int = 0
) -> str:
    """
    Get a specific image URL from the library (for fallback scenarios).
    
    Args:
        category: Main category (e.g., 'ecommerce')
        subcategory: Subcategory path (e.g., 'electronics.headphones')
        index: Image index within the subcategory
        
    Returns:
        Unsplash image URL
    """
    if category not in UNSPLASH_IMAGE_LIBRARY:
        return "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop"
    
    data = UNSPLASH_IMAGE_LIBRARY[category]
    
    # Navigate nested structure
    if subcategory:
        for key in subcategory.split('.'):
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop"
    
    # Get image from list
    if isinstance(data, list):
        return data[index % len(data)]
    elif isinstance(data, dict):
        # Get first available image list
        for value in data.values():
            if isinstance(value, list):
                return value[index % len(value)]
    
    return "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop"


def validate_image_urls_in_components(components: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate that all visual components have proper image URLs.
    
    Args:
        components: List of component dictionaries
        
    Returns:
        Validation report
    """
    report = {
        "total_components": len(components),
        "visual_components": 0,
        "missing_images": [],
        "invalid_images": [],
        "valid_images": 0
    }
    
    visual_types = [
        "productcard", "cartitem", "image", "illustrationheader",
        "herosection", "avatar", "customproductcard", "customcartitem"
    ]
    
    def check_component(comp: Dict[str, Any], parent_id: str = None):
        comp_type = (comp.get("type") or "").lower()
        comp_id = comp.get("id", "unknown")
        full_id = f"{parent_id}.{comp_id}" if parent_id else comp_id
        
        if comp_type in visual_types:
            report["visual_components"] += 1
            props = comp.get("props", {})
            
            # Check for image property based on component type
            image_prop = None
            if comp_type in ("productcard", "cartitem", "customproductcard", "customcartitem"):
                image_prop = props.get("image")
            elif comp_type in ("image", "customimage"):
                image_prop = props.get("src")
            elif comp_type in ("illustrationheader", "customillustrationheader"):
                image_prop = props.get("illustration")
            elif comp_type in ("herosection", "hero", "customherosection"):
                image_prop = props.get("coverImage")
            elif comp_type in ("avatar", "customavatar"):
                image_prop = props.get("src") or props.get("image")
            
            # Validate image URL
            if not image_prop:
                report["missing_images"].append({
                    "id": full_id,
                    "type": comp_type,
                    "reason": "No image property found"
                })
            elif isinstance(image_prop, str):
                # Check for placeholder/invalid URLs
                invalid_patterns = [
                    "placeholder",
                    "example.com",
                    "via.placeholder",
                    "placehold.co",
                    "dummyimage.com"
                ]
                
                if any(pattern in image_prop.lower() for pattern in invalid_patterns):
                    report["invalid_images"].append({
                        "id": full_id,
                        "type": comp_type,
                        "url": image_prop,
                        "reason": "Placeholder URL detected"
                    })
                elif not image_prop.startswith(("http://", "https://")):
                    report["invalid_images"].append({
                        "id": full_id,
                        "type": comp_type,
                        "url": image_prop,
                        "reason": "Invalid URL format"
                    })
                else:
                    report["valid_images"] += 1
        
        # Recursively check children
        children = comp.get("children", [])
        for child in children:
            check_component(child, full_id)
    
    # Process all components
    for component in components:
        check_component(component)
    
    return report


###############################################################################
# 🎨 INTEGRATION EXAMPLE FOR CoT ORCHESTRATOR
###############################################################################

def integrate_with_cot_orchestrator():
    """
    Example of how to integrate image guidance with existing CoT orchestrator.
    
    USAGE IN cot_orchestrator.py:
```python
    from LLM_Schema.image_guidance_system import enhance_prompt_with_images
    
    def get_enhanced_prompt(base_prompt, user_prompt, design_strategy=None):
        # Step 1: Detect categories
        categories = detect_categories(user_prompt, design_strategy)
        
        # Step 2: Build CoT section
        cot_section = build_cot_prompt(categories)
        
        # Step 3: Add image guidance (NEW!)
        enhanced = enhance_prompt_with_images(
            base_prompt + "\n\n" + cot_section,
            categories
        )
        
        # Step 4: Add user task
        enhanced += f"\n\nUSER INPUT: {user_prompt}\n\nOUTPUT (strict JSON):"
        
        return enhanced
```
    """
    pass


###############################################################################
# 📊 STATISTICS & DEBUGGING
###############################################################################

def get_image_library_stats() -> Dict[str, Any]:
    """Get statistics about the image library"""
    stats = {
        "total_categories": len(UNSPLASH_IMAGE_LIBRARY),
        "categories": {},
        "total_images": 0
    }
    
    def count_images(data):
        count = 0
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            for value in data.values():
                count += count_images(value)
        return count
    
    for category, library in UNSPLASH_IMAGE_LIBRARY.items():
        image_count = count_images(library)
        stats["categories"][category] = {
            "images": image_count,
            "subcategories": len(library) if isinstance(library, dict) else 0
        }
        stats["total_images"] += image_count
    
    return stats


def print_image_library_overview():
    """Print overview of image library"""
    print("\n🖼️ IMAGE LIBRARY OVERVIEW")
    print("=" * 80)
    
    stats = get_image_library_stats()
    
    print(f"Total Categories: {stats['total_categories']}")
    print(f"Total Images: {stats['total_images']}")
    print(f"\nPer-Category Breakdown:")
    
    for category, data in stats['categories'].items():
        print(f"  {category.upper():15} {data['images']:3} images")
        if data['subcategories'] > 0:
            print(f"                  ({data['subcategories']} subcategories)")


###############################################################################
# 🚀 EXPORT PUBLIC API
###############################################################################

__all__ = [
    # Main functions
    "enhance_prompt_with_images",
    "get_image_library_for_category",
    "get_random_image_from_category",
    
    # Validation
    "validate_image_urls_in_components",
    
    # Statistics
    "get_image_library_stats",
    "print_image_library_overview",
    
    # Constants
    "UNSPLASH_IMAGE_LIBRARY",
    "IMAGE_SELECTION_PROMPT",
]


###############################################################################
# 🎮 CLI TESTING INTERFACE
###############################################################################

if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 80)
    print("🖼️ INTELLIGENT IMAGE SELECTION SYSTEM")
    print("=" * 80)
    
    # Print library overview
    print_image_library_overview()
    
    # Run tests if requested
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-library":
            print("\n📚 TESTING IMAGE LIBRARY ACCESS:")
            
            test_cases = [
                ("ecommerce", "electronics.headphones", 0),
                ("ecommerce", "fashion.shoes", 1),
                ("food", "meals.burgers", 0),
                ("social", "profiles.avatars", 2),
                ("auth", "illustrations.welcome", 0),
            ]
            
            for category, subcategory, index in test_cases:
                url = get_random_image_from_category(category, subcategory, index)
                print(f"\n{category} > {subcategory} [{index}]:")
                print(f"  {url}")
        
        elif sys.argv[1] == "--test-validation":
            print("\n🔍 TESTING COMPONENT VALIDATION:")
            
            test_components = [
                {
                    "id": "product-1",
                    "type": "ProductCard",
                    "props": {
                        "title": "Headphones",
                        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop"
                    }
                },
                {
                    "id": "product-2",
                    "type": "ProductCard",
                    "props": {
                        "title": "Laptop",
                        "image": "https://via.placeholder.com/400x300"  # Invalid
                    }
                },
                {
                    "id": "product-3",
                    "type": "ProductCard",
                    "props": {
                        "title": "Watch"
                        # Missing image
                    }
                }
            ]
            
            report = validate_image_urls_in_components(test_components)
            
            print(f"\nTotal Components: {report['total_components']}")
            print(f"Visual Components: {report['visual_components']}")
            print(f"Valid Images: {report['valid_images']}")
            print(f"Missing Images: {len(report['missing_images'])}")
            print(f"Invalid Images: {len(report['invalid_images'])}")
            
            if report["missing_images"]:
                print("\n⚠️ Missing Images:")
                for item in report["missing_images"]:
                    print(f"  - {item['id']} ({item['type']}): {item['reason']}")
            
            if report["invalid_images"]:
                print("\n❌ Invalid Images:")
                for item in report["invalid_images"]:
                    print(f"  - {item['id']} ({item['type']}): {item['reason']}")
                    print(f"    URL: {item['url']}")
        
        elif sys.argv[1] == "--show-category":
            if len(sys.argv) > 2:
                category = sys.argv[2]
                library_text = get_image_library_for_category(category)
                if library_text:
                    print(library_text)
                else:
                    print(f"\n❌ Category '{category}' not found")
                    print(f"Available: {', '.join(UNSPLASH_IMAGE_LIBRARY.keys())}")
            else:
                print("\n❌ Usage: --show-category <category_name>")
                print(f"Available: {', '.join(UNSPLASH_IMAGE_LIBRARY.keys())}")
        
        elif sys.argv[1] == "--demo":
            print("\n🎮 INTERACTIVE DEMO")
            print("=" * 80)
            
            # Simulate component generation with image selection
            print("\n📦 E-commerce Product Grid (4 items):")
            products = ["Headphones", "Smart Watch", "Running Shoes", "Laptop"]
            
            for idx, product in enumerate(products):
                # Determine subcategory
                subcategory_map = {
                    "Headphones": "electronics.headphones",
                    "Smart Watch": "electronics.watches",
                    "Running Shoes": "fashion.shoes",
                    "Laptop": "electronics.laptops"
                }
                
                subcategory = subcategory_map.get(product, "generic_products")
                url = get_random_image_from_category("ecommerce", subcategory, idx)
                
                print(f"\n{idx + 1}. {product}")
                print(f"   Image: {url}")
            
            print("\n🍔 Food Delivery Menu (3 items):")
            meals = ["Classic Burger", "Margherita Pizza", "Fresh Salad"]
            
            for idx, meal in enumerate(meals):
                subcategory_map = {
                    "Classic Burger": "meals.burgers",
                    "Margherita Pizza": "meals.pizza",
                    "Fresh Salad": "meals.salads"
                }
                
                subcategory = subcategory_map.get(meal, "meals")
                url = get_random_image_from_category("food", subcategory, idx)
                
                print(f"\n{idx + 1}. {meal}")
                print(f"   Image: {url}")
    
    else:
        print("\n💡 USAGE:")
        print("  python image_guidance_system.py --test-library      # Test library access")
        print("  python image_guidance_system.py --test-validation   # Test validation")
        print("  python image_guidance_system.py --show-category <cat> # Show category images")
        print("  python image_guidance_system.py --demo              # Interactive demo")
        print("\n📚 IMPORT IN YOUR CODE:")
        print("  from LLM_Schema.image_guidance_system import enhance_prompt_with_images")
        print("  from LLM_Schema.image_guidance_system import validate_image_urls_in_components")