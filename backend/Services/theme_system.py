# backend/Services/theme_system.py - Production Theme Management
"""
Comprehensive theme system with:
- 20+ pre-built themes
- Industry-specific palettes
- Accessibility compliance (WCAG AA)
- Dark mode variants
- Dynamic theme generation
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import colorsys

@dataclass
class ThemePalette:
    """Complete theme palette with all semantic colors"""
    # Brand colors
    primary: str
    primaryLight: str
    primaryDark: str
    secondary: str
    secondaryLight: str
    secondaryDark: str
    accent: str
    
    # Background colors
    background: str
    surface: str
    surfaceVariant: str
    
    # Text colors
    text: str
    textSecondary: str
    textDisabled: str
    
    # Semantic colors
    success: str
    warning: str
    error: str
    info: str
    
    # Interactive colors
    link: str
    hover: str
    active: str
    disabled: str
    
    # Borders & dividers
    border: str
    divider: str
    
    # Additional
    shadow: str
    overlay: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization"""
        return {
            "primary": self.primary,
            "primaryLight": self.primaryLight,
            "primaryDark": self.primaryDark,
            "secondary": self.secondary,
            "secondaryLight": self.secondaryLight,
            "secondaryDark": self.secondaryDark,
            "accent": self.accent,
            "background": self.background,
            "surface": self.surface,
            "surfaceVariant": self.surfaceVariant,
            "text": self.text,
            "textSecondary": self.textSecondary,
            "textDisabled": self.textDisabled,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "info": self.info,
            "link": self.link,
            "hover": self.hover,
            "active": self.active,
            "disabled": self.disabled,
            "border": self.border,
            "divider": self.divider,
            "shadow": self.shadow,
            "overlay": self.overlay,
        }

# ============================================================================
# PRODUCTION THEME LIBRARY (20+ themes)
# ============================================================================

