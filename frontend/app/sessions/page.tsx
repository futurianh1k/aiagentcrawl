"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, Search, Trash2, Eye, Calendar, FileText, MessageSquare, AlertCircle, CheckCircle, Clock, XCircle, Download, FileSpreadsheet, FileJson, Image as ImageIcon, X, ChevronLeft, ChevronRight } from 'lucide-react';

type SessionType = 'news' | 'image';

interface NewsSession {
  id: number;
  keyword: string;
  status: string;
  article_count: number;
  overall_summary?: string;
  // 토큰 사용량
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  estimated_cost?: number;
  created_at: string;
  completed_at?: string;
}

interface ImageSession {
  id: number;
  query: string;
  query_type: string;
  search_operator: string;
  status: string;
  total_results: number;
  created_at: string;
  completed_at?: string;
}

interface NewsSessionListResponse {
  sessions: NewsSession[];
  total: number;
  page: number;
  per_page: number;
}

interface MediaImage {
  id: number;
  url: string;
  caption?: string;
  article_title?: string;
}

interface SessionMedia {
  session_id: number;
  total_images: number;
  total_tables: number;
  articles: Array<{
    article_id: number;
    article_title: string;
    images: MediaImage[];
  }>;
}

interface UsageStats {
  total_sessions: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_estimated_cost: number;
  total_tokens_formatted: string;
  total_cost_formatted: string;
  free_credit_limit: number;
  remaining_credit: number;
  usage_percentage: number;
}

