// src/utils/NormalizeBackendLayout.js

/**
 * Deep clone helper
 */
function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Resolve component using map if exists
 */
function resolveComponent(component, compMap = {}, fallbackId) {
  if (!component) return null;
  if (component.id && compMap[component.id]) return compMap[component.id];
  return { ...component, id: component.id || fallbackId };
}

/**
 * Convert backend structure (props.items / Form.fields / Form.buttons) to frontend structure (children)
 */
function convertBackendToFrontend(components) {
  if (!Array.isArray(components)) return [];

  const canonType = (t) => {
    if (!t) return t;
    const k = String(t).toLowerCase();
    if (k === "password" || k === "passwordinput") return "PasswordInput";
    return t;
  };

  return components.map((comp) => {
    if (!comp || typeof comp !== "object") return comp;

    // start from the raw comp
    const normalizedComp = { ...comp };
    normalizedComp.type = canonType(normalizedComp.type);
    const props = { ...(normalizedComp.props || {}) };

    // seed children from common places
    let children =
      (Array.isArray(props.children) && props.children) ||
      (Array.isArray(props.items) && props.items) ||
      normalizedComp.children ||
      [];

    // ✅ REQUIRED UPDATE:
    // If this is a Form, hoist props.fields and props.buttons into children
    if ((normalizedComp.type || "").toLowerCase() === "form") {
      const fields = Array.isArray(props.fields) ? props.fields : [];
      const buttons = Array.isArray(props.buttons) ? props.buttons : [];

      const hoisted = [
        ...fields.map((f, i) => ({
          id: f?.id || `field-${i}`,
          type: canonType(f?.type || "TextInput"),
          props: {
            ...(f?.props || {}),
            // if it’s a password-like field, mark secure to help inputs render correctly
            ...( /password/i.test(f?.type || "") ? { secure: true } : {} ),
          },
        })),
        ...buttons.map((b, i) => ({
          id: b?.id || `btn-${i}`,
          type: canonType(b?.type || "Button"),
          props: { ...(b?.props || {}) },
        })),
      ];

      // Convert any nested items within hoisted nodes too
      normalizedComp.children = convertBackendToFrontend(hoisted);

      // Clean structural props so renderer doesn't see them
      delete props.fields;
      delete props.buttons;
    } else {
      // For non-Form nodes, also normalize any nested children recursively
      normalizedComp.children = convertBackendToFrontend(children);
    }

    // Always clean structural props on the way out
    const cleanProps = { ...props };
    delete cleanProps.children;
    delete cleanProps.items;

    normalizedComp.props = cleanProps;

    return normalizedComp;
  });
}

/**
 * Normalize backend layout
 */
export function normalizeBackendLayout(rawLayout = {}, intermediate = {}) {
  if (!rawLayout) return { pages: [] };

  const raw =
    rawLayout.layout && typeof rawLayout.layout === "object"
      ? rawLayout.layout
      : rawLayout;

  const compList = (intermediate.components || []).filter(Boolean);
  const compMap = compList.reduce((acc, c) => {
    if (c?.id) acc[c.id] = c;
    return acc;
  }, {});

  const pages = [];

  // Accept either raw.pages or raw.screens
  const screens =
    (Array.isArray(raw.pages) && raw.pages.length ? raw.pages : []) ||
    (Array.isArray(raw.screens) ? raw.screens : []);

  // deterministic fallback blocks (when nothing is provided)
  const generateFallbackComponents = (screenName) => [
    {
      id: `hero-${screenName}`,
      type: "HeroSection",
      props: { title: "Welcome", subtitle: "Your hero section" },
      children: [],
    },
    {
      id: `features-${screenName}`,
      type: "Grid",
      props: { columns: 3 },
      children: [
        {
          id: `feature-1-${screenName}`,
          type: "FeatureCard",
          props: { title: "Feature 1" },
        },
        {
          id: `feature-2-${screenName}`,
          type: "FeatureCard",
          props: { title: "Feature 2" },
        },
        {
          id: `feature-3-${screenName}`,
          type: "FeatureCard",
          props: { title: "Feature 3" },
        },
      ],
    },
    {
      id: `footer-${screenName}`,
      type: "Footer",
      props: { text: "© 2025 Your Company" },
      children: [],
    },
  ];

  if (screens.length === 0) {
    const fallbackComponents = generateFallbackComponents("default");
    pages.push({
      name: raw.name || "Screen",
      layout_type: raw.layout_type || "sectioned",
      sections: [{ name: "Main", components: fallbackComponents }],
    });
  } else {
    screens.forEach((s, si) => {
      const screenName =
        typeof s === "string" ? s : s.name || s.title || `Screen ${si + 1}`;

      const compsRaw =
        typeof s === "object" ? s.components || s.content || s.items || [] : [];

      let components = compsRaw
        .map((c, i) => resolveComponent(c, compMap, `s${si}-c${i}`))
        .filter(Boolean);

      if (components.length === 0) {
        components = generateFallbackComponents(screenName);
      }

      const frontendComponents = convertBackendToFrontend(components);

      pages.push({
        name: screenName,
        layout_type:
          typeof s === "object" ? s.layout_type || "sectioned" : "sectioned",
        sections: [{ name: "Main", components: frontendComponents }],
      });
    });
  }

  return {
    pages,
    tokens: raw.tokens || {},
    theme: raw.theme || {},
  };
}
