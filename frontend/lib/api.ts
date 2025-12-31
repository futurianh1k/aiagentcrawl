import axios, { AxiosResponse } from 'axios';

// API 기본 설정
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터
api.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// TypeScript 인터페이스 정의
export interface AnalysisRequest {
  keyword: string;
  sources: string[];
  max_articles: number;
}

export interface SentimentDistribution {
  positive: number;
  negative: number;
  neutral: number;
}

export interface KeywordData {
  keyword: string;
  frequency: number;
  sentiment_score: number;
}

export interface ArticleData {
  id: number;
  title: string;
  content: string;
  url?: string;
  source?: string;
  sentiment_score?: number;
  sentiment_label?: string;
  confidence?: number;
  comment_count: number;
}

export interface AnalysisResponse {
  session_id: number;
  keyword: string;
  status: string;
  total_articles: number;
  sentiment_distribution: SentimentDistribution;
  keywords: KeywordData[];
  articles: ArticleData[];
  created_at: string;
  completed_at?: string;
}

// 인증 관련 인터페이스
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: number;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login_at?: string;
}

// 인증 API 함수들
export const authApi = {
  // 회원 가입
  register: async (data: RegisterRequest): Promise<{ message: string; detail?: string }> => {
    const response = await api.post('/api/auth/register', data);
    return response.data;
  },

  // 로그인
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post('/api/auth/login', data);
    return response.data;
  },

  // 현재 사용자 정보 조회
  getCurrentUser: async (token: string): Promise<UserResponse> => {
    const response = await api.get('/api/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },

  // 토큰 갱신
  refreshToken: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await api.post('/api/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  // 이메일 인증
  verifyEmail: async (token: string): Promise<{ message: string }> => {
    const response = await api.post('/api/auth/verify-email', { token });
    return response.data;
  },
};

// API 함수들
export const newsApi = {
  // 뉴스 감정 분석 시작 (선택적 인증)
  analyzeNews: async (data: AnalysisRequest, token?: string): Promise<AnalysisResponse> => {
    const config = token ? {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    } : {};
    const response = await api.post('/api/agents/analyze', data, config);
    return response.data;
  },

  // 분석 결과 조회
  getAnalysisResult: async (sessionId: number): Promise<AnalysisResponse> => {
    const response = await api.get(`/api/analysis/${sessionId}`);
    return response.data;
  },

  // 분석 상태 조회
  getAnalysisStatus: async (sessionId: number): Promise<{ session_id: number; keyword: string; status: string; created_at: string; completed_at?: string }> => {
    const response = await api.get(`/api/agents/status/${sessionId}`);
    return response.data;
  },

  // 분석 세션 목록 조회
  getAnalysisSessions: async (page = 1, perPage = 10, keyword?: string): Promise<{
    sessions: Array<{
      id: number;
      keyword: string;
      status: string;
      article_count: number;
      created_at: string;
      completed_at?: string;
    }>;
    total: number;
    page: number;
    per_page: number;
  }> => {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      ...(keyword && { keyword }),
    });
    const response = await api.get(`/api/analysis/sessions?${params}`);
    return response.data;
  },

  // 분석 세션 삭제
  deleteAnalysisSession: async (sessionId: number): Promise<{ message: string }> => {
    const response = await api.delete(`/api/analysis/${sessionId}`);
    return response.data;
  },
};

export default api;