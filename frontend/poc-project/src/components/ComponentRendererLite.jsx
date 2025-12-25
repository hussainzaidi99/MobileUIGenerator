
import React, { useContext, useState } from "react";
import {
  Mail,
  User,
  Lock,
  Phone,
  Search,
  ChevronRight,
  Settings,
  Bell,
  Palette,
  HelpCircle,
  Info,
  LogOut,
} from "lucide-react";
import { FaGoogle, FaCog, FaApple, FaFacebook, FaGithub } from "react-icons/fa";
import { ThemeCtx } from "./CanvasRendererLite";

const StarIcon = () => <span style={{ color: "#FCD34D" }}>★</span>;

/* ============================================
   ✅ CACHE-BUSTING UTILITY
   ============================================ */
/**
 * Add cache-busting timestamp to image URLs
 * Forces browser to fetch fresh images instead of using cache
 */
function addCacheBuster(url) {
  if (!url || typeof url !== 'string') return url;

  // Don't add to data URLs or already cache-busted URLs
  if (url.startsWith('data:') || url.includes('_t=')) return url;

  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}_t=${Date.now()}`;
}

/* ============================================
   PHONE SPACING CONSTANT - GLOBAL
   ============================================ */
// ✅ MOVED TO TOP - Must be accessible to all components
const PHONE_SPACING = {
  container: '12px',
  component: '10px',
  card: '12px',
  text: '8px',
  input: '12px',
  image: '10px',
  divider: '12px',
  badge: '8px',
};

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
    const G = Math.min(255, ((num >> 8) & 0x00ff) + amt);
    const B = Math.min(255, (num & 0x0000ff) + amt);
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
      green: "linear-gradient(135deg, #10B981 0%, #059669 100%)",
    };
    return map[variant] || map.primary;
  };
  const PHONE_SPACING = {
    container: '12px',
    component: '10px',
    card: '12px',
    text: '8px',
    input: '12px',
  };

  return {
    primary,
    background: theme?.background || "#F7FAFC",
    surface: theme?.surface || "#FFFFFF",
    text: theme?.text || "#0F172A",
    textSecondary: "#64748B",
    getDynamicGradient,
    lightenColor,
  };
}

/* ============================================
   LAYOUT COMPONENTS
   ============================================ */
export const Container = ({
  padding = "16",
  width,
  background,
  radius,
  elevation,
  direction = "column",
  gap = "0",
  align,
  children,
  style,
}) => {
  const pad = padding === "0" || padding === 0
    ? "0"
    : String(padding).endsWith("px")
      ? padding
      : `${padding}px`;
  const br = radius != null ? Number(radius) : 0;

  const elevationMap = {
    sm: "0 1px 2px rgba(0,0,0,0.05)",
    md: "0 4px 6px rgba(0,0,0,0.07)",
    lg: "0 10px 15px rgba(0,0,0,0.1)",
    xl: "0 20px 25px rgba(0,0,0,0.15)",
  };

  return (
    <div
      style={{
        padding: pad,
        width: width || "100%",
        background: background || "transparent",
        borderRadius: br,
        boxShadow: elevationMap[elevation] || "none",
        display: "flex",
        flexDirection: direction,
        gap: gap ? `${gap}px` : "0",
        alignItems: align || "stretch",
        boxSizing: "border-box",
        overflow: "hidden",
        marginBottom: PHONE_SPACING.container,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const Card = ({
  padding = "20",
  elevation = "md",
  borderRadius = "lg",
  background,
  children,
  style,
}) => {
  const colors = useThemeColors();
  const elevationMap = {
    none: "none",
    sm: "0 1px 2px rgba(0,0,0,0.05)",
    md: "0 4px 6px rgba(0,0,0,0.07)",
    lg: "0 10px 15px rgba(0,0,0,0.1)",
    xl: "0 20px 25px rgba(0,0,0,0.15)",
  };
  const radiusMap = {
    sm: "8px",
    md: "12px",
    lg: "16px",
    xl: "24px",
    full: "999px",
  };

  return (
    <div
      style={{
        padding: `${padding}px`,
        borderRadius: radiusMap[borderRadius] || "12px",
        boxShadow: elevationMap[elevation] || elevationMap.md,
        background: background || colors.surface,
        marginBottom: PHONE_SPACING.card,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const Spacer = ({ height = "16", style }) => (
  <div style={{ height: `${height}px`, ...style }} />
);

export const Grid = ({ columns = 2, gap = "16", children, style }) => (
  <div
    style={{
      display: "grid",
      gridTemplateColumns: `repeat(${columns}, 1fr)`,
      gap: `${gap}px`,
      marginBottom: "16px",
      ...style,
    }}
  >
    {children}
  </div>
);

export const Stack = ({ children, style }) => (
  <div style={{ position: "relative", marginBottom: PHONE_SPACING.component, ...style }}>{children}</div>
);

/* ============================================
   CONTENT COMPONENTS
   ============================================ */
export const Header = ({
  title = "Header",
  size = "xl",
  color,
  align = "left",
  weight = "bold",
  style,
}) => {
  const colors = useThemeColors();
  const sizeMap = {
    xs: "12px",
    sm: "14px",
    base: "16px",
    lg: "18px",
    xl: "20px",
    "2xl": "24px",
    "3xl": "30px",
    "4xl": "36px",
  };
  const weightMap = {
    normal: "400",
    medium: "500",
    semibold: "600",
    bold: "700",
  };

  return (
    <h2
      style={{
        fontSize: sizeMap[size] || sizeMap.xl,
        fontWeight: weightMap[weight] || "700",
        color: color || colors.text,
        textAlign: align,
        marginBottom: PHONE_SPACING.text,
        lineHeight: "1.3",
        ...style,
      }}
    >
      {title}
    </h2>
  );
};

export const Text = ({
  text = "",
  size = "base",
  color,
  align = "left",
  weight = "normal",
  spacing,
  style,
}) => {
  const colors = useThemeColors();
  const sizeMap = {
    xs: "12px",
    sm: "14px",
    base: "16px",
    lg: "18px",
    xl: "20px",
    "2xl": "24px",
    "3xl": "30px",
  };

  return (
    <p
      style={{
        fontSize: sizeMap[size] || sizeMap.base,
        color: color || colors.text,
        textAlign: align,
        fontWeight: weight === "bold" ? "600" : "400",
        marginBottom: spacing
          ? `${spacing === "md" ? 12 : spacing === "lg" ? 16 : 8}px`
          : PHONE_SPACING.text,
        lineHeight: "1.6",
        ...style,
      }}
    >
      {text}
    </p>
  );
};

export const RichText = ({ content = "", spacing, style }) => (
  <div
    style={{
      fontSize: "16px",
      lineHeight: "1.8",
      color: "#374151",
      marginBottom: spacing ? `${spacing === "md" ? 16 : 24}px` : PHONE_SPACING.component,
      ...style,
    }}
    dangerouslySetInnerHTML={{ __html: content }}
  />
);

export const Divider = ({ text, spacing = "md", style }) => {
  const spacingMap = { sm: "8px", md: PHONE_SPACING.divider, lg: "24px" };
  if (text) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          margin: `${spacingMap[spacing]} 0`,
          ...style,
        }}
      >
        <div style={{ flex: 1, height: "1px", background: "#E2E8F0" }} />
        <span
          style={{
            padding: "0 12px",
            fontSize: "14px",
            color: "#64748B",
            fontWeight: "500",
          }}
        >
          {text}
        </span>
        <div style={{ flex: 1, height: "1px", background: "#E2E8F0" }} />
      </div>
    );
  }
  return (
    <hr
      style={{
        border: "none",
        borderTop: "1px solid #E2E8F0",
        margin: `${spacingMap[spacing]} 0`,
        ...style,
      }}
    />
  );
};

export const Badge = ({ text = "Badge", color = "blue", style }) => {
  const colorMap = {
    blue: { bg: "#DBEAFE", text: "#1E40AF" },
    green: { bg: "#D1FAE5", text: "#065F46" },
    red: { bg: "#FEE2E2", text: "#991B1B" },
    yellow: { bg: "#FEF3C7", text: "#92400E" },
    purple: { bg: "#EDE9FE", text: "#5B21B6" },
  };
  const colors = colorMap[color] || colorMap.blue;
  return (
    <span
      style={{
        display: "inline-block",
        padding: "4px 12px",
        borderRadius: "12px",
        fontSize: "12px",
        fontWeight: "600",
        background: colors.bg,
        color: colors.text,
        marginBottom: PHONE_SPACING.badge,
        ...style,
      }}
    >
      {text}
    </span>
  );
};
export const Chip = Badge;

/* ============================================
   INPUT COMPONENTS
   ============================================ */
export const TextInput = ({
  label,
  placeholder,
  name,
  value,
  borderRadius = "md",
  style,
}) => {
  const radiusMap = { sm: "6px", md: "8px", lg: "12px" };
  return (
    <label
      style={{
        display: "block",
        marginBottom: "16px",
        width: "100%",
      }}
    >
      {label && (
        <span
          style={{
            display: "block",
            fontSize: "14px",
            fontWeight: "500",
            marginBottom: PHONE_SPACING.input,
            color: "#374151",
          }}
        >
          {label}
        </span>
      )}
      <input
        type="text"
        name={name}
        placeholder={placeholder}
        defaultValue={value}
        style={{
          width: "100%",
          padding: "10px 12px",
          border: "1px solid #D1D5DB",
          borderRadius: radiusMap[borderRadius] || "8px",
          fontSize: "14px",
          outline: "none",
          transition: "border-color 0.2s",
          ...style,
        }}
        onFocus={(e) => (e.target.style.borderColor = "#0D9488")}
        onBlur={(e) => (e.target.style.borderColor = "#D1D5DB")}
      />
    </label>
  );
};

export const PasswordInput = ({
  label,
  placeholder,
  name,
  borderRadius = "md",
  style,
}) => {
  const radiusMap = { sm: "6px", md: "8px", lg: "12px" };
  return (
    <label
      style={{
        display: "block",
        marginBottom: "16px",
        width: "100%",
      }}
    >
      {label && (
        <span
          style={{
            display: "block",
            fontSize: "14px",
            fontWeight: "500",
            marginBottom: PHONE_SPACING.input,
            color: "#374151",
          }}
        >
          {label}
        </span>
      )}
      <input
        type="password"
        name={name}
        placeholder={placeholder || "••••••••"}
        style={{
          width: "100%",
          padding: "10px 12px",
          border: "1px solid #D1D5DB",
          borderRadius: radiusMap[borderRadius] || "8px",
          fontSize: "14px",
          outline: "none",
          ...style,
        }}
        onFocus={(e) => (e.target.style.borderColor = "#0D9488")}
        onBlur={(e) => (e.target.style.borderColor = "#D1D5DB")}
      />
    </label>
  );
};

export const IconInput = ({
  icon,
  label,
  placeholder,
  type = "text",
  borderRadius = "md",
  style,
}) => {
  const radiusMap = { sm: "6px", md: "8px", lg: "12px" };

  const iconMap = {
    mail: <Mail size={18} />,
    user: <User size={18} />,
    lock: <Lock size={18} />,
    phone: <Phone size={18} />,
    search: <Search size={18} />,
  };

  return (
    <label
      style={{
        display: "block",
        marginBottom: PHONE_SPACING.input,
        width: "100%",
      }}
    >
      {label && (
        <span
          style={{
            display: "block",
            fontSize: "14px",
            fontWeight: "500",
            marginBottom: "6px",
            color: "#374151",
          }}
        >
          {label}
        </span>
      )}
      <div style={{ position: "relative" }}>
        {/* ✅ Icon with proper positioning */}
        <span
          style={{
            position: "absolute",
            left: "14px",
            top: "50%",
            transform: "translateY(-50%)",
            display: "flex",
            alignItems: "center",
            color: "#9CA3AF",
            pointerEvents: "none", // ✅ Don't block clicks
            zIndex: 1,
          }}
        >
          {iconMap[icon] || icon}
        </span>

        {/* ✅ Input with proper padding */}
        <input
          type={type}
          placeholder={placeholder}
          style={{
            width: "100%",
            padding: "12px 14px 12px 44px", // ✅ 44px left padding
            border: "1px solid #D1D5DB",
            borderRadius: radiusMap[borderRadius] || "8px",
            fontSize: "14px",
            outline: "none",
            transition: "border-color 0.2s",
            ...style,
          }}
          onFocus={(e) => (e.target.style.borderColor = "#0D9488")}
          onBlur={(e) => (e.target.style.borderColor = "#D1D5DB")}
        />
      </div>
    </label>
  );
};

/* ============================================
   FIX #2: SEARCH INPUT - Proper Icon Spacing
   ============================================ */
export const SearchInput = ({
  placeholder = "Search...",
  borderRadius = "md",
  style,
}) => {
  const radiusMap = { sm: "6px", md: "8px", lg: "12px" };

  return (
    <label
      style={{
        display: "block",
        marginBottom: PHONE_SPACING.input,
        width: "100%",
      }}
    >
      <div style={{ position: "relative" }}>
        {/* ✅ Icon positioned absolutely */}
        <span
          style={{
            position: "absolute",
            left: "14px",
            top: "50%",
            transform: "translateY(-50%)",
            display: "flex",
            alignItems: "center",
            color: "#9CA3AF",
            pointerEvents: "none", // ✅ Don't block input clicks
            zIndex: 1,
          }}
        >
          <Search size={18} />
        </span>

        {/* ✅ Input with proper left padding */}
        <input
          type="text"
          placeholder={placeholder}
          style={{
            width: "100%",
            padding: "12px 14px 12px 44px", // ✅ 44px left padding for icon
            border: "1px solid #D1D5DB",
            borderRadius: radiusMap[borderRadius] || "8px",
            fontSize: "14px",
            outline: "none",
            transition: "border-color 0.2s",
            ...style,
          }}
          onFocus={(e) => (e.target.style.borderColor = "#0D9488")}
          onBlur={(e) => (e.target.style.borderColor = "#D1D5DB")}
        />
      </div>
    </label>
  );
};
/* ============================================
   CHECKBOX & SWITCH COMPONENTS - FIXED
   Must be defined BEFORE being used in COMPONENT_MAP
   ============================================ */

export const Checkbox = ({ label, value, spacing, style }) => (
  <label
    style={{
      display: "flex",
      alignItems: "center",
      marginBottom: spacing ? "12px" : PHONE_SPACING.component,
      cursor: "pointer",
      ...style,
    }}
  >
    <input
      type="checkbox"
      defaultChecked={value}
      style={{
        marginRight: "8px",
        width: "16px",
        height: "16px",
        cursor: "pointer",
      }}
    />
    <span style={{ fontSize: "14px", color: "#374151" }}>
      {label}
    </span>
  </label>
);

// ✅ Switch is just an alias for Checkbox
export const Switch = Checkbox;

/* ============================================
   BUTTON COMPONENTS
   ============================================ */
export const Button = ({
  text = "Button",
  variant = "primary",
  bg,
  color,
  size = "md",
  borderRadius = "md",
  type = "button",
  style,
}) => {
  const colors = useThemeColors();
  const variantMap = {
    primary: { bg: bg || colors.primary, color: "#FFFFFF" },
    secondary: { bg: "#F3F4F6", color: "#111827" },
    outline: {
      bg: "transparent",
      color: colors.primary,
      border: `1px solid ${colors.primary}`,
    },
    ghost: { bg: "transparent", color: colors.primary },
  };
  const sizeMap = {
    sm: { padding: "8px 16px", fontSize: "14px" },
    md: { padding: "10px 20px", fontSize: "16px" },
    lg: { padding: "14px 28px", fontSize: "16px" },
  };
  const radiusMap = {
    sm: "6px",
    md: "8px",
    lg: "12px",
    xl: "16px",
    full: "999px",
  };
  const variants = variantMap[variant] || variantMap.primary;
  const sizes = sizeMap[size] || sizeMap.md;

  return (
    <button
      type={type}
      style={{
        width: "100%",
        padding: sizes.padding,
        fontSize: sizes.fontSize,
        fontWeight: "600",
        background: variants.bg,
        color: color || variants.color,
        border: variants.border || "none",
        borderRadius: radiusMap[borderRadius] || "8px",
        cursor: "pointer",
        transition: "all 0.2s",
        ...style,
      }}
      onMouseOver={(e) => {
        if (variant === "primary") e.target.style.opacity = "0.9";
      }}
      onMouseOut={(e) => {
        if (variant === "primary") e.target.style.opacity = "1";
      }}
    >
      {text}
    </button>
  );
};

export const GradientButton = ({
  text = "Button",
  gradient = "primary",
  size = "md",
  borderRadius = "md",
  elevation,
  icon,
  style,
}) => {
  const colors = useThemeColors();
  const sizeMap = {
    sm: { padding: "8px 16px", fontSize: "14px" },
    md: { padding: "10px 20px", fontSize: "16px" },
    lg: {
      padding: "14px 28px",
      fontSize: "16px",
      fontWeight: "700",
    },
  };
  const radiusMap = {
    sm: "6px",
    md: "8px",
    lg: "12px",
    xl: "16px",
  };
  const elevationMap = {
    sm: "0 2px 4px rgba(0,0,0,0.1)",
    md: "0 4px 8px rgba(0,0,0,0.15)",
    lg: "0 8px 16px rgba(0,0,0,0.2)",
  };
  const sizes = sizeMap[size] || sizeMap.md;

  return (
    <button
      style={{
        width: "100%",
        padding: sizes.padding,
        fontSize: sizes.fontSize,
        fontWeight: sizes.fontWeight || "600",
        background: colors.getDynamicGradient(gradient),
        color: "#FFFFFF",
        border: "none",
        borderRadius: radiusMap[borderRadius] || "8px",
        boxShadow: elevationMap[elevation] || "none",
        cursor: "pointer",
        transition: "transform 0.2s, box-shadow 0.2s",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "8px",
        ...style,
      }}
      onMouseOver={(e) => {
        e.target.style.transform = "translateY(-1px)";
        e.target.style.boxShadow = "0 6px 12px rgba(0,0,0,0.2)";
      }}
      onMouseOut={(e) => {
        e.target.style.transform = "translateY(0)";
        e.target.style.boxShadow = elevationMap[elevation] || "none";
      }}
    >
      {icon && <span>{icon}</span>}
      {text}
    </button>
  );
};

export const SocialButton = ({ provider = "Google", text, style }) => {
  const providerMap = {
    Google: {
      icon: <FaGoogle size={18} />,
      bg: "#FFFFFF",
      color: "#000000",
      border: "1px solid #D1D5DB",
    },
    Apple: {
      icon: <FaApple size={20} />,
      bg: "#000000",
      color: "#FFFFFF",
    },
    Facebook: {
      icon: <FaFacebook size={18} />,
      bg: "#1877F2",
      color: "#FFFFFF",
    },
    GitHub: {
      icon: <FaGithub size={18} />,
      bg: "#181717",
      color: "#FFFFFF",
    },
  };
  const config = providerMap[provider] || providerMap.Google;

  return (
    <button
      style={{
        width: "100%",
        padding: "10px 20px",
        fontSize: "14px",
        fontWeight: "600",
        background: config.bg,
        color: config.color,
        border: config.border || "none",
        borderRadius: "8px",
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "10px",
        marginBottom: PHONE_SPACING.component,
        transition: "opacity 0.2s",
        ...style,
      }}
      onMouseOver={(e) => (e.target.style.opacity = "0.9")}
      onMouseOut={(e) => (e.target.style.opacity = "1")}
    >
      {config.icon}
      {text || `Continue with ${provider}`}
    </button>
  );
};

export const IconButton = ({ icon, label, style }) => (
  <button
    title={label}
    style={{
      padding: "8px 12px",
      background: "transparent",
      border: "none",
      cursor: "pointer",
      fontSize: "14px",
      color: "#64748B",
      display: "flex",
      alignItems: "center",
      gap: "4px",
      transition: "color 0.2s",
      ...style,
    }}
    onMouseOver={(e) => (e.target.style.color = "#0D9488")}
    onMouseOut={(e) => (e.target.style.color = "#64748B")}
  >
    <span>{icon}</span>
    {label && <span style={{ fontSize: "13px" }}>{label}</span>}
  </button>
);

export const FloatingActionButton = ({
  icon = "Add",
  position = "bottom-right",
  gradient = "primary",
  style,
}) => {
  const colors = useThemeColors();
  const positionMap = {
    "bottom-right": { bottom: "24px", right: "24px" },
    "bottom-left": { bottom: "24px", left: "24px" },
    "top-right": { top: "24px", right: "24px" },
    "top-left": { top: "24px", left: "24px" },
  };
  return (
    <button
      style={{
        position: "absolute",
        ...positionMap[position],
        width: "56px",
        height: "56px",
        borderRadius: "50%",
        background: colors.getDynamicGradient(gradient),
        color: "#FFFFFF",
        border: "none",
        fontSize: "24px",
        cursor: "pointer",
        boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "transform 0.2s",
        zIndex: 100,
        ...style,
      }}
      onMouseOver={(e) => (e.target.style.transform = "scale(1.1)")}
      onMouseOut={(e) => (e.target.style.transform = "scale(1)")}
    >
      {icon}
    </button>
  );
};

export const LinkButton = ({
  text = "Link",
  href = "#",
  align = "left",
  size = "base",
  style,
}) => {
  const sizeMap = { sm: "12px", base: "14px", lg: "16px" };
  return (
    <a
      href={href}
      style={{
        display: "block",
        textAlign: align,
        fontSize: sizeMap[size] || "14px",
        color: "#0D9488",
        textDecoration: "none",
        fontWeight: "500",
        marginBottom: PHONE_SPACING.component,
        transition: "color 0.2s",
        ...style,
      }}
      onMouseOver={(e) => (e.target.style.color = "#0F766E")}
      onMouseOut={(e) => (e.target.style.color = "#0D9488")}
    >
      {text}
    </a>
  );
};
export const Link = LinkButton;


/* ============================================
   MEDIA COMPONENTS — PEXELS-FIRST DYNAMIC IMAGE SYSTEM
   ============================================ */

import { searchPexelsPhoto, generatePexelsQuery } from '../utils/pexelsClient';

/**
 * Helper to check if a URL is a placeholder
 */
function isPlaceholderUrl(url) {
  if (!url) return true;
  const str = String(url).toLowerCase();

  return (
    str.includes("placeholder.com") ||
    str.includes("via.placeholder") ||
    str.includes("dummyimage.com") ||
    str === "placeholder" ||
    str === "image" ||
    str.endsWith(".jpg") && str.length < 20 // Only very short .jpg strings
  );
}

/**
 * Get image URL from props (backend approach - now secondary)
 */
function getImageUrlFromProps(props) {
  const candidates = [
    props?.image,
    props?.src,
    props?.illustration,
    props?.coverImage,
  ];

  for (const url of candidates) {
    if (!url) continue;

    const urlStr = String(url);

    // ✅ Valid URL patterns
    if (
      urlStr.startsWith('http://') ||
      urlStr.startsWith('https://') ||
      urlStr.startsWith('data:image/')
    ) {
      // ✅ Check if it's NOT a placeholder
      if (!isPlaceholderUrl(urlStr)) {
        console.log(`✅ Using backend image URL: ${urlStr.substring(0, 60)}...`);
        return urlStr;
      }
    }
  }

  return null;
}

/**
 * Unsplash fallback (when Pexels fails)
 */
function getUnsplashFallback(alt, width = 400, height = 400) {
  const category = alt?.toLowerCase() || 'abstract';
  return `https://source.unsplash.com/random/${width}x${height}/?${category}`;
}

