// src/utils/layoutUtils.js
export function ensureLayoutShape(raw) {
  if (!raw) return null;

  // if backend wrapped as { layout: {...} }
  if (raw.layout && typeof raw.layout === "object") raw = raw.layout;

  // If old "screens" key exists, convert to pages with sections preserving nested components
  if (!raw.pages && raw.screens) {
    raw.pages = raw.screens.map((s) => ({
      name: s.name || s.title || "Screen",
      layout_type: s.layout_type || "sectioned",
      sections: [
        {
          name: "Main Section",
          components: s.components || [],
        },
      ],
    }));
  }

  // Ensure pages array
  if (!Array.isArray(raw.pages)) raw.pages = [];

  // Provide default theme/tokens
  raw.theme = raw.theme || raw.tokens?.theme || raw.theme || {
    primary: "#0D9488",
    secondary: "#CCFBF1",
    background: "#F9FAFB",
    text: "#0F172A",
  };

  raw.tokens = raw.tokens || { gap: 16, padding: 20 };

  return raw;
}

/**
 * Walk nested path array (variable length) in a layout object and return:
 * { parent, listRef, index, node } so callers can modify easily.
 *
 * Path is an array like [pageIndex, sectionIndex, compIndex, childIndex, ...]
 */
export function lookupByPath(layout, path = []) {
  if (!Array.isArray(path) || path.length < 3) return { node: null };

  let node = layout.pages?.[path[0]];
  if (!node) return { node: null };
  let parent = null;
  let listRef = null;
  for (let i = 1; i < path.length; i++) {
    if (i === 1) {
      // section
      const sIdx = path[1];
      parent = node;
      node = parent.sections?.[sIdx];
      if (!node) return { node: null };
      continue;
    }
    // remaining indices traverse components or children
    const idx = path[i];
    parent = node;
    let comps = parent.components || parent.props?.items || parent.props?.children;
    if (!Array.isArray(comps)) return { node: null };
    listRef = comps;
    node = comps[idx];
    if (!node) return { node: null };
  }
  return { parent, listRef, node, index: path[path.length - 1] };
}

export function setNodeByPath(layout, path = [], newNode) {
  const copy = JSON.parse(JSON.stringify(layout));
  const lookup = lookupByPath(copy, path);
  if (!lookup.node) return copy;
  if (lookup.listRef && typeof lookup.index === "number") {
    lookup.listRef[lookup.index] = newNode;
  }
  return copy;
}

export function deleteNodeByPath(layout, path = []) {
  const copy = JSON.parse(JSON.stringify(layout));
  if (!Array.isArray(path)) return copy;
  if (path.length < 3) return copy;
  const tail = path[path.length - 1];
  const parentPath = path.slice(0, path.length - 1);
  const lookup = lookupByPath(copy, parentPath);
  if (!lookup.node && !lookup.listRef) return copy;
  const list = lookup.listRef;
  if (!Array.isArray(list)) return copy;
  list.splice(tail, 1);
  return copy;
}

export function ensurePositionAndSizeRecursive(layout) {
  // Mutates layout in-place (used early)
  const ensure = (comp) => {
    comp.props = comp.props || {};
    if (typeof comp.props.x !== "number") comp.props.x = Math.round(Math.random() * 40 + 24);
    if (typeof comp.props.y !== "number") comp.props.y = Math.round(Math.random() * 40 + 24);
    if (typeof comp.props.width !== "number") comp.props.width = comp.props.width ? Number(comp.props.width) : 300;
    if (typeof comp.props.height !== "number") comp.props.height = comp.props.height ? Number(comp.props.height) : 140;
    // children stored in props.items or props.children
    const kids = comp.props.items || comp.props.children;
    if (Array.isArray(kids)) {
      kids.forEach(ensure);
    }
  };

  (layout.pages || []).forEach((page) => {
    (page.sections || []).forEach((sec) => {
      (sec.components || []).forEach(ensure);
    });
  });

  return layout;
}
