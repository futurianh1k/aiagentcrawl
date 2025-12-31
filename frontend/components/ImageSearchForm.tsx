"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Image as ImageIcon, Upload, Search, Loader2 } from 'lucide-react';

interface ImageSearchFormProps {
  isLoading: boolean;
}

export default function ImageSearchForm({ isLoading }: ImageSearchFormProps) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOperator, setSearchOperator] = useState<'AND' | 'OR'>('AND');
  const [maxResults, setMaxResults] = useState(20);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const handleTextSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSearching(true);

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
      router.push(`/image-search?session_id=${result.session_id}`);
    } catch (error) {
      console.error('Image search error:', error);
      alert('이미지 검색 중 오류가 발생했습니다.');
      setIsSearching(false);
    }
  };

  const handleImageUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!uploadedFile) {
      alert('이미지 파일을 선택해주세요.');
      return;
    }

    setIsSearching(true);

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
      router.push(`/image-search?session_id=${result.session_id}`);
    } catch (error) {
      console.error('Image upload search error:', error);
      alert('이미지 업로드 검색 중 오류가 발생했습니다.');
      setIsSearching(false);
    }
  };

  return (
    <div className="card p-8 max-w-2xl mx-auto">
      {/* Text Search Form */}
      <form onSubmit={handleTextSearch} className="space-y-6 mb-8">
        <div>
          <label htmlFor="imageQuery" className="block text-sm font-medium text-gray-700 mb-2">
            검색어 (프롬프트)
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              id="imageQuery"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="예: 사과 오렌지, 사과 or 오렌지"
              className="input pl-10 w-full"
              disabled={isSearching || isLoading}
              required
            />
          </div>
          <p className="text-sm text-gray-500 mt-1">
            💡 AND: "사과 오렌지" → 둘 다 포함, OR: "사과 or 오렌지" → 둘 중 하나만 포함
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              검색 연산자
            </label>
            <select
              value={searchOperator}
              onChange={(e) => setSearchOperator(e.target.value as 'AND' | 'OR')}
              className="input w-full"
              disabled={isSearching || isLoading}
            >
              <option value="AND">AND (모두 포함)</option>
              <option value="OR">OR (하나라도 포함)</option>
            </select>
          </div>

          <div>
            <label htmlFor="maxResults" className="block text-sm font-medium text-gray-700 mb-2">
              최대 결과 수: {maxResults}개
            </label>
            <input
              type="range"
              id="maxResults"
              min="10"
              max="100"
              step="10"
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              disabled={isSearching || isLoading}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isSearching || isLoading || !searchQuery.trim()}
          className="btn btn-primary w-full py-3 px-6 text-base font-semibold disabled:opacity-50"
        >
          {isSearching ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              이미지 검색 중...
            </>
          ) : (
            <>
              <Search className="w-5 h-5 mr-2" />
              이미지 검색 시작
            </>
          )}
        </button>
      </form>

      {/* Divider */}
      <div className="relative my-8">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">또는</span>
        </div>
      </div>

      {/* Image Upload Form */}
      <form onSubmit={handleImageUpload} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            샘플 이미지 업로드
          </label>
          <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              {uploadedFile ? (
                <>
                  <ImageIcon className="w-10 h-10 mb-2 text-purple-600" />
                  <p className="text-sm font-medium text-gray-900">{uploadedFile.name}</p>
                  <p className="text-xs text-gray-500">
                    {(uploadedFile.size / 1024).toFixed(2)} KB
                  </p>
                </>
              ) : (
                <>
                  <Upload className="w-10 h-10 mb-2 text-gray-400" />
                  <p className="text-sm text-gray-500">
                    <span className="font-semibold">클릭하여 이미지 선택</span> 또는 드래그 앤 드롭
                  </p>
                  <p className="text-xs text-gray-500 mt-1">PNG, JPG, GIF, WEBP (최대 10MB)</p>
                </>
              )}
            </div>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
              className="hidden"
              disabled={isSearching || isLoading}
            />
          </label>
        </div>

        <div>
          <label htmlFor="uploadQuery" className="block text-sm font-medium text-gray-700 mb-2">
            추가 검색어 (선택사항)
          </label>
          <input
            type="text"
            id="uploadQuery"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="예: 자연, 실내, 야외 등"
            className="input w-full"
            disabled={isSearching || isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={isSearching || isLoading || !uploadedFile}
          className="btn btn-secondary w-full py-3 px-6 text-base font-semibold disabled:opacity-50"
        >
          {isSearching ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              유사 이미지 검색 중...
            </>
          ) : (
            <>
              <ImageIcon className="w-5 h-5 mr-2" />
              유사 이미지 검색
            </>
          )}
        </button>
      </form>

      {(isSearching || isLoading) && (
        <div className="mt-6 p-4 bg-purple-50 rounded-lg">
          <div className="flex items-center">
            <Loader2 className="w-5 h-5 animate-spin text-purple-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-purple-800">이미지 검색 중입니다</p>
              <p className="text-xs text-purple-600">이미지를 수집하고 있습니다...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
