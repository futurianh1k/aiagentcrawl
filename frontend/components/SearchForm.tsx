"use client";

import { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface SearchFormProps {
  onAnalyze: (keyword: string, sources: string[], maxArticles: number) => void;
  isLoading: boolean;
}

export default function SearchForm({ onAnalyze, isLoading }: SearchFormProps) {
  const [keyword, setKeyword] = useState('');
  const [sources, setSources] = useState<string[]>(['네이버']);
  const [maxArticles, setMaxArticles] = useState(20);

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

  // 지원되는 뉴스 소스 (네이버, 구글만 실제 크롤링 지원, 나머지는 네이버로 매핑)
  const availableSources = ['네이버', '구글'];

  return (
    <div className="card p-8 max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Keyword Input */}
        <div>
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
              placeholder="예: 인공지능, 경제, 정치 등"
              className="input pl-10 w-full"
              disabled={isLoading}
            />
          </div>
          <p className="text-sm text-gray-500 mt-1">
            분석하고자 하는 뉴스 주제의 키워드를 입력하세요
          </p>
        </div>

        {/* News Sources */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            뉴스 소스 선택
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {availableSources.map((source) => (
              <label key={source} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={sources.includes(source)}
                  onChange={(e) => handleSourceChange(source, e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  disabled={isLoading}
                />
                <span className="text-sm text-gray-700">{source}</span>
              </label>
            ))}
          </div>
          <p className="text-sm text-gray-500 mt-2">
            선택된 소스: {sources.length > 0 ? sources.join(', ') : '없음'}
          </p>
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