/**
 * Simple colored placeholder generator (last resort)
 */
function getColoredPlaceholder(text, width = 400, height = 400) {
  const colors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899'];
  const hash = Array.from(text || 'image').reduce((acc, char) => {
    return ((acc << 5) - acc) + char.charCodeAt(0);
  }, 0);
  const bgColor = colors[Math.abs(hash) % colors.length];

  // Use a simple SVG data URL
  const svg = `
    <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="${bgColor}"/>
      <text x="50%" y="50%" 
            dominant-baseline="middle" 
            text-anchor="middle" 
            font-family="sans-serif" 
            font-size="24" 
            font-weight="bold" 
            fill="white">
        ${text || 'Image'}
      </text>
    </svg>
  `;

  return `data:image/svg+xml;base64,${btoa(svg)}`;
}

/**
 * Main Image Component - ✅ BACKEND-FIRST APPROACH (FIXED)
 * Priority: Backend URL → Pexels → Unsplash → Colored Placeholder
 */
export const Image = ({
  src,
  image,
  illustration,
  alt,
  fit = "cover",
  borderRadius = "md",
  style,
  loading,
  onError
}) => {
  const radiusMap = { sm: "8px", md: "12px", lg: "16px" };
  const [imgSrc, setImgSrc] = React.useState(getColoredPlaceholder(alt || 'Image', 400, 400));
  const [isLoading, setIsLoading] = React.useState(true);
  const [errorCount, setErrorCount] = React.useState(0);

  // ✅ BACKEND-FIRST: Check backend URLs before fetching from Pexels
  React.useEffect(() => {
    let isMounted = true;

    async function loadImage() {
      setIsLoading(true);
      setErrorCount(0);

      // ✅ PRIORITY 1: Check backend URL FIRST (already has perfect images!)
      const backendUrl = getImageUrlFromProps({ src, image, illustration });
      if (backendUrl && isMounted) {
        console.log(`✅ Using backend image URL: ${backendUrl.substring(0, 60)}...`);
        setImgSrc(backendUrl);
        setIsLoading(false);
        return;
      }

      // ✅ PRIORITY 2: Only fetch from Pexels if backend didn't provide URL
      const query = generatePexelsQuery('Image', alt);
      console.log(`🔵 Attempting Pexels fetch for query: "${query}"`);

      const pexelsUrl = await searchPexelsPhoto(query, { orientation: 'landscape' });

      if (pexelsUrl && isMounted) {
        console.log(`✅ Using Pexels image: ${pexelsUrl.substring(0, 60)}...`);
        setImgSrc(pexelsUrl);
        setIsLoading(false);
        return;
      }

      // ✅ PRIORITY 3: Unsplash fallback
      console.log(`⚠️ Pexels failed, using Unsplash fallback`);
      if (isMounted) {
        setImgSrc(getUnsplashFallback(alt || 'image', 400, 400));
        setIsLoading(false);
      }
    }

    loadImage();

    return () => {
      isMounted = false;
    };
  }, [src, image, illustration, alt]);

  const handleError = (e) => {
    console.error(`❌ Image load error (attempt ${errorCount + 1}):`, e.target.src.substring(0, 60));

    if (errorCount === 0) {
      // First error: Try Unsplash
      setImgSrc(getUnsplashFallback(alt || 'image', 400, 400));
      setErrorCount(1);
    } else if (errorCount === 1) {
      // Second error: Use colored placeholder
      setImgSrc(getColoredPlaceholder(alt || 'Image', 400, 400));
      setErrorCount(2);
    }
    // After 2 errors, keep the colored placeholder
  };

  return (
    <img
      src={imgSrc}
      alt={alt || "Image"}
      style={{
        width: "100%",
        height: "auto",
        maxHeight: "300px",
        objectFit: fit,
        borderRadius: radiusMap[borderRadius] || "12px",
        marginBottom: PHONE_SPACING.image,
        background: "#F3F4F6",
        display: "block",
        opacity: isLoading ? 0.7 : 1,
        transition: "opacity 0.3s ease",
        ...style,
      }}
      onError={handleError}
      onLoad={() => setIsLoading(false)}
      loading="lazy"
    />
  );
};


