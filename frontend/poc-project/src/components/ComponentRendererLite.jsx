// frontend/src/components/ComponentRendererLite.jsx - FULLY THEME-AWARE PRODUCTION VERSION
import React, { useContext, useState } from "react";
import { Mail, User, Lock, Phone, Search } from 'lucide-react';
import { ThemeCtx } from "./CanvasRendererLite";

/* ============================================
   THEME HOOK & UTILITIES
   ============================================ */
function useThemeColors() {
  const { theme } = useContext(ThemeCtx) || {};

  const lightenColor = (hex, percent) => {
    if (!hex) return hex;
    const num = parseInt(hex.replace("#", ""), 16);
    const amt = Math.round(2.55 * percent);
    const R = Math.min(255, (num >> 16) + amt);
    const G = Math.min(255, ((num >> 8) & 0x00FF) + amt);
    const B = Math.min(255, (num & 0x0000FF) + amt);
    return `#${(0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)}`;
  };

  const primary = theme?.primary || "#0D9488";
  const primaryLight = lightenColor(primary, 15);

  const getDynamicGradient = (variant = "primary") => {
    const map = {
      primary: `linear-gradient(135deg, ${primary} 0%, ${primaryLight} 100%)`,
      teal: "linear-gradient(135deg, #0D9488 0%, #14B8A6 100%)",
      blue: "linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)",
      purple: "linear-gradient(135deg, #A78BFA 0%, #8B5CF6 100%)",
      pink: "linear-gradient(135deg, #EC4899 0%, #DB2777 100%)",
      orange: "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
      green: "linear-gradient(135deg, #10B981 0%, #059669 100%)"
    };
    return map[variant] || map.primary;
  };

  return {
    primary,
    background: theme?.background || "#F7FAFC",
    surface: theme?.surface || "#FFFFFF",
    text: theme?.text || "#0F172A",
    textSecondary: "#64748B",
    getDynamicGradient,
    lightenColor
  };
}

/* ============================================
   LAYOUT COMPONENTS
   ============================================ */
export const Container = ({ padding = "16", width, background, radius, elevation, direction = "column", gap = "0", align, children, style }) => {
  const pad = String(padding).endsWith("px") ? padding : `${padding}px`;
  const br = radius != null ? Number(radius) : 0;

  const elevationMap = {
    sm: "0 1px 2px rgba(0,0,0,0.05)",
    md: "0 4px 6px rgba(0,0,0,0.07)",
    lg: "0 10px 15px rgba(0,0,0,0.1)",
    xl: "0 20px 25px rgba(0,0,0,0.15)"
  };

  return (
    <div style={{
      padding: pad,
      width: width || "100%",
      background: background || "transparent",
      borderRadius: br,
      boxShadow: elevationMap[elevation] || "none",
      display: "flex",
      flexDirection: direction,
      gap: gap ? `${gap}px` : "0",
      alignItems: align || "stretch",
      ...style,
    }}>
      {children}
    </div>
  );
};

export const Card = ({ padding = "20", elevation = "md", borderRadius = "lg", background, children, style }) => {
  const colors = useThemeColors();
  const elevationMap = { none: "none", sm: "0 1px 2px rgba(0,0,0,0.05)", md: "0 4px 6px rgba(0,0,0,0.07)", lg: "0 10px 15px rgba(0,0,0,0.1)", xl: "0 20px 25px rgba(0,0,0,0.15)" };
  const radiusMap = { sm: "8px", md: "12px", lg: "16px", xl: "24px", full: "999px" };

  return (
    <div style={{
      padding: `${padding}px`,
      borderRadius: radiusMap[borderRadius] || "12px",
      boxShadow: elevationMap[elevation] || elevationMap.md,
      background: background || colors.surface,
      marginBottom: "16px",
      ...style
    }}>
      {children}
    </div>
  );
};

export const Spacer = ({ height = "16", style }) => <div style={{ height: `${height}px`, ...style }} />;
export const Grid = ({ columns = 2, gap = "16", children, style }) => (
  <div style={{ display: "grid", gridTemplateColumns: `repeat(${columns}, 1fr)`, gap: `${gap}px`, marginBottom: "16px", ...style }}>{children}</div>
);
export const Stack = ({ children, style }) => <div style={{ position: "relative", ...style }}>{children}</div>;

/* ============================================
   CONTENT COMPONENTS
   ============================================ */
export const Header = ({ title = "Header", size = "xl", color, align = "left", weight = "bold", style }) => {
  const colors = useThemeColors();
  const sizeMap = { xs: "12px", sm: "14px", base: "16px", lg: "18px", xl: "20px", "2xl": "24px", "3xl": "30px", "4xl": "36px" };
  const weightMap = { normal: "400", medium: "500", semibold: "600", bold: "700" };

  return (
    <h2 style={{
      fontSize: sizeMap[size] || sizeMap.xl,
      fontWeight: weightMap[weight] || "700",
      color: color || colors.text,
      textAlign: align,
      marginBottom: "12px",
      lineHeight: "1.3",
      ...style
    }}>
      {title}
    </h2>
  );
};

