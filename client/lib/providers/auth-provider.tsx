'use client';

import React, { createContext, useContext, useReducer } from 'react';
import { User, AuthContextType } from '@/types/user.types';
import { tokenStore } from '@/lib/api/tokenStore';

// ── State ─────────────────────────────────────────────────────────────────────

interface AuthState {
  user: User | null;
  isLoading: boolean;
}

type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: User }
  | { type: 'LOGIN_ERROR' }
  | { type: 'LOGOUT' };

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, isLoading: true };
    case 'LOGIN_SUCCESS':
      return { user: action.payload, isLoading: false };
    case 'LOGIN_ERROR':
      return { ...state, isLoading: false };
    case 'LOGOUT':
      return { user: null, isLoading: false };
    default:
      return state;
  }
}

const initialState: AuthState = { user: null, isLoading: false };

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  const login = async (email: string, password: string) => {
    dispatch({ type: 'LOGIN_START' });
    try {
      // TODO: Replace with real auth API call in the auth module integration
      await new Promise((resolve) => setTimeout(resolve, 1000));
      const mockUser: User = {
        id: 'user-1',
        email,
        name: 'Sarah Johnson',
        avatar:
          'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=200',
      };
      tokenStore.setToken('mock-token-123');
      dispatch({ type: 'LOGIN_SUCCESS', payload: mockUser });
    } catch {
      dispatch({ type: 'LOGIN_ERROR' });
      throw new Error('Login failed');
    }
  };

  const register = async (name: string, email: string, _password: string) => {
    dispatch({ type: 'LOGIN_START' });
    try {
      // TODO: Replace with real auth API call — POST /api/v1/auth/register
      await new Promise((resolve) => setTimeout(resolve, 1200));
      const newUser: User = {
        id: `user-${Date.now()}`,
        email,
        name,
        avatar: undefined,
      };
      tokenStore.setToken('mock-token-123');
      dispatch({ type: 'LOGIN_SUCCESS', payload: newUser });
    } catch {
      dispatch({ type: 'LOGIN_ERROR' });
      throw new Error('Registration failed');
    }
  };

  const logout = () => {
    tokenStore.clearToken();
    dispatch({ type: 'LOGOUT' });
  };

  return (
    <AuthContext.Provider
      value={{
        user: state.user,
        isAuthenticated: !!state.user,
        login,
        register,
        logout,
        isLoading: state.isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
