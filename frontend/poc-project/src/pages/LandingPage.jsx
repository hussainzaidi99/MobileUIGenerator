/*frontend/poc-project/src/pages/LandingPage.jsx */
import React from "react";
import {
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
 * NEW: Stores the attempted path and redirects back after login
 */
function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // Show loading state while checking auth
  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#0f172a'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '48px',
            height: '48px',
            border: '4px solid rgba(102, 126, 234, 0.2)',
            borderTopColor: '#667EEA',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            margin: '0 auto 16px'
          }} />
          <p style={{ color: '#94a3b8', fontSize: '14px' }}>Loading...</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Store the current location they were trying to access
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  return children;
}

/**
 * 🆕 NEW: Public wrapper - allows anyone to view the page
 * No authentication required to VIEW, but actions may require auth
 */
function PublicRoute({ children }) {
  // Just render children without any auth check
  return children;
}

/**
 * 🆕 User Dropdown Menu Component
 */
function UserDropdownMenu({ user, userCredits, tierInfo, onLogout }) {
  const [isOpen, setIsOpen] = React.useState(false);
  const dropdownRef = React.useRef(null);
  const navigate = useNavigate();

  const initials = React.useMemo(() => {
    if (!user) return "U";
    const name = user.full_name || user.username || user.email || "User";
    const parts = name.trim().split(" ");
    if (parts.length === 1) return parts[0][0]?.toUpperCase() || "U";
    return (
      (parts[0][0] || "").toUpperCase() +
      (parts[1][0] || "").toUpperCase()
    );
  }, [user]);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="user-dropdown-container" ref={dropdownRef}>
      {/* User Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="user-dropdown-button"
      >
        <div 
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '14px',
            fontWeight: '600'
          }}
        >
          {initials}
        </div>
        <span style={{ fontSize: '14px', fontWeight: '500', color: '#334155' }}>
          {user.username || user.email?.split('@')[0] || 'User'}
        </span>
        <span style={{ fontSize: '12px', color: '#94A3B8', marginLeft: '-4px' }}>
          {isOpen ? '▲' : '▼'}
        </span>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="user-dropdown-menu">
          {/* User Info Section */}
          <div style={{ padding: '20px', borderBottom: '1px solid #E2E8F0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
              <div 
                style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
                  color: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '20px',
                  fontWeight: '600'
                }}
              >
                {initials}
              </div>
              <div>
                <div style={{ fontSize: '16px', fontWeight: '700', color: '#0F172A' }}>
                  {user.full_name || user.username || 'User'}
                </div>
                <div style={{ fontSize: '13px', color: '#64748B' }}>
                  {user.email}
                </div>
              </div>
            </div>

            {/* Tier Badge */}
            {tierInfo && (
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: '700',
                background: tierInfo.tier === 'pro' ? 'rgba(168, 85, 247, 0.1)' : 
                           tierInfo.tier === 'starter' ? 'rgba(6, 182, 212, 0.1)' : 
                           tierInfo.tier === 'enterprise' ? 'rgba(245, 158, 11, 0.1)' : 
                           'rgba(100, 116, 139, 0.1)',
                color: tierInfo.tier === 'pro' ? '#A855F7' : 
                       tierInfo.tier === 'starter' ? '#06B6D4' : 
                       tierInfo.tier === 'enterprise' ? '#F59E0B' : 
                       '#64748B',
                border: '1px solid',
                borderColor: tierInfo.tier === 'pro' ? 'rgba(168, 85, 247, 0.2)' : 
                            tierInfo.tier === 'starter' ? 'rgba(6, 182, 212, 0.2)' : 
                            tierInfo.tier === 'enterprise' ? 'rgba(245, 158, 11, 0.2)' : 
                            'rgba(100, 116, 139, 0.2)'
              }}>
                <span>{tierInfo.tier === 'pro' ? '⚡' : tierInfo.tier === 'starter' ? '🚀' : tierInfo.tier === 'enterprise' ? '👑' : '🆓'}</span>
                <span>{tierInfo.tier.toUpperCase()}</span>
              </div>
            )}
          </div>

          {/* Credits & Tokens Section */}
          {userCredits ? (
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #E2E8F0' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', color: '#64748B', fontWeight: '600' }}>💳 Credits</span>
                  <span style={{ fontSize: '16px', fontWeight: '700', color: '#0F172A' }}>
                    {userCredits.credits.toFixed(2)}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', color: '#64748B', fontWeight: '600' }}>🔢 Tokens</span>
                  <span style={{ fontSize: '16px', fontWeight: '700', color: '#0F172A' }}>
                    {new Intl.NumberFormat().format(userCredits.tokens_remaining)}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #E2E8F0', textAlign: 'center' }}>
              <span style={{ fontSize: '13px', color: '#64748B' }}>Loading credits...</span>
            </div>
          )}

          {/* Action Buttons */}
          <div style={{ padding: '12px' }}>
            <button
              onClick={() => {
                setIsOpen(false);
                navigate('/pricing');
              }}
              style={{
                width: '100%',
                padding: '12px',
                background: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '700',
                cursor: 'pointer',
                marginBottom: '8px',
                transition: 'all 0.2s',
                boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-1px)';
                e.target.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.3)';
              }}
            >
              ➕ {tierInfo?.can_upgrade ? 'Upgrade Plan' : 'Buy More Credits'}
            </button>
            
            <button
              onClick={() => {
                setIsOpen(false);
                onLogout();
              }}
              style={{
                width: '100%',
                padding: '12px',
                background: 'transparent',
                color: '#DC2626',
                border: '1px solid #FEE2E2',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#FEF2F2';
                e.target.style.borderColor = '#FECACA';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent';
                e.target.style.borderColor = '#FEE2E2';
              }}
            >
              🚪 Logout
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * 🆕 NEW: Modern Navigation Bar (AI Builder Style)
 */
