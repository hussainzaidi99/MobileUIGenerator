import React from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useLocation,
  useNavigate,
  Link,
} from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import AuthPage from "./AuthPage";
import App from "../App";
import { PaymentSuccess, PaymentCancelled } from './PaymentStatusPage';
import PricingPage from './PricingPage';

/**
 * Protects routes that require authentication.
 */
function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  return children;
}

/**
 * Top navigation/header. Uses header-user + btn-logout CSS you already have.
 */
function MainHeader() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const initials = React.useMemo(() => {
    if (!user) return "AB";
    const name =
      user.full_name || user.username || user.email || "User";
    const parts = name.trim().split(" ");
    if (parts.length === 1) return parts[0][0]?.toUpperCase() || "U";
    return (
      (parts[0][0] || "").toUpperCase() +
      (parts[1][0] || "").toUpperCase()
    );
  }, [user]);

  const handleLogout = async () => {
    await logout();
    navigate("/", { replace: true });
  };

  const goToAuth = () => navigate("/auth");

  return (
    <header className="app-header">
      <div className="header-content" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        {/* Left side: logo + title */}
        <div>
          <Link
            to="/"
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <h1 className="app-title">Mobile UI Generator</h1>
            <p className="app-subtitle">
              AI-Powered Mobile User Interfaces Generator
            </p>
          </Link>
        </div>

        {/* Right side: user section */}
        <div className="header-user">
          {isAuthenticated ? (
            <>
              <div className="user-info">
                <div className="user-avatar">{initials}</div>
                <div className="user-details">
                  <span className="user-name">
                    {user.full_name || user.username || "Authenticated User"}
                  </span>
                  <span className="user-email">{user.email}</span>
                </div>
              </div>
              <button className="btn-logout" onClick={handleLogout}>
                Logout
              </button>
            </>
          ) : (
            <button className="btn-primary" onClick={goToAuth}>
              Sign in / Sign up
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

/**
 * Simple marketing hero for "/".
 */
function HomeHero() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleStart = () => {
    if (isAuthenticated) {
      navigate("/app");
    } else {
      navigate("/auth");
    }
  };

  return (
    <main className="preview-section full-view">
      <div
        style={{
          maxWidth: "900px",
          margin: "0 auto",
          display: "flex",
          flexDirection: "column",
          gap: "2rem",
        }}
      >
        <section>
          <h2
            style={{
              fontSize: "2.25rem",
              fontWeight: 700,
              marginBottom: "0.75rem",
            }}
          >
            From prompt to production-ready mobile UI.
          </h2>
          <p
            style={{
              fontSize: "1rem",
              color: "var(--text-secondary)",
              maxWidth: "620px",
            }}
          >
            Describe your screens in plain English and let the AI generate
            beautiful layouts, live previews, and clean React Native code for
            your app. Perfect for rapid prototyping and internal tools.
          </p>
        </section>

        <section style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <button className="btn-primary" onClick={handleStart}>
            {isAuthenticated ? "Open Builder" : "Get Started – It’s free"}
          </button>
          <button
            className="btn-secondary"
            onClick={() => navigate("/app")}
            disabled={!isAuthenticated}
            title={
              isAuthenticated
                ? "Open the playground"
                : "Sign in first to access the playground"
            }
          >
            View Demo Workspace
          </button>
        </section>

        <section
          style={{
            marginTop: "1rem",
            padding: "1rem 1.25rem",
            borderRadius: "12px",
            background: "white",
            boxShadow: "var(--shadow-md)",
            border: "1px solid var(--border)",
          }}
        >
          <h3
            style={{
              fontSize: "1rem",
              fontWeight: 600,
              marginBottom: "0.5rem",
            }}
          >
            What you get
          </h3>
          <ul
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "0.75rem",
              listStyle: "none",
            }}
          >
            <li>
              <strong>🎯 Prompt-to-UI</strong>
              <div style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>
                Turn rough ideas into structured multi-screen layouts.
              </div>
            </li>
            <li>
              <strong>📱 Live preview</strong>
              <div style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>
                See your app screens side-by-side in a phone-like frame.
              </div>
            </li>
            <li>
              <strong>💻 React Native code</strong>
              <div style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>
                Export ready-to-edit components for your project.
              </div>
            </li>
          </ul>
        </section>
      </div>
    </main>
  );
}

/**
 * Wrapper for AuthPage so we can navigate after success.
 */
function AuthRoute() {
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/app";

  const handleSuccess = () => {
    navigate(from, { replace: true });
  };

  return <AuthPage onSuccess={handleSuccess} />;
}

/**
 * Layout for all routes (header + routed content).
 */
function Shell() {
  return (
    <>
      <MainHeader />
      <Routes>
        <Route path="/" element={<HomeHero />} />
        <Route path="/auth" element={<AuthRoute />} />
        <Route path="/pricing" element={<PricingPage />} />
        
        {/* NEW: Payment status routes */}
        <Route 
          path="/payment/success" 
          element={
            <RequireAuth>
              <PaymentSuccess />
            </RequireAuth>
          } 
        />
        <Route 
          path="/payment/cancel" 
          element={
            <RequireAuth>
              <PaymentCancelled />
            </RequireAuth>
          } 
        />
        
        <Route
          path="/app"
          element={
            <RequireAuth>
              <App />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

/**
 * Public export – mount this from index.jsx:
 * ReactDOM.createRoot(...).render(
 *   <AuthProvider>
 *     <LandingPage />
 *   </AuthProvider>
 * );
 */
export default function LandingPage() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  );
}
