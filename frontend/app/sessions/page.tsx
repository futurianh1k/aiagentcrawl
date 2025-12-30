"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, Search, Trash2, Eye, Calendar, FileText, MessageSquare, AlertCircle, CheckCircle, Clock, XCircle, Download, FileSpreadsheet, FileJson } from 'lucide-react';

interface Session {
  id: number;
  keyword: string;
  status: string;
  article_count: number;
  overall_summary?: string;
  created_at: string;
  completed_at?: string;
}

interface SessionListResponse {
  sessions: Session[];
  total: number;
  page: number;
  per_page: number;
}

export default function SessionsPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [perPage] = useState(10);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [exportingId, setExportingId] = useState<number | null>(null);
  const [showExportMenu, setShowExportMenu] = useState<number | null>(null);

  const fetchSessions = async (pageNum: number = 1, keyword: string = '') => {
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
        throw new Error('세션 목록을 가져오는데 실패했습니다.');
      }

      const data: SessionListResponse = await response.json();
      setSessions(data.sessions);
      setTotal(data.total);
      setPage(data.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (sessionId: number) => {
    if (!confirm('정말 이 분석 세션을 삭제하시겠습니까? 관련된 모든 기사와 댓글도 함께 삭제됩니다.')) {
      return;
    }

    setDeletingId(sessionId);
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/analysis/${sessionId}`,
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">분석 세션 목록</h1>
          <p className="text-gray-600">저장된 뉴스 분석 기록을 조회하고 관리할 수 있습니다.</p>
        </div>

        {/* Search Bar */}
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
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[300px]">
                        요약
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
                    {sessions.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                          분석 세션이 없습니다.
                        </td>
                      </tr>
                    ) : (
                      sessions.map((session) => (
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
                          <td className="px-6 py-4 text-sm text-gray-500 max-w-[300px]">
                            {session.overall_summary ? (
                              <p className="line-clamp-2 text-gray-600" title={session.overall_summary}>
                                {session.overall_summary}
                              </p>
                            ) : (
                              <span className="text-gray-400 italic">요약 없음</span>
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
    </div>
  );
}

