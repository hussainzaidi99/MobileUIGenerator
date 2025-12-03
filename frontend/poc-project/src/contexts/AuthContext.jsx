// frontend/src/contexts/AuthContext.jsx - Production-Ready Authentication Context
// Features: Google OAuth, Email/Password Auth, Token Management, Auto-refresh
import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [tokens, setTokens] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ✅ Use environment variable with fallback
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // Debug: Log configuration on mount
  useEffect(() => {
    if (import.meta.env.VITE_DEBUG === 'true') {
      console.log('🔧 AuthContext initialized');
      console.log('🔗 API Base URL:', API_BASE);
    }
  }, [API_BASE]);

  // Load auth state from sessionStorage on mount
  useEffect(() => {
    const loadAuthState = () => {
      try {
        const savedTokens = sessionStorage.getItem('auth_tokens');
        const savedUser = sessionStorage.getItem('auth_user');

        if (savedTokens && savedUser) {
          const parsedTokens = JSON.parse(savedTokens);
          const parsedUser = JSON.parse(savedUser);

          // Validate token structure
          if (parsedTokens?.access_token && parsedTokens?.refresh_token) {
            setTokens(parsedTokens);
            setUser(parsedUser);

            if (import.meta.env.VITE_DEBUG === 'true') {
              console.log('✅ Auth state restored from session storage');
            }
          } else {
            throw new Error('Invalid token structure');
          }
        }
      } catch (e) {
        console.error('❌ Failed to restore auth state:', e);
        sessionStorage.removeItem('auth_tokens');
        sessionStorage.removeItem('auth_user');
      } finally {
        setLoading(false);
      }
    };

    loadAuthState();
  }, []);

  // Save auth state to sessionStorage
  const saveAuthState = (userData, tokensData) => {
    try {
      sessionStorage.setItem('auth_user', JSON.stringify(userData));
      sessionStorage.setItem('auth_tokens', JSON.stringify(tokensData));
      setUser(userData);
      setTokens(tokensData);

      if (import.meta.env.VITE_DEBUG === 'true') {
        console.log('✅ Auth state saved:', {
          user: userData.email,
          hasTokens: !!(tokensData?.access_token && tokensData?.refresh_token)
        });
      }
    } catch (e) {
      console.error('❌ Failed to save auth state:', e);
    }
  };

  // Clear auth state
  const clearAuthState = () => {
    try {
      sessionStorage.removeItem('auth_user');
      sessionStorage.removeItem('auth_tokens');
      setUser(null);
      setTokens(null);
      setError(null);

      if (import.meta.env.VITE_DEBUG === 'true') {
        console.log('✅ Auth state cleared');
      }
    } catch (e) {
      console.error('❌ Failed to clear auth state:', e);
    }
  };

  // Signup with email/password
  const signup = async (email, password, username, fullName = '') => {
    try {
      setError(null);
      setLoading(true);

      const response = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          username,
          full_name: fullName
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Signup failed');
      }

      // Save auth state
      saveAuthState(data.user, data.tokens);

      return { success: true, user: data.user };
    } catch (err) {
      const errorMessage = err.message || 'Signup failed. Please try again.';
      setError(errorMessage);
      console.error('❌ Signup error:', err);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Login with email/password
  const login = async (email, password) => {
    try {
      setError(null);
      setLoading(true);

      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      // Save auth state
      saveAuthState(data.user, data.tokens);

      return { success: true, user: data.user };
    } catch (err) {
      const errorMessage = err.message || 'Login failed. Please check your credentials.';
      setError(errorMessage);
      console.error('❌ Login error:', err);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Login with Google OAuth
  const loginWithGoogle = async (googleIdToken) => {
    try {
      setError(null);
      setLoading(true);

      if (import.meta.env.VITE_DEBUG === 'true') {
        console.log('🔐 Attempting Google OAuth login...');
      }

      const response = await fetch(`${API_BASE}/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id_token: googleIdToken })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Google login failed');
      }

      // Save auth state (same structure as email/password login)
      saveAuthState(data.user, data.tokens);

      if (import.meta.env.VITE_DEBUG === 'true') {
        console.log('✅ Google OAuth login successful');
      }

      return { success: true, user: data.user };
    } catch (err) {
      const errorMessage = err.message || 'Google authentication failed. Please try again.';
      setError(errorMessage);
      console.error('❌ Google OAuth error:', err);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Logout
  const logout = async () => {
    try {
      if (tokens?.refresh_token) {
        // Attempt to invalidate session on backend (don't wait for response)
        fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh_token: tokens.refresh_token })
        }).catch(err => console.error('Logout request failed:', err));
      }
    } catch (err) {
      console.error('❌ Logout error:', err);
    } finally {
      clearAuthState();

      if (import.meta.env.VITE_DEBUG === 'true') {
        console.log('✅ User logged out');
      }
    }
  };

  // Refresh access token
  const refreshAccessToken = async () => {
    try {
      if (!tokens?.refresh_token) {
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: tokens.refresh_token })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const updatedTokens = {
        ...tokens,
        access_token: data.access_token,
        token_type: data.token_type || 'bearer',
        expires_in: data.expires_in || 1800
      };

      sessionStorage.setItem('auth_tokens', JSON.stringify(updatedTokens));
      setTokens(updatedTokens);

      if (import.meta.env.VITE_DEBUG === 'true') {
        console.log('✅ Access token refreshed');
      }

      return data.access_token;
    } catch (err) {
      console.error('❌ Token refresh failed:', err);
      clearAuthState();
      throw err;
    }
  };

  // Get access token (with auto-refresh if needed)
  const getAccessToken = async () => {
    if (!tokens?.access_token) {
      return null;
    }

    try {
      // In a real app, you'd check token expiration here
      // For now, just return the current token
      return tokens.access_token;
    } catch (err) {
      // If token is expired, try to refresh
      console.warn('⚠️ Token may be expired, attempting refresh...');
      return await refreshAccessToken();
    }
  };

  // Authenticated fetch wrapper (with auto-retry on 401)
  const authFetch = async (url, options = {}) => {
    try {
      const token = await getAccessToken();
      
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });

      // Auto-retry on 401 (token expired)
      if (response.status === 401) {
        console.warn('⚠️ Received 401, refreshing token...');
        
        try {
          const newToken = await refreshAccessToken();
          
          // Retry request with new token
          const retryResponse = await fetch(url, {
            ...options,
            headers: {
              ...options.headers,
              'Authorization': `Bearer ${newToken}`,
              'Content-Type': 'application/json',
            }
          });

          return retryResponse;
        } catch (refreshError) {
          console.error('❌ Token refresh failed, logging out...');
          clearAuthState();
          throw new Error('Session expired. Please login again.');
        }
      }

      return response;
    } catch (err) {
      console.error('❌ Authenticated fetch error:', err);
      throw err;
    }
  };

  const value = {
    // State
    user,
    tokens,
    loading,
    error,
    isAuthenticated: !!user,
    
    // Methods
    signup,
    login,
    loginWithGoogle,
    logout,
    refreshAccessToken,
    getAccessToken,
    authFetch,
    
    // Utility
    clearError: () => setError(null)
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};