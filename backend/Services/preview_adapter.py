# backend/Services/preview_adapter.py
from typing import Dict, Any
from LLM_Schema.normalize import normalize_layout

class PreviewAdapter:
    @staticmethod
    def to_web_preview(component_model: Dict[str, Any]) -> Dict[str, Any]:
        normalized = normalize_layout(component_model or {})
        return {
            "screens": normalized.get("screens", []),
            "theme": normalized.get("theme", {}),
            "tokens": normalized.get("tokens", {})
        }
    
    @staticmethod
    def optimize_for_preview(layout: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optional optimizations for preview rendering.
        Future: lazy loading, placeholder images, etc.
        """
        # For Beta, just return as-is
        return layout