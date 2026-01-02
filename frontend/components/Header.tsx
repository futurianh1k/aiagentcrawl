'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';
import { User, LogOut, LogIn, UserPlus } from 'lucide-react';

export default function Header() {
  const router = useRouter();
  const { user, isAuthenticated, logout, isLoading } = useAuth();

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div>
            <Link href="/">
              <h1 className="text-2xl font-bold text-gray-900 cursor-pointer hover:text-blue-600 transition-colors">
                🤖 News Sentiment AI Agent
              </h1>
            </Link>
            <p className="text-sm text-gray-600 mt-1">
              LangChain 기반 뉴스 감정 분석 시스템
            </p>
          </div>
          
          <nav className="flex items-center gap-4">
            <Link
              href="/"
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              홈
            </Link>
            <Link
              href="/dashboard"
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              대시보드
            </Link>
            <Link
              href="/sessions"
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              세션 목록
            </Link>

            {!isLoading && (
              <>
                {isAuthenticated ? (
                  <>
                    <div className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700">
                      <User className="w-4 h-4" />
                      <span className="font-medium">{user?.email}</span>
                      {user?.full_name && (
                        <span className="text-gray-500">({user.full_name})</span>
                      )}
                    </div>
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      로그아웃
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      href="/auth/login"
                      className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                    >
                      <LogIn className="w-4 h-4" />
                      로그인
                    </Link>
                    <Link
                      href="/auth/register"
                      className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      <UserPlus className="w-4 h-4" />
                      회원가입
                    </Link>
                  </>
                )}
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