export const Text = ({ text = "", size = "base", color, align = "left", weight = "normal", spacing, style }) => {
  const colors = useThemeColors();
  const sizeMap = { xs: "12px", sm: "14px", base: "16px", lg: "18px", xl: "20px", "2xl": "24px", "3xl": "30px" };

  return (
    <p style={{
      fontSize: sizeMap[size] || sizeMap.base,
      color: color || colors.text,
      textAlign: align,
      fontWeight: weight === "bold" ? "600" : "400",
      marginBottom: spacing ? `${spacing === "md" ? 12 : spacing === "lg" ? 16 : 8}px` : "8px",
      lineHeight: "1.6",
      ...style
    }}>
      {text}
    </p>
  );
};

export const RichText = ({ content = "", spacing, style }) => (
  <div style={{ fontSize: "16px", lineHeight: "1.8", color: "#374151", marginBottom: spacing ? `${spacing === "md" ? 16 : 24}px` : "16px", ...style }}
    dangerouslySetInnerHTML={{ __html: content }} />
);

export const Divider = ({ text, spacing = "md", style }) => {
  const spacingMap = { sm: "8px", md: "16px", lg: "24px" };
  if (text) {
    return (
      <div style={{ display: "flex", alignItems: "center", margin: `${spacingMap[spacing]} 0`, ...style }}>
        <div style={{ flex: 1, height: "1px", background: "#E2E8F0" }} />
        <span style={{ padding: "0 12px", fontSize: "14px", color: "#64748B", fontWeight: "500" }}>{text}</span>
        <div style={{ flex: 1, height: "1px", background: "#E2E8F0" }} />
      </div>
    );
  }
  return <hr style={{ border: "none", borderTop: "1px solid #E2E8F0", margin: `${spacingMap[spacing]} 0`, ...style }} />;
};

export const Badge = ({ text = "Badge", color = "blue", style }) => {
  const colorMap = {
    blue: { bg: "#DBEAFE", text: "#1E40AF" },
    green: { bg: "#D1FAE5", text: "#065F46" },
    red: { bg: "#FEE2E2", text: "#991B1B" },
    yellow: { bg: "#FEF3C7", text: "#92400E" },
    purple: { bg: "#EDE9FE", text: "#5B21B6" }
  };
  const colors = colorMap[color] || colorMap.blue;
  return <span style={{ display: "inline-block", padding: "4px 12px", borderRadius: "12px", fontSize: "12px", fontWeight: "600", background: colors.bg, color: colors.text, ...style }}>{text}</span>;
};
export const Chip = Badge;

/* ============================================
   INPUT COMPONENTS
   ============================================ */
export const TextInput = ({ label, placeholder, name, value, borderRadius = "md", style }) => {
  const radiusMap = { sm: "6px", md: "8px", lg: "12px" };
  return (
    <label style={{ display: "block", marginBottom: "16px", width: "100%" }}>
      {label && <span style={{ display: "block", fontSize: "14px", fontWeight: "500", marginBottom: "6px", color: "#374151" }}>{label}</span>}
      <input type="text" name={name} placeholder={placeholder} defaultValue={value}
        style={{ width: "100%", padding: "10px 12px", border: "1px solid #D1D5DB", borderRadius: radiusMap[borderRadius] || "8px", fontSize: "14px", outline: "none", transition: "border-color 0.2s", ...style }}
        onFocus={e => e.target.style.borderColor = "#0D9488"} onBlur={e => e.target.style.borderColor = "#D1D5DB"} />
    </label>
  );
};

export const PasswordInput = ({ label, placeholder, name, borderRadius = "md", style }) => {
  const radiusMap = { sm: "6px", md: "8px", lg: "12px" };
  return (
    <label style={{ display: "block", marginBottom: "16px", width: "100%" }}>
      {label && <span style={{ display: "block", fontSize: "14px", fontWeight: "500", marginBottom: "6px", color: "#374151" }}>{label}</span>}
      <input type="password" name={name} placeholder={placeholder || "••••••••"}
        style={{ width: "100%", padding: "10px 12px", border: "1px solid #D1D5DB", borderRadius: radiusMap[borderRadius] || "8px", fontSize: "14px", outline: "none", ...style }}
        onFocus={e => e.target.style.borderColor = "#0D9488"} onBlur={e => e.target.style.borderColor = "#D1D5DB"} />
    </label>
  );
};

