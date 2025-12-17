// frontend/src/components/CanvasRendererLite.jsx - PRODUCTION READY v2.3
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
 * Features:
 * - Responsive grid layout (1→2→3 columns)
 * - Dynamic background rendering per screen
 * - Theme context propagation
 * - Safe fallbacks for missing data
 * - Production-grade error handling
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

  // Memoized theme context
  const ctx = useMemo(() => ({ theme, tokens: safeTokens }), [theme, safeTokens]);

  console.log("[CANVAS] Rendering layout:", {
    screens: screens.length,
    theme,
    tokens: safeTokens
  });

  // Empty state
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

  // Root CSS variables for consistent theming
  const rootStyle = {
    "--gap": `${safeTokens.gap}px`,
    "--pad": `${safeTokens.padding}px`,
    "--card-radius": `${safeTokens.cardRadius}px`,
    background: theme.background || "#F8FAFC",
    color: theme.text || "#0F172A",
    minHeight: "100%",
    width: "100%"
  };

  return (
    <ThemeCtx.Provider value={ctx}>
      <div className="ui-root" style={rootStyle}>
        {/* Single screen rendering - no additional wrapper */}
        {screens.map((s, idx) => {
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
            <div key={s?.name || idx} style={{ width: '100%' }}>
              {/* Dynamic background wrapper for phone content */}
              <DynamicBackgroundPreview config={backgroundConfig}>
                <div style={{ 
                  padding: '16px',
                  minHeight: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: `${safeTokens.gap}px`
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
        })}
      </div>
    </ThemeCtx.Provider>
  );
}