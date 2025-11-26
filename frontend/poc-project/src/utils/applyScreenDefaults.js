// utils/applyScreenDefaults.js

export function applyScreenDefaults(screen, theme = {}) {
  if (!screen) return screen;

  const defaultTokens = {
    padding: "2rem",
    margin: "auto",
    gap: "1.25rem",
    fontFamily: "Inter, system-ui, sans-serif",
    background: theme.background || "#FFFFFF",
    textColor: theme.text || "#0F172A",
  };

  const styledSections = (screen.sections || []).map((section) => {
    const secStyle = {
      padding: section?.style?.padding || defaultTokens.padding,
      margin: section?.style?.margin || "0 auto",
      maxWidth: section?.style?.maxWidth || "1000px",
      background: section?.style?.background || "transparent",
      display: "flex",
      flexDirection: "column",
      gap: section?.style?.gap || defaultTokens.gap,
    };

    const styledComponents = (section.components || []).map((comp) => {
      const baseCompStyle = {
        margin: comp?.style?.margin || "0",
        padding: comp?.style?.padding || "0.5rem 0",
        fontFamily: comp?.style?.fontFamily || defaultTokens.fontFamily,
        color: comp?.style?.color || defaultTokens.textColor,
      };

      return {
        ...comp,
        style: { ...baseCompStyle, ...comp.style },
      };
    });

    return {
      ...section,
      style: secStyle,
      components: styledComponents,
    };
  });

  return {
    ...screen,
    style: {
      fontFamily: defaultTokens.fontFamily,
      background: screen?.style?.background || defaultTokens.background,
      color: screen?.style?.color || defaultTokens.textColor,
      minHeight: "100vh",
      padding: "2rem 1rem",
    },
    sections: styledSections,
  };
}