export const IconInput = ({ icon, label, placeholder, type = "text", borderRadius = "md", style }) => {
  const radiusMap = { sm: "6px", md: "8px", lg: "12px" };
  
  // Icon component map
  const iconMap = { 
    mail: <Mail size={18} />, 
    user: <User size={18} />, 
    lock: <Lock size={18} />, 
    phone: <Phone size={18} />, 
    search: <Search size={18} /> 
  };
  
  return (
    <label style={{ display: "block", marginBottom: "16px", width: "100%" }}>
      {label && <span style={{ display: "block", fontSize: "14px", fontWeight: "500", marginBottom: "6px", color: "#374151" }}>{label}</span>}
      <div style={{ position: "relative" }}>
        <span style={{ 
          position: "absolute", 
          left: "12px", 
          top: "50%", 
          transform: "translateY(-50%)", 
          display: "flex",
          alignItems: "center",
          color: "#9CA3AF"
        }}>
          {iconMap[icon] || icon}
        </span>
        <input type={type} placeholder={placeholder}
          style={{ 
            width: "100%", 
            padding: "10px 12px 10px 40px", 
            border: "1px solid #D1D5DB", 
            borderRadius: radiusMap[borderRadius] || "8px", 
            fontSize: "14px", 
            outline: "none", 
            ...style 
          }}
          onFocus={e => e.target.style.borderColor = "#0D9488"} 
          onBlur={e => e.target.style.borderColor = "#D1D5DB"} />
      </div>
    </label>
  );
};

export const SearchInput = ({ placeholder = "Search...", borderRadius = "md", style }) => (
  <IconInput icon="search" placeholder={placeholder} borderRadius={borderRadius} style={style} />
);

export const Checkbox = ({ label, value, spacing, style }) => (
  <label style={{ display: "flex", alignItems: "center", marginBottom: spacing ? "12px" : "8px", cursor: "pointer" }}>
    <input type="checkbox" defaultChecked={value} style={{ marginRight: "8px", width: "16px", height: "16px" }} />
    <span style={{ fontSize: "14px", color: "#374151", ...style }}>{label}</span>
  </label>
);
export const Switch = Checkbox;

/* ============================================
   BUTTON COMPONENTS (FULLY THEME-AWARE)
   ============================================ */
export const Button = ({ text = "Button", variant = "primary", bg, color, size = "md", borderRadius = "md", type = "button", style }) => {
  const colors = useThemeColors();
  const variantMap = {
    primary: { bg: bg || colors.primary, color: "#FFFFFF" },
    secondary: { bg: "#F3F4F6", color: "#111827" },
    outline: { bg: "transparent", color: colors.primary, border: `1px solid ${colors.primary}` },
    ghost: { bg: "transparent", color: colors.primary }
  };
  const sizeMap = { sm: { padding: "8px 16px", fontSize: "14px" }, md: { padding: "10px 20px", fontSize: "16px" }, lg: { padding: "14px 28px", fontSize: "16px" } };
  const radiusMap = { sm: "6px", md: "8px", lg: "12px", xl: "16px", full: "999px" };
  const variants = variantMap[variant] || variantMap.primary;
  const sizes = sizeMap[size] || sizeMap.md;

  return (
    <button type={type} style={{
      width: "100%", padding: sizes.padding, fontSize: sizes.fontSize, fontWeight: "600",
      background: variants.bg, color: color || variants.color, border: variants.border || "none",
      borderRadius: radiusMap[borderRadius] || "8px", cursor: "pointer", transition: "all 0.2s", ...style
    }}
      onMouseOver={e => { if (variant === "primary") e.target.style.opacity = "0.9"; }}
      onMouseOut={e => { if (variant === "primary") e.target.style.opacity = "1"; }}>
      {text}
    </button>
  );
};

export const GradientButton = ({ text = "Button", gradient = "primary", size = "md", borderRadius = "md", elevation, icon, style }) => {
  const colors = useThemeColors();
  const sizeMap = { sm: { padding: "8px 16px", fontSize: "14px" }, md: { padding: "10px 20px", fontSize: "16px" }, lg: { padding: "14px 28px", fontSize: "16px", fontWeight: "700" } };
  const radiusMap = { sm: "6px", md: "8px", lg: "12px", xl: "16px" };
  const elevationMap = { sm: "0 2px 4px rgba(0,0,0,0.1)", md: "0 4px 8px rgba(0,0,0,0.15)", lg: "0 8px 16px rgba(0,0,0,0.2)" };
  const sizes = sizeMap[size] || sizeMap.md;

  return (
    <button style={{
      width: "100%", padding: sizes.padding, fontSize: sizes.fontSize, fontWeight: sizes.fontWeight || "600",
      background: colors.getDynamicGradient(gradient), color: "#FFFFFF", border: "none",
      borderRadius: radiusMap[borderRadius] || "8px", boxShadow: elevationMap[elevation] || "none",
      cursor: "pointer", transition: "transform 0.2s, box-shadow 0.2s", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", ...style
    }}
      onMouseOver={e => { e.target.style.transform = "translateY(-1px)"; e.target.style.boxShadow = "0 6px 12px rgba(0,0,0,0.2)"; }}
      onMouseOut={e => { e.target.style.transform = "translateY(0)"; e.target.style.boxShadow = elevationMap[elevation] || "none"; }}>
      {icon && <span>{icon}</span>}
      {text}
    </button>
  );
};

