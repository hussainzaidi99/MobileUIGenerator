// frontend/src/components/CanvasRendererLite.jsx - ULTIMATE VERSION
import React, { createContext, useMemo } from "react";
import ComponentRendererLite from "./ComponentRendererLite";

export const ThemeCtx = createContext({ theme: {}, tokens: {} });

function toCssVarNumber(v, fallback) {
  const n = typeof v === "number" ? v : parseInt(String(v || ""), 10);
  return Number.isFinite(n) ? n : fallback;
}

export default function CanvasRendererLite({ layout }) {
  const screens = Array.isArray(layout?.screens) ? layout.screens : [];
  const theme = layout?.theme || {};
  const tokens = layout?.tokens || {};

  const safeTokens = {
    gap: toCssVarNumber(tokens.gap, 16),
    padding: toCssVarNumber(tokens.padding, 20),
    cardRadius: toCssVarNumber(tokens.cardRadius, 12),
  };

  const ctx = useMemo(() => ({ theme, tokens: safeTokens }), [theme, safeTokens]);

  console.log("[CANVAS] Rendering layout:", {
    screens: screens.length,
    theme,
    tokens: safeTokens
  });

  if (!screens.length) {
    return (
      <div style={{ textAlign: "center", padding: "48px 24px", color: "#9CA3AF" }}>
        <div style={{ fontSize: "64px", marginBottom: "16px" }}>📱</div>
        <div style={{ fontSize: "18px", fontWeight: "600", color: "#64748B" }}>
          No screens to display
        </div>
      </div>
    );
  }

  // CSS vars for consistent spacing/colors
  const rootStyle = {
    "--gap": `${safeTokens.gap}px`,
    "--pad": `${safeTokens.padding}px`,
    "--card-radius": `${safeTokens.cardRadius}px`,
    background: theme.background || "#F8FAFC",
    color: theme.text || "#0F172A",
    minHeight: "100%"
  };

  return (
    <ThemeCtx.Provider value={ctx}>
      <div className="ui-root" style={rootStyle}>
        {/* RESPONSIVE GRID: 1 → 2 → 3 columns */}
        <div className="screens-grid">
          {screens.map((s, idx) => {
            const screenName = s?.name || `Screen ${idx + 1}`;
            const components = Array.isArray(s?.components) ? s.components : [];

            console.log(`[SCREEN] ${screenName}:`, {
              componentCount: components.length,
              components: components.map(c => ({ type: c.type, id: c.id }))
            });

            return (
              <article key={s?.name || idx} className="phone-frame">
                <header className="phone-header">
                  📱 {screenName}
                </header>

                <div className="phone-body">
                  {components.length > 0 ? (
                    components.map((node, nidx) => {
                      console.log(`  ↳ Rendering component ${nidx}:`, node.type, node.id);
                      return (
                        <ComponentRendererLite
                          key={String(node?.id ?? `${idx}-${nidx}`)}
                          node={node}
                        />
                      );
                    })
                  ) : (
                    <div style={{ textAlign: "center", padding: "32px 16px", color: "#9CA3AF" }}>
                      <div style={{ fontSize: "32px", marginBottom: "8px" }}>📦</div>
                      <div style={{ fontSize: "14px" }}>No components in this screen</div>
                    </div>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </ThemeCtx.Provider>
  );
}