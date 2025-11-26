# backend/cot_orchestrator.py - Category-Based Chain-of-Thought Orchestration
"""
Smart CoT selection system that dynamically loads relevant examples based on screen categories.
Optimized for DeepSeek API with generous token limits.
"""

import re
from typing import List, Dict, Set, Tuple

###############################################################################
# 📚 CATEGORY-SPECIFIC CoT LIBRARIES
###############################################################################

# ============================================================================
# 🔐 AUTH CATEGORY - Login/Signup/Onboarding Flows
# ============================================================================
AUTH_COT_EXAMPLES = """
AUTH SCREEN PATTERNS (Login, Signup, Forgot Password, OTP Verification):

**Core Components:**
- IllustrationHeader: Welcoming visual (auth-welcome, secure-login, signup-success)
- Card: Elevated container (elevation: md, padding: 24)
- IconInput: Email (mail), Password (lock), Name (user), Phone (phone)
- GradientButton: Primary CTA (teal/blue gradient, size: lg)
- SocialButton: OAuth providers (Google, Apple, Facebook)
- Divider: "OR" separator between forms and social login
- LinkButton: "Forgot Password?", "Sign Up", "Terms & Conditions"

**Design Patterns:**
1. **Modern Login:**
   IllustrationHeader(title:"Welcome Back", subtitle:"Sign in to continue")
   → Spacer(32) → Card(elevation:md) → IconInput(icon:mail, label:"Email")
   → Spacer(16) → IconInput(icon:lock, type:password, label:"Password")
   → LinkButton(text:"Forgot Password?", align:right)
   → Spacer(24) → GradientButton(text:"Sign In", gradient:teal, size:lg)
   → Divider(text:"OR") → SocialButton(Google) → Spacer(12) → SocialButton(Apple)

2. **Signup with Name:**
   IllustrationHeader(title:"Create Account", subtitle:"Join us today")
   → Card(elevation:md) → IconInput(icon:user, label:"Full Name")
   → Spacer(16) → IconInput(icon:mail, label:"Email")
   → Spacer(16) → IconInput(icon:lock, type:password, label:"Password")
   → Checkbox(label:"I agree to Terms & Conditions")
   → Spacer(24) → GradientButton(text:"Sign Up", gradient:blue, size:lg)
   → Divider(text:"OR") → SocialButton(Google) → SocialButton(Apple)
   → LinkButton(text:"Already have an account? Sign In", align:center)

3. **OTP Verification:**
   IllustrationHeader(title:"Verify Code", subtitle:"Enter the 6-digit code sent to your email")
   → Card(elevation:md) → Grid(columns:6, gap:8) → TextInput(style:otp) × 6
   → Spacer(24) → GradientButton(text:"Verify", size:lg)
   → LinkButton(text:"Resend Code", align:center)

4. **Forgot Password:**
   IllustrationHeader(title:"Reset Password", subtitle:"Enter your email to receive reset link")
   → Card(elevation:md) → IconInput(icon:mail, label:"Email")
   → Spacer(24) → GradientButton(text:"Send Reset Link", gradient:blue, size:lg)
   → LinkButton(text:"Back to Sign In", align:center)

**Edge Cases:**
- Always include social login for modern auth
- Password fields must have type:password
- Use LinkButton for secondary actions
- Add subtle validation hints (Text with size:sm, color:error)

**Theme Recommendations:**
- Finance/Banking → Blue gradient
- Health/Wellness → Teal/Green
- Tech/SaaS → Purple/Blue
- Social Apps → Vibrant multi-color
"""

