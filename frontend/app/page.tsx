"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import SearchForm from '@/components/SearchForm';
import ImageSearchForm from '@/components/ImageSearchForm';
import { Search, TrendingUp, BarChart3, Users, Image as ImageIcon } from 'lucide-react';

type SearchType = 'news' | 'image';

export default function HomePage() {
  const router = useRouter();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [searchType, setSearchType] = useState<SearchType>('news');

  const handleAnalysis = async (keyword: string, sources: string[], maxArticles: number) => {
    setIsAnalyzing(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/agents/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          keyword,
          sources,
          max_articles: maxArticles
        })
      });

      if (!response.ok) {
        throw new Error('분석 요청 실패');
      }

      const result = await response.json();
      router.push(`/analyze?session_id=${result.session_id}`);

    } catch (error) {
      console.error('Analysis error:', error);
      alert('분석 중 오류가 발생했습니다.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl md:text-6xl font-bold mb-6 animate-fade-in">
            AI Agent 검색 시스템
          </h1>
          <p className="text-xl md:text-2xl mb-8 animate-slide-up">
            LangChain과 OpenAI를 활용한 뉴스 감정 분석 및 이미지 검색
          </p>
          <div className="flex justify-center items-center space-x-8 text-sm">
            <div className="flex items-center">
              <Search className="w-5 h-5 mr-2" />
              지능형 뉴스 수집
            </div>
            <div className="flex items-center">
              <TrendingUp className="w-5 h-5 mr-2" />
              실시간 감정 분석
            </div>
            <div className="flex items-center">
              <ImageIcon className="w-5 h-5 mr-2" />
              이미지 검색
            </div>
          </div>
        </div>
      </section>

      {/* Search Section */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Search Type Tabs */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setSearchType('news')}
                className={`px-6 py-3 rounded-md font-medium transition-all ${
                  searchType === 'news'
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
                onClick={() => setSearchType('image')}
                className={`px-6 py-3 rounded-md font-medium transition-all ${
                  searchType === 'image'
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

          {/* Search Form */}
          {searchType === 'news' ? (
            <div>
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-gray-900 mb-4">
                  뉴스 감정 분석 시작하기
                </h2>
                <p className="text-lg text-gray-600">
                  키워드를 입력하고 AI Agent가 뉴스를 수집하여 감정을 분석합니다
                </p>
              </div>
              <SearchForm onAnalyze={handleAnalysis} isLoading={isAnalyzing} />
            </div>
          ) : (
            <div>
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-gray-900 mb-4">
                  이미지 검색 시작하기
                </h2>
                <p className="text-lg text-gray-600">
                  프롬프트로 이미지를 검색하거나 샘플 이미지를 업로드하여 유사한 이미지를 찾습니다
                </p>
              </div>
              <ImageSearchForm isLoading={isAnalyzing} />
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">주요 기능</h2>
            <p className="text-lg text-gray-600">AI Agent 기반의 강력한 뉴스 분석 기능들</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="card p-6 text-center hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Search className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">지능형 뉴스 수집</h3>
              <p className="text-gray-600">
                LangChain Agent가 키워드 기반으로 다양한 소스에서 관련 뉴스를 자동 수집합니다.
              </p>
            </div>

            <div className="card p-6 text-center hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">실시간 감정 분석</h3>
              <p className="text-gray-600">
                OpenAI GPT 모델을 활용하여 뉴스와 댓글의 감정을 정확하게 분석합니다.
              </p>
            </div>

            <div className="card p-6 text-center hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">시각화 대시보드</h3>
              <p className="text-gray-600">
                Recharts를 이용한 감정 분포, 키워드 클라우드 등 직관적인 데이터 시각화를 제공합니다.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Stack */}
      <section className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">기술 스택</h2>
            <p className="text-lg text-gray-600">최신 AI 기술과 웹 기술의 결합</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { name: 'LangChain', desc: 'AI Agent 프레임워크' },
              { name: 'OpenAI GPT', desc: '자연어 처리 및 감정 분석' },
              { name: 'FastAPI', desc: '고성능 비동기 백엔드' },
              { name: 'Next.js 14', desc: 'React 기반 풀스택 프레임워크' },
            ].map((tech, index) => (
              <div key={index} className="card p-4 text-center">
                <h4 className="font-semibold text-lg mb-2">{tech.name}</h4>
                <p className="text-sm text-gray-600">{tech.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}