/**
 * Avatar Component
 */
export const Avatar = ({ size = "md", name = "User", border, position, style }) => {
  const colors = useThemeColors();
  const sizeMap = {
    sm: "32px",
    md: "48px",
    lg: "64px",
    xl: "96px",
  };
  const avatarSize = sizeMap[size] || "48px";

  return (
    <div
      style={{
        width: avatarSize,
        height: avatarSize,
        borderRadius: "50%",
        background: `linear-gradient(135deg, ${colors.primary}, ${colors.lightenColor(
          colors.primary,
          20
        )})`,
        color: "#FFFFFF",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: `calc(${avatarSize} / 2.5)`,
        fontWeight: "600",
        border: border ? "3px solid #FFFFFF" : "none",
        boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
        margin: position === "center" ? "0 auto" : "0",
        marginBottom: PHONE_SPACING.component, // ✅ ADDED
        ...style,
      }}
    >
      {name.charAt(0).toUpperCase()}
    </div>
  );
};

/**
 * Illustration Header Component
 */
export const IllustrationHeader = ({
  illustration,
  title,
  subtitle,
  spacing = "xl",
  style,
}) => {
  const spacingMap = {
    md: "16px",
    lg: "24px",
    xl: "32px",
    "2xl": "48px",
  };

  return (
    <div
      style={{
        textAlign: "center",
        marginBottom: spacingMap[spacing] || "32px",
        ...style,
      }}
    >
      <Image
        illustration={addCacheBuster(illustration)}
        alt={title || "Illustration"}
        loading="eager"
        style={{
          width: "100%",
          height: "180px",
          objectFit: "cover",
          borderRadius: "16px",
          marginBottom: "20px",
        }}
        onError={(e) => {
          console.error('❌ [IMAGE] Failed to load:', illustration);
          e.target.style.background = '#F3F4F6';
        }}
      />
      {title && (
        <h1
          style={{
            fontSize: "28px",
            fontWeight: "700",
            color: "#0F172A",
            marginBottom: "8px",
          }}
        >
          {title}
        </h1>
      )}
      {subtitle && (
        <p
          style={{
            fontSize: "16px",
            color: "#64748B",
            lineHeight: "1.6",
          }}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
};

/**
 * Hero Section Component - PEXELS-FIRST
 */
export const HeroSection = ({
  coverImage,
  height = "240",
  spacing,
  children,
  style,
}) => {
  const [bgUrl, setBgUrl] = React.useState(getColoredPlaceholder('Hero', 800, 400));
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    let isMounted = true;

    async function loadHeroImage() {
      setIsLoading(true);

      // Priority 1: Try Pexels
      const query = generatePexelsQuery('HeroSection', 'hero banner', {});
      const pexelsUrl = await searchPexelsPhoto(query, { orientation: 'landscape' });

      if (pexelsUrl && isMounted) {
        setBgUrl(pexelsUrl);
        setIsLoading(false);
        return;
      }

      // Priority 2: Backend URL
      const backendUrl = getImageUrlFromProps({ coverImage });
      if (backendUrl && isMounted) {
        setBgUrl(backendUrl);
        setIsLoading(false);
        return;
      }

      // Priority 3: Unsplash fallback
      if (isMounted) {
        setBgUrl(getUnsplashFallback('hero', 800, 400));
        setIsLoading(false);
      }
    }

    loadHeroImage();

    return () => {
      isMounted = false;
    };
  }, [coverImage]);

  return (
    <div
      style={{
        width: "100%",
        height: `${height}px`,
        backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url(${bgUrl})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        borderRadius: "16px",
        marginBottom: spacing ? "24px" : PHONE_SPACING.component,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#FFFFFF",
        fontSize: "24px",
        fontWeight: "600",
        opacity: isLoading ? 0.8 : 1,
        transition: "opacity 0.5s ease",
        ...style,
      }}
    >
      {children || "Hero Section"}
    </div>
  );
};

/**
 * Image Gallery Component
 */
export const ImageGallery = ({ images = [], spacing, style }) => {
  const displayImages = images.length > 0 ? images : [
    getColoredPlaceholder('Photo 1', 300, 300),
    getColoredPlaceholder('Photo 2', 300, 300),
    getColoredPlaceholder('Photo 3', 300, 300),
    getColoredPlaceholder('Photo 4', 300, 300),
    getColoredPlaceholder('Photo 5', 300, 300),
    getColoredPlaceholder('Photo 6', 300, 300),
  ];

  return (
    <div
      style={{
        display: "flex",
        gap: "8px",
        overflowX: "auto",
        marginBottom: spacing ? "16px" : "12px",
        ...style,
      }}
    >
      {displayImages.map((img, idx) => (
        <img
          key={idx}
          src={typeof img === "string" ? img : getColoredPlaceholder(`Photo ${idx + 1}`, 300, 300)}
          alt={`Gallery ${idx + 1}`}
          style={{
            minWidth: "120px",
            height: "120px",
            objectFit: "cover",
            borderRadius: "8px",
          }}
          loading="lazy"
        />
      ))}
    </div>
  );
};
/* ============================================
   SPECIAL COMPONENTS
   ============================================ */
export const StatCard = ({
  icon,
  value,
  label,
  color = "primary",
  elevation = "sm",
  style,
}) => {
  const colors = useThemeColors();
  const colorMap = {
    primary: colors.primary,
    blue: "#3B82F6",
    green: "#10B981",
    orange: "#F59E0B",
    purple: "#8B5CF6",
    cyan: "#06B6D4",
  };
  const elevationMap = {
    sm: "0 1px 2px rgba(0,0,0,0.05)",
    md: "0 4px 6px rgba(0,0,0,0.07)",
  };
  return (
    <div
      style={{
        padding: "20px",
        background: colors.surface,
        borderRadius: "12px",
        boxShadow: elevationMap[elevation] || elevationMap.sm,
        textAlign: "center",
        marginBottom: PHONE_SPACING.card,
        ...style,
      }}
    >
      {icon && (
        <div
          style={{
            fontSize: "32px",
            marginBottom: "8px",
          }}
        >
          {icon}
        </div>
      )}
      <div
        style={{
          fontSize: "24px",
          fontWeight: "700",
          color: colorMap[color] || colorMap.primary,
          marginBottom: "4px",
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: "14px",
          color: colors.textSecondary,
        }}
      >
        {label}
      </div>
    </div>
  );
};

export const ProductCard = ({
  image,
  title,
  price,
  rating,
  badge,
  elevation = "sm",
  borderRadius = "md",
  style,
}) => {
  const colors = useThemeColors();
  const elevationMap = {
    none: "none",
    sm: "0 1px 3px rgba(0,0,0,0.1)",
    md: "0 4px 6px rgba(0,0,0,0.1)",
    lg: "0 10px 15px rgba(0,0,0,0.1)",
  };
  const radiusMap = { sm: "8px", md: "12px", lg: "16px" };

  return (
    <div
      style={{
        position: "relative",
        padding: "12px",
        background: "#FFFFFF",
        borderRadius: radiusMap[borderRadius] || "12px",
        boxShadow: elevationMap[elevation] || elevationMap.sm,
        transition: "transform 0.2s, box-shadow 0.2s",
        cursor: "pointer",
        marginBottom: PHONE_SPACING.card,
        ...style,
      }}
      onMouseOver={(e) => {
        e.currentTarget.style.transform = "translateY(-4px)";
        e.currentTarget.style.boxShadow = "0 8px 16px rgba(0,0,0,0.15)";
      }}
      onMouseOut={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = elevationMap[elevation] || elevationMap.sm;
      }}
    >
      {badge && (
        <div style={{ position: "absolute", top: "8px", right: "8px", zIndex: 10 }}>
          <Badge text={badge} color="red" />
        </div>
      )}

      {/* Use Image component with proper props */}
      <Image
        image={image}
        alt={title || "Product"}
        borderRadius="md"
        style={{
          height: "160px",
          width: "100%",
          objectFit: "cover",
          marginBottom: "12px",
        }}
      />

      <div style={{
        fontSize: "14px",
        fontWeight: "600",
        color: "#0F172A",
        marginBottom: "8px",
        lineHeight: "1.4",
        minHeight: "40px",
      }}>
        {title}
      </div>

      {rating && (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "4px",
          marginBottom: "8px",
          fontSize: "12px",
          color: "#64748B",
        }}>
          <span style={{ color: "#FCD34D" }}>★</span>
          <span style={{ fontWeight: "500" }}>{rating}</span>
        </div>
      )}

      <div style={{
        fontSize: "20px",
        fontWeight: "700",
        color: colors.primary,
        marginBottom: "12px",
      }}>
        {price}
      </div>

      <button
        style={{
          width: "100%",
          padding: "8px 16px",
          background: "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
          color: "#FFFFFF",
          border: "none",
          borderRadius: "6px",
          fontSize: "13px",
          fontWeight: "600",
          cursor: "pointer",
          transition: "opacity 0.2s",
        }}
        onMouseOver={(e) => (e.target.style.opacity = "0.9")}
        onMouseOut={(e) => (e.target.style.opacity = "1")}
      >
        Add to Cart
      </button>
    </div>
  );
};