# ============================================================================
# 🛒 ECOMMERCE CATEGORY - Shopping, Products, Cart
# ============================================================================
ECOMMERCE_COT_EXAMPLES = """
ECOMMERCE SCREEN PATTERNS (Product List, Product Detail, Cart, Checkout):

**Core Components:**
- SearchInput: Rounded search bar (borderRadius: full, icon: search)
- Grid: Product grid (columns: 2, gap: 16)
- ProductCard: Image, title, price, rating, badge, Add to Cart button
- FloatingActionButton: Cart icon (position: bottom-right, gradient: orange)
- CartItem: Product thumbnail, title, price, QuantityControl, Remove button
- PriceBreakdown: Subtotal, shipping, tax, total
- Badge: Sale tags (color: red, text: "20% OFF")
- TabBar: Navigation (Home, Categories, Cart, Profile)

**Design Patterns:**
1. **Product Listing:**
   SearchInput(placeholder:"Search products...", borderRadius:full)
   → Spacer(16) → Grid(columns:2, gap:16)
   → ProductCard(
       image, title:"Premium Headphones", price:"$99.99", 
       rating:4.5, badge:"Sale", elevation:sm
     ) × N
   → FloatingActionButton(icon:🛒, position:bottom-right, gradient:orange)

2. **Product Detail:**
   Image(src, fit:cover, borderRadius:lg, style:{height:"300px"})
   → Spacer(16) → Header(title:"Premium Wireless Headphones", size:2xl)
   → Rating(value:4.5, reviews:234)
   → Spacer(8) → Header(text:"$99.99", size:3xl, color:teal)
   → Badge(text:"20% OFF", color:red)
   → Spacer(16) → Text(text:"Description...", size:base, color:secondary)
   → Spacer(24) → GradientButton(text:"Add to Cart", gradient:orange, size:lg)
   → Spacer(12) → Button(text:"Buy Now", variant:outline, size:lg)

3. **Shopping Cart:**
   AppBar(title:"Shopping Cart", subtitle:"3 items")
   → CardList(spacing:md)
   → CartItem(
       image, title:"Product Name", price:"$99.99",
       quantity:1, onQuantityChange, onRemove
     ) × N
   → Spacer(16) → PriceBreakdown(
       subtotal:"$299.97", shipping:"$10.00", 
       tax:"$24.00", total:"$333.97"
     )
   → GradientButton(text:"Proceed to Checkout", gradient:orange, size:lg)
   → Button(text:"Continue Shopping", variant:ghost)

4. **Checkout:**
   AppBar(title:"Checkout")
   → FormSection(title:"Shipping Address")
   → IconInput(icon:user, label:"Full Name")
   → Spacer(12) → IconInput(icon:mail, label:"Email")
   → Spacer(12) → IconInput(icon:phone, label:"Phone")
   → TextInput(label:"Address", placeholder:"Street, City, ZIP")
   → Spacer(24) → FormSection(title:"Payment Method")
   → IconInput(icon:💳, label:"Card Number")
   → Grid(columns:2, gap:12) → TextInput(label:"Expiry") + TextInput(label:"CVV")
   → Spacer(24) → PriceBreakdown(total:"$333.97")
   → GradientButton(text:"Place Order", gradient:green, size:lg)

**Edge Cases:**
- Always include SearchInput at top for filtering
- ProductCard must have "Add to Cart" button with gradient
- Use FloatingActionButton for cart access (not TabBar item)
- CartItem needs QuantityControl component
- PriceBreakdown should always show total prominently

**Theme Recommendations:**
- Fashion → Purple/Pink gradients
- Food Delivery → Orange/Red
- Electronics → Blue/Cyan
- Groceries → Green/Teal
"""