export const SocialButton = ({ provider = "Google", text, style }) => {
  const providerMap = {
    Google: { icon: "Google", bg: "#FFFFFF", color: "#000000", border: "1px solid #D1D5DB" },
    Apple: { icon: "Apple", bg: "#000000", color: "#FFFFFF" },
    Facebook: { icon: "Facebook", bg: "#1877F2", color: "#FFFFFF" },
    GitHub: { icon: "GitHub", bg: "#181717", color: "#FFFFFF" }
  };
  const config = providerMap[provider] || providerMap.Google;
  return (
    <button style={{
      width: "100%", padding: "10px 20px", fontSize: "14px", fontWeight: "600",
      background: config.bg, color: config.color, border: config.border || "none",
      borderRadius: "8px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "10px", marginBottom: "8px", transition: "opacity 0.2s", ...style
    }}
      onMouseOver={e => e.target.style.opacity = "0.9"} onMouseOut={e => e.target.style.opacity = "1"}>
      <span style={{ fontSize: "18px" }}>{config.icon}</span>
      {text || `Continue with ${provider}`}
    </button>
  );
};

export const IconButton = ({ icon, label, style }) => (
  <button title={label} style={{
    padding: "8px 12px", background: "transparent", border: "none", cursor: "pointer",
    fontSize: "14px", color: "#64748B", display: "flex", alignItems: "center", gap: "4px", transition: "color 0.2s", ...style
  }}
    onMouseOver={e => e.target.style.color = "#0D9488"} onMouseOut={e => e.target.style.color = "#64748B"}>
    <span>{icon}</span>
    {label && <span style={{ fontSize: "13px" }}>{label}</span>}
  </button>
);

export const FloatingActionButton = ({ icon = "Add", position = "bottom-right", gradient = "primary", style }) => {
  const colors = useThemeColors();
  const positionMap = { "bottom-right": { bottom: "24px", right: "24px" }, "bottom-left": { bottom: "24px", left: "24px" }, "top-right": { top: "24px", right: "24px" } };
  return (
    <button style={{
      position: "fixed", ...positionMap[position], width: "56px", height: "56px", borderRadius: "50%",
      background: colors.getDynamicGradient(gradient), color: "#FFFFFF", border: "none", fontSize: "24px",
      cursor: "pointer", boxShadow: "0 4px 12px rgba(0,0,0,0.2)", display: "flex", alignItems: "center", justifyContent: "center",
      transition: "transform 0.2s", zIndex: 100, ...style
    }}
      onMouseOver={e => e.target.style.transform = "scale(1.1)"} onMouseOut={e => e.target.style.transform = "scale(1)"}>
      {icon}
    </button>
  );
};

export const LinkButton = ({ text = "Link", href = "#", align = "left", size = "base", style }) => {
  const sizeMap = { sm: "12px", base: "14px", lg: "16px" };
  return (
    <a href={href} style={{
      display: "block", textAlign: align, fontSize: sizeMap[size] || "14px", color: "#0D9488",
      textDecoration: "none", fontWeight: "500", marginBottom: "8px", transition: "color 0.2s", ...style
    }}
      onMouseOver={e => e.target.style.color = "#0F766E"} onMouseOut={e => e.target.style.color = "#0D9488"}>
      {text}
    </a>
  );
};
export const Link = LinkButton;

/* ============================================
   MEDIA COMPONENTS
   ============================================ */
export const Image = ({ src, alt, fit = "cover", borderRadius = "md", style }) => {
  const radiusMap = { sm: "8px", md: "12px", lg: "16px" };
  if (src && !src.includes("placeholder")) {
    return <img src={src} alt={alt || ""} style={{ width: "100%", height: "auto", objectFit: fit, borderRadius: radiusMap[borderRadius] || "12px", marginBottom: "12px", ...style }} />;
  }
  return (
    <div style={{
      width: "100%", height: "180px", background: "#F3F4F6", borderRadius: radiusMap[borderRadius] || "12px",
      display: "flex", alignItems: "center", justifyContent: "center", color: "#9CA3AF", fontSize: "14px",
      marginBottom: "12px", border: "2px dashed #E5E7EB", ...style
    }}>
      Image {alt || "Image"}
    </div>
  );
};

export const Avatar = ({ size = "md", name = "User", border, position, style }) => {
  const colors = useThemeColors();
  const sizeMap = { sm: "32px", md: "48px", lg: "64px", xl: "96px" };
  const avatarSize = sizeMap[size] || "48px";
  return (
    <div style={{
      width: avatarSize, height: avatarSize, borderRadius: "50%",
      background: `linear-gradient(135deg, ${colors.primary}, ${colors.lightenColor(colors.primary, 20)})`,
      color: "#FFFFFF", display: "flex", alignItems: "center", justifyContent: "center",
      fontSize: `calc(${avatarSize} / 2.5)`, fontWeight: "600", border: border ? "3px solid #FFFFFF" : "none",
      boxShadow: "0 2px 8px rgba(0,0,0,0.1)", margin: position === "center" ? "0 auto" : "0", ...style
    }}>
      {name.charAt(0).toUpperCase()}
    </div>
  );
};