export const QuantityControl = ({
  value = 1,
  min = 0,
  max = 99,
  onChange,
  style,
}) => {
  const [quantity, setQuantity] = useState(value);
  const handleDecrease = () => {
    if (quantity > min) {
      const v = quantity - 1;
      setQuantity(v);
      onChange?.(v);
    }
  };
  const handleIncrease = () => {
    if (quantity < max) {
      const v = quantity + 1;
      setQuantity(v);
      onChange?.(v);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
        background: "#F3F4F6",
        padding: "3px 6px",
        borderRadius: "6px",
        width: "fit-content",
        ...style,
      }}
    >
      <button
        onClick={handleDecrease}
        disabled={quantity <= min}
        style={{
          width: "28px",
          height: "28px",
          borderRadius: "6px",
          border: "none",
          background: quantity > min ? "#FFFFFF" : "#E5E7EB",
          color: quantity > min ? "#0F172A" : "#9CA3AF",
          fontSize: "16px",
          fontWeight: "600",
          cursor: quantity > min ? "pointer" : "not-allowed",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "all 0.2s",
        }}
        onMouseOver={(e) => {
          if (quantity > min) e.target.style.background = "#F9FAFB";
        }}
        onMouseOut={(e) => {
          if (quantity > min) e.target.style.background = "#FFFFFF";
        }}
      >
        -
      </button>
      <span
        style={{
          fontSize: "14px",
          fontWeight: "600",
          color: "#0F172A",
          minWidth: "24px",
          textAlign: "center",
        }}
      >
        {quantity}
      </span>
      <button
        onClick={handleIncrease}
        disabled={quantity >= max}
        style={{
          width: "28px",
          height: "28px",
          borderRadius: "6px",
          border: "none",
          background: quantity < max ? "#FFFFFF" : "#E5E7EB",
          color: quantity < max ? "#0F172A" : "#9CA3AF",
          fontSize: "16px",
          fontWeight: "600",
          cursor: quantity < max ? "pointer" : "not-allowed",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "all 0.2s",
        }}
        onMouseOver={(e) => {
          if (quantity < max) e.target.style.background = "#F9FAFB";
        }}
        onMouseOut={(e) => {
          if (quantity < max) e.target.style.background = "#FFFFFF";
        }}
      >
        +
      </button>
    </div>
  );
};

