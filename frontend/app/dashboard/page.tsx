"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, TrendingUp, FileText, MessageSquare, Hash, CheckCircle, Clock, XCircle, BarChart3 } from 'lucide-react';
import SentimentChart from '@/components/SentimentChart';

interface Statistics {
  sessions: {
    total: number;
    completed: number;
    processing: number;
    failed: number;
  };
  articles: {
    total: number;
  };
  comments: {
    total: number;
  };
  keywords: {
    total: number;
  };
  sentiment_distribution: {
    positive: number;
    negative: number;
    neutral: number;
  };
  recent_keywords: Array<{
    keyword: string;
    count: number;
  }>;
}

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/analysis/stats/summary`
      );

      if (!response.ok) {
        throw new Error('통계를 가져오는데 실패했습니다.');
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-600" />
          <h2 className="text-2xl font-semibold mb-2">통계 로딩 중...</h2>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || '데이터를 불러올 수 없습니다.'}</p>
          <button
            onClick={fetchStatistics}
            className="btn btn-primary px-6 py-2"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  const completionRate = stats.sessions.total > 0
    ? ((stats.sessions.completed / stats.sessions.total) * 100).toFixed(1)
    : '0';

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">통계 대시보드</h1>
          <p className="text-gray-600">전체 분석 데이터의 통계를 확인할 수 있습니다.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Sessions Card */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">전체 세션</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.sessions.total}</p>
                <div className="flex items-center mt-4 gap-4 text-xs">
                  <div className="flex items-center text-green-600">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    {stats.sessions.completed} 완료
                  </div>
                  <div className="flex items-center text-yellow-600">
                    <Clock className="w-4 h-4 mr-1" />
                    {stats.sessions.processing} 진행중
                  </div>
                  <div className="flex items-center text-red-600">
                    <XCircle className="w-4 h-4 mr-1" />
                    {stats.sessions.failed} 실패
                  </div>
                </div>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <BarChart3 className="w-8 h-8 text-blue-600" />
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs text-gray-500">완료율: {completionRate}%</p>
            </div>
          </div>

          {/* Articles Card */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">전체 기사</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.articles.total}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <FileText className="w-8 h-8 text-green-600" />
              </div>
            </div>
          </div>

          {/* Comments Card */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">전체 댓글</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.comments.total}</p>
              </div>
              <div className="p-3 bg-purple-100 rounded-lg">
                <MessageSquare className="w-8 h-8 text-purple-600" />
              </div>
            </div>
          </div>

          {/* Keywords Card */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">전체 키워드</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.keywords.total}</p>
              </div>
              <div className="p-3 bg-orange-100 rounded-lg">
                <Hash className="w-8 h-8 text-orange-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Sentiment Distribution */}
          <div className="card p-6">
            <h2 className="text-xl font-semibold mb-4">전체 감정 분포</h2>
            <SentimentChart data={stats.sentiment_distribution} />
          </div>

          {/* Recent Keywords */}
          <div className="card p-6">
            <h2 className="text-xl font-semibold mb-4">최근 분석 키워드</h2>
            {stats.recent_keywords.length === 0 ? (
              <p className="text-gray-500 text-center py-8">분석된 키워드가 없습니다.</p>
            ) : (
              <div className="space-y-3">
                {stats.recent_keywords.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
                    onClick={() => router.push(`/sessions?keyword=${encodeURIComponent(item.keyword)}`)}
                  >
                    <div className="flex items-center">
                      <span className="w-8 h-8 flex items-center justify-center bg-blue-100 text-blue-600 rounded-full font-semibold text-sm mr-3">
                        {index + 1}
                      </span>
                      <span className="font-medium text-gray-900">{item.keyword}</span>
                    </div>
                    <div className="flex items-center text-gray-600">
                      <TrendingUp className="w-4 h-4 mr-1" />
                      <span className="text-sm">{item.count}회</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card p-6">
          <h2 className="text-xl font-semibold mb-4">빠른 작업</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => router.push('/')}
              className="btn btn-primary px-6 py-3 text-left"
            >
              <div className="font-semibold mb-1">새 분석 시작</div>
              <div className="text-sm opacity-90">키워드로 뉴스 분석을 시작합니다</div>
            </button>
            <button
              onClick={() => router.push('/sessions')}
              className="btn btn-secondary px-6 py-3 text-left"
            >
              <div className="font-semibold mb-1">세션 목록 보기</div>
              <div className="text-sm opacity-90">저장된 모든 분석 기록을 확인합니다</div>
            </button>
            <button
              onClick={fetchStatistics}
              className="btn btn-outline px-6 py-3 text-left"
            >
              <div className="font-semibold mb-1">통계 새로고침</div>
              <div className="text-sm opacity-90">최신 통계 데이터를 불러옵니다</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

