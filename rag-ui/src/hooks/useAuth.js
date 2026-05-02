import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check for existing token on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const userData = await api.getMe();
          setUser(userData);
        } catch (error) {
          console.error("Token validation failed", error);
          localStorage.removeItem('access_token');
          setUser(null);
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const login = useCallback(async (username, password) => {
    setError(null);
    setLoading(true);
    try {
      await api.login(username, password);
      const userData = await api.getMe();
      setUser(userData);
      return true;
    } catch (err) {
      setError(err.message || 'Login failed');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (userData) => {
    // userData: { username, email, password, role, first_name, last_name }
    setError(null);
    setLoading(true);
    try {
      await api.register(userData);
      // Auto-login after registration
      await api.login(userData.username, userData.password);
      const fullUserData = await api.getMe();
      setUser(fullUserData);
      return true;
    } catch (err) {
      setError(err.message || 'Registration failed');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setLoading(true);
    try {
      await api.logout();
    } catch {}
    setUser(null);
    setLoading(false);
  }, []);

  const forgotPassword = useCallback(async (email) => {
    setError(null);
    setLoading(true);
    try {
      await api.forgotPassword(email);
      setError(null);
      return { success: true, message: 'Password reset link sent to your email' };
    } catch (err) {
      setError(err.message || 'Failed to send reset link');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return {
    user,
    loading,
    error,
    login,
    register,
    logout,
    clearError,
    isAuthenticated: !!user,
  };
}