"use client";

import { useState, useEffect } from 'react';
import { Search, Loader2, History, Clock, X, Trash2 } from 'lucide-react';

interface SearchFormProps {
  onAnalyze: (keyword: string, sources: string[], maxArticles: number) => void;
  isLoading: boolean;
}

interface SearchHistoryItem {
  id: number;
  keyword: string;
  sources: string[];
  max_articles: number;
  search_count: number;
  last_searched_at: string;
}

export default function SearchForm({ onAnalyze, isLoading }: SearchFormProps) {
  const [keyword, setKeyword] = useState('');
  const [sources, setSources] = useState<string[]>(['네이버']);
  const [maxArticles, setMaxArticles] = useState(10);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  // 검색 히스토리 불러오기
  const fetchSearchHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/analysis/search-history?limit=10`);
      if (response.ok) {
        const data = await response.json();
        setSearchHistory(data.history);
      }
    } catch (error) {
      console.error('Failed to fetch search history:', error);
    } finally {
      setHistoryLoading(false);
    }
  };

  // 히스토리 항목 삭제
  const deleteHistoryItem = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/analysis/search-history/${id}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        setSearchHistory(prev => prev.filter(h => h.id !== id));
      }
    } catch (error) {
      console.error('Failed to delete history:', error);
    }
  };

  // 히스토리 항목 클릭 시 검색 폼에 적용
  const applyHistoryItem = (item: SearchHistoryItem) => {
    setKeyword(item.keyword);
    setSources(item.sources);
    setMaxArticles(item.max_articles);
    setShowHistory(false);
  };

  // 컴포넌트 마운트 시 히스토리 로드
  useEffect(() => {
    fetchSearchHistory();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) {
      alert('키워드를 입력해주세요.');
      return;
    }
    if (sources.length === 0) {
      alert('최소 하나의 뉴스 소스를 선택해주세요.');
      return;
    }

    onAnalyze(keyword.trim(), sources, maxArticles);
  };

  const handleSourceChange = (source: string, checked: boolean) => {
    if (checked) {
      setSources([...sources, source]);
    } else {
      setSources(sources.filter(s => s !== source));
    }
  };

  // 현재 지원되는 뉴스 소스 (네이버, 구글만 지원)
  const availableSources: string[] = ['네이버', '구글'];

  return (
    <div className="card p-8 max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Keyword Input */}
        <div className="relative">
          <label htmlFor="keyword" className="block text-sm font-medium text-gray-700 mb-2">
            검색 키워드
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              id="keyword"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onFocus={() => searchHistory.length > 0 && setShowHistory(true)}
              placeholder="예: 삼성전자 || LG전자 (OR 검색)"
              className="input pl-10 pr-10 w-full"
              disabled={isLoading}
            />
            {searchHistory.length > 0 && (
              <button
                type="button"
                onClick={() => setShowHistory(!showHistory)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-blue-500"
              >
                <History className="w-5 h-5" />
              </button>
            )}
          </div>
          
          {/* 검색 히스토리 드롭다운 */}
          {showHistory && searchHistory.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
              <div className="p-2 border-b border-gray-100 flex justify-between items-center">
                <span className="text-xs font-medium text-gray-500 flex items-center">
                  <Clock className="w-3 h-3 mr-1" />
                  최근 검색어
                </span>
                <button
                  type="button"
                  onClick={() => setShowHistory(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              {searchHistory.map((item) => (
                <div
                  key={item.id}
                  onClick={() => applyHistoryItem(item)}
                  className="px-3 py-2 hover:bg-blue-50 cursor-pointer flex justify-between items-center group"
                >
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-900">{item.keyword}</span>
                    <div className="flex items-center text-xs text-gray-500 mt-0.5">
                      <span>{item.sources.join(', ')}</span>
                      <span className="mx-1">•</span>
                      <span>{item.max_articles}개</span>
                      <span className="mx-1">•</span>
                      <span>검색 {item.search_count}회</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => deleteHistoryItem(item.id, e)}
                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 p-1"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
          
          <p className="text-sm text-gray-500 mt-1">
            💡 <strong>OR 검색:</strong> "삼성전자 || LG전자" 또는 "삼성전자 OR LG전자" 형식 지원
          </p>
        </div>

        {/* News Sources */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            뉴스 소스 선택
          </label>
          <div className="grid grid-cols-2 gap-3">
            {availableSources.map((source) => (
              <label 
                key={source} 
                className="flex items-center space-x-2 cursor-pointer p-3 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <input
                  type="checkbox"
                  checked={sources.includes(source)}
                  onChange={(e) => handleSourceChange(source, e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  disabled={isLoading}
                />
                <span className="text-sm font-medium text-gray-700">{source}</span>
              </label>
            ))}
          </div>
          <div className="mt-3 space-y-1">
            <p className="text-sm text-gray-600">
              선택된 소스: <span className="font-medium text-blue-600">{sources.length > 0 ? sources.join(', ') : '없음'}</span>
            </p>
            <p className="text-xs text-gray-500">
              💡 현재 네이버와 구글 뉴스만 지원합니다
            </p>
          </div>
        </div>

        {/* Max Articles */}
        <div>
          <label htmlFor="maxArticles" className="block text-sm font-medium text-gray-700 mb-2">
            최대 기사 수: {maxArticles}개
          </label>
          <input
            type="range"
            id="maxArticles"
            min="5"
            max="50"
            step="5"
            value={maxArticles}
            onChange={(e) => setMaxArticles(Number(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            disabled={isLoading}
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>5개</span>
            <span>25개</span>
            <span>50개</span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            더 많은 기사를 분석할수록 시간이 오래 걸립니다
          </p>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading || !keyword.trim() || sources.length === 0}
          className="btn btn-primary w-full py-3 px-6 text-base font-semibold disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              AI Agent 분석 중...
            </>
          ) : (
            <>
              <Search className="w-5 h-5 mr-2" />
              감정 분석 시작
            </>
          )}
        </button>
      </form>

      {isLoading && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <div className="flex items-center">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-blue-800">AI Agent가 작업 중입니다</p>
              <p className="text-xs text-blue-600">뉴스 수집 및 감정 분석을 진행하고 있습니다...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}