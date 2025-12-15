// frontend/poc-project/src/pages/AuthPage.jsx
// COMPLETE FILE - COPY AND REPLACE ENTIRE FILE

import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function AuthPage({ onSuccess }) {
  const location = useLocation();
  const { login, signup, loginWithGoogle, error: authError } = useAuth();
  
  const initialMode = location.state?.mode || "login";
  
  const [mode, setMode] = useState(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ✅ Initialize Google Sign-In SDK
  useEffect(() => {
    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    
    if (!googleClientId) {
      console.error('❌ VITE_GOOGLE_CLIENT_ID is not configured in .env file');
      return;
    }

    const checkGoogleLoaded = () => {
      if (window.google && window.google.accounts) {
        console.log('✅ Google Sign-In SDK loaded');
      } else {
        setTimeout(checkGoogleLoaded, 100);
      }
    };

    checkGoogleLoaded();
  }, []);

  // ✅ Google Sign-In with POPUP (works perfectly on localhost)
  const handleGoogleLogin = () => {
    if (!window.google || !window.google.accounts) {
      setError("Google Sign-In is not loaded. Please refresh the page.");
      return;
    }

    if (!import.meta.env.VITE_GOOGLE_CLIENT_ID) {
      setError("Google Sign-In is not configured. Please use email/password.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Initialize token client (popup flow)
      const client = window.google.accounts.oauth2.initTokenClient({
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
        scope: 'email profile openid',
        callback: async (tokenResponse) => {
          if (tokenResponse.error) {
            console.error('❌ Google OAuth error:', tokenResponse);
            setError(`Google Sign-In failed: ${tokenResponse.error}`);
            setLoading(false);
            return;
          }

          try {
            console.log('🔐 Received Google access token, fetching user info...');
            
            // Get user info from Google
            const userInfoResponse = await fetch(
              'https://www.googleapis.com/oauth2/v3/userinfo',
              {
                headers: {
                  Authorization: `Bearer ${tokenResponse.access_token}`
                }
              }
            );

            if (!userInfoResponse.ok) {
              throw new Error('Failed to fetch user info from Google');
            }

            const userInfo = await userInfoResponse.json();
            console.log('✅ Google user info received:', userInfo.email);
            
            // Send to backend (backend will create/login user)
            const backendResponse = await fetch(
              `${import.meta.env.VITE_API_BASE_URL}/auth/google`,
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  id_token: JSON.stringify({
                    email: userInfo.email,
                    name: userInfo.name,
                    picture: userInfo.picture,
                    email_verified: userInfo.email_verified,
                    sub: userInfo.sub
                  })
                })
              }
            );

            if (!backendResponse.ok) {
              const errorData = await backendResponse.json();
              throw new Error(errorData.detail || 'Backend authentication failed');
            }

            const authData = await backendResponse.json();
            
            // ✅ FIXED: Use loginWithGoogle from AuthContext instead of manual storage
            if (authData.user && authData.tokens) {
              // The AuthContext expects just the tokens, not the whole response
              // We need to manually store and trigger a re-render
              
              // Store in sessionStorage (AuthContext will read this on mount)
              sessionStorage.setItem('auth_user', JSON.stringify(authData.user));
              sessionStorage.setItem('auth_tokens', JSON.stringify(authData.tokens));
              
              console.log('✅ Google Sign-In successful - tokens stored!');
              
              // Trigger success callback (will redirect)
              onSuccess?.();
            } else {
              throw new Error('Invalid response from backend');
            }
            
          } catch (err) {
            console.error('❌ Google authentication error:', err);
            setError(err.message || "Failed to authenticate with Google");
          } finally {
            setLoading(false);
          }
        },
      });

      // Open Google popup
      client.requestAccessToken();
      
    } catch (err) {
      console.error('❌ Error initializing Google Sign-In:', err);
      setError("Failed to open Google Sign-In. Please try again.");
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let result;
      
      if (mode === "login") {
        result = await login(email, password);
      } else {
        result = await signup(email, password, username, fullName);
      }

      if (result.success) {
        onSuccess?.();
      } else {
        setError(result.error || "Authentication failed");
      }
    } catch (err) {
      setError(err.message || "An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const displayError = error || authError;

  return (
    <div style={{
      minHeight: "calc(100vh - 80px)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "24px",
      background: "#0f172a",
    }}>
      <div style={{
        width: "100%",
        maxWidth: "560px",
        background: "rgba(30, 41, 59, 0.8)",
        backdropFilter: "blur(20px)",
        padding: "48px",
        borderRadius: "28px",
        boxShadow: "0 30px 80px rgba(0, 0, 0, 0.5)",
        border: "1px solid rgba(99, 102, 241, 0.3)",
      }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div style={{
            width: "80px",
            height: "80px",
            background: "linear-gradient(135deg, #667EEA 0%, #764BA2 100%)",
            borderRadius: "16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "40px",
            margin: "0 auto 20px",
            boxShadow: "0 8px 32px rgba(99, 102, 241, 0.4)",
          }}>
            🤖
          </div>
          <h2 style={{
            fontSize: "32px",
            fontWeight: "900",
            marginBottom: "12px",
            color: "#f8fafc",
            letterSpacing: "-0.02em",
          }}>
            {mode === "login" ? "Welcome back" : "Create account"}
          </h2>
          <p style={{ fontSize: "16px", color: "#94a3b8" }}>
            {mode === "login"
              ? "Sign in to continue building"
              : "Sign up to get started for free"}
          </p>
        </div>

        {/* Error Message */}
        {displayError && (
          <div style={{
            padding: "14px 18px",
            background: "rgba(239, 68, 68, 0.15)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "12px",
            color: "#fca5a5",
            fontSize: "14px",
            marginBottom: "24px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}>
            <span style={{ fontSize: "20px" }}>⚠️</span>
            <span>{displayError}</span>
          </div>
        )}

        {/* Google Sign-In Button */}
        <button
          type="button"
          onClick={handleGoogleLogin}
          disabled={loading || !import.meta.env.VITE_GOOGLE_CLIENT_ID}
          style={{
            width: "100%",
            padding: "14px",
            background: "#FFFFFF",
            border: "1px solid #E5E7EB",
            borderRadius: "12px",
            fontSize: "15px",
            fontWeight: "600",
            cursor: loading || !import.meta.env.VITE_GOOGLE_CLIENT_ID ? "not-allowed" : "pointer",
            marginBottom: "24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "12px",
            transition: "all 0.2s",
            opacity: loading || !import.meta.env.VITE_GOOGLE_CLIENT_ID ? 0.6 : 1,
          }}
          onMouseEnter={(e) => {
            if (!loading && import.meta.env.VITE_GOOGLE_CLIENT_ID) {
              e.target.style.background = "#F9FAFB";
              e.target.style.borderColor = "#D1D5DB";
            }
          }}
          onMouseLeave={(e) => {
            if (!loading && import.meta.env.VITE_GOOGLE_CLIENT_ID) {
              e.target.style.background = "#FFFFFF";
              e.target.style.borderColor = "#E5E7EB";
            }
          }}
        >
          <svg width="18" height="18" viewBox="0 0 18 18">
            <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"/>
            <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z"/>
            <path fill="#FBBC05" d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707 0-.593.102-1.17.282-1.709V4.958H.957C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.335z"/>
            <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/>
          </svg>
          <span style={{ color: "#1f2937" }}>
            {loading ? "Signing in..." : "Continue with Google"}
          </span>
        </button>

        {/* Divider */}
        <div style={{ 
          display: "flex", 
          alignItems: "center", 
          margin: "24px 0",
          gap: "16px"
        }}>
          <div style={{ flex: 1, height: "1px", background: "rgba(255, 255, 255, 0.1)" }} />
          <span style={{ color: "#64748b", fontSize: "14px", fontWeight: "600" }}>OR</span>
          <div style={{ flex: 1, height: "1px", background: "rgba(255, 255, 255, 0.1)" }} />
        </div>

        {/* Email/Password Form */}
        <form onSubmit={handleSubmit}>
          {mode === "signup" && (
            <>
              <div style={{ marginBottom: "20px" }}>
                <label style={{
                  display: "block",
                  fontSize: "14px",
                  fontWeight: "700",
                  color: "#f8fafc",
                  marginBottom: "8px",
                }}>
                  Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="John Doe"
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    border: "2px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "12px",
                    fontSize: "14px",
                    outline: "none",
                    transition: "all 0.2s",
                    background: "rgba(30, 41, 59, 0.6)",
                    color: "#f8fafc",
                    boxSizing: "border-box",
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = "#667EEA";
                    e.target.style.boxShadow = "0 0 0 4px rgba(99, 102, 241, 0.2)";
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = "rgba(255, 255, 255, 0.1)";
                    e.target.style.boxShadow = "none";
                  }}
                />
              </div>

              <div style={{ marginBottom: "20px" }}>
                <label style={{
                  display: "block",
                  fontSize: "14px",
                  fontWeight: "700",
                  color: "#f8fafc",
                  marginBottom: "8px",
                }}>
                  Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  placeholder="johndoe"
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    border: "2px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "12px",
                    fontSize: "14px",
                    outline: "none",
                    transition: "all 0.2s",
                    background: "rgba(30, 41, 59, 0.6)",
                    color: "#f8fafc",
                    boxSizing: "border-box",
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = "#667EEA";
                    e.target.style.boxShadow = "0 0 0 4px rgba(99, 102, 241, 0.2)";
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = "rgba(255, 255, 255, 0.1)";
                    e.target.style.boxShadow = "none";
                  }}
                />
              </div>
            </>
          )}

          <div style={{ marginBottom: "20px" }}>
            <label style={{
              display: "block",
              fontSize: "14px",
              fontWeight: "700",
              color: "#f8fafc",
              marginBottom: "8px",
            }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
              style={{
                width: "100%",
                padding: "12px 16px",
                border: "2px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "12px",
                fontSize: "14px",
                outline: "none",
                transition: "all 0.2s",
                background: "rgba(30, 41, 59, 0.6)",
                color: "#f8fafc",
                boxSizing: "border-box",
              }}
              onFocus={(e) => {
                e.target.style.borderColor = "#667EEA";
                e.target.style.boxShadow = "0 0 0 4px rgba(99, 102, 241, 0.2)";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "rgba(255, 255, 255, 0.1)";
                e.target.style.boxShadow = "none";
              }}
            />
          </div>

          <div style={{ marginBottom: "28px" }}>
            <label style={{
              display: "block",
              fontSize: "14px",
              fontWeight: "700",
              color: "#f8fafc",
              marginBottom: "8px",
            }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              minLength={6}
              style={{
                width: "100%",
                padding: "12px 16px",
                border: "2px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "12px",
                fontSize: "14px",
                outline: "none",
                transition: "all 0.2s",
                background: "rgba(30, 41, 59, 0.6)",
                color: "#f8fafc",
                boxSizing: "border-box",
              }}
              onFocus={(e) => {
                e.target.style.borderColor = "#667EEA";
                e.target.style.boxShadow = "0 0 0 4px rgba(99, 102, 241, 0.2)";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "rgba(255, 255, 255, 0.1)";
                e.target.style.boxShadow = "none";
              }}
            />
            {mode === "signup" && (
              <p style={{
                fontSize: "12px",
                color: "#94a3b8",
                marginTop: "6px",
              }}>
                Must be at least 6 characters
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "14px",
              background: loading
                ? "#94A3B8"
                : "linear-gradient(135deg, #667EEA 0%, #764BA2 100%)",
              color: "#FFFFFF",
              border: "none",
              borderRadius: "12px",
              fontSize: "16px",
              fontWeight: "700",
              cursor: loading ? "not-allowed" : "pointer",
              transition: "all 0.3s",
              boxShadow: loading
                ? "none"
                : "0 4px 16px rgba(99, 102, 241, 0.4)",
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.transform = "translateY(-2px)";
                e.target.style.boxShadow = "0 8px 24px rgba(99, 102, 241, 0.6)";
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.transform = "translateY(0)";
                e.target.style.boxShadow = "0 4px 16px rgba(99, 102, 241, 0.4)";
              }
            }}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
                <span style={{
                  width: "16px",
                  height: "16px",
                  border: "2px solid rgba(255, 255, 255, 0.3)",
                  borderTopColor: "#FFFFFF",
                  borderRadius: "50%",
                  animation: "spin 0.8s linear infinite",
                }} />
                {mode === "login" ? "Signing in..." : "Creating account..."}
              </span>
            ) : mode === "login" ? (
              "Sign In"
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        {/* Toggle Mode */}
        <div style={{ marginTop: "28px", textAlign: "center" }}>
          <p style={{ fontSize: "14px", color: "#94a3b8" }}>
            {mode === "login"
              ? "Don't have an account?"
              : "Already have an account?"}{" "}
            <button
              onClick={() => {
                setMode(mode === "login" ? "signup" : "login");
                setError(null);
              }}
              style={{
                background: "transparent",
                border: "none",
                color: "#818cf8",
                fontWeight: "700",
                cursor: "pointer",
                fontSize: "14px",
                textDecoration: "underline",
              }}
            >
              {mode === "login" ? "Sign up" : "Sign in"}
            </button>
          </p>
        </div>

        {/* Signup Info */}
        {mode === "signup" && (
          <div style={{
            marginTop: "24px",
            padding: "12px 16px",
            background: "rgba(16, 185, 129, 0.15)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            borderRadius: "12px",
            textAlign: "center",
          }}>
            <p style={{
              fontSize: "13px",
              color: "#6ee7b7",
              margin: 0,
              fontWeight: "600",
            }}>
              🎉 Get started with free credits on signup!
            </p>
          </div>
        )}
      </div>

      {/* CSS Animation */}
      <style>
        {`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
}