export default function SessionsPage() {
  const router = useRouter();
  const [sessionType, setSessionType] = useState<SessionType>('news');
  const [newsSessions, setNewsSessions] = useState<NewsSession[]>([]);
  const [imageSessions, setImageSessions] = useState<ImageSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [perPage] = useState(10);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [exportingId, setExportingId] = useState<number | null>(null);
  const [showExportMenu, setShowExportMenu] = useState<number | null>(null);
  
  // 미디어 관련 상태
  const [sessionMedia, setSessionMedia] = useState<Record<number, SessionMedia>>({});
  const [loadingMedia, setLoadingMedia] = useState<Record<number, boolean>>({});
  const [expandedMedia, setExpandedMedia] = useState<number | null>(null);
  
  // 이미지 팝업 상태
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [allImages, setAllImages] = useState<MediaImage[]>([]);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  
  // 사용량 통계
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);

  const fetchUsageStats = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/analysis/stats/usage`
      );
      if (response.ok) {
        const data = await response.json();
        setUsageStats(data);
      }
    } catch (err) {
      console.error('사용량 통계 조회 실패:', err);
    }
  };

  const fetchNewsSessions = async (pageNum: number = 1, keyword: string = '') => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        page: pageNum.toString(),
        per_page: perPage.toString(),
      });
      
      if (keyword) {
        params.append('keyword', keyword);
      }
      
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/analysis/sessions?${params}`
      );

      if (!response.ok) {
        throw new Error('뉴스 세션 목록을 가져오는데 실패했습니다.');
      }

      const data: NewsSessionListResponse = await response.json();
      setNewsSessions(data.sessions);
      setTotal(data.total);
      setPage(data.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const fetchImageSessions = async (pageNum: number = 1) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        page: pageNum.toString(),
        per_page: perPage.toString(),
      });
      
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/image-search/sessions?${params}`
      );

      if (!response.ok) {
        throw new Error('이미지 세션 목록을 가져오는데 실패했습니다.');
      }

      const data = await response.json();
      setImageSessions(data.sessions || []);
      setTotal(data.total || 0);
      setPage(data.page || 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSessions = async (pageNum: number = 1, keyword: string = '') => {
    if (sessionType === 'news') {
      await fetchNewsSessions(pageNum, keyword);
    } else {
      await fetchImageSessions(pageNum);
    }
  };

  const handleDelete = async (sessionId: number) => {
    const confirmMessage = sessionType === 'news'
      ? '정말 이 뉴스 분석 세션을 삭제하시겠습니까? 관련된 모든 기사와 댓글도 함께 삭제됩니다.'
      : '정말 이 이미지 검색 세션을 삭제하시겠습니까? 관련된 모든 검색 결과도 함께 삭제됩니다.';
    
    if (!confirm(confirmMessage)) {
      return;
    }

    setDeletingId(sessionId);
    
    try {
      const endpoint = sessionType === 'news'
        ? `/api/analysis/${sessionId}`
        : `/api/image-search/sessions/${sessionId}`;
      
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoint}`,
        { method: 'DELETE' }
      );

      if (!response.ok) {
        throw new Error('세션 삭제에 실패했습니다.');
      }

      // 목록 새로고침
      fetchSessions(page, searchKeyword);
    } catch (err) {
      alert(err instanceof Error ? err.message : '삭제 중 오류가 발생했습니다.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchSessions(1, searchKeyword);
  };

  const handleExport = async (sessionId: number, format: 'csv' | 'json') => {
    setExportingId(sessionId);
    setShowExportMenu(null);
    
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
      
      // 파일 다운로드
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
      setExportingId(null);
    }
  };

  // 세션의 미디어 데이터 가져오기
  const fetchSessionMedia = async (sessionId: number) => {
    if (sessionMedia[sessionId] || loadingMedia[sessionId]) return;
    
    setLoadingMedia(prev => ({ ...prev, [sessionId]: true }));
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/media/session/${sessionId}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setSessionMedia(prev => ({ ...prev, [sessionId]: data }));
      }
    } catch (err) {
      console.error('미디어 로딩 실패:', err);
    } finally {
      setLoadingMedia(prev => ({ ...prev, [sessionId]: false }));
    }
  };

  // 이미지 클릭 시 팝업 열기
  const openImagePopup = (imageUrl: string, sessionId: number) => {
    const media = sessionMedia[sessionId];
    if (!media) return;
    
    // 모든 이미지 목록 생성
    const images: MediaImage[] = [];
    media.articles.forEach(article => {
      article.images.forEach(img => {
        images.push({
          ...img,
          article_title: article.article_title
        });
      });
    });
    
    const index = images.findIndex(img => img.url === imageUrl);
    setAllImages(images);
    setCurrentImageIndex(index >= 0 ? index : 0);
    setSelectedImage(imageUrl);
  };

  // 이전/다음 이미지
  const navigateImage = (direction: 'prev' | 'next') => {
    if (allImages.length === 0) return;
    
    let newIndex = currentImageIndex;
    if (direction === 'prev') {
      newIndex = currentImageIndex > 0 ? currentImageIndex - 1 : allImages.length - 1;
    } else {
      newIndex = currentImageIndex < allImages.length - 1 ? currentImageIndex + 1 : 0;
    }
    
    setCurrentImageIndex(newIndex);
    setSelectedImage(allImages[newIndex].url);
  };

  // 키보드 이벤트 핸들러
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!selectedImage) return;
      
      if (e.key === 'Escape') {
        setSelectedImage(null);
      } else if (e.key === 'ArrowLeft') {
        navigateImage('prev');
      } else if (e.key === 'ArrowRight') {
        navigateImage('next');
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedImage, currentImageIndex, allImages]);

  useEffect(() => {
    fetchSessions();
    if (sessionType === 'news') {
      fetchUsageStats();
    }
  }, [sessionType]);

  useEffect(() => {
    fetchSessions();
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '완료';
      case 'processing':
        return '진행중';
      case 'failed':
        return '실패';
      default:
        return status;
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">세션 목록</h1>
          <p className="text-gray-600">저장된 분석 기록을 조회하고 관리할 수 있습니다.</p>
        </div>

        {/* Session Type Tabs */}
        <div className="mb-6">
          <div className="inline-flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => {
                setSessionType('news');
                setPage(1);
                setSearchKeyword('');
              }}
              className={`px-6 py-3 rounded-md font-medium transition-all ${
                sessionType === 'news'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center">
                <Search className="w-5 h-5 mr-2" />
                뉴스 감정 분석
              </div>
            </button>
            <button
              onClick={() => {
                setSessionType('image');
                setPage(1);
                setSearchKeyword('');
              }}
              className={`px-6 py-3 rounded-md font-medium transition-all ${
                sessionType === 'image'
                  ? 'bg-white text-purple-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center">
                <ImageIcon className="w-5 h-5 mr-2" />
                이미지 검색
              </div>
            </button>
          </div>
        </div>

        {/* LLM Usage Stats (News sessions only) */}
        {sessionType === 'news' && usageStats && usageStats.total_tokens > 0 && (
          <div className="card p-4 mb-6 bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200">
            <h3 className="text-sm font-semibold mb-3 text-amber-800 flex items-center">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              LLM 사용량 통계 (gpt-4o-mini)
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                <div className="text-lg font-bold text-blue-600">{usageStats.total_sessions}</div>
                <div className="text-xs text-gray-500">분석 세션</div>
              </div>
              <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                <div className="text-lg font-bold text-amber-600">{usageStats.total_prompt_tokens.toLocaleString()}</div>
                <div className="text-xs text-gray-500">📥 입력 토큰</div>
              </div>
              <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                <div className="text-lg font-bold text-teal-600">{usageStats.total_completion_tokens.toLocaleString()}</div>
                <div className="text-xs text-gray-500">📤 출력 토큰</div>
              </div>
              <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                <div className="text-lg font-bold text-orange-600">{usageStats.total_tokens_formatted}</div>
                <div className="text-xs text-gray-500">🔢 총 토큰</div>
              </div>
              <div className="text-center p-3 bg-white rounded-lg shadow-sm border-2 border-green-200">
                <div className="text-lg font-bold text-green-600">{usageStats.total_cost_formatted}</div>
                <div className="text-xs text-gray-500">💵 총 비용</div>
              </div>
            </div>
            
            {/* Usage Progress Bar */}
            <div className="mt-4 p-3 bg-white rounded-lg shadow-sm">
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Free Credit 사용량</span>
                <span>{usageStats.usage_percentage.toFixed(1)}% (${usageStats.total_estimated_cost.toFixed(4)} / ${usageStats.free_credit_limit})</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className={`h-2.5 rounded-full ${
                    usageStats.usage_percentage < 50 
                      ? 'bg-green-500' 
                      : usageStats.usage_percentage < 80 
                      ? 'bg-yellow-500' 
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(usageStats.usage_percentage, 100)}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>잔여: ${usageStats.remaining_credit.toFixed(4)}</span>
                <span className="text-gray-400">Input: $0.15/1M, Output: $0.6/1M</span>
              </div>
            </div>
          </div>
        )}

        {/* Search Bar (News sessions only) */}
        {sessionType === 'news' && (
          <div className="card p-4 mb-6">
            <div className="flex gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="키워드로 검색..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <button
                onClick={handleSearch}
                className="btn btn-primary px-6 py-2"
              >
                <Search className="w-4 h-4 mr-2" />
                검색
              </button>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600">로딩 중...</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="card p-6 mb-6 bg-red-50 border-red-200">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Sessions List */}
        {!loading && !error && (
          <>
            {sessionType === 'news' ? (
              <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          ID
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          키워드
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          상태
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          기사 수
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[180px]">
                          이미지
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[250px]">
                          요약
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          토큰/비용
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          생성일시
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          작업
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {newsSessions.length === 0 ? (
                        <tr>
                          <td colSpan={9} className="px-6 py-12 text-center text-gray-500">
                            뉴스 분석 세션이 없습니다.
                          </td>
                        </tr>
                      ) : (
                        newsSessions.map((session) => (
                        <tr key={session.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            #{session.id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <span className="font-semibold">{session.keyword}</span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {getStatusIcon(session.status)}
                              <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(session.status)}`}>
                                {getStatusText(session.status)}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <div className="flex items-center">
                              <FileText className="w-4 h-4 mr-1" />
                              {session.article_count}개
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {/* 이미지 썸네일 */}
                            {session.status === 'completed' && (
                              <div>
                                {!sessionMedia[session.id] && !loadingMedia[session.id] ? (
                                  <button
                                    onClick={() => fetchSessionMedia(session.id)}
                                    className="flex items-center text-blue-600 hover:text-blue-800 text-xs"
                                  >
                                    <ImageIcon className="w-4 h-4 mr-1" />
                                    이미지 보기
                                  </button>
                                ) : loadingMedia[session.id] ? (
                                  <div className="flex items-center text-gray-400 text-xs">
                                    <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                                    로딩 중...
                                  </div>
                                ) : sessionMedia[session.id]?.total_images > 0 ? (
                                  <div>
                                    <div className="flex items-center gap-1 mb-2">
                                      <ImageIcon className="w-4 h-4 text-blue-600" />
                                      <span className="text-xs text-blue-600 font-medium">
                                        {sessionMedia[session.id].total_images}개
                                      </span>
                                      <button
                                        onClick={() => setExpandedMedia(expandedMedia === session.id ? null : session.id)}
                                        className="text-xs text-gray-500 hover:text-gray-700 ml-1"
                                      >
                                        {expandedMedia === session.id ? '접기' : '펼치기'}
                                      </button>
                                    </div>
                                    
                                    {/* 썸네일 그리드 */}
                                    <div className={`flex flex-wrap gap-1 ${expandedMedia === session.id ? '' : 'max-h-16 overflow-hidden'}`}>
                                      {sessionMedia[session.id].articles.flatMap(article => 
                                        article.images.slice(0, expandedMedia === session.id ? undefined : 3).map((img, idx) => (
                                          <div
                                            key={`${article.article_id}-${idx}`}
                                            className="relative w-12 h-12 rounded overflow-hidden cursor-pointer hover:opacity-80 transition-opacity border border-gray-200"
                                            onClick={() => openImagePopup(img.url, session.id)}
                                            title={article.article_title}
                                          >
                                            <img
                                              src={img.url?.startsWith('/api') 
                                                ? `${process.env.NEXT_PUBLIC_API_BASE_URL}${img.url}`
                                                : img.url
                                              }
                                              alt={img.caption || '기사 이미지'}
                                              className="w-full h-full object-cover"
                                              onError={(e) => {
                                                (e.target as HTMLImageElement).style.display = 'none';
                                              }}
                                            />
                                          </div>
                                        ))
                                      ).slice(0, expandedMedia === session.id ? undefined : 4)}
                                      {!expandedMedia && sessionMedia[session.id].total_images > 4 && (
                                        <div 
                                          className="w-12 h-12 rounded bg-gray-100 flex items-center justify-center text-xs text-gray-500 cursor-pointer hover:bg-gray-200"
                                          onClick={() => setExpandedMedia(session.id)}
                                        >
                                          +{sessionMedia[session.id].total_images - 4}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                ) : (
                                  <span className="text-gray-400 text-xs italic">이미지 없음</span>
                                )}
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500 max-w-[250px]">
                            {session.overall_summary ? (
                              <p className="line-clamp-2 text-gray-600" title={session.overall_summary}>
                                {session.overall_summary}
                              </p>
                            ) : (
                              <span className="text-gray-400 italic">요약 없음</span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {session.total_tokens && session.total_tokens > 0 ? (
                              <div className="text-xs">
                                <div className="font-medium text-orange-600">
                                  {session.total_tokens.toLocaleString()} tok
                                </div>
                                <div className="text-green-600">
                                  ${(session.estimated_cost || 0).toFixed(4)}
                                </div>
                              </div>
                            ) : (
                              <span className="text-gray-400 text-xs">-</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <div className="flex items-center">
                              <Calendar className="w-4 h-4 mr-1" />
                              {formatDate(session.created_at)}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div className="flex items-center justify-end gap-1">
                              <button
                                onClick={() => router.push(`/analyze?session_id=${session.id}`)}
                                className="text-blue-600 hover:text-blue-900 p-2 hover:bg-blue-50 rounded"
                                title="상세 보기"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              
                              {/* 내보내기 드롭다운 */}
                              <div className="relative">
                                <button
                                  onClick={() => setShowExportMenu(showExportMenu === session.id ? null : session.id)}
                                  disabled={exportingId === session.id}
                                  className="text-green-600 hover:text-green-900 p-2 hover:bg-green-50 rounded disabled:opacity-50"
                                  title="내보내기"
                                >
                                  {exportingId === session.id ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <Download className="w-4 h-4" />
                                  )}
                                </button>
                                
                                {showExportMenu === session.id && (
                                  <div className="absolute right-0 mt-1 w-36 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                                    <button
                                      onClick={() => handleExport(session.id, 'csv')}
                                      className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                                    >
                                      <FileSpreadsheet className="w-4 h-4 mr-2 text-green-600" />
                                      CSV (엑셀)
                                    </button>
                                    <button
                                      onClick={() => handleExport(session.id, 'json')}
                                      className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                                    >
                                      <FileJson className="w-4 h-4 mr-2 text-blue-600" />
                                      JSON
                                    </button>
                                  </div>
                                )}
                              </div>
                              
                              <button
                                onClick={() => handleDelete(session.id)}
                                disabled={deletingId === session.id}
                                className="text-red-600 hover:text-red-900 p-2 hover:bg-red-50 rounded disabled:opacity-50"
                                title="삭제"
                              >
                                {deletingId === session.id ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Trash2 className="w-4 h-4" />
                                )}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
            ) : (
              <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          ID
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          검색어
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          검색 타입
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          연산자
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          상태
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          결과 수
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          생성일시
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          작업
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {imageSessions.length === 0 ? (
                        <tr>
                          <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                            이미지 검색 세션이 없습니다.
                          </td>
                        </tr>
                      ) : (
                        imageSessions.map((session) => (
                          <tr key={session.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              #{session.id}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              <span className="font-semibold">{session.query}</span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                                {session.query_type === 'text' ? '텍스트' : session.query_type === 'image' ? '이미지' : '혼합'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                                {session.search_operator}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                {getStatusIcon(session.status)}
                                <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(session.status)}`}>
                                  {getStatusText(session.status)}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <div className="flex items-center">
                                <ImageIcon className="w-4 h-4 mr-1" />
                                {session.total_results}개
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <div className="flex items-center">
                                <Calendar className="w-4 h-4 mr-1" />
                                {formatDate(session.created_at)}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <div className="flex items-center justify-end gap-1">
                                <button
                                  onClick={() => router.push(`/image-search?session_id=${session.id}`)}
                                  className="text-blue-600 hover:text-blue-900 p-2 hover:bg-blue-50 rounded"
                                  title="상세 보기"
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleDelete(session.id)}
                                  disabled={deletingId === session.id}
                                  className="text-red-600 hover:text-red-900 p-2 hover:bg-red-50 rounded disabled:opacity-50"
                                  title="삭제"
                                >
                                  {deletingId === session.id ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <Trash2 className="w-4 h-4" />
                                  )}
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-6 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  총 <span className="font-medium">{total}</span>개의 세션 중{' '}
                  <span className="font-medium">
                    {(page - 1) * perPage + 1}
                  </span>
                  -
                  <span className="font-medium">
                    {Math.min(page * perPage, total)}
                  </span>
                  개 표시
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => fetchSessions(page - 1, searchKeyword)}
                    disabled={page === 1}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    이전
                  </button>
                  <div className="flex items-center px-4 py-2 text-sm text-gray-700">
                    {page} / {totalPages}
                  </div>
                  <button
                    onClick={() => fetchSessions(page + 1, searchKeyword)}
                    disabled={page === totalPages}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    다음
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* 이미지 팝업 모달 */}
      {selectedImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-6xl max-h-[90vh] w-full mx-4" onClick={e => e.stopPropagation()}>
            {/* 닫기 버튼 */}
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-4 right-4 text-white bg-black bg-opacity-50 rounded-full p-2 hover:bg-opacity-75 z-10"
            >
              <X className="w-6 h-6" />
            </button>
            
            {/* 이전 버튼 */}
            {allImages.length > 1 && (
              <button
                onClick={() => navigateImage('prev')}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-white bg-black bg-opacity-50 rounded-full p-3 hover:bg-opacity-75 z-10"
              >
                <ChevronLeft className="w-8 h-8" />
              </button>
            )}
            
            {/* 다음 버튼 */}
            {allImages.length > 1 && (
              <button
                onClick={() => navigateImage('next')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-white bg-black bg-opacity-50 rounded-full p-3 hover:bg-opacity-75 z-10"
              >
                <ChevronRight className="w-8 h-8" />
              </button>
            )}
            
            {/* 이미지 */}
            <div className="flex items-center justify-center h-[80vh]">
              <img
                src={selectedImage.startsWith('/api')
                  ? `${process.env.NEXT_PUBLIC_API_BASE_URL}${selectedImage}`
                  : selectedImage
                }
                alt="확대 이미지"
                className="max-w-full max-h-full object-contain"
              />
            </div>
            
            {/* 이미지 정보 */}
            <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white p-4">
              <div className="flex items-center justify-between">
                <div>
                  {allImages[currentImageIndex]?.article_title && (
                    <p className="text-sm text-gray-300 mb-1">
                      📰 {allImages[currentImageIndex].article_title}
                    </p>
                  )}
                  {allImages[currentImageIndex]?.caption && (
                    <p className="text-sm">{allImages[currentImageIndex].caption}</p>
                  )}
                </div>
                <div className="text-sm text-gray-400">
                  {currentImageIndex + 1} / {allImages.length}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

