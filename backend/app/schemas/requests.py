"""
Pydantic 스키마 정의
요청/응답 데이터 모델
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    """분석 요청 스키마"""
    keyword: str = Field(..., min_length=1, max_length=100, description="검색할 키워드")
    sources: Optional[List[str]] = Field(default=["네이버", "다음"], description="뉴스 소스 목록")
    max_articles: Optional[int] = Field(default=20, ge=1, le=100, description="최대 기사 수")

class SentimentDistribution(BaseModel):
    """감정 분포 스키마"""
    positive: int = Field(default=0, description="긍정 기사 수")
    negative: int = Field(default=0, description="부정 기사 수") 
    neutral: int = Field(default=0, description="중립 기사 수")

class TimingInfo(BaseModel):
    """성능 측정 정보 스키마"""
    crawling_time: float = Field(default=0.0, description="크롤링 소요 시간(초)")
    sentiment_time: float = Field(default=0.0, description="감성 분석 소요 시간(초)")
    summary_time: float = Field(default=0.0, description="요약 생성 소요 시간(초)")
    total_time: float = Field(default=0.0, description="총 소요 시간(초)")

class TokenUsage(BaseModel):
    """LLM 토큰 사용량 스키마"""
    prompt_tokens: int = Field(default=0, description="프롬프트 토큰 수")
    completion_tokens: int = Field(default=0, description="완료 토큰 수")
    total_tokens: int = Field(default=0, description="총 토큰 수")
    estimated_cost: float = Field(default=0.0, description="예상 비용 (USD)")

class KeywordData(BaseModel):
    """키워드 데이터 스키마"""
    keyword: str = Field(..., description="키워드")
    frequency: int = Field(..., description="빈도수")
    sentiment_score: Optional[float] = Field(default=0.0, description="감정 점수")

class ArticleData(BaseModel):
    """기사 데이터 스키마"""
    id: int
    title: str
    content: str
    summary: Optional[str] = Field(default="", description="AI 요약")
    url: Optional[str]
    source: Optional[str]
    published_at: Optional[datetime]
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    confidence: Optional[float]
    comment_count: int = Field(default=0, description="댓글 수")

class AnalysisResponse(BaseModel):
    """분석 응답 스키마"""
    session_id: int = Field(..., description="분석 세션 ID")
    keyword: str = Field(..., description="분석 키워드")
    status: str = Field(..., description="분석 상태")
    total_articles: int = Field(default=0, description="총 기사 수")
    sentiment_distribution: SentimentDistribution = Field(..., description="감정 분포")
    keywords: List[KeywordData] = Field(default=[], description="키워드 목록")
    articles: List[ArticleData] = Field(default=[], description="기사 목록")
    overall_summary: Optional[str] = Field(default="", description="종합 요약")
    timing: Optional[TimingInfo] = Field(default=None, description="성능 측정 정보")
    token_usage: Optional[TokenUsage] = Field(default=None, description="LLM 토큰 사용량")
    created_at: datetime = Field(..., description="생성 시간")
    completed_at: Optional[datetime] = Field(default=None, description="완료 시간")

class SessionListResponse(BaseModel):
    """세션 목록 응답 스키마"""
    sessions: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int

class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    detail: str = Field(..., description="에러 메시지")
    error_code: Optional[str] = Field(default=None, description="에러 코드")

class UsageStatsResponse(BaseModel):
    """전체 사용량 통계 응답 스키마"""
    total_sessions: int = Field(default=0, description="총 세션 수")
    total_prompt_tokens: int = Field(default=0, description="총 프롬프트 토큰")
    total_completion_tokens: int = Field(default=0, description="총 완료 토큰")
    total_tokens: int = Field(default=0, description="총 토큰 수")
    total_estimated_cost: float = Field(default=0.0, description="총 예상 비용 (USD)")
    
    # 사람이 읽기 쉬운 형식
    total_tokens_formatted: str = Field(default="0", description="토큰 수 (포맷)")
    total_cost_formatted: str = Field(default="$0.00", description="비용 (포맷)")
    
    # Free tier 정보 (OpenAI Free tier: $5.00 기본 제공)
    free_credit_limit: float = Field(default=5.0, description="무료 크레딧 한도 (USD)")
    remaining_credit: float = Field(default=5.0, description="잔여 크레딧 (USD)")
    usage_percentage: float = Field(default=0.0, description="사용률 (%)")
