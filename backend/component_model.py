# backend/component_model.py
from typing import Dict, Any, List, Optional
import json

class ComponentModel:
    """
    Manages the component model (single source of truth).
    In Beta, we don't persist to DB - just in-memory management.
    """
    
    def __init__(self, layout: Dict[str, Any]):
        self.layout = layout
        self.screens = layout.get("screens", [])
        self.theme = layout.get("theme", {})
        self.tokens = layout.get("tokens", {})
    
    def get_screen_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific screen by name"""
        for screen in self.screens:
            if screen.get("name") == name:
                return screen
        return None
    
    def get_component_by_id(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Find component by ID across all screens"""
        for screen in self.screens:
            for comp in self._find_in_tree(screen.get("components", []), component_id):
                return comp
        return None
    
    def _find_in_tree(self, components: List[Dict], target_id: str) -> List[Dict]:
        """Recursively search component tree"""
        results = []
        for comp in components:
            if not isinstance(comp, dict):
                continue
            if comp.get("id") == target_id:
                results.append(comp)
            # Search children
            children = comp.get("children") or comp.get("props", {}).get("children") or []
            if isinstance(children, list):
                results.extend(self._find_in_tree(children, target_id))
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary"""
        return {
            "screens": self.screens,
            "theme": self.theme,
            "tokens": self.tokens
        }
    
    def to_json(self) -> str:
        """Export as JSON string"""
        return json.dumps(self.to_dict(), indent=2)


def create_component_model(layout: Dict[str, Any]) -> ComponentModel:
    """Factory function to create ComponentModel"""
    return ComponentModel(layout)