export const IllustrationHeader = ({ illustration, title, subtitle, spacing = "xl", style }) => {
  const spacingMap = { md: "16px", lg: "24px", xl: "32px", "2xl": "48px" };
  return (
    <div style={{ textAlign: "center", marginBottom: spacingMap[spacing] || "32px", ...style }}>
      <div style={{ width: "100%", height: "180px", background: "linear-gradient(135deg, #E0F2FE, #BAE6FD)", borderRadius: "16px", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "20px", fontSize: "48px" }}>Illustration</div>
      {title && <h1 style={{ fontSize: "28px", fontWeight: "700", color: "#0F172A", marginBottom: "8px" }}>{title}</h1>}
      {subtitle && <p style={{ fontSize: "16px", color: "#64748B", lineHeight: "1.6" }}>{subtitle}</p>}
    </div>
  );
};

export const HeroSection = ({ coverImage, height = "240", spacing, children, style }) => (
  <div style={{
    width: "100%", height: `${height}px`, background: "linear-gradient(135deg, #667EEA, #764BA2)",
    borderRadius: "16px", marginBottom: spacing ? "24px" : "16px", display: "flex", alignItems: "center",
    justifyContent: "center", color: "#FFFFFF", fontSize: "24px", fontWeight: "600", ...style
  }}>
    {children || "Hero Section"}
  </div>
);

export const ImageGallery = ({ images = [], spacing, style }) => (
  <div style={{ display: "flex", gap: "8px", overflowX: "auto", marginBottom: spacing ? "16px" : "12px", ...style }}>
    {images.map((_, idx) => (
      <div key={idx} style={{ minWidth: "120px", height: "120px", background: "#F3F4F6", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "32px" }}>Image</div>
    ))}
  </div>
);

/* ============================================
   SPECIAL COMPONENTS
   ============================================ */
export const StatCard = ({ icon, value, label, color = "primary", elevation = "sm", style }) => {
  const colors = useThemeColors();
  const colorMap = { primary: colors.primary, blue: "#3B82F6", green: "#10B981", orange: "#F59E0B", purple: "#8B5CF6", cyan: "#06B6D4" };
  const elevationMap = { sm: "0 1px 2px rgba(0,0,0,0.05)", md: "0 4px 6px rgba(0,0,0,0.07)" };
  return (
    <div style={{ padding: "20px", background: colors.surface, borderRadius: "12px", boxShadow: elevationMap[elevation] || elevationMap.sm, textAlign: "center", ...style }}>
      {icon && <div style={{ fontSize: "32px", marginBottom: "8px" }}>{icon}</div>}
      <div style={{ fontSize: "24px", fontWeight: "700", color: colorMap[color] || colorMap.primary, marginBottom: "4px" }}>{value}</div>
      <div style={{ fontSize: "14px", color: colors.textSecondary }}>{label}</div>
    </div>
  );
};

export const ProductCard = ({ image, title, price, rating, badge, elevation = "sm", borderRadius = "md", style }) => {
  const colors = useThemeColors();
  const elevationMap = { none: "none", sm: "0 1px 3px rgba(0,0,0,0.1)", md: "0 4px 6px rgba(0,0,0,0.1)", lg: "0 10px 15px rgba(0,0,0,0.1)" };
  const radiusMap = { sm: "8px", md: "12px", lg: "16px" };

  return (
    <div style={{
      position: "relative", padding: "12px", background: "#FFFFFF", borderRadius: radiusMap[borderRadius] || "12px",
      boxShadow: elevationMap[elevation] || elevationMap.sm, transition: "transform 0.2s, box-shadow 0.2s",
      cursor: "pointer", marginBottom: "16px", ...style
    }}
      onMouseOver={e => { e.currentTarget.style.transform = "translateY(-4px)"; e.currentTarget.style.boxShadow = "0 8px 16px rgba(0,0,0,0.15)"; }}
      onMouseOut={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = elevationMap[elevation] || elevationMap.sm; }}>
      {badge && <div style={{ position: "absolute", top: "8px", right: "8px", zIndex: 10 }}><Badge text={badge} color="red" /></div>}
      <Image src={image} alt={title} borderRadius="md" style={{ height: "160px", width: "100%", objectFit: "cover", marginBottom: "12px" }} />
      <div style={{ fontSize: "14px", fontWeight: "600", color: "#0F172A", marginBottom: "8px", lineHeight: "1.4", minHeight: "40px" }}>{title}</div>
      {rating && <div style={{ display: "flex", alignItems: "center", gap: "4px", marginBottom: "8px", fontSize: "12px", color: "#64748B" }}><span>Star</span><span style={{ fontWeight: "500" }}>{rating}</span></div>}
      <div style={{ fontSize: "20px", fontWeight: "700", color: colors.primary, marginBottom: "12px" }}>{price}</div>
      <button style={{
        width: "100%", padding: "8px 16px", background: "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
        color: "#FFFFFF", border: "none", borderRadius: "6px", fontSize: "13px", fontWeight: "600", cursor: "pointer", transition: "opacity 0.2s"
      }}
        onMouseOver={e => e.target.style.opacity = "0.9"} onMouseOut={e => e.target.style.opacity = "1"}>
        Add to Cart
      </button>
    </div>
  );
};

