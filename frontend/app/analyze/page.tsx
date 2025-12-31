"use client";

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import SentimentChart from '@/components/SentimentChart';
import KeywordCloud from '@/components/KeywordCloud';
import ArticleList from '@/components/ArticleList';
import { Loader2, RefreshCw, AlertCircle, Download, FileSpreadsheet, FileJson, Image as ImageIcon, Table as TableIcon, X } from 'lucide-react';

interface TimingInfo {
  crawling_time: number;
  sentiment_time: number;
  summary_time: number;
  total_time: number;
}

interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost: number;
}

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
    summary?: string;
    url?: string;
    source?: string;
    sentiment_label?: string;
    sentiment_score?: number;
    confidence?: number;
    comment_count: number;
    image_count?: number;
    table_count?: number;
  }>;
  overall_summary?: string;
  timing?: TimingInfo;
  token_usage?: TokenUsage;
  created_at: string;
  completed_at?: string;
}

export default function AnalyzePage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');

  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [mediaData, setMediaData] = useState<any>(null);
  const [showMediaGallery, setShowMediaGallery] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const handleExport = async (format: 'csv' | 'json') => {
    if (!sessionId) return;
    
    setExporting(true);
    setShowExportMenu(false);
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/analysis/export/${sessionId}/${format}`
      );
      
      if (!response.ok) {
        throw new Error('내보내기 실패');
      }
      
      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `analysis_${sessionId}.${format}`;
      
      if (contentDisposition) {
        const match = contentDisposition.match(/filename=(.+)/);
        if (match) filename = match[1];
      }
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
    } catch (err) {
      alert(err instanceof Error ? err.message : '내보내기 중 오류가 발생했습니다.');
    } finally {
      setExporting(false);
    }
  };

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
      
      // 미디어 데이터도 가져오기
      fetchMediaData();
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const fetchMediaData = async () => {
    if (!sessionId) return;
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/media/session/${sessionId}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setMediaData(data);
      }
    } catch (err) {
      console.error('미디어 데이터 로딩 실패:', err);
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
            <div className="flex items-center gap-2">
              {/* 내보내기 드롭다운 */}
              <div className="relative">
                <button 
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  disabled={exporting}
                  className="btn btn-primary px-4 py-2 flex items-center"
                >
                  {exporting ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4 mr-2" />
                  )}
                  내보내기
                </button>
                
                {showExportMenu && (
                  <div className="absolute right-0 mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                    <button
                      onClick={() => handleExport('csv')}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center rounded-t-lg"
                    >
                      <FileSpreadsheet className="w-4 h-4 mr-2 text-green-600" />
                      CSV (엑셀)
                    </button>
                    <button
                      onClick={() => handleExport('json')}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center rounded-b-lg"
                    >
                      <FileJson className="w-4 h-4 mr-2 text-blue-600" />
                      JSON
                    </button>
                  </div>
                )}
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
        </div>

        {/* Performance & Usage Info */}
        {(analysisData.timing || analysisData.token_usage) && (
          <div className="card p-4 mb-6 bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200">
            {/* Timing Info */}
            {analysisData.timing && (
              <>
                <h3 className="text-sm font-semibold mb-3 text-gray-700 flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  성능 측정
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                    <div className="text-2xl font-bold text-blue-600">{analysisData.timing.crawling_time}s</div>
                    <div className="text-xs text-gray-500 mt-1">🕷️ 크롤링</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                    <div className="text-2xl font-bold text-green-600">{analysisData.timing.sentiment_time}s</div>
                    <div className="text-xs text-gray-500 mt-1">💭 감성 분석</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                    <div className="text-2xl font-bold text-purple-600">{analysisData.timing.summary_time}s</div>
                    <div className="text-xs text-gray-500 mt-1">📝 요약 생성</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm border-2 border-indigo-200">
                    <div className="text-2xl font-bold text-indigo-600">{analysisData.timing.total_time}s</div>
                    <div className="text-xs text-gray-500 mt-1">⏱️ 총 소요 시간</div>
                  </div>
                </div>
              </>
            )}

            {/* Token Usage Info */}
            {analysisData.token_usage && analysisData.token_usage.total_tokens > 0 && (
              <>
                <h3 className="text-sm font-semibold mb-3 text-gray-700 flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  LLM 토큰 사용량
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                    <div className="text-xl font-bold text-amber-600">
                      {analysisData.token_usage.prompt_tokens.toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">📥 입력 토큰</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                    <div className="text-xl font-bold text-teal-600">
                      {analysisData.token_usage.completion_tokens.toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">📤 출력 토큰</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                    <div className="text-xl font-bold text-orange-600">
                      {analysisData.token_usage.total_tokens.toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">🔢 총 토큰</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm border-2 border-green-200">
                    <div className="text-xl font-bold text-green-600">
                      ${analysisData.token_usage.estimated_cost.toFixed(4)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">💵 예상 비용</div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* Overall Summary */}
        {analysisData.overall_summary && (
          <div className="card p-6 mb-8 bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500">
            <h2 className="text-xl font-semibold mb-4 text-blue-800 flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              AI 종합 요약
            </h2>
            <p className="text-gray-700 leading-relaxed whitespace-pre-line">
              {analysisData.overall_summary}
            </p>
          </div>
        )}

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

        {/* Media Gallery Section */}
        {mediaData && (mediaData.total_images > 0 || mediaData.total_tables > 0) && (
          <div className="card p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center">
                <ImageIcon className="w-6 h-6 mr-2 text-blue-600" />
                미디어 갤러리
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (이미지 {mediaData.total_images}개, 테이블 {mediaData.total_tables}개)
                </span>
              </h2>
              <button
                onClick={() => setShowMediaGallery(!showMediaGallery)}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                {showMediaGallery ? '접기' : '펼치기'}
              </button>
            </div>
            
            {showMediaGallery && (
              <div className="space-y-6">
                {mediaData.articles?.map((articleMedia: any) => (
                  <div key={articleMedia.article_id} className="border-b pb-4">
                    <h3 className="font-medium text-gray-800 mb-3">
                      {articleMedia.article_title}...
                    </h3>
                    
                    {/* 이미지 그리드 */}
                    {articleMedia.images?.length > 0 && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                        {articleMedia.images.map((img: any, idx: number) => (
                          <div
                            key={idx}
                            className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:opacity-80 transition-opacity"
                            onClick={() => setSelectedImage(img.url)}
                          >
                            <img
                              src={img.url?.startsWith('/api') 
                                ? `${process.env.NEXT_PUBLIC_API_BASE_URL}${img.url}`
                                : img.url
                              }
                              alt={img.caption || '기사 이미지'}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = '/placeholder-image.png';
                              }}
                            />
                            {img.caption && (
                              <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1 truncate">
                                {img.caption}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* 테이블 미리보기 */}
                    {articleMedia.tables?.length > 0 && (
                      <div className="space-y-2">
                        {articleMedia.tables.map((tbl: any, idx: number) => (
                          <div key={idx} className="flex items-center text-sm text-gray-600">
                            <TableIcon className="w-4 h-4 mr-2 text-green-600" />
                            <span>{tbl.caption || `테이블 ${idx + 1}`}</span>
                            {tbl.url && (
                              <a
                                href={tbl.url?.startsWith('/api')
                                  ? `${process.env.NEXT_PUBLIC_API_BASE_URL}${tbl.url}`
                                  : tbl.url
                                }
                                target="_blank"
                                rel="noopener noreferrer"
                                className="ml-2 text-blue-600 hover:underline"
                              >
                                보기
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Image Modal */}
        {selectedImage && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
            onClick={() => setSelectedImage(null)}
          >
            <div className="relative max-w-4xl max-h-[90vh]">
              <button
                onClick={() => setSelectedImage(null)}
                className="absolute top-2 right-2 text-white bg-black bg-opacity-50 rounded-full p-2 hover:bg-opacity-75"
              >
                <X className="w-6 h-6" />
              </button>
              <img
                src={selectedImage.startsWith('/api')
                  ? `${process.env.NEXT_PUBLIC_API_BASE_URL}${selectedImage}`
                  : selectedImage
                }
                alt="확대 이미지"
                className="max-w-full max-h-[90vh] object-contain"
              />
            </div>
          </div>
        )}

        {/* Articles List */}
        <div className="card p-6">
          <h2 className="text-xl font-semibold mb-4">분석된 기사 목록</h2>
          <ArticleList articles={analysisData.articles} />
        </div>
      </div>
    </div>
  );
}