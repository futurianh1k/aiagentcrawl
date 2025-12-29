import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'News Sentiment AI Agent',
  description: 'AI Agent 기반 뉴스 감정 분석 시스템',
  keywords: ['AI', 'Agent', 'News', 'Sentiment', 'Analysis', 'LangChain'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" className="h-full">
      <body className={`${inter.className} h-full bg-gray-50`}>
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
            <h1 className="text-2xl font-bold text-gray-900">
              🤖 News Sentiment AI Agent
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              LangChain 기반 뉴스 감정 분석 시스템
            </p>
              </div>
              <nav className="flex items-center gap-4">
                <a
                  href="/"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  홈
                </a>
                <a
                  href="/dashboard"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  대시보드
                </a>
                <a
                  href="/sessions"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  세션 목록
                </a>
              </nav>
            </div>
          </div>
        </header>

        <main className="min-h-screen">
          {children}
        </main>

        <footer className="bg-gray-800 text-white py-8 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p>&copy; 2024 News Sentiment AI Agent System. All rights reserved.</p>
            <p className="text-sm text-gray-400 mt-2">
              4일차 AI Agent 강의용 프로젝트
            </p>
          </div>
        </footer>
      </body>
    </html>
  )
}