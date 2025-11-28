# backend/background_generator.py
"""
Dynamic Background Generation System
Generates context-aware background configurations for mobile screens
"""

from typing import Dict, Any, List
from enum import Enum

class BackgroundStyle(Enum):
    """Background style categories"""
    GRADIENT = "gradient"
    GEOMETRIC = "geometric"
    GLASSMORPHISM = "glassmorphism"
    FLOATING_SHAPES = "floating_shapes"
    PARTICLES = "particles"
    MESH_GRADIENT = "mesh_gradient"
    AURORA = "aurora"

class BackgroundGenerator:
    """
    Generates dynamic background configurations based on screen type and design strategy.
    Works alongside existing component generation - completely non-invasive.
    """
    
    # Screen type → Background pattern mapping
    BACKGROUND_PATTERNS = {
        "auth": {
            "primary_style": BackgroundStyle.GRADIENT,
            "secondary_style": BackgroundStyle.FLOATING_SHAPES,
            "mood": "welcoming",
            "complexity": "medium",
            "colors": ["primary", "primaryLight", "accent"],
        },
        "ecommerce": {
            "primary_style": BackgroundStyle.MESH_GRADIENT,
            "secondary_style": BackgroundStyle.GEOMETRIC,
            "mood": "energetic",
            "complexity": "high",
            "colors": ["orange", "yellow", "red"],
        },
        "social": {
            "primary_style": BackgroundStyle.AURORA,
            "secondary_style": BackgroundStyle.PARTICLES,
            "mood": "vibrant",
            "complexity": "high",
            "colors": ["blue", "purple", "pink"],
        },
        "dashboard": {
            "primary_style": BackgroundStyle.GEOMETRIC,
            "secondary_style": BackgroundStyle.GLASSMORPHISM,
            "mood": "professional",
            "complexity": "low",
            "colors": ["blue", "cyan", "gray"],
        },
        "onboarding": {
            "primary_style": BackgroundStyle.FLOATING_SHAPES,
            "secondary_style": BackgroundStyle.GRADIENT,
            "mood": "playful",
            "complexity": "medium",
            "colors": ["primary", "secondary", "accent"],
        },
        "settings": {
            "primary_style": BackgroundStyle.GRADIENT,
            "secondary_style": BackgroundStyle.GEOMETRIC,
            "mood": "calm",
            "complexity": "low",
            "colors": ["gray", "blueGray", "slate"],
        },
    }
    
    def __init__(self, theme: Dict[str, Any] = None):
        """Initialize with optional theme override"""
        self.theme = theme or {}
    
    def generate_for_screen(
        self, 
        screen_name: str, 
        screen_type: str, 
        design_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate background configuration for a specific screen.
        
        Args:
            screen_name: Name of the screen (e.g., "Login", "ProductList")
            screen_type: Category (auth, ecommerce, social, dashboard, etc.)
            design_strategy: Design strategy from intent extraction
            
        Returns:
            Background configuration dict with all rendering parameters
        """
        pattern = self.BACKGROUND_PATTERNS.get(
            screen_type, 
            self.BACKGROUND_PATTERNS["auth"]
        )
        
        # Extract theme colors
        primary_color = self.theme.get("primary", "#0D9488")
        design_style = design_strategy.get("design_style", "modern")
        
        # Build background configuration
        background_config = {
            "enabled": True,
            "screen_name": screen_name,
            "screen_type": screen_type,
            "primary_style": pattern["primary_style"].value,
            "secondary_style": pattern["secondary_style"].value,
            "mood": pattern["mood"],
            "complexity": pattern["complexity"],
            
            # Gradient configuration
            "gradient": self._generate_gradient_config(
                pattern["colors"], 
                primary_color,
                design_style
            ),
            
            # Floating shapes configuration
            "floating_shapes": self._generate_shapes_config(
                screen_type,
                pattern["complexity"]
            ),
            
            # Glassmorphism effects
            "glassmorphism": {
                "enabled": pattern["secondary_style"] == BackgroundStyle.GLASSMORPHISM,
                "blur": 10,
                "opacity": 0.1,
            },
            
            # Animation settings
            "animations": {
                "enabled": True,
                "duration": 20000,  # 20 seconds
                "easing": "ease-in-out",
            },
            
            # Performance settings
            "performance": {
                "reduce_motion": False,  # Respect user preferences
                "optimize_for_low_end": False,
            }
        }
        
        return background_config
    
    def _generate_gradient_config(
        self, 
        color_palette: List[str], 
        primary_color: str,
        design_style: str
    ) -> Dict[str, Any]:
        """Generate gradient configuration"""
        
        # Map color names to actual hex values
        color_map = {
            "primary": primary_color,
            "primaryLight": self._lighten_color(primary_color, 20),
            "accent": self._shift_hue(primary_color, 30),
            "blue": "#3B82F6",
            "purple": "#8B5CF6",
            "pink": "#EC4899",
            "orange": "#F97316",
            "yellow": "#FCD34D",
            "teal": "#14B8A6",
            "cyan": "#06B6D4",
            "gray": "#6B7280",
            "blueGray": "#64748B",
            "slate": "#475569",
        }
        
        colors = [color_map.get(c, primary_color) for c in color_palette[:3]]
        
        if design_style == "minimal":
            # Subtle, monochromatic gradient
            return {
                "type": "linear",
                "colors": [colors[0], self._lighten_color(colors[0], 10)],
                "angle": 135,
                "opacity": 0.05,
            }
        elif design_style == "bold":
            # Vibrant, multi-color gradient
            return {
                "type": "radial",
                "colors": colors,
                "center": {"x": 0.5, "y": 0.3},
                "opacity": 0.15,
            }
        else:  # modern (default)
            return {
                "type": "linear",
                "colors": colors[:2],
                "angle": 135,
                "opacity": 0.08,
            }
    
    def _generate_shapes_config(
        self, 
        screen_type: str, 
        complexity: str
    ) -> Dict[str, Any]:
        """Generate floating shapes configuration"""
        
        shape_count = {
            "low": 2,
            "medium": 4,
            "high": 6
        }.get(complexity, 3)
        
        shapes = []
        
        for i in range(shape_count):
            shapes.append({
                "type": ["circle", "square", "blob", "triangle"][i % 4],
                "size": 120 + (i * 40),
                "position": {
                    "x": (i * 25) % 100,
                    "y": (i * 30) % 100,
                },
                "opacity": 0.03 + (i * 0.01),
                "blur": 40 + (i * 10),
                "rotation": i * 45,
                "animation": {
                    "type": "float",
                    "duration": 15000 + (i * 2000),
                    "direction": "alternate",
                }
            })
        
        return {
            "enabled": True,
            "shapes": shapes,
            "blend_mode": "normal",
        }
    
    def _lighten_color(self, hex_color: str, percent: int) -> str:
        """Lighten a hex color by percentage"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb_light = tuple(min(255, int(c + (255 - c) * percent / 100)) for c in rgb)
        return f"#{rgb_light[0]:02x}{rgb_light[1]:02x}{rgb_light[2]:02x}"
    
    def _shift_hue(self, hex_color: str, degrees: int) -> str:
        """Shift hue of a color (simplified)"""
        # Simplified hue shift - in production, use proper HSL conversion
        hex_color = hex_color.lstrip('#')
        rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        # Rotate RGB values
        rgb_shifted = [rgb[(i + 1) % 3] for i in range(3)]
        return f"#{rgb_shifted[0]:02x}{rgb_shifted[1]:02x}{rgb_shifted[2]:02x}"


# Integration function for main.py
def enrich_screens_with_backgrounds(
    screens: List[Dict[str, Any]],
    theme: Dict[str, Any],
    design_strategy: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Enrich screen configurations with background data.
    This is called in main.py after component generation.
    
    Args:
        screens: List of screen dictionaries
        theme: Theme configuration
        design_strategy: Design strategy from intent extraction
        
    Returns:
        Enriched screens with background configurations
    """
    generator = BackgroundGenerator(theme)
    screen_type = design_strategy.get("screen_type", "general")
    
    for screen in screens:
        screen_name = screen.get("name", "Screen")
        
        # Generate background config
        bg_config = generator.generate_for_screen(
            screen_name, 
            screen_type, 
            design_strategy
        )
        
        # Add to screen metadata (doesn't affect components)
        screen["background"] = bg_config
        
        print(f"   🎨 Added {bg_config['primary_style']} background to {screen_name}")
    
    return screens


# Example usage and testing
if __name__ == "__main__":
    # Test background generation
    generator = BackgroundGenerator({
        "primary": "#0D9488",
        "background": "#F7FAFC",
    })
    
    test_screens = [
        ("Login", "auth"),
        ("ProductList", "ecommerce"),
        ("Feed", "social"),
        ("Dashboard", "dashboard"),
    ]
    
    print("\n🎨 BACKGROUND GENERATOR TEST\n")
    
    for screen_name, screen_type in test_screens:
        bg = generator.generate_for_screen(
            screen_name, 
            screen_type, 
            {"design_style": "modern"}
        )
        
        print(f"📱 {screen_name} ({screen_type}):")
        print(f"   Style: {bg['primary_style']} + {bg['secondary_style']}")
        print(f"   Mood: {bg['mood']}")
        print(f"   Shapes: {len(bg['floating_shapes']['shapes'])}")
        print(f"   Gradient: {bg['gradient']['type']} with {len(bg['gradient']['colors'])} colors")
        print()