# ============================================================================
# 👥 SOCIAL CATEGORY - Feeds, Profiles, Posts
# ============================================================================
SOCIAL_COT_EXAMPLES = """
SOCIAL SCREEN PATTERNS (Feed, Profile, Post Detail, Messaging):

**Core Components:**
- AppBar: Screen title with avatar
- Avatar: User profile picture (sizes: sm, md, lg, xl)
- CardList: Vertical post list (spacing: md)
- Card: Post container (elevation: sm)
- ImageGallery: Horizontal scrollable images
- IconButton: Like (heart), Comment (comment), Share (share)
- TabBar: Bottom navigation
- StatCard: Followers, Following, Posts counts

**Design Patterns:**
1. **Social Feed:**
   AppBar(title:"Feed", avatar, actions:["search", "notifications"])
   → CardList(spacing:md)
   → Card(elevation:sm, padding:16)
     → Container(direction:row, gap:12, align:center)
       → Avatar(size:md, name:"John Doe")
       → Container(direction:column)
         → Text(text:"John Doe", weight:bold, size:base)
         → Text(text:"2 hours ago", size:sm, color:secondary)
     → Spacer(12)
     → Text(text:"Post content here...", size:base)
     → Spacer(12)
     → Image(src, borderRadius:md, fit:cover)
     → Spacer(12)
     → Container(direction:row, gap:16, align:center)
       → IconButton(icon:❤️, label:"1.2k")
       → IconButton(icon:💬, label:"234")
       → IconButton(icon:↗️, label:"Share")
   → FloatingActionButton(icon:➕, gradient:blue, position:bottom-right)
   → TabBar(tabs:["Home", "Search", "Notifications", "Profile"])

2. **User Profile:**
   HeroSection(height:240, coverImage)
   → Container(direction:column, align:center)
     → Avatar(size:xl, name:"John Doe", border, position:center)
     → Spacer(12)
     → Header(title:"John Doe", size:2xl, align:center)
     → Text(text:"@johndoe", size:base, color:secondary, align:center)
     → Text(text:"Bio: Love coding and design", size:sm, align:center)
     → Spacer(16)
     → Grid(columns:3, gap:16)
       → StatCard(value:"1.2k", label:"Posts", color:blue)
       → StatCard(value:"10k", label:"Followers", color:green)
       → StatCard(value:"500", label:"Following", color:purple)
     → Spacer(16)
     → Container(direction:row, gap:12)
       → GradientButton(text:"Follow", gradient:blue, size:md)
       → Button(text:"Message", variant:outline, size:md)
   → Divider(spacing:lg)
   → Grid(columns:3, gap:8) → Image × 9 (user posts grid)
   → TabBar(tabs:["Home", "Search", "Notifications", "Profile"])

3. **Post Detail:**
   AppBar(title:"Post", actions:["share"])
   → Card(elevation:md, padding:20)
     → Container(direction:row, gap:12)
       → Avatar(size:lg, name:"John Doe")
       → Container(direction:column)
         → Text(text:"John Doe", weight:bold)
         → Text(text:"2 hours ago", size:sm, color:secondary)
     → Spacer(16)
     → Text(text:"Post content...", size:base)
     → Spacer(16)
     → Image(src, borderRadius:md)
     → Spacer(16)
     → Container(direction:row, gap:24)
       → IconButton(icon:❤️, label:"1,234 likes")
       → IconButton(icon:💬, label:"56 comments")
   → Divider(text:"Comments")
   → CardList(spacing:sm)
     → Card(elevation:none, padding:12) × N (comments)

4. **Messaging:**
   AppBar(title:"Messages")
   → SearchInput(placeholder:"Search conversations...")
   → Spacer(16)
   → CardList(spacing:sm)
     → Card(elevation:none, padding:16) × N
       → Container(direction:row, gap:12, align:center)
         → Avatar(size:md, name:"Jane Smith")
         → Container(direction:column, flex:1)
           → Text(text:"Jane Smith", weight:bold, size:base)
           → Text(text:"Last message preview...", size:sm, color:secondary)
         → Badge(text:"3", color:blue) (unread count)

**Edge Cases:**
- Always show Avatar for user identification
- Post cards need 3 IconButtons (like, comment, share)
- Profile must show StatCards for followers/following
- Use FloatingActionButton for "Create Post" action
- TabBar should always be at bottom

**Theme Recommendations:**
- Professional Networks → Blue/Gray
- Creative Communities → Purple/Pink
- Lifestyle Apps → Vibrant multi-color
"""