export const CartItem = ({
  image,
  title,
  price,
  quantity = 1,
  onQuantityChange,
  onRemove,
  style,
}) => {
  return (
    <div
      style={{
        display: "flex",
        gap: "12px",
        padding: "12px",
        background: "#FFFFFF",
        borderRadius: "12px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
        marginBottom: PHONE_SPACING.component,
        alignItems: "flex-start",
        ...style,
      }}
    >
      <div
        style={{
          width: "70px",
          height: "70px",
          minWidth: "80",
          minHeight: "80",
          borderRadius: "8px",
          background: "#F3F4F6",
          flexShrink: 0,
          overflow: "hidden",
          position: "relative",
        }}
      >
        <Image
          image={image}
          alt={title || "Cart Item"}
          borderRadius="sm"
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            marginBottom: 0,
            positon: "absolute",
            top: 0,
            left: 0,
          }}
        />
      </div>
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: "6px",
          minWidth: 0,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            fontSize: "13px",
            fontWeight: "600",
            color: "#0F172A",
            lineHeight: "1.4",
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontSize: "18px",
            fontWeight: "700",
            color: "#0D9488",
          }}
        >
          {price}
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: "auto",
          }}
        >
          <QuantityControl value={quantity} onChange={onQuantityChange} />
          <button
            onClick={onRemove}
            style={{
              padding: "6px 12px",
              background: "transparent",
              border: "1px solid #E5E7EB",
              borderRadius: "6px",
              fontSize: "12px",
              color: "#EF4444",
              cursor: "pointer",
              fontWeight: "500",
              transition: "all 0.2s",
            }}
            onMouseOver={(e) => {
              e.target.style.background = "#FEF2F2";
              e.target.style.borderColor = "#EF4444";
            }}
            onMouseOut={(e) => {
              e.target.style.background = "transparent";
              e.target.style.borderColor = "#E5E7EB";
            }}
          >
            Remove
          </button>
        </div>
      </div>
    </div>
  );
};