export const QuantityControl = ({ value = 1, min = 0, max = 99, onChange, style }) => {
  const [quantity, setQuantity] = useState(value);
  const handleDecrease = () => { if (quantity > min) { const v = quantity - 1; setQuantity(v); onChange?.(v); } };
  const handleIncrease = () => { if (quantity < max) { const v = quantity + 1; setQuantity(v); onChange?.(v); } };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "12px", background: "#F3F4F6", padding: "4px 8px", borderRadius: "8px", width: "fit-content", ...style }}>
      <button onClick={handleDecrease} disabled={quantity <= min}
        style={{ width: "32px", height: "32px", borderRadius: "6px", border: "none", background: quantity > min ? "#FFFFFF" : "#E5E7EB", color: quantity > min ? "#0F172A" : "#9CA3AF", fontSize: "18px", fontWeight: "600", cursor: quantity > min ? "pointer" : "not-allowed", display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.2s" }}
        onMouseOver={e => { if (quantity > min) e.target.style.background = "#F9FAFB"; }} onMouseOut={e => { if (quantity > min) e.target.style.background = "#FFFFFF"; }}>-</button>
      <span style={{ fontSize: "16px", fontWeight: "600", color: "#0F172A", minWidth: "24px", textAlign: "center" }}>{quantity}</span>
      <button onClick={handleIncrease} disabled={quantity >= max}
        style={{ width: "32px", height: "32px", borderRadius: "6px", border: "none", background: quantity < max ? "#FFFFFF" : "#E5E7EB", color: quantity < max ? "#0F172A" : "#9CA3AF", fontSize: "18px", fontWeight: "600", cursor: quantity < max ? "pointer" : "not-allowed", display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.2s" }}
        onMouseOver={e => { if (quantity < max) e.target.style.background = "#F9FAFB"; }} onMouseOut={e => { if (quantity < max) e.target.style.background = "#FFFFFF"; }}>+</button>
    </div>
  );
};

export const CartItem = ({ image, title, price, quantity = 1, onQuantityChange, onRemove, style }) => {
  return (
    <div style={{ display: "flex", gap: "16px", padding: "16px", background: "#FFFFFF", borderRadius: "12px", boxShadow: "0 1px 3px rgba(0,0,0,0.1)", marginBottom: "12px", ...style }}>
      <div style={{ width: "80px", height: "80px", borderRadius: "8px", background: "#F3F4F6", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "32px" }}>
        {image ? <img src={image} alt={title} style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: "8px" }} /> : "Cart"}
      </div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "8px" }}>
        <div style={{ fontSize: "14px", fontWeight: "600", color: "#0F172A", lineHeight: "1.4" }}>{title}</div>
        <div style={{ fontSize: "18px", fontWeight: "700", color: "#0D9488" }}>{price}</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "auto" }}>
          <QuantityControl value={quantity} onChange={onQuantityChange} />
          <button onClick={onRemove} style={{
            padding: "6px 12px", background: "transparent", border: "1px solid #E5E7EB", borderRadius: "6px",
            fontSize: "12px", color: "#EF4444", cursor: "pointer", fontWeight: "500", transition: "all 0.2s"
          }}
            onMouseOver={e => { e.target.style.background = "#FEF2F2"; e.target.style.borderColor = "#EF4444"; }}
            onMouseOut={e => { e.target.style.background = "transparent"; e.target.style.borderColor = "#E5E7EB"; }}>
            Remove
          </button>
        </div>
      </div>
    </div>
  );
};

export const PriceBreakdown = ({ subtotal, shipping = 0, tax = 0, total, style }) => {
  return (
    <div style={{ padding: "20px", background: "#FFFFFF", borderRadius: "12px", boxShadow: "0 4px 6px rgba(0,0,0,0.07)", marginBottom: "16px", ...style }}>
      <div style={{ fontSize: "16px", fontWeight: "600", color: "#0F172A", marginBottom: "16px", paddingBottom: "12px", borderBottom: "1px solid #E5E7EB" }}>Order Summary</div>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "14px" }}><span style={{ color: "#64748B" }}>Subtotal</span><span style={{ fontWeight: "500", color: "#0F172A" }}>{subtotal}</span></div>
        {shipping > 0 && <div style={{ display: "flex", justifyContent: "space-between", fontSize: "14px" }}><span style={{ color: "#64748B" }}>Shipping</span><span style={{ fontWeight: "500", color: "#0F172A" }}>{shipping}</span></div>}
        {tax > 0 && <div style={{ display: "flex", justifyContent: "space-between", fontSize: "14px" }}><span style={{ color: "#64748B" }}>Tax</span><span style={{ fontWeight: "500", color: "#0F172A" }}>{tax}</span></div>}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", paddingTop: "16px", borderTop: "2px solid #E5E7EB" }}>
        <span style={{ fontSize: "18px", fontWeight: "700", color: "#0F172A" }}>Total</span>
        <span style={{ fontSize: "22px", fontWeight: "700", color: "#0D9488" }}>{total}</span>
      </div>
    </div>
  );
};