# ============================================================================
# 📊 DASHBOARD CATEGORY - Analytics, Stats, Admin Panels
# ============================================================================
DASHBOARD_COT_EXAMPLES = """
DASHBOARD SCREEN PATTERNS (Analytics, Admin Panel, Reports):

**Core Components:**
- AppBar: Title with subtitle showing date range
- Card: Stats container (elevation: md)
- StatCard: Key metrics with icons
- ProgressBar: Goal progress (with labels)
- Grid: Multi-column layout (2 or 3 columns)
- IconButton: Filter, refresh, export actions

**Design Patterns:**
1. **Analytics Dashboard:**
   AppBar(title:"Dashboard", subtitle:"January 2025")
   → Card(elevation:md, padding:24)
     → Header(title:"Overview", size:xl)
     → Grid(columns:2, gap:16)
       → StatCard(icon:💰, value:"$24,500", label:"Revenue", color:green, elevation:sm)
       → StatCard(icon:👥, value:"1,234", label:"Users", color:blue, elevation:sm)
       → StatCard(icon:📈, value:"+15%", label:"Growth", color:purple, elevation:sm)
       → StatCard(icon:🎯, value:"89%", label:"Conversion", color:orange, elevation:sm)
   → Spacer(24)
   → Card(elevation:md, padding:20)
     → Header(title:"Monthly Goal", size:lg)
     → ProgressBar(value:67, label:"$20,000 / $30,000", color:blue)
   → Spacer(16)
   → Card(elevation:md, padding:20)
     → Header(title:"Top Products", size:lg)
     → List(spacing:md)
       → ListItem(title:"Product A", subtitle:"$5,600", trailing:📊) × 5

2. **Fitness Dashboard:**
   AppBar(title:"Fitness Tracker", subtitle:"Today's Progress")
   → Card(elevation:md, padding:24)
     → Header(title:"Daily Goals", size:xl)
     → Grid(columns:2, gap:16)
       → StatCard(icon:🔥, value:"2,450", label:"Calories", color:orange, elevation:sm)
       → StatCard(icon:👣, value:"8,234", label:"Steps", color:blue, elevation:sm)
       → StatCard(icon:💧, value:"6/8", label:"Water", color:cyan, elevation:sm)
       → StatCard(icon:🌙, value:"7.5h", label:"Sleep", color:purple, elevation:sm)
   → Spacer(24)
   → Card(elevation:md, padding:20)
     → Header(title:"Weekly Progress", size:lg)
     → ProgressBar(value:85, label:"17,000 / 20,000 steps", color:green)
     → Spacer(16)
     → ProgressBar(value:60, label:"1,200 / 2,000 calories", color:orange)
   → Spacer(16)
   → GradientButton(text:"Log Workout", gradient:blue, size:lg)

3. **Admin Panel:**
   AppBar(title:"Admin Panel", actions:["notifications", "settings"])
   → Grid(columns:3, gap:16)
     → StatCard(icon:👤, value:"1,234", label:"Total Users", color:blue)
     → StatCard(icon:📦, value:"567", label:"Orders", color:green)
     → StatCard(icon:💳, value:"$45k", label:"Revenue", color:purple)
   → Spacer(24)
   → Card(elevation:md, padding:20)
     → Header(title:"Recent Activity", size:lg)
     → CardList(spacing:sm)
       → ListItem(icon:✅, title:"Order #1234 completed", subtitle:"2 min ago") × 5

**Edge Cases:**
- StatCards should use icons that match metric type
- Always show Grid with 2-4 StatCards for key metrics
- ProgressBar needs clear labels (current/target)
- Use Card containers to group related stats
- AppBar subtitle should show time period or filters

**Theme Recommendations:**
- Finance → Blue/Green (trust colors)
- Health → Teal/Cyan (calming)
- Admin Panels → Gray/Blue (professional)
"""

