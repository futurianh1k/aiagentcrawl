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
