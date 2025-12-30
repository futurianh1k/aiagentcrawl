"use client";

import { useState } from 'react';
import { ExternalLink, MessageSquare, TrendingUp, TrendingDown, Minus, Image as ImageIcon, Table as TableIcon, ChevronDown, ChevronUp } from 'lucide-react';

interface ArticleMedia {
  id?: number;
  url: string;
  caption?: string;
  alt_text?: string;
  width?: number;
  height?: number;
}

interface ArticleTable {
  id?: number;
  url?: string;
  caption?: string;
  table_html?: string;
  rows?: number;
  cols?: number;
}

interface Article {
  id: number;
  title: string;
  content: string;
  summary?: string;
  url?: string;
  source?: string;
  sentiment_label?: string;
  sentiment_score?: number;
  confidence?: number;
  comment_count: number;
  image_count?: number;
  table_count?: number;
}

interface ArticleListProps {
  articles: Article[];
}

export default function ArticleList({ articles }: ArticleListProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedSentiment, setSelectedSentiment] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('confidence');

  const articlesPerPage = 5;

  // 감정 레이블 정규화 함수
  const normalizeSentimentLabel = (label?: string): string => {
    if (!label) return 'neutral';
    const normalized = label.toLowerCase();
    if (normalized === 'positive' || label === '긍정' || label === '긍정적') return 'positive';
    if (normalized === 'negative' || label === '부정' || label === '부정적') return 'negative';
    return 'neutral';
  };

  // 필터링 및 정렬
  const filteredArticles = articles
    .filter(article => {
      if (selectedSentiment === 'all') return true;
      const normalized = normalizeSentimentLabel(article.sentiment_label);
      return normalized === selectedSentiment;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'confidence':
          return (b.confidence || 0) - (a.confidence || 0);
        case 'sentiment':
          return (b.sentiment_score || 0) - (a.sentiment_score || 0);
        case 'comments':
          return b.comment_count - a.comment_count;
        default:
          return 0;
      }
    });

  // 페이지네이션
  const totalPages = Math.ceil(filteredArticles.length / articlesPerPage);
  const startIndex = (currentPage - 1) * articlesPerPage;
  const paginatedArticles = filteredArticles.slice(startIndex, startIndex + articlesPerPage);

  const getSentimentIcon = (label?: string, score?: number) => {
    if (!label) return <Minus className="w-4 h-4 text-gray-400" />;

    // 한국어 레이블도 처리
    const normalizedLabel = label.toLowerCase();
    if (normalizedLabel === 'positive' || label === '긍정' || label === '긍정적') {
        return <TrendingUp className="w-4 h-4 text-green-600" />;
    } else if (normalizedLabel === 'negative' || label === '부정' || label === '부정적') {
        return <TrendingDown className="w-4 h-4 text-red-600" />;
    } else {
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getSentimentColor = (label?: string) => {
    if (!label) return 'text-gray-700 bg-gray-100';
    
    // 한국어 레이블도 처리
    const normalizedLabel = label.toLowerCase();
    if (normalizedLabel === 'positive' || label === '긍정' || label === '긍정적') {
      return 'text-green-700 bg-green-100';
    } else if (normalizedLabel === 'negative' || label === '부정' || label === '부정적') {
      return 'text-red-700 bg-red-100';
    } else {
      return 'text-gray-700 bg-gray-100';
    }
  };

  const getSentimentText = (label?: string) => {
    if (!label) return '중립';
    
    // 한국어 레이블도 처리
    const normalizedLabel = label.toLowerCase();
    if (normalizedLabel === 'positive' || label === '긍정' || label === '긍정적') {
      return '긍정';
    } else if (normalizedLabel === 'negative' || label === '부정' || label === '부정적') {
      return '부정';
    } else {
      return '중립';
    }
  };

  if (!articles || articles.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">분석된 기사가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 필터 및 정렬 컨트롤 */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-4">
          <select
            value={selectedSentiment}
            onChange={(e) => {
              setSelectedSentiment(e.target.value);
              setCurrentPage(1);
            }}
            className="input w-auto text-sm"
          >
            <option value="all">모든 감정</option>
            <option value="positive">긍정</option>
            <option value="negative">부정</option>
            <option value="neutral">중립</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="input w-auto text-sm"
          >
            <option value="confidence">신뢰도순</option>
            <option value="sentiment">감정점수순</option>
            <option value="comments">댓글수순</option>
          </select>
        </div>

        <div className="text-sm text-gray-600">
          총 {filteredArticles.length}개 기사
        </div>
      </div>

      {/* 기사 목록 */}
      <div className="space-y-4">
        {paginatedArticles.map((article) => (
          <div key={article.id} className="border rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-3">
                {getSentimentIcon(article.sentiment_label, article.sentiment_score)}
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSentimentColor(article.sentiment_label)}`}>
                  {getSentimentText(article.sentiment_label)}
                </span>
                {article.source && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                    {article.source}
                  </span>
                )}
              </div>

              <div className="flex items-center space-x-4 text-sm text-gray-500">
                {article.confidence && (
                  <span>신뢰도: {(article.confidence * 100).toFixed(1)}%</span>
                )}
                <div className="flex items-center">
                  <MessageSquare className="w-4 h-4 mr-1" />
                  {article.comment_count}
                </div>
                {(article.image_count ?? 0) > 0 && (
                  <div className="flex items-center text-blue-600">
                    <ImageIcon className="w-4 h-4 mr-1" />
                    {article.image_count}
                  </div>
                )}
                {(article.table_count ?? 0) > 0 && (
                  <div className="flex items-center text-green-600">
                    <TableIcon className="w-4 h-4 mr-1" />
                    {article.table_count}
                  </div>
                )}
              </div>
            </div>

            <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
              {article.title}
            </h3>

            {/* AI 요약 */}
            {article.summary && (
              <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mb-3 rounded-r">
                <p className="text-sm text-blue-800 font-medium mb-1 flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  AI 요약
                </p>
                <p className="text-sm text-blue-700">{article.summary}</p>
              </div>
            )}

            <p className="text-gray-600 text-sm mb-3 line-clamp-3">
              {article.content}
            </p>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                {article.sentiment_score !== undefined && (
                  <span>
                    감정점수: {article.sentiment_score.toFixed(2)}
                  </span>
                )}
              </div>

              {article.url && (
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm"
                >
                  원문 보기 <ExternalLink className="w-3 h-3 ml-1" />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-3 py-2 text-sm border rounded-md disabled:opacity-50 hover:bg-gray-50"
          >
            이전
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <button
              key={page}
              onClick={() => setCurrentPage(page)}
              className={`px-3 py-2 text-sm border rounded-md ${
                currentPage === page
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'hover:bg-gray-50'
              }`}
            >
              {page}
            </button>
          ))}

          <button
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-2 text-sm border rounded-md disabled:opacity-50 hover:bg-gray-50"
          >
            다음
          </button>
        </div>
      )}
    </div>
  );
}