# ============================================================================
# 🎯 ONBOARDING CATEGORY - Welcome Flows, Tutorials
# ============================================================================
ONBOARDING_COT_EXAMPLES = """
ONBOARDING SCREEN PATTERNS (Welcome, Tutorial Steps, Permissions):

**Core Components:**
- IllustrationHeader: Large visual (spacing: 2xl)
- ProgressBar: Step indicator (with steps and currentStep)
- Header: Step title (size: 2xl, align: center)
- Text: Step description (size: base, align: center, color: secondary)
- GradientButton: Primary CTA (size: lg)
- Button: Skip option (variant: ghost)

**Design Patterns:**
1. **Multi-Step Onboarding:**
   IllustrationHeader(
     illustration:"welcome-hand", 
     title:"Welcome to AppName",
     subtitle:"Discover amazing features",
     spacing:2xl
   )
   → ProgressBar(value:33, steps:3, currentStep:1, color:blue)
   → Spacer(32)
   → GradientButton(text:"Continue", gradient:blue, size:lg)
   → Spacer(16)
   → Button(text:"Skip", variant:ghost, size:md)

2. **Feature Showcase (Step 2):**
   IllustrationHeader(
     illustration:"features",
     title:"Track Your Progress",
     subtitle:"Set goals and monitor achievements",
     spacing:2xl
   )
   → ProgressBar(value:66, steps:3, currentStep:2, color:blue)
   → Spacer(32)
   → GradientButton(text:"Next", gradient:blue, size:lg)
   → Spacer(16)
   → Button(text:"Skip", variant:ghost)

3. **Permission Request (Step 3):**
   IllustrationHeader(
     illustration:"notifications",
     title:"Stay Updated",
     subtitle:"Enable notifications for important updates",
     spacing:2xl
   )
   → ProgressBar(value:100, steps:3, currentStep:3, color:blue)
   → Spacer(32)
   → GradientButton(text:"Enable Notifications", gradient:green, size:lg)
   → Spacer(16)
   → Button(text:"Maybe Later", variant:ghost)

4. **Setup Complete:**
   IllustrationHeader(
     illustration:"success",
     title:"All Set!",
     subtitle:"You're ready to get started",
     spacing:2xl
   )
   → Spacer(48)
   → GradientButton(text:"Get Started", gradient:green, size:lg)

**Edge Cases:**
- Always include ProgressBar with steps count
- Use IllustrationHeader for every step (spacing: 2xl)
- Primary button should use gradient, secondary is ghost
- Last step should have "Get Started" or "Done" CTA
- Skip button is optional but recommended

**Theme Recommendations:**
- Productivity Apps → Blue/Purple
- Health/Fitness → Teal/Green
- Social Apps → Vibrant multi-color
"""

# ============================================================================
# ⚙️ SETTINGS CATEGORY - Preferences, Account, Profile Edit
# ============================================================================
SETTINGS_COT_EXAMPLES = """
SETTINGS SCREEN PATTERNS (Account Settings, Preferences, Profile Edit):

**Core Components:**
- Header: Section title (size: 2xl)
- FormSection: Grouped settings
- List: Setting items container
- ListItem: Individual setting (icon, title, trailing)
- Switch: Toggle settings
- Avatar: Profile picture
- TextInput: Edit fields

**Design Patterns:**
1. **Settings Menu:**
   Header(title:"Settings", size:2xl)
   → Spacer(24)
   → FormSection(title:"Account", spacing:lg)
     → List(spacing:sm)
       → ListItem(icon:👤, title:"Edit Profile", trailing:chevron-right)
       → ListItem(icon:🔒, title:"Privacy", trailing:chevron-right)
       → ListItem(icon:📧, title:"Email Preferences", trailing:chevron-right)
   → FormSection(title:"Preferences", spacing:lg)
     → List(spacing:sm)
       → ListItem(icon:🔔, title:"Push Notifications", trailing:switch, value:true)
       → ListItem(icon:🎨, title:"Dark Mode", trailing:switch, value:false)
       → ListItem(icon:🌐, title:"Language", subtitle:"English", trailing:chevron-right)
   → FormSection(title:"Support", spacing:lg)
     → List(spacing:sm)
       → ListItem(icon:❓, title:"Help Center", trailing:chevron-right)
       → ListItem(icon:📋, title:"Terms of Service", trailing:chevron-right)
       → ListItem(icon:🚪, title:"Sign Out", trailing:chevron-right)

2. **Edit Profile:**
   Header(title:"Edit Profile", size:2xl)
   → Spacer(16)
   → Avatar(size:xl, name:"John Doe", position:center)
   → Spacer(8)
   → LinkButton(text:"Change Photo", align:center)
   → Spacer(24)
   → FormSection(title:"Personal Information")
     → IconInput(icon:user, label:"Full Name", value:"John Doe")
     → Spacer(16)
     → IconInput(icon:mail, label:"Email", value:"john@example.com")
     → Spacer(16)
     → IconInput(icon:phone, label:"Phone", value:"+1234567890")
     → Spacer(16)
     → TextInput(label:"Bio", placeholder:"Tell us about yourself...", style:{height:"100px"})
   → Spacer(24)
   → GradientButton(text:"Save Changes", gradient:teal, size:lg)
   → Spacer(12)
   → Button(text:"Cancel", variant:ghost)

3. **Notification Settings:**
   Header(title:"Notifications", size:2xl)
   → FormSection(title:"Push Notifications", spacing:lg)
     → List(spacing:md)
       → ListItem(icon:📧, title:"Email Notifications", trailing:switch, value:true)
       → ListItem(icon:💬, title:"Messages", subtitle:"New messages from connections", trailing:switch, value:true)
       → ListItem(icon:❤️, title:"Likes & Comments", trailing:switch, value:false)
       → ListItem(icon:📢, title:"Promotions", trailing:switch, value:false)
   → FormSection(title:"Email Preferences", spacing:lg)
     → List(spacing:md)
       → ListItem(title:"Weekly Summary", trailing:switch, value:true)
       → ListItem(title:"Product Updates", trailing:switch, value:true)

**Edge Cases:**
- Use FormSection to group related settings
- ListItem with trailing:switch for toggles
- ListItem with trailing:chevron-right for navigation
- Edit Profile should have Avatar at top with "Change Photo" link
- Always include "Save Changes" button for edit screens

**Theme Recommendations:**
- Professional Apps → Blue/Gray
- Creative Apps → Purple/Pink
- Productivity → Teal/Blue
"""

