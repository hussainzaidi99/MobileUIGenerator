# backend/LLM_Schema/normalize.py
from typing import Dict, Any, List

# Base synonyms - provider agnostic, shared by preview + RN
SYNONYMS = {
    "textfield": "TextInput", "text_field": "TextInput", "textinput": "TextInput",
    "input": "TextInput",

    "passwordinput": "PasswordInput", "pwd": "PasswordInput", "password": "PasswordInput",

    "cta": "Button", "action": "Button", "primarybutton": "Button", "submit": "Button",

    "heroimage": "Image", "banner": "Image", "hero": "Image",

    "panel": "Card", "card": "Card", "container": "Container",

    "link": "Link", "anchor": "Link", "a": "Link",

    "form": "Form", "group": "Form",

    "header": "Header", "footer": "Footer",
}

# Extra mappings that still preserve semantic component types
SYNONYMS.update({
    # marketing / landing style names
    "herosection": "Container",   # if you don't have a dedicated HeroSection type
    "avatar": "Avatar",           # keep Avatar distinct
    "grid": "Grid",               # keep Grid distinct
    "featurecard": "Card",        # featurecard → Card
})


def _canon_type(raw_type: str) -> str:
    """
    Canonicalize a raw type name from the LLM into a stable component name.
    """
    if not raw_type:
        return "Div"  # generic fallback
    key = str(raw_type).lower().strip()
    if key in SYNONYMS:
        return SYNONYMS[key]
    # If already capitalized, trust it; else title-case it.
    return raw_type if raw_type and raw_type[0].isupper() else str(raw_type).title()


def normalize_component(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a single component object:
    - Canonicalizes type (including synonyms)
    - Ensures props exists
    - Normalizes nested Form fields/buttons
    - Adds small safety defaults for TextInput / Link
    """
    if not isinstance(raw, dict):
        return raw

    t = raw.get("type") or raw.get("kind") or ""
    canon = _canon_type(t)
    raw["type"] = canon

    props = raw.get("props") or {}
    raw["props"] = props

    # Normalize Form children if present
    if canon == "Form":
        fields = props.get("fields") or []
        props["fields"] = [
            {
                "type": _canon_type(f.get("type") or ""),
                "props": f.get("props") or {}
            }
            for f in fields
            if isinstance(f, dict)
        ]

        btns = props.get("buttons") or []
        props["buttons"] = [
            {
                "type": _canon_type(b.get("type") or ""),
                "props": b.get("props") or {}
            }
            for b in btns
            if isinstance(b, dict)
        ]

    # Safety defaults that help preview + RN converters
    if raw.get("type") == "TextInput":
        if "label" not in props and "placeholder" in props:
            props["label"] = props.get("placeholder")

    if raw.get("type") == "Link":
        props.setdefault("href", "#")
        if not props.get("text") and "label" in props:
            props["text"] = props["label"]

    return raw


def normalize_layout(layout: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a layout / component model into a consistent shape:

    Supports:
    - { "layout": { ... } }                     → unwraps to layout
    - { "screen": {...} }                       → wraps into "screens" list
    - { "screens": [{ name, components: [...] }]} → normalizes all components
    - { "components": [...] } with "screen" field on each component
        → groups into screens by name and normalizes
    """
    if not isinstance(layout, dict):
        return layout

    # Unwrap nested layout key if present
    if "layout" in layout and isinstance(layout["layout"], dict):
        layout = layout["layout"]

    # NEW: handle flat component model: { "components": [...] }
    if "screens" not in layout and "components" in layout:
        comps = layout.get("components") or []
        screens_by_name: Dict[str, Dict[str, Any]] = {}

        for c in comps:
            if not isinstance(c, dict):
                continue

            screen_name = c.get("screen") or "Screen"
            norm_comp = normalize_component(c)

            if screen_name not in screens_by_name:
                screens_by_name[screen_name] = {
                    "name": screen_name,
                    "components": []
                }

            screens_by_name[screen_name]["components"].append(norm_comp)

        layout["screens"] = list(screens_by_name.values())

    # Legacy / alternate shape: "screen" → "screens"
    if "screen" in layout and "screens" not in layout:
        layout["screens"] = (
            layout["screen"]
            if isinstance(layout["screen"], list)
            else [layout["screen"]]
        )

    # Normalize each screen's components
    screens = layout.get("screens") or []
    normalized_screens: List[Dict[str, Any]] = []

    for s in screens:
        if not isinstance(s, dict):
            normalized_screens.append(s)
            continue

        comps = s.get("components") or []
        normalized_comps = [normalize_component(c) for c in comps]
        s["components"] = normalized_comps
        normalized_screens.append(s)

    layout["screens"] = normalized_screens

    # Ensure theme is a dict if present
    if "theme" in layout and not isinstance(layout["theme"], dict):
        layout["theme"] = {}

    return layout
