// frontend/poc-project/src/contexts/AuthContext.jsx
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

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // ✅ STEP 1: Load auth state from sessionStorage on mount
  useEffect(() => {
    const loadAuthState = () => {
      try {
        const savedTokens = sessionStorage.getItem('auth_tokens');
        const savedUser = sessionStorage.getItem('auth_user');

        console.log('🔍 Checking auth state...', {
          hasTokens: !!savedTokens,
          hasUser: !!savedUser
        });

        if (savedTokens && savedUser) {
          const parsedTokens = JSON.parse(savedTokens);
          const parsedUser = JSON.parse(savedUser);

          if (parsedTokens?.access_token && parsedTokens?.refresh_token) {
            setTokens(parsedTokens);
            setUser(parsedUser);

            console.log('✅ Auth state restored:', parsedUser.email);
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

  // ✅ STEP 2: Define ALL functions BEFORE the value object

  const saveAuthState = (userData, tokensData) => {
    try {
      sessionStorage.setItem('auth_user', JSON.stringify(userData));
      sessionStorage.setItem('auth_tokens', JSON.stringify(tokensData));
      setUser(userData);
      setTokens(tokensData);
    } catch (e) {
      console.error('❌ Failed to save auth state:', e);
    }
  };

  const clearAuthState = () => {
    try {
      sessionStorage.removeItem('auth_user');
      sessionStorage.removeItem('auth_tokens');
      setUser(null);
      setTokens(null);
      setError(null);
    } catch (e) {
      console.error('❌ Failed to clear auth state:', e);
    }
  };

  const signup = async (email, password, username, fullName = '') => {
    try {
      setError(null);
      setLoading(true);

      const response = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, username, full_name: fullName })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Signup failed');
      }

      saveAuthState(data.user, data.tokens);
      return { success: true, user: data.user };
    } catch (err) {
      const errorMessage = err.message || 'Signup failed. Please try again.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      setError(null);
      setLoading(true);

      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      saveAuthState(data.user, data.tokens);
      return { success: true, user: data.user };
    } catch (err) {
      const errorMessage = err.message || 'Login failed. Please check your credentials.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async (googleIdToken) => {
    try {
      setError(null);
      setLoading(true);

      const response = await fetch(`${API_BASE}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: googleIdToken })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Google login failed');
      }

      saveAuthState(data.user, data.tokens);
      return { success: true, user: data.user };
    } catch (err) {
      const errorMessage = err.message || 'Google authentication failed.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (tokens?.refresh_token) {
        fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: tokens.refresh_token })
        }).catch(err => console.error('Logout request failed:', err));
      }
    } catch (err) {
      console.error('❌ Logout error:', err);
    } finally {
      clearAuthState();
    }
  };

  const refreshAccessToken = async () => {
    try {
      if (!tokens?.refresh_token) {
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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

      return data.access_token;
    } catch (err) {
      console.error('❌ Token refresh failed:', err);
      clearAuthState();
      throw err;
    }
  };

  const getAccessToken = async () => {
    if (!tokens?.access_token) {
      return null;
    }
    return tokens.access_token;
  };

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

      if (response.status === 401) {
        try {
          const newToken = await refreshAccessToken();
          
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

  // ✅ STEP 3: Create value object LAST (after all functions are defined)
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