###############################################################################
# 🎯 CATEGORY MAPPING & DETECTION
###############################################################################

CATEGORY_KEYWORDS = {
    "auth": [
        "login", "signin", "sign in", "signup", "sign up", "register",
        "authentication", "forgot password", "reset password", "otp",
        "verification", "verify", "password", "email", "auth", "access",
        "account creation", "create account", "social login", "oauth"
    ],
    "ecommerce": [
        "product", "shop", "store", "cart", "checkout", "buy", "purchase",
        "ecommerce", "e-commerce", "shopping", "order", "payment", "price",
        "add to cart", "catalog", "inventory", "payment method", "shipping"
    ],
    "social": [
        "feed", "post", "social", "profile", "follow", "follower", "like",
        "comment", "share", "message", "chat", "conversation", "friend",
        "timeline", "news feed", "activity", "notification", "mention"
    ],
    "dashboard": [
        "dashboard", "analytics", "stats", "report", "metrics", "admin",
        "overview", "summary", "kpi", "chart", "graph", "progress",
        "performance", "revenue", "sales", "users", "tracking", "monitor"
    ],
    "onboarding": [
        "onboard", "welcome", "intro", "tutorial", "getting started", "guide",
        "walkthrough", "setup", "first time", "introduction", "step", "tour"
    ],
    "settings": [
        "settings", "preferences", "configuration", "account", "profile edit",
        "options", "privacy", "security", "notifications", "edit profile",
        "manage account", "change password", "theme", "dark mode"
    ]
}

COT_LIBRARY = {
    "auth": AUTH_COT_EXAMPLES,
    "ecommerce": ECOMMERCE_COT_EXAMPLES,
    "social": SOCIAL_COT_EXAMPLES,
    "dashboard": DASHBOARD_COT_EXAMPLES,
    "onboarding": ONBOARDING_COT_EXAMPLES,
    "settings": SETTINGS_COT_EXAMPLES
}

###############################################################################
# 🧠 ORCHESTRATION LOGIC
###############################################################################

def detect_categories(prompt: str, design_strategy: Dict = None) -> Set[str]:
    """
    Detect relevant categories from user prompt and design strategy.
    
    Args:
        prompt: User's natural language prompt
        design_strategy: Optional design strategy from intent extraction
        
    Returns:
        Set of detected category names
    """
    prompt_lower = prompt.lower()
    detected = set()
    
    # 1. Check design_strategy if available (highest priority)
    if design_strategy and isinstance(design_strategy, dict):
        screen_type = design_strategy.get("screen_type", "").lower()
        if screen_type in COT_LIBRARY:
            detected.add(screen_type)
    
    # 2. Keyword matching
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in prompt_lower:
                detected.add(category)
                break  # One match per category is enough
    
    # 3. Default fallback (if no categories detected)
    if not detected:
        # Try to infer from common patterns
        if any(word in prompt_lower for word in ["screen", "app", "mobile", "ui"]):
            detected.add("auth")  # Most common starting point
    
    return detected


