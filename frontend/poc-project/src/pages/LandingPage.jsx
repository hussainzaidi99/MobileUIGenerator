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
 * 🎨 DARK VEIL: User Dropdown Menu Component
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
    <div style={{ position: 'relative' }} ref={dropdownRef}>
      {/* User Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '8px 14px',
          background: 'rgba(30, 30, 50, 0.6)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '10px',
          cursor: 'pointer',
          transition: 'all 0.2s',
          backdropFilter: 'blur(10px)'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'rgba(139, 92, 246, 0.2)';
          e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.5)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(30, 30, 50, 0.6)';
          e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)';
        }}
      >
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '14px',
            fontWeight: '600',
            boxShadow: '0 2px 8px rgba(139, 92, 246, 0.4)'
          }}
        >
          {initials}
        </div>
        <span style={{ fontSize: '14px', fontWeight: '500', color: '#cbd5e1' }}>
          {user.username || user.email?.split('@')[0] || 'User'}
        </span>
        <span style={{ fontSize: '12px', color: '#94A3B8', marginLeft: '-4px' }}>
          {isOpen ? '▲' : '▼'}
        </span>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            right: 0,
            minWidth: '320px',
            background: 'rgba(20, 20, 35, 0.95)',
            backdropFilter: 'blur(30px) saturate(180%)',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            borderRadius: '16px',
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.5)',
            zIndex: 9999,
            animation: 'dropdownSlideIn 0.2s ease-out'
          }}
        >
          <style>{`
            @keyframes dropdownSlideIn {
              from {
                opacity: 0;
                transform: translateY(-10px);
              }
              to {
                opacity: 1;
                transform: translateY(0);
              }
            }
          `}</style>

          {/* User Info Section */}
          <div style={{ padding: '20px', borderBottom: '1px solid rgba(139, 92, 246, 0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
              <div
                style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
                  color: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '20px',
                  fontWeight: '600',
                  boxShadow: '0 4px 12px rgba(139, 92, 246, 0.4)'
                }}
              >
                {initials}
              </div>
              <div>
                <div style={{ fontSize: '16px', fontWeight: '700', color: '#f8fafc' }}>
                  {user.full_name || user.username || 'User'}
                </div>
                <div style={{ fontSize: '13px', color: '#94a3b8' }}>
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
                background: tierInfo.tier === 'pro' ? 'rgba(168, 85, 247, 0.2)' :
                  tierInfo.tier === 'starter' ? 'rgba(6, 182, 212, 0.2)' :
                    tierInfo.tier === 'enterprise' ? 'rgba(245, 158, 11, 0.2)' :
                      'rgba(100, 116, 139, 0.2)',
                color: tierInfo.tier === 'pro' ? '#c084fc' :
                  tierInfo.tier === 'starter' ? '#67e8f9' :
                    tierInfo.tier === 'enterprise' ? '#fbbf24' :
                      '#94a3b8',
                border: '1px solid',
                borderColor: tierInfo.tier === 'pro' ? 'rgba(168, 85, 247, 0.4)' :
                  tierInfo.tier === 'starter' ? 'rgba(6, 182, 212, 0.4)' :
                    tierInfo.tier === 'enterprise' ? 'rgba(245, 158, 11, 0.4)' :
                      'rgba(100, 116, 139, 0.4)'
              }}>
                <span>{tierInfo.tier === 'pro' ? '⚡' : tierInfo.tier === 'starter' ? '🚀' : tierInfo.tier === 'enterprise' ? '👑' : '🆓'}</span>
                <span>{tierInfo.tier.toUpperCase()}</span>
              </div>
            )}
          </div>

          {/* Credits & Tokens Section */}
          {userCredits ? (
            <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(139, 92, 246, 0.2)' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600' }}>💳 Credits</span>
                  <span style={{ fontSize: '16px', fontWeight: '700', color: '#f8fafc' }}>
                    {userCredits.credits.toFixed(2)}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600' }}>🔢 Tokens</span>
                  <span style={{ fontSize: '16px', fontWeight: '700', color: '#f8fafc' }}>
                    {new Intl.NumberFormat().format(userCredits.tokens_remaining)}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(139, 92, 246, 0.2)', textAlign: 'center' }}>
              <span style={{ fontSize: '13px', color: '#94a3b8' }}>Loading credits...</span>
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
                background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '700',
                cursor: 'pointer',
                marginBottom: '8px',
                transition: 'all 0.2s',
                boxShadow: '0 4px 16px rgba(139, 92, 246, 0.4)'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 8px 24px rgba(139, 92, 246, 0.6)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 16px rgba(139, 92, 246, 0.4)';
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
                background: 'rgba(239, 68, 68, 0.15)',
                color: '#fca5a5',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s',
                backdropFilter: 'blur(10px)'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'rgba(239, 68, 68, 0.25)';
                e.target.style.borderColor = 'rgba(239, 68, 68, 0.5)';
                e.target.style.color = '#fff';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'rgba(239, 68, 68, 0.15)';
                e.target.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                e.target.style.color = '#fca5a5';
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
 * 🎨 DARK VEIL: Modern Navigation Bar (React Bits Style)
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
        background: 'rgba(10, 10, 20, 0.8)',
        backdropFilter: 'blur(20px) saturate(180%)',
        borderBottom: '1px solid rgba(139, 92, 246, 0.3)',
        padding: '16px 0',
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        boxShadow: '0 4px 24px rgba(0, 0, 0, 0.3)'
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
            color: '#f8fafc'
          }}
        >
          <div
            style={{
              width: '36px',
              height: '36px',
              background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '20px',
              boxShadow: '0 4px 12px rgba(139, 92, 246, 0.4)'
            }}
          >
            🤖
          </div>
          <span
            style={{
              fontSize: '20px',
              fontWeight: '700',
              background: 'linear-gradient(135deg, #a78bfa 0%, #ec4899 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}
          >
            App Builder
          </span>
        </Link>

        {/* Center: Navigation Links */}
        <nav style={{ display: 'flex', gap: '32px', alignItems: 'center' }}>
          <Link
            to="/features"
            style={{
              fontSize: '15px',
              fontWeight: isActive('/features') ? '600' : '500',
              color: isActive('/features') ? '#f8fafc' : '#cbd5e1',
              textDecoration: 'none',
              transition: 'all 0.2s',
              cursor: 'pointer',
              padding: '8px 16px',
              borderRadius: '8px',
              background: isActive('/features') ? 'rgba(139, 92, 246, 0.2)' : 'transparent'
            }}
            onMouseEnter={(e) => {
              e.target.style.color = '#f8fafc';
              if (!isActive('/features')) {
                e.target.style.background = 'rgba(139, 92, 246, 0.15)';
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.color = isActive('/features') ? '#f8fafc' : '#cbd5e1';
              if (!isActive('/features')) {
                e.target.style.background = 'transparent';
              }
            }}
          >
            Features
          </Link>
          <Link
            to="/templates"
            style={{
              fontSize: '15px',
              fontWeight: isActive('/templates') ? '600' : '500',
              color: isActive('/templates') ? '#f8fafc' : '#cbd5e1',
              textDecoration: 'none',
              transition: 'all 0.2s',
              cursor: 'pointer',
              padding: '8px 16px',
              borderRadius: '8px',
              background: isActive('/templates') ? 'rgba(139, 92, 246, 0.2)' : 'transparent'
            }}
            onMouseEnter={(e) => {
              e.target.style.color = '#f8fafc';
              if (!isActive('/templates')) {
                e.target.style.background = 'rgba(139, 92, 246, 0.15)';
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.color = isActive('/templates') ? '#f8fafc' : '#cbd5e1';
              if (!isActive('/templates')) {
                e.target.style.background = 'transparent';
              }
            }}
          >
            Templates
          </Link>
          <Link
            to="/pricing"
            style={{
              fontSize: '15px',
              fontWeight: isActive('/pricing') ? '600' : '500',
              color: isActive('/pricing') ? '#f8fafc' : '#cbd5e1',
              textDecoration: 'none',
              transition: 'all 0.2s',
              cursor: 'pointer',
              padding: '8px 16px',
              borderRadius: '8px',
              background: isActive('/pricing') ? 'rgba(139, 92, 246, 0.2)' : 'transparent'
            }}
            onMouseEnter={(e) => {
              e.target.style.color = '#f8fafc';
              if (!isActive('/pricing')) {
                e.target.style.background = 'rgba(139, 92, 246, 0.15)';
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.color = isActive('/pricing') ? '#f8fafc' : '#cbd5e1';
              if (!isActive('/pricing')) {
                e.target.style.background = 'transparent';
              }
            }}
          >
            Pricing
          </Link>
          <Link
            to="/showcase"
            style={{
              fontSize: '15px',
              fontWeight: isActive('/showcase') ? '600' : '500',
              color: isActive('/showcase') ? '#f8fafc' : '#cbd5e1',
              textDecoration: 'none',
              transition: 'all 0.2s',
              cursor: 'pointer',
              padding: '8px 16px',
              borderRadius: '8px',
              background: isActive('/showcase') ? 'rgba(139, 92, 246, 0.2)' : 'transparent'
            }}
            onMouseEnter={(e) => {
              e.target.style.color = '#f8fafc';
              if (!isActive('/showcase')) {
                e.target.style.background = 'rgba(139, 92, 246, 0.15)';
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.color = isActive('/showcase') ? '#f8fafc' : '#cbd5e1';
              if (!isActive('/showcase')) {
                e.target.style.background = 'transparent';
              }
            }}
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
                  color: '#cbd5e1',
                  background: 'transparent',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = 'rgba(139, 92, 246, 0.2)';
                  e.target.style.color = '#f8fafc';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'transparent';
                  e.target.style.color = '#cbd5e1';
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
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: '0 4px 16px rgba(139, 92, 246, 0.5)'
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 8px 24px rgba(139, 92, 246, 0.6)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 4px 16px rgba(139, 92, 246, 0.5)';
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
 * 🎨 FEATURES PAGE - Dark Veil Theme
 * Premium animated features showcase with React Bits style
 */

function FeaturesPage() {
  const [activeFeature, setActiveFeature] = React.useState(0);
  const [isVisible, setIsVisible] = React.useState({});

  // Intersection Observer for scroll animations
  React.useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible((prev) => ({
              ...prev,
              [entry.target.id]: true
            }));
          }
        });
      },
      { threshold: 0.1 }
    );

    document.querySelectorAll('.animate-on-scroll').forEach((el) => {
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const mainFeatures = [
    {
      icon: '🎯',
      title: 'AI-Powered Generation',
      description: 'Transform your ideas into production-ready mobile UIs in seconds',
      details: 'Our advanced AI understands natural language descriptions and generates complete, multi-screen mobile applications with proper navigation, components, and styling.',
      gradient: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)'
    },
    {
      icon: '📱',
      title: 'Live Preview',
      description: 'See your designs come to life in real-time phone mockups',
      details: 'Instantly visualize your generated UI in realistic iPhone-style frames. Multiple screens displayed side-by-side for easy comparison and iteration.',
      gradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)'
    },
    {
      icon: '💻',
      title: 'React Native Export',
      description: 'Get production-ready code you can use immediately',
      details: 'Export clean, organized React Native components with proper file structure. Copy-paste ready code that follows best practices and industry standards.',
      gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
    },
    {
      icon: '✨',
      title: 'Smart Refinement',
      description: 'Iterate and improve your designs with conversational editing',
      details: 'Make changes using natural language. Ask for color adjustments, layout modifications, or content updates - the AI understands and implements your requests.',
      gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
    }
  ];

  const detailedFeatures = [
    {
      icon: '🎨',
      title: 'Beautiful Design System',
      description: 'Professionally designed components with modern aesthetics',
      color: '#a855f7'
    },
    {
      icon: '🚀',
      title: 'Lightning Fast',
      description: 'Generate complete apps in under 30 seconds',
      color: '#06b6d4'
    },
    {
      icon: '📐',
      title: 'Responsive Layouts',
      description: 'Perfect scaling across all device sizes',
      color: '#10b981'
    },
    {
      icon: '🔄',
      title: 'Version History',
      description: 'Track changes and revert to previous versions',
      color: '#f59e0b'
    },
    {
      icon: '🎭',
      title: 'Theme Support',
      description: 'Light and dark mode out of the box',
      color: '#ec4899'
    },
    {
      icon: '🔌',
      title: 'Component Library',
      description: 'Pre-built components ready to use',
      color: '#8b5cf6'
    }
  ];

  const useCases = [
    {
      title: 'Rapid Prototyping',
      description: 'Create mockups for client presentations in minutes',
      icon: '⚡',
      color: '#8b5cf6'
    },
    {
      title: 'MVP Development',
      description: 'Build and launch your minimum viable product faster',
      icon: '🎯',
      color: '#06b6d4'
    },
    {
      title: 'Design Exploration',
      description: 'Try multiple design directions effortlessly',
      icon: '🎨',
      color: '#10b981'
    },
    {
      title: 'Learning & Education',
      description: 'Teach mobile UI design with practical examples',
      icon: '📚',
      color: '#f59e0b'
    }
  ];

  return (
    <div style={{
      minHeight: '100vh',
      background: 'transparent',
      color: '#f8fafc',
      overflow: 'hidden'
    }}>
      {/* Hero Section */}
      <section style={{
        padding: '120px 24px 80px',
        textAlign: 'center',
        position: 'relative'
      }}>
        <div style={{
          maxWidth: '900px',
          margin: '0 auto',
          position: 'relative',
          zIndex: 1
        }}>
          <div style={{
            display: 'inline-block',
            padding: '8px 20px',
            background: 'rgba(139, 92, 246, 0.2)',
            border: '1px solid rgba(139, 92, 246, 0.4)',
            borderRadius: '20px',
            fontSize: '14px',
            fontWeight: '700',
            color: '#c084fc',
            marginBottom: '24px',
            animation: 'fadeInDown 0.6s ease-out'
          }}>
            ✨ POWERFUL FEATURES
          </div>

          <h1 style={{
            fontSize: '64px',
            fontWeight: '900',
            marginBottom: '24px',
            background: 'linear-gradient(135deg, #f8fafc 0%, #c084fc 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            lineHeight: '1.1',
            animation: 'fadeInUp 0.8s ease-out 0.2s both'
          }}>
            Everything You Need<br />
            to Build Amazing Apps
          </h1>

          <p style={{
            fontSize: '22px',
            color: '#cbd5e1',
            lineHeight: '1.6',
            maxWidth: '700px',
            margin: '0 auto',
            animation: 'fadeInUp 0.8s ease-out 0.4s both'
          }}>
            From idea to production-ready code in seconds. App Builder gives you all the tools to create, iterate, and export beautiful mobile interfaces.
          </p>
        </div>

        {/* Floating Elements */}
        <div style={{
          position: 'absolute',
          top: '10%',
          right: '10%',
          width: '300px',
          height: '300px',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.15), transparent 70%)',
          borderRadius: '50%',
          filter: 'blur(60px)',
          animation: 'float 8s ease-in-out infinite',
          pointerEvents: 'none'
        }} />
      </section>

      {/* Main Features - Interactive Cards */}
      <section
        id="main-features"
        className="animate-on-scroll"
        style={{
          padding: '80px 24px',
          maxWidth: '1200px',
          margin: '0 auto',
          opacity: isVisible['main-features'] ? 1 : 0,
          transform: isVisible['main-features'] ? 'translateY(0)' : 'translateY(40px)',
          transition: 'all 0.8s ease-out'
        }}
      >
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '24px'
        }}>
          {mainFeatures.map((feature, index) => (
            <div
              key={index}
              onMouseEnter={() => setActiveFeature(index)}
              style={{
                background: activeFeature === index
                  ? 'rgba(30, 30, 50, 0.8)'
                  : 'rgba(30, 30, 50, 0.4)',
                backdropFilter: 'blur(20px)',
                border: `2px solid ${activeFeature === index ? 'rgba(139, 92, 246, 0.6)' : 'rgba(139, 92, 246, 0.2)'}`,
                borderRadius: '20px',
                padding: '32px',
                cursor: 'pointer',
                transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                transform: activeFeature === index ? 'translateY(-8px)' : 'translateY(0)',
                boxShadow: activeFeature === index
                  ? '0 20px 60px rgba(139, 92, 246, 0.3)'
                  : '0 8px 24px rgba(0, 0, 0, 0.2)',
                animation: `fadeInUp 0.6s ease-out ${index * 0.1}s both`
              }}
            >
              <div style={{
                width: '72px',
                height: '72px',
                background: feature.gradient,
                borderRadius: '16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '36px',
                marginBottom: '24px',
                transform: activeFeature === index ? 'scale(1.1) rotate(5deg)' : 'scale(1)',
                transition: 'transform 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
                boxShadow: '0 8px 24px rgba(139, 92, 246, 0.4)'
              }}>
                {feature.icon}
              </div>

              <h3 style={{
                fontSize: '24px',
                fontWeight: '800',
                color: '#f8fafc',
                marginBottom: '12px'
              }}>
                {feature.title}
              </h3>

              <p style={{
                fontSize: '16px',
                color: '#94a3b8',
                lineHeight: '1.6',
                marginBottom: '16px'
              }}>
                {feature.description}
              </p>

              <p style={{
                fontSize: '14px',
                color: '#64748b',
                lineHeight: '1.6',
                opacity: activeFeature === index ? 1 : 0,
                maxHeight: activeFeature === index ? '200px' : '0',
                overflow: 'hidden',
                transition: 'all 0.4s ease-out'
              }}>
                {feature.details}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Detailed Features Grid */}
      <section
        id="detailed-features"
        className="animate-on-scroll"
        style={{
          padding: '80px 24px',
          background: 'rgba(10, 10, 20, 0.4)',
          backdropFilter: 'blur(10px)',
          opacity: isVisible['detailed-features'] ? 1 : 0,
          transform: isVisible['detailed-features'] ? 'translateY(0)' : 'translateY(40px)',
          transition: 'all 0.8s ease-out'
        }}
      >
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h2 style={{
            fontSize: '48px',
            fontWeight: '900',
            textAlign: 'center',
            marginBottom: '16px',
            background: 'linear-gradient(135deg, #f8fafc 0%, #a78bfa 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            Packed with Premium Features
          </h2>
          <p style={{
            textAlign: 'center',
            fontSize: '18px',
            color: '#94a3b8',
            marginBottom: '60px',
            maxWidth: '600px',
            margin: '0 auto 60px'
          }}>
            Everything you need for professional mobile app development
          </p>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '24px'
          }}>
            {detailedFeatures.map((feature, index) => (
              <div
                key={index}
                style={{
                  background: 'rgba(30, 30, 50, 0.4)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(139, 92, 246, 0.2)',
                  borderRadius: '16px',
                  padding: '28px',
                  transition: 'all 0.3s ease-out',
                  animation: `fadeInUp 0.5s ease-out ${index * 0.05}s both`,
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.5)';
                  e.currentTarget.style.background = 'rgba(30, 30, 50, 0.6)';
                  e.currentTarget.style.boxShadow = '0 12px 40px rgba(139, 92, 246, 0.2)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.2)';
                  e.currentTarget.style.background = 'rgba(30, 30, 50, 0.4)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{
                  fontSize: '40px',
                  marginBottom: '16px',
                  display: 'inline-block',
                  transition: 'transform 0.3s ease-out'
                }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'scale(1.2) rotate(-10deg)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'scale(1) rotate(0deg)';
                  }}
                >
                  {feature.icon}
                </div>
                <h4 style={{
                  fontSize: '18px',
                  fontWeight: '700',
                  color: '#f8fafc',
                  marginBottom: '8px'
                }}>
                  {feature.title}
                </h4>
                <p style={{
                  fontSize: '14px',
                  color: '#94a3b8',
                  lineHeight: '1.6'
                }}>
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section
        id="use-cases"
        className="animate-on-scroll"
        style={{
          padding: '80px 24px',
          maxWidth: '1200px',
          margin: '0 auto',
          opacity: isVisible['use-cases'] ? 1 : 0,
          transform: isVisible['use-cases'] ? 'translateY(0)' : 'translateY(40px)',
          transition: 'all 0.8s ease-out'
        }}
      >
        <h2 style={{
          fontSize: '48px',
          fontWeight: '900',
          textAlign: 'center',
          marginBottom: '16px',
          background: 'linear-gradient(135deg, #f8fafc 0%, #ec4899 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}>
          Perfect For Any Use Case
        </h2>
        <p style={{
          textAlign: 'center',
          fontSize: '18px',
          color: '#94a3b8',
          marginBottom: '60px',
          maxWidth: '600px',
          margin: '0 auto 60px'
        }}>
          Whether you're a founder, designer, or developer
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '32px'
        }}>
          {useCases.map((useCase, index) => (
            <div
              key={index}
              style={{
                position: 'relative',
                background: 'rgba(30, 30, 50, 0.6)',
                backdropFilter: 'blur(20px)',
                border: '2px solid rgba(139, 92, 246, 0.3)',
                borderRadius: '20px',
                padding: '40px 28px',
                textAlign: 'center',
                transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                animation: `scaleIn 0.6s ease-out ${index * 0.1}s both`,
                cursor: 'pointer',
                overflow: 'hidden'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px) scale(1.02)';
                e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.6)';
                e.currentTarget.style.boxShadow = '0 20px 60px rgba(139, 92, 246, 0.3)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0) scale(1)';
                e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={{
                width: '80px',
                height: '80px',
                background: `linear-gradient(135deg, ${useCase.color}, ${useCase.color}dd)`,
                borderRadius: '20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '40px',
                margin: '0 auto 24px',
                boxShadow: `0 8px 32px ${useCase.color}66`,
                transition: 'transform 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55)'
              }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'rotate(10deg) scale(1.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'rotate(0deg) scale(1)';
                }}
              >
                {useCase.icon}
              </div>
              <h3 style={{
                fontSize: '22px',
                fontWeight: '800',
                color: '#f8fafc',
                marginBottom: '12px'
              }}>
                {useCase.title}
              </h3>
              <p style={{
                fontSize: '15px',
                color: '#94a3b8',
                lineHeight: '1.6'
              }}>
                {useCase.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section style={{
        padding: '100px 24px',
        textAlign: 'center',
        position: 'relative'
      }}>
        <div style={{
          maxWidth: '700px',
          margin: '0 auto',
          position: 'relative',
          zIndex: 1
        }}>
          <h2 style={{
            fontSize: '56px',
            fontWeight: '900',
            marginBottom: '24px',
            background: 'linear-gradient(135deg, #a78bfa 0%, #ec4899 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            lineHeight: '1.1'
          }}>
            Ready to Build Something Amazing?
          </h2>
          <p style={{
            fontSize: '20px',
            color: '#cbd5e1',
            marginBottom: '40px',
            lineHeight: '1.6'
          }}>
            Join thousands of developers already using App Builder
          </p>
          <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => window.location.href = '/'}
              style={{
                padding: '16px 40px',
                fontSize: '18px',
                fontWeight: '700',
                color: '#FFFFFF',
                background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
                border: 'none',
                borderRadius: '12px',
                cursor: 'pointer',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                boxShadow: '0 8px 32px rgba(139, 92, 246, 0.5)'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-4px)';
                e.target.style.boxShadow = '0 12px 48px rgba(139, 92, 246, 0.6)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 8px 32px rgba(139, 92, 246, 0.5)';
              }}
            >
              Start Building Now →
            </button>
            <button
              onClick={() => window.location.href = '/pricing'}
              style={{
                padding: '16px 40px',
                fontSize: '18px',
                fontWeight: '700',
                color: '#cbd5e1',
                background: 'rgba(30, 30, 50, 0.6)',
                border: '2px solid rgba(139, 92, 246, 0.3)',
                borderRadius: '12px',
                cursor: 'pointer',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                backdropFilter: 'blur(10px)'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-4px)';
                e.target.style.background = 'rgba(139, 92, 246, 0.2)';
                e.target.style.borderColor = 'rgba(139, 92, 246, 0.5)';
                e.target.style.color = '#f8fafc';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.background = 'rgba(30, 30, 50, 0.6)';
                e.target.style.borderColor = 'rgba(139, 92, 246, 0.3)';
                e.target.style.color = '#cbd5e1';
              }}
            >
              View Pricing
            </button>
          </div>
        </div>

        {/* Background Glow */}
        <div style={{
          position: 'absolute',
          bottom: '0',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '600px',
          height: '400px',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.2), transparent 70%)',
          borderRadius: '50%',
          filter: 'blur(80px)',
          pointerEvents: 'none'
        }} />
      </section>

      {/* Animations */}
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes fadeInDown {
          from {
            opacity: 0;
            transform: translateY(-30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-30px);
          }
        }

        @keyframes scaleIn {
          from {
            opacity: 0;
            transform: scale(0.8);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        @media (max-width: 768px) {
          h1 {
            font-size: 40px !important;
          }
          h2 {
            font-size: 32px !important;
          }
        }
      `}</style>
    </div>
  );
}

const templates = [
  { title: "Analytics Dashboard", category: "Business", image: "/templates/AnalyticsDashboard.png", screens: 8, color: "#8b5cf6" },
  { title: "Shopping Cart", category: "E-commerce", image: "/templates/Cart.png", screens: 4, color: "#06b6d4" },
  { title: "User Signup", category: "Social", image: "/templates/Signup.png", screens: 3, color: "#10b981" },
  { title: "Checkout Flow", category: "Finance", image: "/templates/checkout.png", screens: 6, color: "#f59e0b" },
  { title: "Profile Editor", category: "Utility", image: "/templates/editprofile.png", screens: 2, color: "#ec4899" },
  { title: "Social Feed", category: "Social", image: "/templates/feed.png", screens: 10, color: "#8b5cf6" },
  { title: "Fitness Tracker", category: "Health", image: "/templates/fitnesstracker.png", screens: 12, color: "#06b6d4" },
  { title: "Product Listing", category: "Shopping", image: "/templates/productlist.png", screens: 5, color: "#10b981" },
  { title: "User Profile", category: "Social", image: "/templates/userprofile.png", screens: 4, color: "#f59e0b" },
  { title: "Login Screen", category: "Auth", image: "/templates/login.png", screens: 3, color: "#ec4899" },
];

function TemplateCard({ template }) {
  const [isHovered, setIsHovered] = React.useState(false);

  return (
    <div
      style={{
        flex: '0 0 350px',
        height: '450px',
        position: 'relative',
        borderRadius: '24px',
        overflow: 'hidden',
        background: 'rgba(30, 30, 50, 0.4)',
        border: `1px solid ${isHovered ? template.color : 'rgba(139, 92, 246, 0.2)'}`,
        transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
        transform: isHovered ? 'scale(1.05) translateY(-10px)' : 'scale(1) translateY(0)',
        boxShadow: isHovered ? `0 20px 40px ${template.color}33` : '0 10px 30px rgba(0,0,0,0.2)',
        cursor: 'pointer'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Image */}
      <img
        src={template.image}
        alt={template.title}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transition: 'transform 0.5s ease',
          transform: isHovered ? 'scale(1.1)' : 'scale(1)'
        }}
      />

      {/* Overlay */}
      <div style={{
        position: 'absolute',
        inset: 0,
        background: 'linear-gradient(to top, rgba(15, 23, 42, 0.9) 0%, rgba(15, 23, 42, 0.4) 50%, transparent 100%)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-end',
        padding: '24px',
        opacity: isHovered ? 1 : 0.8,
        transition: 'opacity 0.3s ease'
      }}>
        <div style={{
          padding: '6px 12px',
          background: `${template.color}22`,
          border: `1px solid ${template.color}44`,
          borderRadius: '20px',
          fontSize: '12px',
          fontWeight: '700',
          color: template.color,
          width: 'fit-content',
          marginBottom: '12px'
        }}>
          {template.category}
        </div>
        <h3 style={{
          fontSize: '24px',
          fontWeight: '800',
          color: '#f8fafc',
          marginBottom: '8px'
        }}>
          {template.title}
        </h3>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: '#94a3b8',
          fontSize: '14px'
        }}>
          <span>📱 {template.screens} Screens</span>
          <span style={{ color: '#475569' }}>•</span>
          <span>Ready to Export</span>
        </div>
      </div>

      {/* Hover Light Effect */}
      {isHovered && (
        <div style={{
          position: 'absolute',
          top: '-50%',
          left: '-50%',
          width: '200%',
          height: '200%',
          background: `radial-gradient(circle, ${template.color}11 0%, transparent 70%)`,
          pointerEvents: 'none',
          animation: 'rotateGlow 4s linear infinite'
        }} />
      )}
    </div>
  );
}

function TemplatesPage() {
  return (
    <div style={{
      minHeight: 'calc(100vh - 80px)',
      background: 'transparent',
      color: '#f8fafc',
      padding: '80px 0',
      overflow: 'hidden',
      position: 'relative'
    }}>
      {/* Background Orbs */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '5%',
        width: '400px',
        height: '400px',
        background: 'radial-gradient(circle, rgba(139, 92, 246, 0.1), transparent 70%)',
        filter: 'blur(80px)',
        pointerEvents: 'none'
      }} />
      <div style={{
        position: 'absolute',
        bottom: '10%',
        right: '5%',
        width: '500px',
        height: '500px',
        background: 'radial-gradient(circle, rgba(6, 182, 212, 0.08), transparent 70%)',
        filter: 'blur(80px)',
        pointerEvents: 'none'
      }} />

      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '0 24px',
        textAlign: 'center',
        marginBottom: '80px',
        position: 'relative',
        zIndex: 2
      }}>
        <div style={{
          display: 'inline-block',
          padding: '8px 20px',
          background: 'rgba(139, 92, 246, 0.2)',
          border: '1px solid rgba(139, 92, 246, 0.4)',
          borderRadius: '20px',
          fontSize: '14px',
          fontWeight: '700',
          color: '#c084fc',
          marginBottom: '24px'
        }}>
          🎨 DESIGN GALLERY
        </div>
        <h1 style={{
          fontSize: '64px',
          fontWeight: '900',
          marginBottom: '24px',
          background: 'linear-gradient(135deg, #f8fafc 0%, #c084fc 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          lineHeight: '1.1'
        }}>
          Industry-Leading Templates
        </h1>
        <p style={{
          fontSize: '20px',
          color: '#94a3b8',
          maxWidth: '700px',
          margin: '0 auto',
          lineHeight: '1.6'
        }}>
          Jumpstart your next project with our professionally designed collection of mobile UI templates. Fully customizable and ready for production.
        </p>
      </div>

      {/* Marquee Container */}
      <div style={{
        position: 'relative',
        width: '100%',
        padding: '40px 0',
        background: 'rgba(15, 23, 42, 0.3)',
        backdropFilter: 'blur(20px)',
        borderY: '1px solid rgba(255, 255, 255, 0.05)',
        display: 'flex',
        alignItems: 'center',
        overflow: 'hidden'
      }}>
        {/* Left Mask */}
        <div style={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: '200px',
          background: 'linear-gradient(to right, #0f172a 0%, transparent 100%)',
          zIndex: 10,
          pointerEvents: 'none'
        }} />

        {/* Right Mask */}
        <div style={{
          position: 'absolute',
          right: 0,
          top: 0,
          bottom: 0,
          width: '200px',
          background: 'linear-gradient(to left, #0f172a 0%, transparent 100%)',
          zIndex: 10,
          pointerEvents: 'none'
        }} />

        <div className="marquee-track" style={{
          display: 'flex',
          gap: '32px',
          padding: '0 16px',
          width: 'fit-content',
          animation: 'scroll-left 30s linear infinite'
        }}>
          {/* First set */}
          {templates.map((template, idx) => (
            <TemplateCard key={`set1-${idx}`} template={template} />
          ))}
          {/* Second set for seamless loop */}
          {templates.map((template, idx) => (
            <TemplateCard key={`set2-${idx}`} template={template} />
          ))}
        </div>
      </div>

      <div style={{
        marginTop: '100px',
        textAlign: 'center',
        position: 'relative',
        zIndex: 2
      }}>
        <button
          onClick={() => window.location.href = '/'}
          style={{
            padding: '16px 40px',
            fontSize: '18px',
            fontWeight: '700',
            color: '#FFFFFF',
            background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
            border: 'none',
            borderRadius: '12px',
            cursor: 'pointer',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            boxShadow: '0 8px 32px rgba(139, 92, 246, 0.5)'
          }}
          onMouseEnter={(e) => {
            e.target.style.transform = 'translateY(-4px)';
            e.target.style.boxShadow = '0 12px 48px rgba(139, 92, 246, 0.6)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)';
            e.target.style.boxShadow = '0 8px 32px rgba(139, 92, 246, 0.5)';
          }}
        >
          View All 50+ Templates
        </button>
      </div>

      <style>{`
        @keyframes scroll-left {
          from {
            transform: translateX(0);
          }
          to {
            transform: translateX(calc(-50% - 16px));
          }
        }

        .marquee-track:hover {
          animation-play-state: paused;
        }

        @keyframes rotateGlow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
          h1 { font-size: 40px !important; }
          .marquee-track { gap: 16px !important; }
          div[style*="flex: 0 0 350px"] { flex: 0 0 280px !important; height: 380px !important; }
        }
      `}</style>
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
        See what others have built with App Builder
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
  const location = useLocation();
  const isAuthPage = location.pathname === '/auth' || location.pathname.startsWith('/auth/');
  return (
    <>
      {!isAuthPage && <MainHeader />}
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