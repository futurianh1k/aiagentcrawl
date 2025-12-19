"""
공통 데이터 모델

모든 Lab에서 공통으로 사용하는 데이터 모델을 정의합니다.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class BaseModel:
    """기본 모델 클래스"""

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """딕셔너리에서 생성"""
        return cls(**data)


class SentimentType(Enum):
    """감성 유형 열거형"""
    POSITIVE = "긍정"
    NEGATIVE = "부정"
    NEUTRAL = "중립"


@dataclass
class Comment(BaseModel):
    """댓글 데이터 모델"""
    id: str
    text: str
    author: Optional[str] = None
    timestamp: Optional[datetime] = None
    sentiment: Optional[SentimentType] = None
    confidence: Optional[float] = None


@dataclass
class NewsArticle(BaseModel):
    """뉴스 기사 데이터 모델"""
    url: str
    title: str
    content: str
    comments: List[Comment] = field(default_factory=list)
    published_date: Optional[datetime] = None
    source: Optional[str] = None
    keyword: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (댓글 포함)"""
        result = super().to_dict()
        result["comments"] = [comment.to_dict() for comment in self.comments]
        return result


@dataclass
class SentimentResult(BaseModel):
    """감성 분석 결과 데이터 모델"""
    text: str
    sentiment: SentimentType
    confidence: float
    reason: str
    keywords: List[str] = field(default_factory=list)
    timestamp: Optional[datetime] = None


@dataclass
class TrendAnalysis(BaseModel):
    """동향 분석 결과 데이터 모델"""
    keyword: str
    overall_sentiment: SentimentType
    sentiment_distribution: Dict[str, float] = field(default_factory=dict)
    key_topics: List[str] = field(default_factory=list)
    summary: str = ""
    total_comments: int = 0