def build_cot_prompt(categories: Set[str], max_categories: int = 3) -> str:
    """
    Build a combined CoT prompt from selected categories.
    
    Args:
        categories: Set of category names
        max_categories: Maximum number of categories to include (token limit)
        
    Returns:
        Combined CoT examples string
    """
    # Limit to max_categories to avoid token overflow
    selected_categories = list(categories)[:max_categories]
    
    if not selected_categories:
        return ""
    
    cot_sections = []
    
    for category in selected_categories:
        if category in COT_LIBRARY:
            cot_sections.append(f"# {category.upper()} CATEGORY")
            cot_sections.append(COT_LIBRARY[category])
            cot_sections.append("\n" + "="*80 + "\n")
    
    combined = "\n\n".join(cot_sections)
    
    print(f"📚 [CoT] Loaded {len(selected_categories)} categories: {', '.join(selected_categories)}")
    print(f"📏 [CoT] Total CoT length: {len(combined)} characters")
    
    return combined


def get_enhanced_prompt(
    base_prompt: str,
    user_prompt: str,
    design_strategy: Dict = None
) -> str:
    """
    Main orchestration function: Combines base prompt + relevant CoT examples.
    
    Args:
        base_prompt: The original compact prompt template
        user_prompt: User's input prompt
        design_strategy: Optional design strategy from intent extraction
        
    Returns:
        Enhanced prompt with relevant CoT examples
    """
    # Detect categories
    categories = detect_categories(user_prompt, design_strategy)
    
    # Build CoT section
    cot_section = build_cot_prompt(categories, max_categories=3)
    
    # Combine: Base Prompt + CoT Examples + User Input
    if cot_section:
        enhanced = f"""{base_prompt}

# ==========================================
# 📚 RELEVANT EXAMPLES & PATTERNS
# ==========================================

{cot_section}

# ==========================================
# 🎯 YOUR TASK
# ==========================================

Now analyze this user prompt and apply the relevant patterns above:

USER INPUT: {user_prompt}

OUTPUT (strict JSON):"""
    else:
        # No CoT needed, use base prompt only
        enhanced = f"{base_prompt}\n\nUSER INPUT: {user_prompt}\n\nOUTPUT (strict JSON):"
    
    return enhanced


###############################################################################
# 🧪 TESTING & VALIDATION
###############################################################################

def test_category_detection():
    """Test category detection with various prompts"""
    test_cases = [
        ("Create login and signup screens", {"auth"}),
        ("E-commerce app with products and cart", {"ecommerce"}),
        ("Social feed with posts and profiles", {"social"}),
        ("Analytics dashboard with stats", {"dashboard"}),
        ("Onboarding flow with 3 steps", {"onboarding"}),
        ("Settings screen with preferences", {"settings"}),
        ("Login, products, and checkout flow", {"auth", "ecommerce"}),
        ("Social app with onboarding", {"social", "onboarding"}),
        ("Dashboard with settings", {"dashboard", "settings"}),
    ]
    
    print("\n🧪 TESTING CATEGORY DETECTION")
    print("=" * 80)
    
    for prompt, expected in test_cases:
        detected = detect_categories(prompt)
        match = "✅" if detected == expected else "❌"
        print(f"{match} Prompt: '{prompt}'")
        print(f"   Expected: {expected}")
        print(f"   Detected: {detected}\n")


def estimate_token_count(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters)"""
    return len(text) // 4


def test_prompt_sizes():
    """Test final prompt sizes for different category combinations"""
    # Simple base prompt for testing (no need to import from llm_client)
    simple_base_prompt = """You are a mobile UI design strategist.