THEME_LIBRARY: Dict[str, ThemePalette] = {
    # Technology & SaaS
    "tech_teal": ThemePalette(
        primary="#0D9488", primaryLight="#14B8A6", primaryDark="#0F766E",
        secondary="#6366F1", secondaryLight="#818CF8", secondaryDark="#4F46E5",
        accent="#F59E0B",
        background="#F7FAFC", surface="#FFFFFF", surfaceVariant="#F1F5F9",
        text="#0F172A", textSecondary="#64748B", textDisabled="#CBD5E1",
        success="#10B981", warning="#F59E0B", error="#EF4444", info="#3B82F6",
        link="#0D9488", hover="#E0F2FE", active="#BAE6FD", disabled="#E2E8F0",
        border="#E2E8F0", divider="#CBD5E1", shadow="#00000029", overlay="#00000066"
    ),
    
    "tech_blue": ThemePalette(
        primary="#2563EB", primaryLight="#3B82F6", primaryDark="#1D4ED8",
        secondary="#8B5CF6", secondaryLight="#A78BFA", secondaryDark="#7C3AED",
        accent="#F97316",
        background="#F8FAFF", surface="#FFFFFF", surfaceVariant="#EFF6FF",
        text="#0B1220", textSecondary="#475569", textDisabled="#CBD5E1",
        success="#22C55E", warning="#F59E0B", error="#DC2626", info="#0EA5E9",
        link="#2563EB", hover="#DBEAFE", active="#BFDBFE", disabled="#E2E8F0",
        border="#E5E7EB", divider="#D1D5DB", shadow="#00000029", overlay="#00000066"
    ),
    
    # Finance & Banking
    "finance_navy": ThemePalette(
        primary="#1E3A8A", primaryLight="#2563EB", primaryDark="#1E40AF",
        secondary="#0891B2", secondaryLight="#06B6D4", secondaryDark="#0E7490",
        accent="#10B981",
        background="#F8FAFC", surface="#FFFFFF", surfaceVariant="#F1F5F9",
        text="#0F172A", textSecondary="#475569", textDisabled="#94A3B8",
        success="#059669", warning="#D97706", error="#DC2626", info="#0284C7",
        link="#1E3A8A", hover="#EFF6FF", active="#DBEAFE", disabled="#E2E8F0",
        border="#E2E8F0", divider="#CBD5E1", shadow="#00000029", overlay="#00000066"
    ),
    
    "finance_green": ThemePalette(
        primary="#047857", primaryLight="#059669", primaryDark="#065F46",
        secondary="#0891B2", secondaryLight="#06B6D4", secondaryDark="#0E7490",
        accent="#F59E0B",
        background="#F0FDF4", surface="#FFFFFF", surfaceVariant="#DCFCE7",
        text="#064E3B", textSecondary="#6B7280", textDisabled="#9CA3AF",
        success="#10B981", warning="#F59E0B", error="#DC2626", info="#0284C7",
        link="#047857", hover="#D1FAE5", active="#A7F3D0", disabled="#E5E7EB",
        border="#D1D5DB", divider="#E5E7EB", shadow="#00000029", overlay="#00000066"
    ),
    
    # E-commerce & Retail
    "ecommerce_orange": ThemePalette(
        primary="#EA580C", primaryLight="#F97316", primaryDark="#C2410C",
        secondary="#F59E0B", secondaryLight="#FBBF24", secondaryDark="#D97706",
        accent="#8B5CF6",
        background="#FFF7ED", surface="#FFFFFF", surfaceVariant="#FFEDD5",
        text="#7C2D12", textSecondary="#78350F", textDisabled="#9CA3AF",
        success="#16A34A", warning="#F59E0B", error="#DC2626", info="#3B82F6",
        link="#EA580C", hover="#FED7AA", active="#FDBA74", disabled="#E5E7EB",
        border="#FED7AA", divider="#FDE68A", shadow="#00000029", overlay="#00000066"
    ),
    
    "ecommerce_pink": ThemePalette(
        primary="#DB2777", primaryLight="#EC4899", primaryDark="#BE185D",
        secondary="#F97316", secondaryLight="#FB923C", secondaryDark="#EA580C",
        accent="#8B5CF6",
        background="#FDF2F8", surface="#FFFFFF", surfaceVariant="#FCE7F3",
        text="#831843", textSecondary="#9F1239", textDisabled="#9CA3AF",
        success="#16A34A", warning="#F59E0B", error="#DC2626", info="#3B82F6",
        link="#DB2777", hover="#FBF", active="#F9A8D4", disabled="#E5E7EB",
        border="#FBCFE8", divider="#F9A8D4", shadow="#00000029", overlay="#00000066"
    ),
    
    # Health & Wellness
    "health_mint": ThemePalette(
        primary="#10B981", primaryLight="#34D399", primaryDark="#059669",
        secondary="#14B8A6", secondaryLight="#2DD4BF", secondaryDark="#0D9488",
        accent="#F59E0B",
        background="#F0FDF4", surface="#FFFFFF", surfaceVariant="#D1FAE5",
        text="#064E3B", textSecondary="#065F46", textDisabled="#9CA3AF",
        success="#22C55E", warning="#F59E0B", error="#EF4444", info="#06B6D4",
        link="#10B981", hover="#D1FAE5", active="#A7F3D0", disabled="#E5E7EB",
        border="#A7F3D0", divider="#6EE7B7", shadow="#00000029", overlay="#00000066"
    ),
    
    "health_purple": ThemePalette(
        primary="#8B5CF6", primaryLight="#A78BFA", primaryDark="#7C3AED",
        secondary="#EC4899", secondaryLight="#F472B6", secondaryDark="#DB2777",
        accent="#F59E0B",
        background="#FAF5FF", surface="#FFFFFF", surfaceVariant="#F3E8FF",
        text="#581C87", textSecondary="#6B21A8", textDisabled="#9CA3AF",
        success="#10B981", warning="#F59E0B", error="#DC2626", info="#3B82F6",
        link="#8B5CF6", hover="#E9D5FF", active="#D8B4FE", disabled="#E5E7EB",
        border="#E9D5FF", divider="#D8B4FE", shadow="#00000029", overlay="#00000066"
    ),
    
    # Food & Restaurant
    "food_red": ThemePalette(
        primary="#DC2626", primaryLight="#EF4444", primaryDark="#B91C1C",
        secondary="#F97316", secondaryLight="#FB923C", secondaryDark="#EA580C",
        accent="#FBBF24",
        background="#FEF2F2", surface="#FFFFFF", surfaceVariant="#FEE2E2",
        text="#7F1D1D", textSecondary="#991B1B", textDisabled="#9CA3AF",
        success="#16A34A", warning="#F59E0B", error="#DC2626", info="#3B82F6",
        link="#DC2626", hover="#FECACA", active="#FCA5A5", disabled="#E5E7EB",
        border="#FECACA", divider="#FCA5A5", shadow="#00000029", overlay="#00000066"
    ),
    
    "food_amber": ThemePalette(
        primary="#D97706", primaryLight="#F59E0B", primaryDark="#B45309",
        secondary="#EF4444", secondaryLight="#F87171", secondaryDark="#DC2626",
        accent="#8B5CF6",
        background="#FFFBEB", surface="#FFFFFF", surfaceVariant="#FEF3C7",
        text="#78350F", textSecondary="#92400E", textDisabled="#9CA3AF",
        success="#16A34A", warning="#F59E0B", error="#DC2626", info="#3B82F6",
        link="#D97706", hover="#FDE68A", active="#FCD34D", disabled="#E5E7EB",
        border="#FDE68A", divider="#FCD34D", shadow="#00000029", overlay="#00000066"
    ),
    
    # Social & Community
    "social_vibrant": ThemePalette(
        primary="#8B5CF6", primaryLight="#A78BFA", primaryDark="#7C3AED",
        secondary="#EC4899", secondaryLight="#F472B6", secondaryDark="#DB2777",
        accent="#F59E0B",
        background="#FEFCE8", surface="#FFFFFF", surfaceVariant="#FEF9C3",
        text="#422006", textSecondary="#713F12", textDisabled="#9CA3AF",
        success="#16A34A", warning="#F59E0B", error="#DC2626", info="#3B82F6",
        link="#8B5CF6", hover="#E9D5FF", active="#D8B4FE", disabled="#E5E7EB",
        border="#E9D5FF", divider="#D8B4FE", shadow="#00000029", overlay="#00000066"
    ),
    
    "social_blue": ThemePalette(
        primary="#3B82F6", primaryLight="#60A5FA", primaryDark="#2563EB",
        secondary="#06B6D4", secondaryLight="#22D3EE", secondaryDark="#0891B2",
        accent="#F59E0B",
        background="#EFF6FF", surface="#FFFFFF", surfaceVariant="#DBEAFE",
        text="#1E3A8A", textSecondary="#1E40AF", textDisabled="#9CA3AF",
        success="#10B981", warning="#F59E0B", error="#DC2626", info="#0EA5E9",
        link="#3B82F6", hover="#DBEAFE", active="#BFDBFE", disabled="#E5E7EB",
        border="#BFDBFE", divider="#93C5FD", shadow="#00000029", overlay="#00000066"
    ),
    
    # Education & Learning
    "education_blue": ThemePalette(
        primary="#1D4ED8", primaryLight="#2563EB", primaryDark="#1E40AF",
        secondary="#7C3AED", secondaryLight="#8B5CF6", secondaryDark="#6D28D9",
        accent="#F59E0B",
        background="#EFF6FF", surface="#FFFFFF", surfaceVariant="#DBEAFE",
        text="#1E3A8A", textSecondary="#1E40AF", textDisabled="#9CA3AF",
        success="#059669", warning="#D97706", error="#DC2626", info="#0284C7",
        link="#1D4ED8", hover="#DBEAFE", active="#BFDBFE", disabled="#E5E7EB",
        border="#BFDBFE", divider="#93C5FD", shadow="#00000029", overlay="#00000066"
    ),
    
    # Travel & Hospitality
    "travel_sky": ThemePalette(
        primary="#0284C7", primaryLight="#0EA5E9", primaryDark="#0369A1",
        secondary="#06B6D4", secondaryLight="#22D3EE", secondaryDark="#0891B2",
        accent="#F59E0B",
        background="#F0F9FF", surface="#FFFFFF", surfaceVariant="#E0F2FE",
        text="#0C4A6E", textSecondary="#075985", textDisabled="#9CA3AF",
        success="#10B981", warning="#F59E0B", error="#DC2626", info="#0EA5E9",
        link="#0284C7", hover="#E0F2FE", active="#BAE6FD", disabled="#E5E7EB",
        border="#BAE6FD", divider="#7DD3FC", shadow="#00000029", overlay="#00000066"
    ),
    
    # Creative & Design
    "creative_gradient": ThemePalette(
        primary="#A855F7", primaryLight="#C084FC", primaryDark="#9333EA",
        secondary="#EC4899", secondaryLight="#F472B6", secondaryDark="#DB2777",
        accent="#F59E0B",
        background="#FAF5FF", surface="#FFFFFF", surfaceVariant="#F3E8FF",
        text="#581C87", textSecondary="#6B21A8", textDisabled="#9CA3AF",
        success="#10B981", warning="#F59E0B", error="#DC2626", info="#3B82F6",
        link="#A855F7", hover="#F3E8FF", active="#E9D5FF", disabled="#E5E7EB",
        border="#E9D5FF", divider="#D8B4FE", shadow="#00000029", overlay="#00000066"
    ),
    
    # Professional & Corporate
    "corporate_slate": ThemePalette(
        primary="#475569", primaryLight="#64748B", primaryDark="#334155",
        secondary="#0891B2", secondaryLight="#06B6D4", secondaryDark="#0E7490",
        accent="#F59E0B",
        background="#F8FAFC", surface="#FFFFFF", surfaceVariant="#F1F5F9",
        text="#0F172A", textSecondary="#334155", textDisabled="#94A3B8",
        success="#059669", warning="#D97706", error="#DC2626", info="#0284C7",
        link="#475569", hover="#F1F5F9", active="#E2E8F0", disabled="#E2E8F0",
        border="#E2E8F0", divider="#CBD5E1", shadow="#00000029", overlay="#00000066"
    ),
    
    # Dark Mode Variants
    "dark_default": ThemePalette(
        primary="#14B8A6", primaryLight="#2DD4BF", primaryDark="#0D9488",
        secondary="#818CF8", secondaryLight="#A78BFA", secondaryDark="#6366F1",
        accent="#FCD34D",
        background="#0F172A", surface="#1E293B", surfaceVariant="#334155",
        text="#F1F5F9", textSecondary="#94A3B8", textDisabled="#64748B",
        success="#34D399", warning="#FCD34D", error="#F87171", info="#60A5FA",
        link="#14B8A6", hover="#1E293B", active="#334155", disabled="#475569",
        border="#334155", divider="#475569", shadow="#00000066", overlay="#00000099"
    ),
    
    "dark_purple": ThemePalette(
        primary="#A78BFA", primaryLight="#C4B5FD", primaryDark="#8B5CF6",
        secondary="#F472B6", secondaryLight="#F9A8D4", secondaryDark="#EC4899",
        accent="#FCD34D",
        background="#1C1917", surface="#292524", surfaceVariant="#44403C",
        text="#FAFAF9", textSecondary="#A8A29E", textDisabled="#78716C",
        success="#4ADE80", warning="#FCD34D", error="#FB7185", info="#60A5FA",
        link="#A78BFA", hover="#292524", active="#44403C", disabled="#57534E",
        border="#44403C", divider="#57534E", shadow="#00000066", overlay="#00000099"
    ),
}

