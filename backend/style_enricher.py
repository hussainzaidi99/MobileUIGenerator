THEME_PALETTES = {
    "teal":   {"primary": "#0D9488", "background": "#F7FAFC", "surface": "#FFFFFF", "text": "#0F172A"},
    "blue":   {"primary": "#2563EB", "background": "#F8FAFF", "surface": "#FFFFFF", "text": "#0B1220"},
    "green":  {"primary": "#16A34A", "background": "#F6FEF8", "surface": "#FFFFFF", "text": "#06270F"},
    "purple": {"primary": "#7C3AED", "background": "#FBF7FF", "surface": "#FFFFFF", "text": "#1C0B3A"},
    "gray":   {"primary": "#111827", "background": "#F9FAFB", "surface": "#FFFFFF", "text": "#111827"},
}
DEFAULT_THEME = THEME_PALETTES["teal"]
DEFAULT_TOKENS = {
    "gap": 16,
    "padding": 20,
    "cardRadius": 12,
    "cardShadow": "sm",
}

def _pick_theme_from_constraints(constraints):
    cs = " ".join([str(c).lower() for c in (constraints or [])])
    for key in ("teal","blue","green","purple","gray"):
        if key in cs:
            return THEME_PALETTES[key]
    return DEFAULT_THEME

def _merge_theme_tokens(layout, intent):
    layout = layout or {}
    theme = layout.get("theme") if isinstance(layout.get("theme"), dict) else {}
    tokens = layout.get("tokens") if isinstance(layout.get("tokens"), dict) else {}

    chosen = _pick_theme_from_constraints((intent or {}).get("constraints"))
    # do not clobber if already present
    theme = {**chosen, **theme}
    tokens = {**DEFAULT_TOKENS, **tokens}
    layout["theme"] = theme
    layout["tokens"] = tokens
    return layout

def _ensure_padding_on_container(node, tokens):
    props = node.get("props") or {}
    if "padding" not in props:
        props["padding"] = str(tokens.get("padding", 20))
    # light card surfacing for “card-like” things (Container wrapping Feature-ish)
    if props.get("elevated") or props.get("card") or node.get("type","").lower() in ("container","card"):
        props.setdefault("background", tokens.get("cardBg", "#FFFFFF"))
        props.setdefault("radius", tokens.get("cardRadius", 12))
    node["props"] = props

def _ensure_primary_button(node, theme):
    props = node.get("props") or {}
    props.setdefault("variant", "primary")
    props.setdefault("bg", theme.get("primary"))
    props.setdefault("color", "#FFFFFF")
    node["props"] = props

def _decorate_rec(node, theme, tokens):
    if not isinstance(node, dict):
        return node
    t = (node.get("type") or "").lower()
    props = node.get("props") or {}
    children = node.get("children") or []

    if t == "container":
        _ensure_padding_on_container(node, tokens)

    if t == "form":
        # ensure form fields/buttons exist arrays (already normalized earlier)
        props.setdefault("fields", props.get("fields") or [])
        props.setdefault("buttons", props.get("buttons") or [])
        node["props"] = props

    if t == "button":
        _ensure_primary_button(node, theme)

    if t == "header":
        props.setdefault("color", theme.get("text"))
        node["props"] = props

    if t == "image":
        # placeholder images look nicer full-width by default in preview
        props.setdefault("fit", "cover")
        node["props"] = props

    # Recurse children (both direct and props.* arrays)
    out_children = []
    for ch in children:
        out_children.append(_decorate_rec(ch, theme, tokens))
    if out_children:
        node["children"] = out_children

    for k in ("children","items","fields","buttons"):
        v = props.get(k)
        if isinstance(v, list):
            props[k] = [_decorate_rec(ch, theme, tokens) for ch in v]
    node["props"] = props
    return node

def enrich_styles(layout, intent):

    layout = _merge_theme_tokens(layout, intent)
    theme = layout.get("theme", DEFAULT_THEME)
    tokens = layout.get("tokens", DEFAULT_TOKENS)

    for screen in layout.get("screens", []) or []:
        comps = screen.get("components") or []
        screen["components"] = [_decorate_rec(c, theme, tokens) for c in comps]
    return layout