function MainHeader() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [userCredits, setUserCredits] = React.useState(null);
  const [tierInfo, setTierInfo] = React.useState(null);

  const userId = user?.id;

  // Fetch user credits and tier info
  React.useEffect(() => {
    if (userId) {
      fetchUserCredits();
      fetchTierInfo();
    }
  }, [userId]);

  const fetchUserCredits = async () => {
    if (!userId) return;
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/balance/${userId}`
      );
      if (res.ok) {
        const data = await res.json();
        setUserCredits(data);
      }
    } catch (error) {
      console.error("Failed to fetch credits:", error);
    }
  };

  const fetchTierInfo = async () => {
    if (!userId) return;
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/tier/${userId}`
      );
      if (res.ok) {
        const data = await res.json();
        setTierInfo(data);
      }
    } catch (error) {
      console.error("Failed to fetch tier info:", error);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/", { replace: true });
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header 
      style={{
        background: '#FFFFFF',
        borderBottom: '1px solid #E5E7EB',
        padding: '16px 0',
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)'
      }}
    >
      <div 
        style={{
          maxWidth: '1400px',
          margin: '0 auto',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        {/* Left: Logo */}
        <Link
          to="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            textDecoration: 'none',
            color: '#0F172A'
          }}
        >
          <div 
            style={{
              width: '36px',
              height: '36px',
              background: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '20px'
            }}
          >
            🤖
          </div>
          <span 
            style={{
              fontSize: '20px',
              fontWeight: '700',
              color: '#0F172A'
            }}
          >
            AI Builder
          </span>
        </Link>

        {/* Center: Navigation Links */}
        <nav style={{ display: 'flex', gap: '32px', alignItems: 'center' }}>
          <Link
            to="/features"
            style={{
              fontSize: '15px',
              fontWeight: isActive('/features') ? '600' : '500',
              color: isActive('/features') ? '#667EEA' : '#64748B',
              textDecoration: 'none',
              transition: 'color 0.2s',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => e.target.style.color = '#667EEA'}
            onMouseLeave={(e) => e.target.style.color = isActive('/features') ? '#667EEA' : '#64748B'}
          >
            Features
          </Link>
          <Link
            to="/templates"
            style={{
              fontSize: '15px',
              fontWeight: isActive('/templates') ? '600' : '500',
              color: isActive('/templates') ? '#667EEA' : '#64748B',
              textDecoration: 'none',
              transition: 'color 0.2s',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => e.target.style.color = '#667EEA'}
            onMouseLeave={(e) => e.target.style.color = isActive('/templates') ? '#667EEA' : '#64748B'}
          >
            Templates
          </Link>
          <Link
            to="/pricing"
            style={{
              fontSize: '15px',
              fontWeight: isActive('/pricing') ? '600' : '500',
              color: isActive('/pricing') ? '#667EEA' : '#64748B',
              textDecoration: 'none',
              transition: 'color 0.2s',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => e.target.style.color = '#667EEA'}
            onMouseLeave={(e) => e.target.style.color = isActive('/pricing') ? '#667EEA' : '#64748B'}
          >
            Pricing
          </Link>
          <Link
            to="/showcase"
            style={{
              fontSize: '15px',
              fontWeight: isActive('/showcase') ? '600' : '500',
              color: isActive('/showcase') ? '#667EEA' : '#64748B',
              textDecoration: 'none',
              transition: 'color 0.2s',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => e.target.style.color = '#667EEA'}
            onMouseLeave={(e) => e.target.style.color = isActive('/showcase') ? '#667EEA' : '#64748B'}
          >
            Showcase
          </Link>
        </nav>

        {/* Right: Auth Buttons or User Dropdown */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {isAuthenticated ? (
            <UserDropdownMenu 
              user={user} 
              userCredits={userCredits}
              tierInfo={tierInfo}
              onLogout={handleLogout}
            />
          ) : (
            <>
              <button
                onClick={() => navigate('/auth', { state: { mode: 'login' } })}
                style={{
                  padding: '8px 20px',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#64748B',
                  background: 'transparent',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = '#F8FAFC';
                  e.target.style.color = '#334155';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'transparent';
                  e.target.style.color = '#64748B';
                }}
              >
                Sign In
              </button>
              <button
                onClick={() => navigate('/auth', { state: { mode: 'signup' } })}
                style={{
                  padding: '10px 24px',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#FFFFFF',
                  background: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)'
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateY(-1px)';
                  e.target.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.3)';
                }}
              >
                Get Started
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

/**
 * 🆕 Placeholder pages for Features, Templates, and Showcase
 */
function FeaturesPage() {
  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '80px 24px',
      textAlign: 'center'
    }}>
      <h1 style={{ fontSize: '48px', fontWeight: '700', marginBottom: '24px', color: '#0F172A' }}>
        Features
      </h1>
      <p style={{ fontSize: '20px', color: '#64748B', marginBottom: '48px' }}>
        Discover the powerful features of AI Builder
      </p>
      <div style={{
        padding: '48px',
        background: '#F8FAFC',
        borderRadius: '16px',
        border: '2px dashed #CBD5E1'
      }}>
        <p style={{ fontSize: '16px', color: '#94A3B8' }}>
          Content coming soon...
        </p>
      </div>
    </div>
  );
}

function TemplatesPage() {
  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '80px 24px',
      textAlign: 'center'
    }}>
      <h1 style={{ fontSize: '48px', fontWeight: '700', marginBottom: '24px', color: '#0F172A' }}>
        Templates
      </h1>
      <p style={{ fontSize: '20px', color: '#64748B', marginBottom: '48px' }}>
        Browse our collection of pre-built templates
      </p>
      <div style={{
        padding: '48px',
        background: '#F8FAFC',
        borderRadius: '16px',
        border: '2px dashed #CBD5E1'
      }}>
        <p style={{ fontSize: '16px', color: '#94A3B8' }}>
          Content coming soon...
        </p>
      </div>
    </div>
  );
}

