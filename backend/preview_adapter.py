# backend/preview_adapter.py
from typing import Dict, Any

class PreviewAdapter:
    """
    Converts component model to web-friendly preview format.
    In Beta, component model IS already web-friendly, so this is mostly pass-through.
    Future: Could add web-specific optimizations here.
    """
    
    @staticmethod
    def to_web_preview(component_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert component model to web preview format.
        Currently pass-through since our model is already web-compatible.
        """
        return {
            "screens": component_model.get("screens", []),
            "theme": component_model.get("theme", {}),
            "tokens": component_model.get("tokens", {})
        }
    
    @staticmethod
    def optimize_for_preview(layout: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optional optimizations for preview rendering.
        Future: lazy loading, placeholder images, etc.
        """
        # For Beta, just return as-is
        return layout