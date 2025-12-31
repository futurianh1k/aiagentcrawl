"use client";

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import ImageGallery from '@/components/ImageGallery';
import ImageDetailModal from '@/components/ImageDetailModal';
import { Loader2, RefreshCw, AlertCircle, Image as ImageIcon, Upload, Search } from 'lucide-react';

interface ImageSearchData {
  session_id: number;
  query: string;
  query_type: string;
  search_operator: string;
  status: string;
  total_results: number;
  results: Array<{
    id: number;
    image_url: string;
    thumbnail_url?: string;
    image_path?: string;
    title?: string;
    source_url?: string;
    source_site?: string;
    width?: number;
    height?: number;
    file_size?: number;
    mime_type?: string;
    similarity_score?: number;
    display_order: number;
  }>;
  created_at: string;
  completed_at?: string;
}

export default function ImageSearchPage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');
  
  const [searchData, setSearchData] = useState<ImageSearchData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<ImageSearchData['results'][0] | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOperator, setSearchOperator] = useState<'AND' | 'OR'>('AND');
  const [maxResults, setMaxResults] = useState(20);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  useEffect(() => {
    if (sessionId) {
      fetchImageSearchResult();
    }
  }, [sessionId]);

  const fetchImageSearchResult = async () => {
    if (!sessionId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/image-search/sessions/${sessionId}`
      );
      
      if (!response.ok) {
        throw new Error('이미지 검색 결과를 불러올 수 없습니다.');
      }
      
      const data = await response.json();
      setSearchData(data);
      
      // 처리 중이면 주기적으로 재조회
      if (data.status === 'processing') {
        setTimeout(() => fetchImageSearchResult(), 3000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleTextSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/image-search/search`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: searchQuery,
            query_type: 'text',
            search_operator: searchOperator,
            max_results: maxResults
          })
        }
      );
      
      if (!response.ok) {
        throw new Error('이미지 검색 요청 실패');
      }
      
      const result = await response.json();
      window.location.href = `/image-search?session_id=${result.session_id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : '검색 중 오류가 발생했습니다.');
      setLoading(false);
    }
  };

  const handleImageUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!uploadedFile) {
      alert('이미지 파일을 선택해주세요.');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      formData.append('query', searchQuery || '유사 이미지 검색');
      formData.append('search_operator', searchOperator);
      formData.append('max_results', maxResults.toString());
      
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/image-search/search/upload`,
        {
          method: 'POST',
          body: formData
        }
      );
      
      if (!response.ok) {
        throw new Error('이미지 업로드 검색 실패');
      }
      
      const result = await response.json();
      window.location.href = `/image-search?session_id=${result.session_id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : '업로드 중 오류가 발생했습니다.');
      setLoading(false);
    }
  };

  if (loading && !searchData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-600" />
          <h2 className="text-2xl font-semibold mb-2">이미지 검색 중...</h2>
          <p className="text-gray-600">AI가 이미지를 검색하고 있습니다.</p>
        </div>
      </div>
    );
  }

  if (error && !searchData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
          <h2 className="text-2xl font-semibold mb-2 text-red-600">오류 발생</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.href = '/image-search'}
            className="btn-primary"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">이미지 검색</h1>
          
          {/* Search Form */}
          <div className="space-y-4">
            <form onSubmit={handleTextSearch} className="flex gap-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="검색어를 입력하세요 (예: 사과 오렌지, 사과 or 오렌지)"
                className="flex-1 input"
                required
              />
              <select
                value={searchOperator}
                onChange={(e) => setSearchOperator(e.target.value as 'AND' | 'OR')}
                className="input w-auto"
              >
                <option value="AND">AND (모두 포함)</option>
                <option value="OR">OR (하나라도 포함)</option>
              </select>
              <input
                type="number"
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value))}
                min="1"
                max="100"
                className="input w-24"
              />
              <button type="submit" className="btn-primary" disabled={loading}>
                <Search className="w-5 h-5 mr-2" />
                검색
              </button>
            </form>
            
            {/* Image Upload Form */}
            <form onSubmit={handleImageUpload} className="flex gap-4 items-center">
              <label className="btn-secondary cursor-pointer">
                <Upload className="w-5 h-5 mr-2" />
                이미지 업로드
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
              </label>
              {uploadedFile && (
                <span className="text-sm text-gray-600">{uploadedFile.name}</span>
              )}
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="추가 검색어 (선택사항)"
                className="flex-1 input"
              />
              <button type="submit" className="btn-primary" disabled={loading || !uploadedFile}>
                유사 이미지 검색
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Results */}
      {searchData && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Search Info */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  검색 결과: {searchData.query}
                </h2>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <span>연산자: {searchData.search_operator}</span>
                  <span>결과 수: {searchData.total_results}개</span>
                  <span>상태: {searchData.status === 'completed' ? '완료' : '처리 중'}</span>
                </div>
              </div>
              {searchData.status === 'processing' && (
                <button
                  onClick={fetchImageSearchResult}
                  className="btn-secondary"
                >
                  <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                  새로고침
                </button>
              )}
            </div>
          </div>

          {/* Image Gallery */}
          {searchData.status === 'completed' && searchData.results.length > 0 ? (
            <ImageGallery
              images={searchData.results}
              onImageClick={(image) => setSelectedImage(image)}
            />
          ) : searchData.status === 'processing' ? (
            <div className="text-center py-12">
              <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-600" />
              <p className="text-gray-600">이미지를 검색하고 있습니다...</p>
            </div>
          ) : (
            <div className="text-center py-12">
              <ImageIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">검색 결과가 없습니다.</p>
            </div>
          )}
        </div>
      )}

      {/* Image Detail Modal */}
      {selectedImage && (
        <ImageDetailModal
          image={selectedImage}
          onClose={() => setSelectedImage(null)}
        />
      )}
    </div>
  );
}