function ShowcasePage() {
  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '80px 24px',
      textAlign: 'center'
    }}>
      <h1 style={{ fontSize: '48px', fontWeight: '700', marginBottom: '24px', color: '#0F172A' }}>
        Showcase
      </h1>
      <p style={{ fontSize: '20px', color: '#64748B', marginBottom: '48px' }}>
        See what others have built with AI Builder
      </p>
      <div style={{
        padding: '48px',
        background: '#F8FAFC',
        borderRadius: '16px',
        border: '2px dashed #CBD5E1'
      }}>
        <p style={{ fontSize: '16px', color: '#94A3B8' }}>
          Content coming soon...
        </p>
      </div>
    </div>
  );
}

function HomeHero() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleStart = () => {
    navigate("/");
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
            {isAuthenticated ? "Start Building" : "Get Started — It's free"}
          </button>
          <button
            className="btn-secondary"
            onClick={() => navigate("/pricing")}
          >
            View Pricing
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
 * Wrapper for AuthPage with redirect logic
 * NEW: Redirects back to the page user was trying to access
 */
function AuthRoute() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get the page they were trying to access, default to home (generation page)
  const from = location.state?.from?.pathname || "/";

  const handleSuccess = () => {
    console.log('✅ Auth successful, redirecting to:', from);
    
    navigate(from, { replace: true });
  };

  return <AuthPage onSuccess={handleSuccess} />;
}

/**
 * Layout wrapper for all routes (header + routed content)
 */
function Shell() {
  return (
    <>
      <MainHeader />
      <Routes>
        {/* 🆕 Default route - PUBLIC generation page */}
        <Route path="/" element={<App />} />

        {/* Navigation pages */}
        <Route path="/features" element={<FeaturesPage />} />
        <Route path="/templates" element={<TemplatesPage />} />
        <Route path="/showcase" element={<ShowcasePage />} />

        {/* Auth page - accessible to all */}
        <Route path="/auth" element={<AuthRoute />} />

        {/* Pricing page - accessible to all but requires auth for purchase */}
        <Route path="/pricing" element={<PricingPage />} />

        {/* 🆕 Optional about page (old landing hero) */}
        <Route path="/about" element={<HomeHero />} />
        
        {/* Payment status routes - require auth */}
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

        {/* Catch all - redirect to home (generation page) */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

/**
 * Public export — mount this from main.jsx:
 * ReactDOM.createRoot(...).render(
 *   <AuthProvider>
 *     <LandingPage />
 *   </AuthProvider>
 * );
 */
export default function LandingPage() {
  return (
      <Shell />
  );
} 