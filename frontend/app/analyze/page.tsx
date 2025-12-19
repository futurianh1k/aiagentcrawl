"use client";

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import SentimentChart from '@/components/SentimentChart';
import KeywordCloud from '@/components/KeywordCloud';
import ArticleList from '@/components/ArticleList';
import { Loader2, RefreshCw, AlertCircle } from 'lucide-react';

interface AnalysisData {
  session_id: number;
  keyword: string;
  status: string;
  total_articles: number;
  sentiment_distribution: {
    positive: number;
    negative: number;
    neutral: number;
  };
  keywords: Array<{
    keyword: string;
    frequency: number;
    sentiment_score: number;
  }>;
  articles: Array<{
    id: number;
    title: string;
    content: string;
    url?: string;
    source?: string;
    sentiment_label?: string;
    sentiment_score?: number;
    confidence?: number;
    comment_count: number;
  }>;
  created_at: string;
  completed_at?: string;
}

export default function AnalyzePage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');

  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysisResult = async () => {
    if (!sessionId) {
      setError('세션 ID가 없습니다.');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/analysis/${sessionId}`
      );

      if (!response.ok) {
        throw new Error('분석 결과를 가져오는데 실패했습니다.');
      }

      const data = await response.json();
      setAnalysisData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalysisResult();

    // 분석이 완료되지 않은 경우 5초마다 폴링
    const interval = setInterval(() => {
      if (analysisData?.status === 'processing') {
        fetchAnalysisResult();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [sessionId, analysisData?.status]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-600" />
          <h2 className="text-2xl font-semibold mb-2">분석 중입니다...</h2>
          <p className="text-gray-600">AI Agent가 뉴스를 수집하고 감정을 분석하고 있습니다.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
          <h2 className="text-2xl font-semibold mb-2 text-red-600">오류 발생</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={fetchAnalysisResult}
            className="btn btn-primary px-6 py-2"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  if (!analysisData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-yellow-500" />
          <h2 className="text-2xl font-semibold mb-2">데이터를 찾을 수 없습니다</h2>
          <p className="text-gray-600">분석 결과를 불러올 수 없습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                "{analysisData.keyword}" 뉴스 감정 분석 결과
              </h1>
              <div className="flex items-center mt-2 space-x-4 text-sm text-gray-600">
                <span>세션 ID: {analysisData.session_id}</span>
                <span>총 {analysisData.total_articles}개 기사</span>
                <span className={`px-2 py-1 rounded-full text-xs ${
                  analysisData.status === 'completed' 
                    ? 'bg-green-100 text-green-800' 
                    : analysisData.status === 'processing'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {analysisData.status === 'completed' ? '완료' : 
                   analysisData.status === 'processing' ? '진행중' : '실패'}
                </span>
              </div>
            </div>
            <button 
              onClick={fetchAnalysisResult}
              className="btn btn-secondary px-4 py-2"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              새로고침
            </button>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Sentiment Distribution */}
          <div className="card p-6">
            <h2 className="text-xl font-semibold mb-4">감정 분포</h2>
            <SentimentChart data={analysisData.sentiment_distribution} />
          </div>

          {/* Keywords */}
          <div className="card p-6">
            <h2 className="text-xl font-semibold mb-4">주요 키워드</h2>
            <KeywordCloud data={analysisData.keywords} />
          </div>
        </div>

        {/* Articles List */}
        <div className="card p-6">
          <h2 className="text-xl font-semibold mb-4">분석된 기사 목록</h2>
          <ArticleList articles={analysisData.articles} />
        </div>
      </div>
    </div>
  );
}