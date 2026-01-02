// frontend/poc-project/src/pages/AuthPage.jsx
// COMPLETE FILE WITH EMAIL VERIFICATION & PASSWORD RESET + TOAST NOTIFICATIONS

import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { toast } from '../utils/toast';
import { getErrorMessage } from '../utils/errorMessages';
import { Eye, EyeOff } from 'lucide-react';

export default function AuthPage({ onSuccess }) {
  const location = useLocation();
  const { login, signup, loginWithGoogle, error: authError } = useAuth();

  const initialMode = location.state?.mode || "login";

  // Main flow state
  const [mode, setMode] = useState(initialMode); // "login" | "signup" | "verify" | "forgot" | "reset"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Verification & Reset state
  const [verificationCode, setVerificationCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [resetToken, setResetToken] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");

  // Visibility toggles
  const [showPassword, setShowPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // Initialize Google Sign-In SDK
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

  // Google Sign-In Handler
  // ✅ FIX: Update handleGoogleLogin to use AuthContext
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

            // Create the ID token payload
            const idTokenPayload = JSON.stringify({
              email: userInfo.email,
              name: userInfo.name,
              picture: userInfo.picture,
              email_verified: userInfo.email_verified,
              sub: userInfo.sub
            });

            // ✅ FIX: Use AuthContext's loginWithGoogle method
            const result = await loginWithGoogle(idTokenPayload);

            if (result.success) {
              console.log('✅ Google authentication successful:', result.user.email);
              onSuccess?.();
            } else {
              throw new Error(result.error || 'Authentication failed');
            }

          } catch (err) {
            console.error('❌ Google authentication error:', err);
            setError(err.message || "Failed to authenticate with Google");
            toast.error("Google Auth Failed", err.message || "Could not authenticate with your Google account.");
            setLoading(false);
          }
        },
      });

      client.requestAccessToken();

    } catch (err) {
      console.error('❌ Error initializing Google Sign-In:', err);
      setError("Failed to open Google Sign-In. Please try again.");
      toast.error("Google Sign-In Error", "Failed to open Google Sign-In. Please check your browser settings.");
      setLoading(false);
    }
  };

  // Email/Password Signup
  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    // ✅ ADD VALIDATION BEFORE SENDING
    console.log("Signup attempt:", {
      email,
      password: `${password.length} chars`,
      username,
      fullName
    });

    // ✅ CHECK EMAIL FORMAT
    if (!email.includes("@") || !email.includes(".")) {
      setError("Please enter a valid email address");
      toast.error("Invalid Email", "Please enter a valid email address (e.g., user@example.com)");
      setLoading(false);
      return;
    }

    // ✅ CHECK PASSWORD STRENGTH
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      toast.error("Weak Password", "Password must be at least 8 characters long.");
      setLoading(false);
      return;
    }
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasDigit = /[0-9]/.test(password);

    if (!hasUpper || !hasLower || !hasDigit) {
      setError("Password must contain uppercase, lowercase, and a number");
      toast.error("Weak Password", "Inlcude uppercase, lowercase letters and at least one number.");
      setLoading(false);
      return;
    }

    // ✅ CHECK USERNAME
    if (username.length < 3) {
      setError("Username must be at least 3 characters");
      toast.error("Invalid Username", "Username must be at least 3 characters long.");
      setLoading(false);
      return;
    }
    if (!/^[a-zA-Z0-9]+$/.test(username)) {
      setError("Username must be alphanumeric (no special characters)");
      toast.error("Invalid Username", "Username can only contain letters and numbers.");
      setLoading(false);
      return;
    }


    try {
      const result = await fetch(`${API_BASE}/auth/signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
          username,
          full_name: fullName,  // ✅ FIXED - matches backend expectation
        }),
      });

      const data = await result.json();  // ✅ FIXED - correct variable name

      if (!result.ok) {  // ✅ FIXED - use result instead of response
        const errorMsg = getErrorMessage({
          error_code: data.error_code,
          status: result.status,
          error: data.detail || data.error
        });

        setError(errorMsg.description);
        toast.error(errorMsg.title, errorMsg.description);
        setLoading(false);
        return;
      }

      // ✅ Move to verification screen
      setMode("verify");
      setSuccessMessage("Verification code sent to your email!");
      toast.success('Account created!', 'Check your email to verify. Then login to start building!');

    } catch (err) {
      const errorMsg = getErrorMessage({
        error: err.message,
        status: err.status
      });

      setError(errorMsg.description);
      toast.error(errorMsg.title, errorMsg.description);
    } finally {
      setLoading(false);
    }
  };

  // Email Verification
  const handleVerifyEmail = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/auth/verify-email/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.toLowerCase(),
          code: verificationCode
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Verification failed');
      }

      setSuccessMessage("Email verified successfully! Redirecting...");
      toast.success('Email verified!', 'You can now log in to your account');

      // Auto-login after verification
      setTimeout(() => {
        onSuccess?.();
      }, 1500);

    } catch (err) {
      const errorMsg = getErrorMessage({
        error: err.message,
        status: err.status
      });

      setError(errorMsg.description);
      toast.error(errorMsg.title, errorMsg.description);
    } finally {
      setLoading(false);
    }
  };

  // Resend Verification Code
  const handleResendVerification = async () => {
    setLoading(true);
    setError(null);

    try {
      // ⚠️ ISSUE: Your backend's /verify-email/send requires AUTH token
      // But user isn't logged in during signup verification
      // SOLUTION: Create a public resend endpoint OR use the send endpoint differently

      // For now, let's use a workaround - re-trigger signup email send
      // You'll need to add a PUBLIC resend endpoint to your backend

      const response = await fetch(`${API_BASE}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.toLowerCase() })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to resend code');
      }

      setSuccessMessage("New verification code sent!");
      toast.success("Code Sent", "A new verification code has been sent to your email.");
      setTimeout(() => setSuccessMessage(""), 3000);

    } catch (err) {
      setError(err.message || "Failed to resend code.");
    } finally {
      setLoading(false);
    }
  };

  // Login
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await login(email, password);

      if (result.success) {
        toast.success('Welcome back!', "You're all set! Let's start building your dream App.");
        onSuccess?.();
      } else {
        // Get user-friendly error message
        const errorMsg = getErrorMessage({
          error_code: result.error_code,
          status: result.status,
          error: result.error
        });

        setError(errorMsg.description);
        toast.error(errorMsg.title, errorMsg.description);
      }
    } catch (err) {
      const errorMsg = getErrorMessage(err);
      setError(errorMsg.description);
      toast.error(errorMsg.title, errorMsg.description);
    } finally {
      setLoading(false);
    }
  };

  // Request Password Reset
  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/auth/password-reset/send-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.toLowerCase() })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Request failed');
      }

      setMode("reset");
      setSuccessMessage("Password reset code sent to your email!");
      toast.success("Reset Code Sent", "Verification code sent to your email.");

    } catch (err) {
      setError(err.message || "Failed to send reset code.");
    } finally {
      setLoading(false);
    }
  };

  // Verify Reset Code & Reset Password
  // Verify Reset Code & Reset Password
  const handleResetPassword = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      setError("Passwords don't match");
      return;
    }

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // ✅ FIXED: Send all 3 fields in ONE request
      const response = await fetch(`${API_BASE}/auth/password-reset/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.toLowerCase(),
          code: verificationCode,
          new_password: newPassword  // ✅ ADD THIS!
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Password reset failed');
      }

      setSuccessMessage("Password reset successful! Redirecting to login...");
      toast.success("Password Reset", "Your password has been successfully updated.");

      setTimeout(() => {
        setMode("login");
        setPassword("");
        setNewPassword("");
        setConfirmPassword("");
        setVerificationCode("");
        setSuccessMessage("");
      }, 2000);

    } catch (err) {
      setError(err.message || "Password reset failed.");
    } finally {
      setLoading(false);
    }
  };

  const displayError = error || authError;

  // Render different UI based on mode
  const renderContent = () => {
    // EMAIL VERIFICATION MODE
    if (mode === "verify") {
      return (
        <>
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
              📧
            </div>
            <h2 style={{
              fontSize: "32px",
              fontWeight: "900",
              marginBottom: "12px",
              color: "#f8fafc",
              letterSpacing: "-0.02em",
            }}>
              Verify your email
            </h2>
            <p style={{ fontSize: "16px", color: "#94a3b8" }}>
              We sent a 6-digit code to <strong>{email}</strong>
            </p>
          </div>

          {successMessage && (
            <div style={{
              padding: "14px 18px",
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              borderRadius: "12px",
              color: "#6ee7b7",
              fontSize: "14px",
              marginBottom: "24px",
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}>
              <span style={{ fontSize: "20px" }}>✅</span>
              <span>{successMessage}</span>
            </div>
          )}

          <form onSubmit={handleVerifyEmail}>
            <div style={{ marginBottom: "28px" }}>
              <label style={{
                display: "block",
                fontSize: "14px",
                fontWeight: "700",
                color: "#f8fafc",
                marginBottom: "8px",
              }}>
                Verification Code
              </label>
              <input
                type="text"
                value={verificationCode}
                onChange={(e) => {
                  const cleaned = e.target.value.replace(/\D/g, '');
                  setVerificationCode(cleaned)
                }}
                required
                placeholder="Enter 6-digit code"
                maxLength={6}
                style={{
                  width: "100%",
                  padding: "16px",
                  border: "2px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "12px",
                  fontSize: "24px",
                  letterSpacing: "8px",
                  textAlign: "center",
                  outline: "none",
                  transition: "all 0.2s",
                  background: "rgba(30, 41, 59, 0.6)",
                  color: "#f8fafc",
                  boxSizing: "border-box",
                  fontWeight: "700",
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

            <button
              type="submit"
              disabled={loading || verificationCode.length !== 6}
              style={{
                width: "100%",
                padding: "14px",
                background: loading || verificationCode.length !== 6
                  ? "#94A3B8"
                  : "linear-gradient(135deg, #667EEA 0%, #764BA2 100%)",
                color: "#FFFFFF",
                border: "none",
                borderRadius: "12px",
                fontSize: "16px",
                fontWeight: "700",
                cursor: loading || verificationCode.length !== 6 ? "not-allowed" : "pointer",
                transition: "all 0.3s",
                boxShadow: loading || verificationCode.length !== 6
                  ? "none"
                  : "0 4px 16px rgba(99, 102, 241, 0.4)",
              }}
            >
              {loading ? "Verifying..." : "Verify Email"}
            </button>
          </form>

          <div style={{ marginTop: "24px", textAlign: "center" }}>
            <p style={{ fontSize: "14px", color: "#94a3b8" }}>
              Didn't receive the code?{" "}
              <button
                onClick={handleResendVerification}
                disabled={loading}
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
                Resend Code
              </button>
            </p>
          </div>
        </>
      );
    }

    // FORGOT PASSWORD MODE
    if (mode === "forgot") {
      return (
        <>
          <div style={{ textAlign: "center", marginBottom: "32px" }}>
            <div style={{
              width: "80px",
              height: "80px",
              background: "linear-gradient(135deg, #F59E0B 0%, #F97316 100%)",
              borderRadius: "16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "40px",
              margin: "0 auto 20px",
              boxShadow: "0 8px 32px rgba(245, 158, 11, 0.4)",
            }}>
              🔑
            </div>
            <h2 style={{
              fontSize: "32px",
              fontWeight: "900",
              marginBottom: "12px",
              color: "#f8fafc",
              letterSpacing: "-0.02em",
            }}>
              Reset password
            </h2>
            <p style={{ fontSize: "16px", color: "#94a3b8" }}>
              Enter your email to receive a reset code
            </p>
          </div>

          <form onSubmit={handleForgotPassword}>
            <div style={{ marginBottom: "28px" }}>
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
            >
              {loading ? "Sending code..." : "Send Reset Code"}
            </button>
          </form>

          <div style={{ marginTop: "28px", textAlign: "center" }}>
            <p style={{ fontSize: "14px", color: "#94a3b8" }}>
              Remember your password?{" "}
              <button
                onClick={() => {
                  setMode("login");
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
                Sign in
              </button>
            </p>
          </div>
        </>
      );
    }

    // PASSWORD RESET MODE (after receiving code)
    if (mode === "reset") {
      return (
        <>
          <div style={{ textAlign: "center", marginBottom: "32px" }}>
            <div style={{
              width: "80px",
              height: "80px",
              background: "linear-gradient(135deg, #10B981 0%, #059669 100%)",
              borderRadius: "16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "40px",
              margin: "0 auto 20px",
              boxShadow: "0 8px 32px rgba(16, 185, 129, 0.4)",
            }}>
              🔐
            </div>
            <h2 style={{
              fontSize: "32px",
              fontWeight: "900",
              marginBottom: "12px",
              color: "#f8fafc",
              letterSpacing: "-0.02em",
            }}>
              Set new password
            </h2>
            <p style={{ fontSize: "16px", color: "#94a3b8" }}>
              Enter the code sent to <strong>{email}</strong>
            </p>
          </div>

          {successMessage && (
            <div style={{
              padding: "14px 18px",
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              borderRadius: "12px",
              color: "#6ee7b7",
              fontSize: "14px",
              marginBottom: "24px",
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}>
              <span style={{ fontSize: "20px" }}>✅</span>
              <span>{successMessage}</span>
            </div>
          )}

          <form onSubmit={handleResetPassword}>
            <div style={{ marginBottom: "20px" }}>
              <label style={{
                display: "block",
                fontSize: "14px",
                fontWeight: "700",
                color: "#f8fafc",
                marginBottom: "8px",
              }}>
                Reset Code
              </label>
              <input
                type="text"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                required
                placeholder="Enter 6-digit code"
                maxLength={6}
                style={{
                  width: "100%",
                  padding: "12px 16px",
                  border: "2px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "12px",
                  fontSize: "18px",
                  letterSpacing: "4px",
                  textAlign: "center",
                  outline: "none",
                  transition: "all 0.2s",
                  background: "rgba(30, 41, 59, 0.6)",
                  color: "#f8fafc",
                  boxSizing: "border-box",
                  fontWeight: "700",
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
                New Password
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showNewPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  minLength={6}
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    paddingRight: "45px",
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
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  style={{
                    position: 'absolute',
                    right: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: '#94a3b8',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '8px',
                    zIndex: 2
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = '#f8fafc')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
                >
                  {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div style={{ marginBottom: "28px" }}>
              <label style={{
                display: "block",
                fontSize: "14px",
                fontWeight: "700",
                color: "#f8fafc",
                marginBottom: "8px",
              }}>
                Confirm Password
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  minLength={6}
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    paddingRight: "45px",
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
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  style={{
                    position: 'absolute',
                    right: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: '#94a3b8',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '8px',
                    zIndex: 2
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = '#f8fafc')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
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
            >
              {loading ? "Resetting password..." : "Reset Password"}
            </button>
          </form>
        </>
      );
    }

    // DEFAULT: LOGIN / SIGNUP MODE
    return (
      <>
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
        >
          <svg width="18" height="18" viewBox="0 0 18 18">
            <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" />
            <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z" />
            <path fill="#FBBC05" d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707 0-.593.102-1.17.282-1.709V4.958H.957C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.335z" />
            <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" />
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
        <form onSubmit={mode === "login" ? handleLogin : handleSignup}>
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

          <div style={{ marginBottom: mode === "login" ? "12px" : "28px" }}>
            <label style={{
              display: "block",
              fontSize: "14px",
              fontWeight: "700",
              color: "#f8fafc",
              marginBottom: "8px",
            }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                minLength={6}
                style={{
                  width: "100%",
                  padding: "12px 16px",
                  paddingRight: "45px",
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
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#94a3b8',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '8px',
                  zIndex: 2
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#f8fafc')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
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

          {/* Forgot Password Link (Login mode only) */}
          {mode === "login" && (
            <div style={{ marginBottom: "28px", textAlign: "right" }}>
              <button
                type="button"
                onClick={() => {
                  setMode("forgot");
                  setError(null);
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#818cf8",
                  fontWeight: "600",
                  cursor: "pointer",
                  fontSize: "13px",
                  textDecoration: "underline",
                }}
              >
                Forgot password?
              </button>
            </div>
          )}

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
                setSuccessMessage("");
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
      </>
    );
  };

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

        {renderContent()}
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