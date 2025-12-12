// frontend/src/components/AuthPage.jsx
// Auth Page with Email Verification, Password Reset & Google OAuth (Vite env-ready)

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './AuthPage.css';

// ✅ Use environment variable for Google Client ID (Vite)
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

// ✅ Use environment variable for API base URL (backend FastAPI)
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function AuthPage({ onSuccess }) {
  const { signup, login, loginWithGoogle, error: authError, loading } = useAuth();

  // Optional debug on mount (safe to keep or remove)
  useEffect(() => {
    console.log('🔐 Google Client ID:', GOOGLE_CLIENT_ID || '(missing)');
    console.log('🔗 API Base URL:', API_BASE);
  }, []);

  // Auth flow state: 'login' | 'signup' | 'verify-email' | 'forgot-password' | 'reset-password'
  const [authFlow, setAuthFlow] = useState('login');
  const [pendingEmail, setPendingEmail] = useState('');

  // Form data
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: '',
    fullName: '',
    verificationCode: '',
    resetCode: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [errors, setErrors] = useState({});
  const [localError, setLocalError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [googleLoaded, setGoogleLoaded] = useState(false);

  // Timer for resend code
  const [resendTimer, setResendTimer] = useState(0);

  // Resend timer countdown
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer((prev) => prev - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }

    setLocalError('');
    setSuccessMessage('');
  };

  const validateForm = () => {
    const newErrors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    // Email validation (not needed only on reset-password step)
    if (authFlow !== 'reset-password' && !formData.email) {
      newErrors.email = 'Email is required';
    } else if (authFlow !== 'reset-password' && !emailRegex.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    // Password validation for login/signup
    if (authFlow === 'login' || authFlow === 'signup') {
      if (!formData.password) {
        newErrors.password = 'Password is required';
      } else if (formData.password.length < 8) {
        newErrors.password = 'Password must be at least 8 characters';
      } else if (authFlow === 'signup') {
        if (!/[A-Z]/.test(formData.password)) {
          newErrors.password = 'Password must contain uppercase letter';
        } else if (!/[a-z]/.test(formData.password)) {
          newErrors.password = 'Password must contain lowercase letter';
        } else if (!/[0-9]/.test(formData.password)) {
          newErrors.password = 'Password must contain a number';
        }
      }
    }

    // Username validation (signup only)
    if (authFlow === 'signup') {
      if (!formData.username) {
        newErrors.username = 'Username is required';
      } else if (formData.username.length < 3) {
        newErrors.username = 'Username must be at least 3 characters';
      } else if (!/^[a-zA-Z0-9]+$/.test(formData.username)) {
        newErrors.username = 'Username must be alphanumeric';
      }
    }

    // Verification code validation
    if (
      authFlow === 'verify-email' &&
      (!formData.verificationCode || formData.verificationCode.length !== 6)
    ) {
      newErrors.verificationCode = 'Enter 6-digit code';
    }

    // Reset code validation
    if (
      authFlow === 'reset-password' &&
      (!formData.resetCode || formData.resetCode.length !== 6)
    ) {
      newErrors.resetCode = 'Enter 6-digit code';
    }

    // New password validation (reset flow)
    if (authFlow === 'reset-password') {
      if (!formData.newPassword) {
        newErrors.newPassword = 'New password is required';
      } else if (formData.newPassword.length < 8) {
        newErrors.newPassword = 'Password must be at least 8 characters';
      } else if (!/[A-Z]/.test(formData.newPassword)) {
        newErrors.newPassword = 'Password must contain uppercase letter';
      } else if (!/[a-z]/.test(formData.newPassword)) {
        newErrors.newPassword = 'Password must contain lowercase letter';
      } else if (!/[0-9]/.test(formData.newPassword)) {
        newErrors.newPassword = 'Password must contain a number';
      }

      if (!formData.confirmPassword) {
        newErrors.confirmPassword = 'Confirm your password';
      } else if (formData.newPassword !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle Login
  const handleLogin = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLocalError('');
    setIsProcessing(true);

    try {
      const result = await login(formData.email, formData.password);

      if (result.success) {
        if (onSuccess) onSuccess();
      } else {
        setLocalError(result.error || 'Login failed');
      }
    } catch (err) {
      setLocalError(err.message || 'Login failed');
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle Signup
  const handleSignup = async (e) => {
    e.preventDefault();

  // Validate the form data before proceeding
    if (!validateForm()) return;

    setLocalError(''); // Reset previous errors
    setIsProcessing(true); // Set processing state

    try {

    // Check free tier availability
      const freeTierRes = await fetch(`${API_BASE}/payment/free-tier/status`);

      if (freeTierRes.ok) {
        const freeTierData = await freeTierRes.json();

      // If the free tier is full, show an error and exit the function
        if (!freeTierData.can_add_new_user) {
          setLocalError(
            `Free tier is full (${freeTierData.current_free_tier_users}/20 users). ` +
            `Please check our paid plans for instant access.`
          );
        // Optionally, you can show a modal or take other actions here
          return; // Stop the function here
        }
      } else {
        setLocalError('Failed to fetch free tier status. Please try again.');
        return;
      }

    // Proceed with signup after free tier check
      const result = await signup(
        formData.email,
        formData.password,
        formData.username,
        formData.fullName
      );

      if (result.success) {
      // Store email for verification
        setPendingEmail(formData.email);
      // Switch to verification flow
        setAuthFlow('verify-email');
        setSuccessMessage('Account created! Check your email for verification code.');
        setResendTimer(60); // 60 seconds cooldown
      } else {
        setLocalError(result.error || 'Signup failed');
      }
    } catch (err) {
      setLocalError(err.message || 'Signup failed');
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle Email Verification
  const handleVerifyEmail = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLocalError('');
    setIsProcessing(true);

    try {
      const response = await fetch(`${API_BASE}/auth/verify-email/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: pendingEmail,
          code: formData.verificationCode,
          type: 'signup',
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccessMessage('✅ Email verified! Logging you in...');

        // Auto-login after verification
        setTimeout(async () => {
          const loginResult = await login(pendingEmail, formData.password);
          if (loginResult.success && onSuccess) {
            onSuccess();
          }
        }, 1500);
      } else {
        setLocalError(data.detail || 'Verification failed');
      }
    } catch (err) {
      setLocalError('Verification failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Resend Verification Code
  const handleResendCode = async () => {
    if (resendTimer > 0) return;

    setLocalError('');
    setIsProcessing(true);

    try {
      const response = await fetch(`${API_BASE}/auth/verify-email/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: pendingEmail }),
      });

      if (response.ok) {
        setSuccessMessage('New code sent to your email!');
        setResendTimer(60);
      } else {
        setLocalError('Failed to resend code');
      }
    } catch (err) {
      setLocalError('Failed to resend code');
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle Forgot Password - Send Reset Code
  const handleSendResetCode = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLocalError('');
    setIsProcessing(true);

    try {
      const response = await fetch(`${API_BASE}/auth/password-reset/send-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email }),
      });

      if (response.ok) {
        setPendingEmail(formData.email);
        setAuthFlow('reset-password');
        setSuccessMessage('Reset code sent to your email!');
        setResendTimer(60);
      } else {
        setLocalError('Failed to send reset code');
      }
    } catch (err) {
      setLocalError('Failed to send reset code');
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle Password Reset
  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLocalError('');
    setIsProcessing(true);

    try {
      const response = await fetch(`${API_BASE}/auth/password-reset/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: pendingEmail,
          code: formData.resetCode,
          new_password: formData.newPassword,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccessMessage('✅ Password reset successful! You can now login.');

        // Reset form and go back to login
        setTimeout(() => {
          setAuthFlow('login');
          setFormData({
            email: pendingEmail,
            password: '',
            username: '',
            fullName: '',
            verificationCode: '',
            resetCode: '',
            newPassword: '',
            confirmPassword: '',
          });
          setSuccessMessage('');
        }, 2000);
      } else {
        setLocalError(data.detail || 'Password reset failed');
      }
    } catch (err) {
      setLocalError('Password reset failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Google OAuth Handler
  const handleGoogleResponse = useCallback(
    async (response) => {
      try {
        console.log('🔐 Google OAuth Response Received');

        const result = await loginWithGoogle(response.credential);

        if (result.success && onSuccess) {
          onSuccess();
        } else {
          setLocalError(result.error || 'Google authentication failed');
        }
      } catch (err) {
        console.error('❌ Google OAuth Error:', err);
        setLocalError(err.message || 'Google authentication failed');
      }
    },
    [loginWithGoogle, onSuccess]
  );

  // Load Google Sign-In Script
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      console.error('❌ VITE_GOOGLE_CLIENT_ID not set in .env');
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => {
      console.log('✅ Google Sign-In script loaded');
      setGoogleLoaded(true);
    };
    script.onerror = () => {
      console.error('❌ Failed to load Google Sign-In script');
    };

    document.body.appendChild(script);

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, []);

  // Initialize Google Sign-In Button
  useEffect(() => {
    if (!googleLoaded || !window.google?.accounts?.id) return;
    if (authFlow !== 'login' && authFlow !== 'signup') return;

    if (!GOOGLE_CLIENT_ID) {
      console.error('❌ Google Client ID missing');
      return;
    }

    try {
      console.log('🔧 Initializing Google Sign-In...');
      console.log('📍 Current Origin:', window.location.origin);

      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleResponse,
        auto_select: false,
        cancel_on_tap_outside: true,
      });

      const buttonDiv = document.getElementById('googleSignInDiv');
      if (buttonDiv) {
        // Clear previous button instance (important when switching login/signup)
        buttonDiv.innerHTML = '';

        window.google.accounts.id.renderButton(buttonDiv, {
          theme: 'outline',
          size: 'large',
          shape: 'pill',
          width: 320,
          text: authFlow === 'login' ? 'signin_with' : 'signup_with',
          logo_alignment: 'left',
        });

        console.log('✅ Google Sign-In button rendered');
      } else {
        console.error('❌ Google Sign-In button container not found');
      }
    } catch (error) {
      console.error('❌ Google Sign-In initialization error:', error);
    }
  }, [googleLoaded, authFlow, handleGoogleResponse]);

  const displayError = localError || authError;

  // JSX per auth flow
  const renderForm = () => {
    switch (authFlow) {
      case 'login':
        return (
          <>
            <div className="auth-header">
              <h2 className="auth-title">Welcome Back</h2>
              <p className="auth-subtitle">Sign in to continue building amazing UIs</p>
            </div>

            <div className="google-signin-section">
              <div id="googleSignInDiv" className="google-btn-container" />
              <div className="auth-divider">
                <span>or continue with email</span>
              </div>
            </div>

            <form onSubmit={handleLogin} className="auth-form">
              <div className="form-group">
                <label htmlFor="email" className="form-label">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={`form-input ${errors.email ? 'error' : ''}`}
                  placeholder="you@example.com"
                  autoComplete="email"
                />
                {errors.email && <span className="form-error">{errors.email}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="password" className="form-label">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className={`form-input ${errors.password ? 'error' : ''}`}
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
                {errors.password && <span className="form-error">{errors.password}</span>}
              </div>

              <button
                type="button"
                onClick={() => setAuthFlow('forgot-password')}
                className="forgot-password-link"
              >
                Forgot password?
              </button>

              {displayError && (
                <div className="alert-error">
                  <span className="alert-icon">⚠️</span>
                  {displayError}
                </div>
              )}

              <button type="submit" className="btn-submit" disabled={isProcessing || loading}>
                {isProcessing || loading ? (
                  <>
                    <span className="spinner-small" />
                    Signing In...
                  </>
                ) : (
                  'Sign In'
                )}
              </button>

              <div className="auth-toggle">
                <span className="toggle-text">Don't have an account?</span>
                <button
                  type="button"
                  onClick={() => setAuthFlow('signup')}
                  className="toggle-button"
                >
                  Sign Up
                </button>
              </div>
            </form>
          </>
        );

      case 'signup':
        return (
          <>
            <div className="auth-header">
              <h2 className="auth-title">Create Account</h2>
              <p className="auth-subtitle">Start building amazing UIs today</p>
            </div>

            <div className="google-signin-section">
              <div id="googleSignInDiv" className="google-btn-container" />
              <div className="auth-divider">
                <span>or continue with email</span>
              </div>
            </div>

            <form onSubmit={handleSignup} className="auth-form">
              <div className="form-group">
                <label htmlFor="email" className="form-label">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={`form-input ${errors.email ? 'error' : ''}`}
                  placeholder="you@example.com"
                  autoComplete="email"
                />
                {errors.email && <span className="form-error">{errors.email}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="username" className="form-label">
                  Username
                </label>
                <input
                  id="username"
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  className={`form-input ${errors.username ? 'error' : ''}`}
                  placeholder="johndoe"
                  autoComplete="username"
                />
                {errors.username && <span className="form-error">{errors.username}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="fullName" className="form-label">
                  Full Name <span className="optional">(optional)</span>
                </label>
                <input
                  id="fullName"
                  type="text"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="John Doe"
                  autoComplete="name"
                />
              </div>

              <div className="form-group">
                <label htmlFor="password" className="form-label">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className={`form-input ${errors.password ? 'error' : ''}`}
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
                {errors.password && <span className="form-error">{errors.password}</span>}
                {!errors.password && (
                  <span className="form-hint">
                    Min 8 characters with uppercase, lowercase &amp; number
                  </span>
                )}
              </div>

              {displayError && (
                <div className="alert-error">
                  <span className="alert-icon">⚠️</span>
                  {displayError}
                </div>
              )}

              <button type="submit" className="btn-submit" disabled={isProcessing || loading}>
                {isProcessing || loading ? (
                  <>
                    <span className="spinner-small" />
                    Creating Account...
                  </>
                ) : (
                  'Create Account'
                )}
              </button>

              <div className="auth-toggle">
                <span className="toggle-text">Already have an account?</span>
                <button
                  type="button"
                  onClick={() => setAuthFlow('login')}
                  className="toggle-button"
                >
                  Sign In
                </button>
              </div>
            </form>
          </>
        );

      case 'verify-email':
        return (
          <>
            <div className="auth-header">
              <h2 className="auth-title">📧 Verify Your Email</h2>
              <p className="auth-subtitle">
                We sent a 6-digit code to <strong>{pendingEmail}</strong>
              </p>
            </div>

            <form onSubmit={handleVerifyEmail} className="auth-form">
              <div className="form-group">
                <label htmlFor="verificationCode" className="form-label">
                  Verification Code
                </label>
                <input
                  id="verificationCode"
                  type="text"
                  name="verificationCode"
                  value={formData.verificationCode}
                  onChange={handleChange}
                  className={`form-input code-input ${
                    errors.verificationCode ? 'error' : ''
                  }`}
                  placeholder="000000"
                  maxLength={6}
                  autoComplete="off"
                  style={{
                    textAlign: 'center',
                    fontSize: '24px',
                    letterSpacing: '8px',
                  }}
                />
                {errors.verificationCode && (
                  <span className="form-error">{errors.verificationCode}</span>
                )}
              </div>

              {successMessage && (
                <div className="alert-success">
                  <span className="alert-icon">✅</span>
                  {successMessage}
                </div>
              )}

              {displayError && (
                <div className="alert-error">
                  <span className="alert-icon">⚠️</span>
                  {displayError}
                </div>
              )}

              <button type="submit" className="btn-submit" disabled={isProcessing}>
                {isProcessing ? (
                  <>
                    <span className="spinner-small" />
                    Verifying...
                  </>
                ) : (
                  'Verify Email'
                )}
              </button>

              <div className="auth-toggle">
                <span className="toggle-text">Didn't receive the code?</span>
                <button
                  type="button"
                  onClick={handleResendCode}
                  className="toggle-button"
                  disabled={resendTimer > 0}
                >
                  {resendTimer > 0 ? `Resend in ${resendTimer}s` : 'Resend Code'}
                </button>
              </div>
            </form>
          </>
        );

      case 'forgot-password':
        return (
          <>
            <div className="auth-header">
              <h2 className="auth-title">🔐 Forgot Password?</h2>
              <p className="auth-subtitle">Enter your email to receive a reset code</p>
            </div>

            <form onSubmit={handleSendResetCode} className="auth-form">
              <div className="form-group">
                <label htmlFor="email" className="form-label">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={`form-input ${errors.email ? 'error' : ''}`}
                  placeholder="you@example.com"
                  autoComplete="email"
                />
                {errors.email && <span className="form-error">{errors.email}</span>}
              </div>

              {successMessage && (
                <div className="alert-success">
                  <span className="alert-icon">✅</span>
                  {successMessage}
                </div>
              )}

              {displayError && (
                <div className="alert-error">
                  <span className="alert-icon">⚠️</span>
                  {displayError}
                </div>
              )}

              <button type="submit" className="btn-submit" disabled={isProcessing}>
                {isProcessing ? (
                  <>
                    <span className="spinner-small" />
                    Sending Code...
                  </>
                ) : (
                  'Send Reset Code'
                )}
              </button>

              <div className="auth-toggle">
                <span className="toggle-text">Remember your password?</span>
                <button
                  type="button"
                  onClick={() => setAuthFlow('login')}
                  className="toggle-button"
                >
                  Back to Login
                </button>
              </div>
            </form>
          </>
        );

      case 'reset-password':
        return (
          <>
            <div className="auth-header">
              <h2 className="auth-title">🔒 Reset Password</h2>
              <p className="auth-subtitle">
                Enter the code sent to <strong>{pendingEmail}</strong>
              </p>
            </div>

            <form onSubmit={handleResetPassword} className="auth-form">
              <div className="form-group">
                <label htmlFor="resetCode" className="form-label">
                  Reset Code
                </label>
                <input
                  id="resetCode"
                  type="text"
                  name="resetCode"
                  value={formData.resetCode}
                  onChange={handleChange}
                  className={`form-input code-input ${errors.resetCode ? 'error' : ''}`}
                  placeholder="000000"
                  maxLength={6}
                  autoComplete="off"
                  style={{
                    textAlign: 'center',
                    fontSize: '24px',
                    letterSpacing: '8px',
                  }}
                />
                {errors.resetCode && <span className="form-error">{errors.resetCode}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="newPassword" className="form-label">
                  New Password
                </label>
                <input
                  id="newPassword"
                  type="password"
                  name="newPassword"
                  value={formData.newPassword}
                  onChange={handleChange}
                  className={`form-input ${errors.newPassword ? 'error' : ''}`}
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
                {errors.newPassword && <span className="form-error">{errors.newPassword}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword" className="form-label">
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={`form-input ${errors.confirmPassword ? 'error' : ''}`}
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
                {errors.confirmPassword && (
                  <span className="form-error">{errors.confirmPassword}</span>
                )}
              </div>

              {successMessage && (
                <div className="alert-success">
                  <span className="alert-icon">✅</span>
                  {successMessage}
                </div>
              )}

              {displayError && (
                <div className="alert-error">
                  <span className="alert-icon">⚠️</span>
                  {displayError}
                </div>
              )}

              <button type="submit" className="btn-submit" disabled={isProcessing}>
                {isProcessing ? (
                  <>
                    <span className="spinner-small" />
                    Resetting Password...
                  </>
                ) : (
                  'Reset Password'
                )}
              </button>

              <div className="auth-toggle">
                <span className="toggle-text">Didn't receive the code?</span>
                <button
                  type="button"
                  onClick={() => setAuthFlow('forgot-password')}
                  className="toggle-button"
                >
                  Try Again
                </button>
              </div>
            </form>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        {/* Left Panel - Branding */}
        <div className="auth-left">
          <div className="auth-brand">
            <div className="brand-icon">📱</div>
            <h1 className="brand-title">App Builder</h1>
            <p className="brand-tagline">
              Transform ideas into beautiful mobile UIs with AI
            </p>
          </div>

          <div className="auth-features">
            <div className="feature-item">
              <span className="feature-icon">✨</span>
              <div>
                <h3>AI-Powered</h3>
                <p>Generate UIs from text descriptions</p>
              </div>
            </div>

            <div className="feature-item">
              <span className="feature-icon">⚡</span>
              <div>
                <h3>Lightning Fast</h3>
                <p>Get results in seconds, not hours</p>
              </div>
            </div>

            <div className="feature-item">
              <span className="feature-icon">🎨</span>
              <div>
                <h3>Production Ready</h3>
                <p>React Native code you can use immediately</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Auth Form */}
        <div className="auth-right">
          <div className="auth-form-container">
            {renderForm()}

            {/* Footer Note */}
            <div className="auth-footer">
              <p className="footer-text">
                By continuing, you agree to our{' '}
                <a href="#" className="footer-link">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="#" className="footer-link">
                  Privacy Policy
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
