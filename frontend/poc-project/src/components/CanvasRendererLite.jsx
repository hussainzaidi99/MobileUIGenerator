// frontend/src/components/CanvasRendererLite.jsx - PRODUCTION READY v3.0
import React, { createContext, useMemo } from "react";
import ComponentRendererLite from "./ComponentRendererLite";
import DynamicBackgroundPreview from "./DynamicBackgroundPreview";

export const ThemeCtx = createContext({ theme: {}, tokens: {} });

/**
 * Safe number parser for CSS variables
 * @param {any} v - Value to parse
 * @param {number} fallback - Fallback value if parsing fails
 * @returns {number} Parsed number or fallback
 */
function toCssVarNumber(v, fallback) {
  const n = typeof v === "number" ? v : parseInt(String(v || ""), 10);
  return Number.isFinite(n) ? n : fallback;
}

/**
 * CanvasRendererLite - Main layout renderer with dynamic background support
 * 
 * Features:
 * - Responsive grid layout (1→2→3 columns)
 * - Dynamic background rendering per screen
 * - Theme context propagation
 * - Safe fallbacks for missing data
 * - Production-grade error handling
 * - Optimized re-rendering with useMemo
 * - Container query support for phone screens
 * 
 * @param {Object} props
 * @param {Object} props.layout - Layout configuration
 * @param {Array} props.layout.screens - Array of screen objects
 * @param {Object} props.layout.theme - Theme colors
 * @param {Object} props.layout.tokens - Design tokens
 */
export default function CanvasRendererLite({ layout }) {
  // Safe extraction with fallbacks
  const screens = Array.isArray(layout?.screens) ? layout.screens : [];
  const theme = layout?.theme || {};
  const tokens = layout?.tokens || {};

  // Normalize tokens to safe numbers
  const safeTokens = useMemo(() => ({
    gap: toCssVarNumber(tokens.gap, 16),
    padding: toCssVarNumber(tokens.padding, 20),
    cardRadius: toCssVarNumber(tokens.cardRadius, 12),
  }), [tokens]);

  // ✅ CACHE-BUSTING: Extract all image URLs from layout
  const extractAllImageUrls = (screens) => {
    const urls = [];

    const extractFromComponent = (comp) => {
      if (!comp) return;

      const props = comp.props || {};
      // Check all possible image properties
      if (props.src) urls.push(props.src);
      if (props.image) urls.push(props.image);
      if (props.illustration) urls.push(props.illustration);
      if (props.coverImage) urls.push(props.coverImage);

      // Recurse through children
      const children = comp.children || [];
      children.forEach(extractFromComponent);
    };

    screens.forEach(screen => {
      const components = screen?.components || [];
      components.forEach(extractFromComponent);
    });

    return urls;
  };

  // ✅ LAYOUT KEY: Generate unique key from image URLs to force re-render
  const layoutKey = useMemo(() => {
    const imageUrls = extractAllImageUrls(screens);
    // Simple hash function
    const hash = imageUrls.join('|').split('').reduce((acc, char) => {
      return ((acc << 5) - acc) + char.charCodeAt(0);
    }, 0);
    return `layout-${hash}`;
  }, [screens]);

  // Memoized theme context
  const ctx = useMemo(() => ({ theme, tokens: safeTokens }), [theme, safeTokens]);

  // Root CSS variables for consistent theming
  const rootStyle = useMemo(() => ({
    "--gap": `${safeTokens.gap}px`,
    "--pad": `${safeTokens.padding}px`,
    "--card-radius": `${safeTokens.cardRadius}px`,
    background: theme.background || "#F8FAFC",
    color: theme.text || "#0F172A",
    minHeight: "100%",
    width: "100%"
  }), [safeTokens, theme]);

  // Memoize screen rendering to prevent unnecessary re-renders
  const renderedScreens = useMemo(() => {
    console.log("[CANVAS] Rendering layout:", {
      screens: screens.length,
      theme,
      tokens: safeTokens
    });

    return screens.map((s, idx) => {
      // Safe screen data extraction
      const screenName = s?.name || `Screen ${idx + 1}`;
      const components = Array.isArray(s?.components) ? s.components : [];
      const backgroundConfig = s?.background || { enabled: false };

      console.log(`[SCREEN] ${screenName}:`, {
        componentCount: components.length,
        backgroundEnabled: backgroundConfig.enabled,
        backgroundStyle: backgroundConfig.primary_style,
        components: components.map(c => ({
          type: c?.type,
          id: c?.id
        }))
      });

      return (
        <div key={`${s?.name || idx}-${layoutKey}`} style={{ width: '100%' }}>
          {/* Dynamic background wrapper for phone content */}
          <DynamicBackgroundPreview config={backgroundConfig}>
            <div style={{
              minHeight: '100%',
              display: 'flex',
              flexDirection: 'column',
              gap: '0',
              boxSizing: 'border-box',
              width: '100%',
            }}>
              {components.length > 0 ? (
                components.map((node, nidx) => {
                  // Validate node structure
                  if (!node || typeof node !== 'object') {
                    console.warn(`[CANVAS] Invalid node at index ${nidx} in screen "${screenName}"`);
                    return null;
                  }

                  console.log(`  ↳ Rendering component ${nidx}:`, node.type, node.id);

                  return (
                    <ComponentRendererLite
                      key={String(node?.id ?? `${screenName}-${idx}-${nidx}`)}
                      node={node}
                    />
                  );
                })
              ) : (
                // Empty screen state
                <div style={{
                  textAlign: "center",
                  padding: "32px 16px",
                  color: "#9CA3AF",
                  background: "rgba(248, 250, 252, 0.5)",
                  borderRadius: "8px",
                  margin: "16px"
                }}>
                  <div style={{
                    fontSize: "32px",
                    marginBottom: "8px"
                  }}>
                    📦
                  </div>
                  <div style={{
                    fontSize: "14px",
                    fontWeight: "500",
                    color: "#64748B"
                  }}>
                    No components in this screen
                  </div>
                  <div style={{
                    fontSize: "12px",
                    color: "#94A3B8",
                    marginTop: "4px"
                  }}>
                    Add components to see them here
                  </div>
                </div>
              )}
            </div>
          </DynamicBackgroundPreview>
        </div>
      );
    });
  }, [screens]); // Only re-render when screens change

  // Empty state - no screens
  if (!screens.length) {
    return (
      <div style={{
        textAlign: "center",
        padding: "48px 24px",
        color: "#9CA3AF",
        minHeight: "400px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center"
      }}>
        <div style={{ fontSize: "64px", marginBottom: "16px" }}>📱</div>
        <div style={{ fontSize: "18px", fontWeight: "600", color: "#64748B" }}>
          No screens to display
        </div>
        <div style={{ fontSize: "14px", color: "#94A3B8", marginTop: "8px" }}>
          Generate a UI to see the preview here
        </div>
      </div>
    );
  }

  return (
    <ThemeCtx.Provider value={ctx}>
      <div className="ui-root" style={rootStyle}>
        {renderedScreens}
      </div>
    </ThemeCtx.Provider>
  );
}