export const ProgressBar = ({ value = 0, label, color = "blue", steps, currentStep, style }) => {
  const colors = useThemeColors();
  const colorMap = { blue: "#3B82F6", green: "#10B981", teal: colors.primary, orange: "#F59E0B" };
  return (
    <div style={{ marginBottom: "16px", ...style }}>
      {label && <Text text={label} size="sm" color="secondary" style={{ marginBottom: "8px" }} />}
      <div style={{ width: "100%", height: "8px", background: "#E5E7EB", borderRadius: "999px", overflow: "hidden" }}>
        <div style={{ width: `${value}%`, height: "100%", background: colorMap[color] || colorMap.blue, borderRadius: "999px", transition: "width 0.3s" }} />
      </div>
      {steps && currentStep && <div style={{ marginTop: "8px", fontSize: "12px", color: "#64748B" }}>Step {currentStep} of {steps}</div>}
    </div>
  );
};

export const AppBar = ({ title, subtitle, avatar, actions, style }) => (
  <div style={{ padding: "16px", background: "#FFFFFF", borderBottom: "1px solid #E5E7EB", display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", ...style }}>
    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
      {avatar && <Avatar size="sm" />}
      <div><div style={{ fontSize: "18px", fontWeight: "600", color: "#0F172A" }}>{title}</div>{subtitle && <div style={{ fontSize: "14px", color: "#64748B" }}>{subtitle}</div>}</div>
    </div>
    {actions && <div style={{ display: "flex", gap: "12px" }}>{actions.map((a, i) => <span key={i} style={{ fontSize: "20px", cursor: "pointer" }}>{a === "search" ? "Search" : a === "notifications" ? "Bell" : "Settings"}</span>)}</div>}
  </div>
);

export const TabBar = ({ tabs = [], style }) => (
  <div style={{ display: "flex", justifyContent: "space-around", padding: "12px 0", background: "#FFFFFF", borderTop: "1px solid #E5E7EB", position: "sticky", bottom: 0, marginTop: "auto", ...style }}>
    {tabs.map((tab, idx) => (
      <div key={idx} style={{ flex: 1, textAlign: "center", fontSize: "12px", color: idx === 0 ? "#0D9488" : "#64748B", fontWeight: idx === 0 ? "600" : "400", cursor: "pointer" }}>{tab}</div>
    ))}
  </div>
);

export const FormSection = ({ title, spacing, children, style }) => {
  const spacingMap = { sm: "12px", md: "16px", lg: "24px" };
  return (
    <div style={{ marginBottom: spacingMap[spacing] || "24px", ...style }}>
      {title && <h3 style={{ fontSize: "16px", fontWeight: "600", color: "#0F172A", marginBottom: "12px" }}>{title}</h3>}
      {children}
    </div>
  );
};

export const List = ({ spacing, children, style }) => {
  const spacingMap = { sm: "4px", md: "8px" };
  return <div style={{ display: "flex", flexDirection: "column", gap: spacingMap[spacing] || "8px", ...style }}>{children}</div>;
};

export const ListItem = ({ icon, title, subtitle, trailing, value, style }) => {
  const iconMap = { user: "User", lock: "Lock", bell: "Bell", mail: "Mail", palette: "Palette", "chevron-right": "Right" };
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", background: "#FFFFFF", borderRadius: "8px", cursor: "pointer", transition: "background 0.2s", ...style }}
      onMouseOver={e => e.currentTarget.style.background = "#F9FAFB"} onMouseOut={e => e.currentTarget.style.background = "#FFFFFF"}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px", flex: 1 }}>
        {icon && <span style={{ fontSize: "20px" }}>{iconMap[icon] || icon}</span>}
        <div><div style={{ fontSize: "14px", fontWeight: "500", color: "#0F172A" }}>{title}</div>{subtitle && <div style={{ fontSize: "12px", color: "#64748B" }}>{subtitle}</div>}</div>
      </div>
      {trailing === "switch" ? <input type="checkbox" defaultChecked={value} style={{ width: "40px", height: "20px" }} /> : trailing === "chevron-right" ? <span style={{ fontSize: "20px", color: "#9CA3AF" }}>Right</span> : null}
    </div>
  );
};

export const CardList = ({ spacing, children, style }) => {
  const spacingMap = { sm: "8px", md: "16px", lg: "24px" };
  return <div style={{ display: "flex", flexDirection: "column", gap: spacingMap[spacing] || "16px", ...style }}>{children}</div>;
};

export const Rating = ({ value = 0, reviews, spacing, style }) => (
  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: spacing ? "12px" : "8px", ...style }}>
    <span style={{ fontSize: "16px" }}>{"Star".repeat(Math.floor(value))}</span>
    <span style={{ fontSize: "14px", color: "#64748B" }}>{value} {reviews && `(${reviews} reviews)`}</span>
  </div>
);

export const Alert = ({ type = "info", title, message, style }) => {
  const typeMap = { success: { bg: "#D1FAE5", border: "#10B981", icon: "Success" }, error: { bg: "#FEE2E2", border: "#EF4444", icon: "Error" }, warning: { bg: "#FEF3C7", border: "#F59E0B", icon: "Warning" }, info: { bg: "#DBEAFE", border: "#3B82F6", icon: "Info" } };
  const config = typeMap[type] || typeMap.info;
  return (
    <div style={{ padding: "12px 16px", background: config.bg, border: `1px solid ${config.border}`, borderRadius: "8px", marginBottom: "16px", display: "flex", gap: "12px", ...style }}>
      <span style={{ fontSize: "20px" }}>{config.icon}</span>
      <div style={{ flex: 1 }}>{title && <div style={{ fontWeight: "600", marginBottom: "4px" }}>{title}</div>}{message && <div style={{ fontSize: "14px" }}>{message}</div>}</div>
    </div>
  );
};