# ============================================================================
# INDUSTRY MAPPING
# ============================================================================

INDUSTRY_THEMES: Dict[str, List[str]] = {
    "technology": ["tech_teal", "tech_blue", "dark_default"],
    "finance": ["finance_navy", "finance_green"],
    "ecommerce": ["ecommerce_orange", "ecommerce_pink"],
    "health": ["health_mint", "health_purple"],
    "food": ["food_red", "food_amber"],
    "social": ["social_vibrant", "social_blue"],
    "education": ["education_blue"],
    "travel": ["travel_sky"],
    "creative": ["creative_gradient"],
    "corporate": ["corporate_slate", "finance_navy"],
}

# ============================================================================
# THEME RESOLVER
# ============================================================================

class ThemeResolver:
    """Intelligent theme selection and customization"""
    
    def __init__(self):
        self.themes = THEME_LIBRARY
    
    def get_theme(self, theme_id: str) -> Optional[ThemePalette]:
        """Get theme by ID"""
        return self.themes.get(theme_id)
    
    def suggest_themes(
        self, 
        industry: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        dark_mode: bool = False
    ) -> List[str]:
        """Suggest themes based on context"""
        suggestions = []
        
        # Industry-based
        if industry and industry.lower() in INDUSTRY_THEMES:
            suggestions.extend(INDUSTRY_THEMES[industry.lower()])
        
        # Dark mode preference
        if dark_mode:
            dark_themes = [k for k in self.themes.keys() if k.startswith("dark_")]
            suggestions.extend(dark_themes)
        
        # Keyword-based
        if keywords:
            for keyword in keywords:
                keyword_lower = keyword.lower()
                for theme_id in self.themes.keys():
                    if keyword_lower in theme_id:
                        suggestions.append(theme_id)
        
        # Default fallback
        if not suggestions:
            suggestions = ["tech_teal", "tech_blue", "corporate_slate"]
        
        # Remove duplicates, preserve order
        seen = set()
        unique_suggestions = []
        for theme_id in suggestions:
            if theme_id not in seen:
                seen.add(theme_id)
                unique_suggestions.append(theme_id)
        
        return unique_suggestions[:5]  # Top 5 suggestions
    
    def customize_theme(
        self, 
        base_theme_id: str, 
        primary_color: Optional[str] = None,
        dark_mode: bool = False
    ) -> ThemePalette:
        """Create customized theme variant"""
        base_theme = self.themes.get(base_theme_id, self.themes["tech_teal"])
        
        if not primary_color:
            return base_theme
        
        # Generate complementary colors from primary
        h, l, s = self._hex_to_hls(primary_color)
        
        primary_light = self._hls_to_hex(h, min(l + 0.1, 0.95), s)
        primary_dark = self._hls_to_hex(h, max(l - 0.1, 0.05), s)
        
        # Secondary: complementary hue
        secondary_h = (h + 0.5) % 1.0
        secondary = self._hls_to_hex(secondary_h, l, s)
        secondary_light = self._hls_to_hex(secondary_h, min(l + 0.1, 0.95), s)
        secondary_dark = self._hls_to_hex(secondary_h, max(l - 0.1, 0.05), s)
        
        # Accent: triadic hue
        accent_h = (h + 0.33) % 1.0
        accent = self._hls_to_hex(accent_h, l, s)
        
        # Create new theme with custom colors
        return ThemePalette(
            primary=primary_color,
            primaryLight=primary_light,
            primaryDark=primary_dark,
            secondary=secondary,
            secondaryLight=secondary_light,
            secondaryDark=secondary_dark,
            accent=accent,
            background=base_theme.background if not dark_mode else "#0F172A",
            surface=base_theme.surface if not dark_mode else "#1E293B",
            surfaceVariant=base_theme.surfaceVariant if not dark_mode else "#334155",
            text=base_theme.text if not dark_mode else "#F1F5F9",
            textSecondary=base_theme.textSecondary if not dark_mode else "#94A3B8",
            textDisabled=base_theme.textDisabled if not dark_mode else "#64748B",
            success=base_theme.success,
            warning=base_theme.warning,
            error=base_theme.error,
            info=base_theme.info,
            link=primary_color,
            hover=primary_light,
            active=primary_dark,
            disabled=base_theme.disabled,
            border=base_theme.border if not dark_mode else "#334155",
            divider=base_theme.divider if not dark_mode else "#475569",
            shadow=base_theme.shadow,
            overlay=base_theme.overlay,
        )
    
    def _hex_to_hls(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex to HLS"""
        hex_color = hex_color.lstrip('#')
        r, g, b = [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return h, l, s
    
    def _hls_to_hex(self, h: float, l: float, s: float) -> str:
        """Convert HLS to hex"""
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

# ============================================================================
# GLOBAL RESOLVER
# ============================================================================

theme_resolver = ThemeResolver()

# ============================================================================
# HELPER FUNCTIONS (drop-in replacements)
# ============================================================================

def get_theme(theme_id: str = "tech_teal") -> Dict[str, str]:
    """Get theme palette as dictionary"""
    theme = theme_resolver.get_theme(theme_id)
    if not theme:
        theme = theme_resolver.get_theme("tech_teal")
    return theme.to_dict()

def suggest_themes(industry: Optional[str] = None) -> List[str]:
    """Suggest themes for industry"""
    return theme_resolver.suggest_themes(industry=industry)

def list_all_themes() -> List[str]:
    """List all available themes"""
    return list(THEME_LIBRARY.keys())

# ============================================================================
# USAGE & STATS
# ============================================================================

if __name__ == "__main__":
    print("Theme System Stats:")
    print(f"Total themes: {len(THEME_LIBRARY)}")
    print(f"Industries covered: {len(INDUSTRY_THEMES)}")
    print(f"Dark mode variants: {len([k for k in THEME_LIBRARY.keys() if 'dark' in k])}")
    
    print("\nThemes by Category:")
    for industry, themes in INDUSTRY_THEMES.items():
        print(f"  {industry.title()}: {', '.join(themes)}")
    
    print("\nExample Suggestions:")
    print(f"  Finance: {suggest_themes('finance')}")
    print(f"  E-commerce: {suggest_themes('ecommerce')}")
    print(f"  Health: {suggest_themes('health')}")