// PASTE THIS INTO ComponentRendererLite.jsx - REPLACE PriceBreakdown COMPONENT (around line 920)

export const PriceBreakdown = ({
  subtotal,
  shipping = 0,
  tax = 0,
  total,
  style,
}) => {
  return (
    <div
      style={{
        padding: "20px",
        background: "#FFFFFF",
        borderRadius: "12px",
        boxShadow: "0 4px 6px rgba(0,0,0,0.07)",
        marginBottom: PHONE_SPACING.card,
        width: "100%",
        boxSizing: "border-box",
        ...style,
      }}
    >
      {/* Header */}
      <div
        style={{
          fontSize: "16px",
          fontWeight: "600",
          color: "#0F172A",
          marginBottom: "16px",
          paddingBottom: "12px",
          borderBottom: "1px solid #E5E7EB",
        }}
      >
        Order Summary
      </div>

      {/* Price Rows */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          marginBottom: "16px",
        }}
      >
        {/* Subtotal */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: "14px",
          }}
        >
          <span style={{ color: "#64748B" }}>Subtotal</span>
          <span
            style={{
              fontWeight: "500",
              color: "#0F172A",
            }}
          >
            {subtotal}
          </span>
        </div>

        {/* Shipping */}
        {shipping !== 0 && (
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: "14px",
            }}
          >
            <span style={{ color: "#64748B" }}>Shipping</span>
            <span
              style={{
                fontWeight: "500",
                color: "#0F172A",
              }}
            >
              {typeof shipping === 'number' ? `$${shipping.toFixed(2)}` : shipping}
            </span>
          </div>
        )}

        {/* Tax */}
        {tax !== 0 && (
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: "14px",
            }}
          >
            <span style={{ color: "#64748B" }}>Tax</span>
            <span
              style={{
                fontWeight: "500",
                color: "#0F172A",
              }}
            >
              {typeof tax === 'number' ? `$${tax.toFixed(2)}` : tax}
            </span>
          </div>
        )}
      </div>

      {/* Total */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          paddingTop: "16px",
          borderTop: "2px solid #E5E7EB",
        }}
      >
        <span
          style={{
            fontSize: "18px",
            fontWeight: "700",
            color: "#0F172A",
          }}
        >
          Total
        </span>
        <span
          style={{
            fontSize: "22px",
            fontWeight: "700",
            color: "#0D9488",
          }}
        >
          {total}
        </span>
      </div>
    </div>
  );
};

