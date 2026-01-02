'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi, UserResponse, TokenResponse } from '../lib/api';

interface AuthContextType {
  user: UserResponse | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<{ message: string }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 로컬 스토리지에서 토큰 로드
  useEffect(() => {
    const loadUser = async () => {
      try {
        const savedToken = localStorage.getItem('access_token');
        if (savedToken) {
          const userData = await authApi.getCurrentUser(savedToken);
          setUser(userData);
          setToken(savedToken);
        }
      } catch (error) {
        console.error('Failed to load user:', error);
        // 토큰이 만료되었거나 유효하지 않으면 제거
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const tokenData: TokenResponse = await authApi.login({ email, password });

      // 토큰 저장
      localStorage.setItem('access_token', tokenData.access_token);
      localStorage.setItem('refresh_token', tokenData.refresh_token);
      setToken(tokenData.access_token);

      // 사용자 정보 가져오기
      const userData = await authApi.getCurrentUser(tokenData.access_token);
      setUser(userData);
    } catch (error: any) {
      console.error('Login failed:', error);
      throw new Error(error.response?.data?.detail || '로그인에 실패했습니다.');
    }
  };

  const register = async (email: string, password: string, fullName?: string) => {
    try {
      const result = await authApi.register({
        email,
        password,
        full_name: fullName,
      });
      return result;
    } catch (error: any) {
      console.error('Registration failed:', error);
      throw new Error(error.response?.data?.detail || '회원 가입에 실패했습니다.');
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setToken(null);
  };

  const refreshUser = async () => {
    if (!token) return;

    try {
      const userData = await authApi.getCurrentUser(token);
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      logout();
    }
  };

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