export const EmptyState = ({ icon = "Search", title = "No items", message, style }) => (
  <div style={{ textAlign: "center", padding: "48px 24px", color: "#64748B", ...style }}>
    <div style={{ fontSize: "64px", marginBottom: "16px" }}>{icon}</div>
    <div style={{ fontSize: "18px", fontWeight: "600", marginBottom: "8px", color: "#374151" }}>{title}</div>
    {message && <div style={{ fontSize: "14px" }}>{message}</div>}
  </div>
);

export const Form = ({ children, style }) => (
  <form onSubmit={e => e.preventDefault()} style={{ width: "100%", display: "flex", flexDirection: "column", ...style }}>{children}</form>
);

export const Footer = ({ text = "© 2025", style }) => (
  <footer style={{ textAlign: "center", fontSize: "12px", color: "#9CA3AF", marginTop: "32px", ...style }}>{text}</footer>
);

/* ============================================
   COMPONENT MAP & RENDERER
   ============================================ */
const COMPONENT_MAP = {
  container: Container, card: Card, spacer: Spacer, grid: Grid, stack: Stack,
  header: Header, text: Text, richtext: RichText, divider: Divider, badge: Badge, chip: Chip,
  textinput: TextInput, passwordinput: PasswordInput, iconinput: IconInput, searchinput: SearchInput,
  checkbox: Checkbox, switch: Switch,
  button: Button, gradientbutton: GradientButton, socialbutton: SocialButton,
  iconbutton: IconButton, floatingactionbutton: FloatingActionButton,
  linkbutton: LinkButton, link: Link,
  image: Image, avatar: Avatar, illustrationheader: IllustrationHeader, herosection: HeroSection, imagegallery: ImageGallery,
  statcard: StatCard, productcard: ProductCard, quantitycontrol: QuantityControl, cartitem: CartItem, pricebreakdown: PriceBreakdown,
  progressbar: ProgressBar, appbar: AppBar, tabbar: TabBar, formsection: FormSection,
  list: List, listitem: ListItem, cardlist: CardList, rating: Rating, alert: Alert, emptystate: EmptyState,
  form: Form, footer: Footer
};

function normalizeNode(node) {
  if (!node || typeof node !== "object") return null;
  const typeLower = String(node.type || "").toLowerCase();
  let props = { ...(node.props || {}) };
  let kids = [];
  if (Array.isArray(props.children)) kids = [...props.children];
  else if (Array.isArray(props.items)) kids = [...props.items];
  else if (Array.isArray(node.children)) kids = [...node.children];
  delete props.children; delete props.items;

  let normalized = { ...node, props, children: kids.map(normalizeNode).filter(Boolean) };

  if (typeLower === "form") {
    const fields = props.fields || [];
    const buttons = props.buttons || [];
    const formChildren = [
      ...fields.map((f, i) => ({ id: f.id || `field-${i}`, type: f.type || "TextInput", props: { ...(f.props || {}) } })),
      ...buttons.map((b, i) => ({ id: b.id || `btn-${i}`, type: b.type || "Button", props: { ...(b.props || {}) } }))
    ];
    const cleanProps = { ...props };
    delete cleanProps.fields; delete cleanProps.buttons;
    normalized = { ...normalized, props: cleanProps, children: formChildren };
  }
  return normalized;
}

export default function ComponentRendererLite({ node }) {
  const { theme } = useContext(ThemeCtx) || {};

  if (!node) return null;
  const n = normalizeNode(node);
  if (!n) return null;

  const key = (n.type || "").toLowerCase();
  const Comp = COMPONENT_MAP[key];

  if (!Comp) {
    console.warn(`Unknown component: ${n.type}`, n);
    return (
      <div style={{ border: "1px dashed #FCA5A5", background: "#FEF2F2", padding: "12px", borderRadius: "8px", marginBottom: "12px" }}>
        <div style={{ fontSize: "12px", color: "#991B1B", marginBottom: "8px" }}>Unknown: {n.type}</div>
        {n.children?.map((c, i) => <ComponentRendererLite key={c.id || i} node={c} />)}
      </div>
    );
  }

  const themedProps = { ...n.props };
  if (key === "header" && !themedProps.color) themedProps.color = theme?.text;
  if (key === "button" && !themedProps.bg && (n.props?.variant ?? "primary") === "primary") {
    themedProps.bg = theme?.primary;
    themedProps.color = "#FFFFFF";
  }

  return (
    <Comp {...themedProps}>
      {Array.isArray(n.children) && n.children.length > 0
        ? n.children.map((c, idx) => <ComponentRendererLite key={c.id || `child-${idx}`} node={c} />)
        : null}
    </Comp>
  );
}