/* ============================================
   PROGRESS BAR - UPDATED
   ============================================ */
export const ProgressBar = ({
  value = 0,
  label,
  color = "blue",
  steps,
  currentStep,
  style,
}) => {
  const colors = useThemeColors();
  const colorMap = {
    blue: "#3B82F6",
    green: "#10B981",
    teal: colors.primary,
    orange: "#F59E0B",
  };

  return (
    <div style={{ marginBottom: PHONE_SPACING.component, ...style }}>
      {label && (
        <div
          style={{
            fontSize: "13px",
            color: "#64748B",
            marginBottom: "6px",
            fontWeight: "500",
          }}
        >
          {label}
        </div>
      )}
      <div
        style={{
          width: "100%",
          height: "6px",
          background: "#E5E7EB",
          borderRadius: "999px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${value}%`,
            height: "100%",
            background: colorMap[color] || colorMap.blue,
            borderRadius: "999px",
            transition: "width 0.3s",
          }}
        />
      </div>
      {steps && currentStep && (
        <div
          style={{
            marginTop: "6px",
            fontSize: "12px",
            color: "#64748B",
          }}
        >
          Step {currentStep} of {steps}
        </div>
      )}
    </div>
  );
};

/* ============================================
   FIX #1: APP BAR - Render Actual Icons
   ============================================ */