Extract intent and design strategy from user prompt.
Output ONLY valid JSON."""
    
    test_prompts = [
        "Login screen",
        "E-commerce products and cart",
        "Login, signup, products, cart, and profile",
    ]
    
    print("\n📏 TESTING PROMPT SIZES")
    print("=" * 80)
    
    for user_prompt in test_prompts:
        enhanced = get_enhanced_prompt(simple_base_prompt, user_prompt)
        tokens = estimate_token_count(enhanced)
        
        print(f"\nPrompt: '{user_prompt}'")
        print(f"  Characters: {len(enhanced):,}")
        print(f"  Est. Tokens: {tokens:,}")
        print(f"  Categories: {detect_categories(user_prompt)}")


###############################################################################
# 🔧 INTEGRATION HELPERS
###############################################################################

def get_category_stats() -> Dict:
    """Get statistics about CoT library"""
    stats = {}
    
    for category, content in COT_LIBRARY.items():
        stats[category] = {
            "characters": len(content),
            "estimated_tokens": estimate_token_count(content),
            "lines": content.count('\n')
        }
    
    return stats


def print_library_overview():
    """Print overview of CoT library"""
    print("\n📚 CoT LIBRARY OVERVIEW")
    print("=" * 80)
    
    stats = get_category_stats()
    total_chars = sum(s["characters"] for s in stats.values())
    total_tokens = sum(s["estimated_tokens"] for s in stats.values())
    
    print(f"Total Categories: {len(stats)}")
    print(f"Total Size: {total_chars:,} chars (~{total_tokens:,} tokens)")
    print(f"\nPer-Category Breakdown:")
    
    for category, data in stats.items():
        print(f"  {category.upper():12} {data['characters']:7,} chars  ~{data['estimated_tokens']:5,} tokens")
    
    print(f"\nAverage per category: ~{total_tokens // len(stats):,} tokens")
    print(f"Max combined (3 cats): ~{(total_tokens // len(stats)) * 3:,} tokens")


###############################################################################
# 🚀 EXPORT PUBLIC API
###############################################################################

__all__ = [
    # Core functions
    "detect_categories",
    "build_cot_prompt",
    "get_enhanced_prompt",
    
    # Testing
    "test_category_detection",
    "test_prompt_sizes",
    "estimate_token_count",
    
    # Stats
    "get_category_stats",
    "print_library_overview",
    
    # Constants
    "CATEGORY_KEYWORDS",
    "COT_LIBRARY",
]


###############################################################################
# 🎮 CLI TESTING INTERFACE
###############################################################################

if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 80)
    print("🎯 CoT ORCHESTRATION SYSTEM")
    print("=" * 80)
    
    # Print library overview
    print_library_overview()
    
    # Run tests if requested
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-detection":
            test_category_detection()
        
        elif sys.argv[1] == "--test-sizes":
            test_prompt_sizes()
        
        elif sys.argv[1] == "--test-all":
            test_category_detection()
            test_prompt_sizes()
        
        elif sys.argv[1] == "--demo":
            print("\n🎮 INTERACTIVE DEMO")
            print("=" * 80)
            
            demo_prompts = [
                "Modern login and signup with social auth",
                "E-commerce app with product grid and cart",
                "Social feed with posts and profiles",
                "Fitness dashboard with daily stats",
                "Multi-step onboarding flow",
                "Settings screen with preferences"
            ]
            
            for prompt in demo_prompts:
                print(f"\n📝 Prompt: '{prompt}'")
                categories = detect_categories(prompt)
                print(f"   Categories: {', '.join(categories) if categories else 'None'}")
                
                if categories:
                    cot = build_cot_prompt(categories, max_categories=2)
                    tokens = estimate_token_count(cot)
                    print(f"   CoT Size: {len(cot):,} chars (~{tokens:,} tokens)")
    
    else:
        print("\n💡 USAGE:")
        print("  python cot_orchestrator.py --test-detection  # Test category detection")
        print("  python cot_orchestrator.py --test-sizes      # Test prompt sizes")
        print("  python cot_orchestrator.py --test-all        # Run all tests")
        print("  python cot_orchestrator.py --demo            # Interactive demo")
        print("\n📚 IMPORT IN YOUR CODE:")
        print("  from cot_orchestrator import get_enhanced_prompt, detect_categories")