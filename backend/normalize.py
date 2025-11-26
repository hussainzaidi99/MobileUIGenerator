# backend/normalize.py
from typing import Dict, Any, List

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

# 🔧 Add these extra mappings for the web-lite preview
SYNONYMS.update({
    # marketing/landing synonyms → primitives your React preview understands
    "herosection": "Container",
    "avatar": "Image",
    "grid": "Container",
    "featurecard": "Container",
    "card": "Container",  # override to Container for preview simplicity
})

def _canon_type(raw_type: str) -> str:
    if not raw_type:
        return "Div"
    key = str(raw_type).lower().strip()
    if key in SYNONYMS:
        return SYNONYMS[key]
    return raw_type if raw_type and raw_type[0].isupper() else raw_type.title()

def normalize_component(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return raw
    t = raw.get("type") or raw.get("kind") or ""
    canon = _canon_type(t)
    raw["type"] = canon

    props = raw.get("props") or {}
    raw["props"] = props

    # Hoist/normalize Form fields & buttons to canonical types
    if canon == "Form":
        fields = props.get("fields") or []
        props["fields"] = [
            {"type": _canon_type(f.get("type") or ""), "props": f.get("props") or {}}
            for f in fields if isinstance(f, dict)
        ]
        btns = props.get("buttons") or []
        props["buttons"] = [
            {"type": _canon_type(b.get("type") or ""), "props": b.get("props") or {}}
            for b in btns if isinstance(b, dict)
        ]

    # Small safety defaults that help the web-lite preview
    if raw.get("type") == "TextInput":
        if "label" not in props and "placeholder" in props:
            props["label"] = props.get("placeholder")
    if raw.get("type") == "Link":
        props.setdefault("href", "#")
        if not props.get("text"):
            # if LLM gave 'label' for links, map it to text
            if "label" in props:
                props["text"] = props["label"]

    return raw

def normalize_layout(layout: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(layout, dict):
        return layout

    if "layout" in layout and isinstance(layout["layout"], dict):
        layout = layout["layout"]

    if "screen" in layout and "screens" not in layout:
        layout["screens"] = layout["screen"] if isinstance(layout["screen"], list) else [layout["screen"]]

    screens = layout.get("screens") or []
    normalized_screens = []
    for s in screens:
        if not isinstance(s, dict):
            normalized_screens.append(s)
            continue
        comps = s.get("components") or []
        normalized_comps = [normalize_component(c) for c in comps]
        s["components"] = normalized_comps
        normalized_screens.append(s)
    layout["screens"] = normalized_screens

    if "theme" in layout and not isinstance(layout["theme"], dict):
        layout["theme"] = {}

    return layout