export const AppBar = ({ title, subtitle, avatar, actions, style }) => {
  // ✅ Icon mapping function
  const renderActionIcon = (action) => {
    switch (action) {
      case "search":
        return <Search size={20} />;
      case "notifications":
      case "bell":
        return <Bell size={20} />;
      case "settings":
        return <Settings size={20} />;
      default:
        return <Settings size={20} />;
    }
  };

  return (
    <div
      style={{
        padding: "12px 14px",
        background: "#FFFFFF",
        borderBottom: "1px solid #E5E7EB",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: PHONE_SPACING.component,
        ...style,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          flex: 1,
          minWidth: 0,
        }}
      >
        {avatar && <Avatar size="sm" name={avatar} style={{ marginBottom: 0 }} />}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: "16px",
              fontWeight: "600",
              color: "#0F172A",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {title}
          </div>
          {subtitle && (
            <div
              style={{
                fontSize: "12px",
                color: "#64748B",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {subtitle}
            </div>
          )}
        </div>
      </div>
      {actions && (
        <div
          style={{
            display: "flex",
            gap: "16px", // ✅ Increased gap between icons
            flexShrink: 0,
          }}
        >
          {actions.map((action, i) => (
            <button
              key={i}
              style={{
                background: "transparent",
                border: "none",
                padding: "6px",
                cursor: "pointer",
                color: "#64748B",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "color 0.2s",
              }}
              onMouseOver={(e) => (e.currentTarget.style.color = "#0D9488")}
              onMouseOut={(e) => (e.currentTarget.style.color = "#64748B")}
            >
              {renderActionIcon(action)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
/* ============================================
   TAB BAR - UPDATED
   ============================================ */
export const TabBar = ({ tabs = [], style }) => (
  <div
    style={{
      display: "flex",
      justifyContent: "space-around",
      padding: "10px 0",
      background: "#FFFFFF",
      borderTop: "1px solid #E5E7EB",
      position: "sticky",
      bottom: 0,
      marginTop: "auto",
      ...style,
    }}
  >
    {tabs.map((tab, idx) => (
      <div
        key={idx}
        style={{
          flex: 1,
          textAlign: "center",
          fontSize: "11px",
          color: idx === 0 ? "#0D9488" : "#64748B",
          fontWeight: idx === 0 ? "600" : "400",
          cursor: "pointer",
          padding: "4px",
        }}
      >
        {tab}
      </div>
    ))}
  </div>
);


export const FormSection = ({ title, spacing, children, style }) => {
  const spacingMap = {
    sm: "12px",
    md: "16px",
    lg: "24px",
  };
  return (
    <div
      style={{
        marginBottom: spacingMap[spacing] || PHONE_SPACING.card,
        ...style,
      }}
    >
      {title && (
        <h3
          style={{
            fontSize: "16px",
            fontWeight: "600",
            color: "#0F172A",
            marginBottom: "12px",
          }}
        >
          {title}
        </h3>
      )}
      {children}
    </div>
  );
};

export const List = ({ spacing, children, style }) => {
  const spacingMap = { sm: "4px", md: "8px" };
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: spacingMap[spacing] || "8px",
        marginBottom: PHONE_SPACING.component,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/* ============================================
   LIST ITEM - UPDATED
   ============================================ */
export const ListItem = ({
  icon,
  title,
  subtitle,
  trailing,
  value,
  style,
}) => {
  // Icon component mapping (Lucide React)
  const iconComponentMap = {
    user: User,
    lock: Lock,
    bell: Bell,
    mail: Mail,
    palette: Palette,
    settings: Settings,
    gear: FaCog,
    cog: FaCog,
    "chevron-right": ChevronRight,
    profile: User,
    notification: Bell,
    notifications: Bell,
    email: Mail,
    theme: Palette,
    appearance: Palette,
    security: Lock,
    privacy: Lock,
    help: HelpCircle,
    info: Info,
    about: Info,
    logout: LogOut,
    signout: LogOut,
    phone: Phone,
    search: Search,

  };

  // Render icon helper
  const renderIcon = () => {
    if (!icon) return null;

    const IconComponent = iconComponentMap[icon];

    if (IconComponent) {
      return (
        <IconComponent
          size={18}
          style={{
            color: "#64748B",
            flexShrink: 0
          }}
        />
      );
    }

    return (
      <span style={{ fontSize: "18px", flexShrink: 0 }}>
        {icon}
      </span>
    );
  };


  // Render trailing element helper
  const renderTrailing = () => {
    if (!trailing) return null;

    switch (trailing) {
      case "switch":
        return (
          <input
            type="checkbox"
            defaultChecked={value}
            style={{
              width: "40px",
              height: "20px",
              cursor: "pointer"
            }}
          />
        );

      case "chevron-right":
        return (
          <ChevronRight
            size={20}
            style={{
              color: "#9CA3AF",
              flexShrink: 0
            }}
          />
        );

      default:
        return (
          <span style={{ fontSize: "18px", color: "#9CA3AF" }}>
            {trailing}
          </span>
        );
    }
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 16px",
        background: "#FFFFFF",
        borderRadius: "8px",
        cursor: "pointer",
        transition: "background 0.2s",
        gap: "10px",
        minHeight: "54px",
        marginBottom: "6px",
        ...style,
      }}
      onMouseOver={(e) => (e.currentTarget.style.background = "#F9FAFB")}
      onMouseOut={(e) => (e.currentTarget.style.background = "#FFFFFF")}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          flex: 1,
          minWidth: 0,
          overflow: "hidden",
        }}
      >
        {renderIcon()}

        <div
          style={{
            flex: 1,
            minWidth: 0,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              fontSize: "14px",
              fontWeight: "500",
              color: "#0F172A",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {title}
          </div>
          {subtitle && (
            <div
              style={{
                fontSize: "12px",
                color: "#64748B",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                marginTop: "2px",
              }}
            >
              {subtitle}
            </div>
          )}
        </div>
      </div>

      <div
        style={{
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
        }}
      >
        {renderTrailing()}
      </div>
    </div>
  );
};

export const CardList = ({ spacing, children, style }) => {
  const spacingMap = {
    sm: "8px",
    md: "16px",
    lg: "24px",
  };
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: spacingMap[spacing] || "16px",
        marginBottom: PHONE_SPACING.component,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const Rating = ({ value = 0, reviews, spacing, style }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: "8px",
      marginBottom: spacing ? "10px" : PHONE_SPACING.badge,
      ...style,
    }}
  >
    <span style={{ fontSize: "16px" }}>
      {Array(Math.floor(value))
        .fill("★")
        .join("")}
      {Array(5 - Math.floor(value))
        .fill("☆")
        .join("")}
    </span>
    <span style={{ fontSize: "14px", color: "#64748B" }}>
      {value} {reviews && `(${reviews} reviews)`}
    </span>
  </div>
);

export const Alert = ({ type = "info", title, message, style }) => {
  const typeMap = {
    success: {
      bg: "#D1FAE5",
      border: "#10B981",
      icon: "Success",
    },
    error: {
      bg: "#FEE2E2",
      border: "#EF4444",
      icon: "Error",
    },
    warning: {
      bg: "#FEF3C7",
      border: "#F59E0B",
      icon: "Warning",
    },
    info: {
      bg: "#DBEAFE",
      border: "#3B82F6",
      icon: "Info",
    },
  };
  const config = typeMap[type] || typeMap.info;
  return (
    <div
      style={{
        padding: "12px 16px",
        background: config.bg,
        border: `1px solid ${config.border}`,
        borderRadius: "8px",
        marginBottom: PHONE_SPACING.component,
        display: "flex",
        gap: "12px",
        ...style,
      }}
    >
      <span style={{ fontSize: "20px" }}>{config.icon}</span>
      <div style={{ flex: 1 }}>
        {title && (
          <div
            style={{
              fontWeight: "600",
              marginBottom: "4px",
            }}
          >
            {title}
          </div>
        )}
        {message && (
          <div style={{ fontSize: "14px" }}>{message}</div>
        )}
      </div>
    </div>
  );
};

export const EmptyState = ({ icon = "Search", title = "No items", message, style }) => (
  <div
    style={{
      textAlign: "center",
      padding: "48px 24px",
      color: "#64748B",
      marginBottom: PHONE_SPACING.component,
      ...style,
    }}
  >
    <div
      style={{
        fontSize: "64px",
        marginBottom: "16px",
      }}
    >
      {icon}
    </div>
    <div
      style={{
        fontSize: "18px",
        fontWeight: "600",
        marginBottom: "8px",
        color: "#374151",
      }}
    >
      {title}
    </div>
    {message && (
      <div style={{ fontSize: "14px" }}>{message}</div>
    )}
  </div>
);

export const Form = ({ children, style }) => (
  <form
    onSubmit={(e) => e.preventDefault()}
    style={{
      width: "100%",
      display: "flex",
      flexDirection: "column",
      ...style,
    }}
  >
    {children}
  </form>
);

export const Footer = ({ text = "© 2025", style }) => (
  <footer
    style={{
      textAlign: "center",
      fontSize: "12px",
      color: "#9CA3AF",
      marginTop: "24px",
      marginBottom: PHONE_SPACING.component,
      ...style,
    }}
  >
    {text}
  </footer>
);

/* ============================================
   COMPONENT MAP & RENDERER
   ============================================ */
const COMPONENT_MAP = {
  container: Container,
  card: Card,
  spacer: Spacer,
  grid: Grid,
  stack: Stack,
  header: Header,
  text: Text,
  richtext: RichText,
  divider: Divider,
  badge: Badge,
  chip: Chip,
  textinput: TextInput,
  passwordinput: PasswordInput,
  iconinput: IconInput,
  searchinput: SearchInput,
  checkbox: Checkbox,
  switch: Switch,
  button: Button,
  gradientbutton: GradientButton,
  socialbutton: SocialButton,
  iconbutton: IconButton,
  floatingactionbutton: FloatingActionButton,
  linkbutton: LinkButton,
  link: Link,
  image: Image,
  avatar: Avatar,
  illustrationheader: IllustrationHeader,
  herosection: HeroSection,
  imagegallery: ImageGallery,
  statcard: StatCard,
  productcard: ProductCard,
  quantitycontrol: QuantityControl,
  cartitem: CartItem,
  pricebreakdown: PriceBreakdown,
  progressbar: ProgressBar,
  appbar: AppBar,
  tabbar: TabBar,
  formsection: FormSection,
  list: List,
  listitem: ListItem,
  cardlist: CardList,
  rating: Rating,
  alert: Alert,
  emptystate: EmptyState,
  form: Form,
  footer: Footer,
};

function normalizeNode(node) {
  if (!node || typeof node !== "object") return null;
  const typeLower = String(node.type || "").toLowerCase();
  let props = { ...(node.props || {}) };
  let kids = [];
  if (Array.isArray(props.children)) kids = [...props.children];
  else if (Array.isArray(props.items)) kids = [...props.items];
  else if (Array.isArray(node.children)) kids = [...node.children];
  delete props.children;
  delete props.items;

  let normalized = {
    ...node,
    props,
    children: kids.map(normalizeNode).filter(Boolean),
  };

  if (typeLower === "form") {
    const fields = props.fields || [];
    const buttons = props.buttons || [];
    const formChildren = [
      ...fields.map((f, i) => ({
        id: f.id || `field-${i}`,
        type: f.type || "TextInput",
        props: { ...(f.props || {}) },
      })),
      ...buttons.map((b, i) => ({
        id: b.id || `btn-${i}`,
        type: b.type || "Button",
        props: { ...(b.props || {}) },
      })),
    ];
    const cleanProps = { ...props };
    delete cleanProps.fields;
    delete cleanProps.buttons;
    normalized = {
      ...normalized,
      props: cleanProps,
      children: formChildren,
    };
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
      <div
        style={{
          border: "1px dashed #FCA5A5",
          background: "#FEF2F2",
          padding: "12px",
          borderRadius: "8px",
          marginBottom: "12px",
        }}
      >
        <div
          style={{
            fontSize: "12px",
            color: "#991B1B",
            marginBottom: "8px",
          }}
        >
          Unknown: {n.type}
        </div>
        {n.children?.map((c, i) => (
          <ComponentRendererLite key={c.id || i} node={c} />
        ))}
      </div>
    );
  }

  const themedProps = { ...n.props };
  if (key === "header" && !themedProps.color) themedProps.color = theme?.text;
  if (
    key === "button" &&
    !themedProps.bg &&
    (n.props?.variant ?? "primary") === "primary"
  ) {
    themedProps.bg = theme?.primary;
    themedProps.color = "#FFFFFF";
  }

  return (
    <Comp {...themedProps}>
      {Array.isArray(n.children) && n.children.length > 0
        ? n.children.map((c, idx) => (
          <ComponentRendererLite key={c.id || `child-${idx}`} node={c} />
        ))
        : null}
    </Comp>
  );
}
