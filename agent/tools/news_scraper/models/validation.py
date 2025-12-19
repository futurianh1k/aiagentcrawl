"""
데이터 검증 모듈

2회차 강의: AI 에이전트 기반 뉴스 감성 분석 시스템
Pydantic을 활용한 데이터 검증 및 직렬화 모델 정의
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
from enum import Enum
import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator, root_validator, HttpUrl
from pydantic.types import constr, confloat, conint


class SentimentLabel(str, Enum):
    """감성 분석 라벨 열거형"""
    POSITIVE = "positive"
    NEGATIVE = "negative"  
    NEUTRAL = "neutral"


class CrawlMethod(str, Enum):
    """크롤링 방법 열거형"""
    PLAYWRIGHT = "playwright"
    FIRECRAWL = "firecrawl"
    REQUESTS = "requests"
    SELENIUM = "selenium"


class ArticleStatus(str, Enum):
    """기사 상태 열거형"""
    ACTIVE = "active"
    DELETED = "deleted"
    HIDDEN = "hidden"
    PENDING = "pending"


class CommentData(BaseModel):
    """
    댓글 데이터 검증 모델

    크롤링한 댓글 데이터의 유효성을 검증하고
    데이터베이스 저장을 위한 정규화를 수행합니다.
    """

    # 필수 필드
    external_id: constr(min_length=1, max_length=255) = Field(..., description="외부 시스템 댓글 ID")
    content: constr(min_length=1, max_length=50000) = Field(..., description="댓글 내용")
    posted_at: datetime = Field(..., description="댓글 작성일시")

    # 선택 필드
    author_name: Optional[constr(max_length=100)] = Field(None, description="작성자명")
    author_id: Optional[constr(max_length=100)] = Field(None, description="작성자 ID")
    parent_id: Optional[str] = Field(None, description="상위 댓글 ID")

    # 통계 필드
    like_count: conint(ge=0) = Field(0, description="좋아요 수")
    dislike_count: conint(ge=0) = Field(0, description="싫어요 수")
    reply_count: conint(ge=0) = Field(0, description="답글 수")

    # 감성 분석 결과 (선택)
    sentiment_score: Optional[confloat(ge=-1.0, le=1.0)] = Field(None, description="감성 점수")
    sentiment_label: Optional[SentimentLabel] = Field(None, description="감성 라벨")
    sentiment_confidence: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="감성 분석 신뢰도")

    # 스팸 및 품질 관리
    is_spam: bool = Field(False, description="스팸 여부")
    spam_confidence: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="스팸 판정 신뢰도")
    toxicity_score: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="독성 점수")

    # 크롤링 메타데이터
    crawl_method: Optional[CrawlMethod] = Field(None, description="크롤링 방법")
    crawled_at: Optional[datetime] = Field(None, description="크롤링 일시")

    class Config:
        """Pydantic 설정"""
        use_enum_values = True
        validate_assignment = True
        str_strip_whitespace = True

    @validator('content')
    def validate_content(cls, v):
        """댓글 내용 검증 및 정제"""
        if not v or not v.strip():
            raise ValueError('댓글 내용은 필수입니다')

        # HTML 태그 제거 (간단한 정규식)
        v = re.sub(r'<[^>]+>', '', v)

        # 연속된 공백 정규화
        v = re.sub(r'\s+', ' ', v)

        # 앞뒤 공백 제거
        v = v.strip()

        return v

    @validator('posted_at')
    def validate_posted_at(cls, v):
        """작성일시 검증"""
        if v is None:
            raise ValueError('댓글 작성일시는 필수입니다')

        # 미래 날짜 검증
        now = datetime.now(timezone.utc)
        if v > now:
            raise ValueError('댓글 작성일시는 현재 시점보다 미래일 수 없습니다')

        # 너무 오래된 날짜 검증 (10년 이전)
        from datetime import timedelta
        ten_years_ago = now - timedelta(days=3650)
        if v < ten_years_ago:
            raise ValueError('댓글 작성일시가 너무 오래되었습니다')

        return v

    @validator('author_name')
    def validate_author_name(cls, v):
        """작성자명 검증"""
        if v is not None:
            # 특수문자 제거
            v = re.sub(r'[<>"']', '', v)
            v = v.strip()

            # 빈 문자열이면 None 처리
            if not v:
                return None

        return v

    @root_validator
    def validate_sentiment_consistency(cls, values):
        """감성 분석 결과 일관성 검증"""
        score = values.get('sentiment_score')
        label = values.get('sentiment_label')

        if score is not None and label is not None:
            # 점수와 라벨 일관성 검증
            if score > 0.1 and label != SentimentLabel.POSITIVE:
                raise ValueError('양수 감성 점수는 positive 라벨과 일치해야 합니다')
            elif score < -0.1 and label != SentimentLabel.NEGATIVE:
                raise ValueError('음수 감성 점수는 negative 라벨과 일치해야 합니다')
            elif -0.1 <= score <= 0.1 and label != SentimentLabel.NEUTRAL:
                raise ValueError('중성 감성 점수는 neutral 라벨과 일치해야 합니다')

        return values

    def to_db_dict(self) -> Dict[str, Any]:
        """데이터베이스 저장용 딕셔너리로 변환"""
        return {
            'external_id': self.external_id,
            'content': self.content,
            'posted_at': self.posted_at,
            'author_name': self.author_name,
            'author_id': self.author_id,
            'like_count': self.like_count,
            'dislike_count': self.dislike_count,
            'reply_count': self.reply_count,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label.value if self.sentiment_label else None,
            'sentiment_confidence': self.sentiment_confidence,
            'is_spam': self.is_spam,
            'spam_confidence': self.spam_confidence,
            'toxicity_score': self.toxicity_score,
            'crawl_method': self.crawl_method.value if self.crawl_method else None,
            'crawled_at': self.crawled_at or datetime.now(timezone.utc)
        }


class ArticleData(BaseModel):
    """
    기사 데이터 검증 모델

    크롤링한 기사 데이터의 유효성을 검증하고
    데이터베이스 저장을 위한 정규화를 수행합니다.
    """

    # 필수 필드
    external_id: constr(min_length=1, max_length=255) = Field(..., description="외부 시스템 기사 ID")
    title: constr(min_length=1, max_length=5000) = Field(..., description="기사 제목")
    content: constr(min_length=50) = Field(..., description="기사 본문")
    source_name: constr(min_length=1, max_length=100) = Field(..., description="언론사명")
    original_url: HttpUrl = Field(..., description="원문 URL")
    published_at: datetime = Field(..., description="기사 발행일시")

    # 선택 필드
    summary: Optional[constr(max_length=10000)] = Field(None, description="기사 요약")
    source_category: Optional[constr(max_length=50)] = Field(None, description="언론사 카테고리")
    category: Optional[constr(max_length=50)] = Field(None, description="기사 카테고리")
    tags: Optional[List[str]] = Field(None, description="태그 목록")

    # 통계 필드
    view_count: conint(ge=0) = Field(0, description="조회수")
    like_count: conint(ge=0) = Field(0, description="좋아요 수")
    share_count: conint(ge=0) = Field(0, description="공유 수")

    # 감성 분석 결과
    sentiment_score: Optional[confloat(ge=-1.0, le=1.0)] = Field(None, description="감성 점수")
    sentiment_label: Optional[SentimentLabel] = Field(None, description="감성 라벨")
    sentiment_confidence: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="감성 분석 신뢰도")

    # 크롤링 메타데이터
    crawl_method: Optional[CrawlMethod] = Field(None, description="크롤링 방법")
    crawl_success: bool = Field(True, description="크롤링 성공 여부")
    crawl_error_message: Optional[str] = Field(None, description="크롤링 오류 메시지")
    crawled_at: Optional[datetime] = Field(None, description="크롤링 일시")

    # 상태 관리
    status: ArticleStatus = Field(ArticleStatus.ACTIVE, description="기사 상태")

    class Config:
        """Pydantic 설정"""
        use_enum_values = True
        validate_assignment = True
        str_strip_whitespace = True

    @validator('title')
    def validate_title(cls, v):
        """기사 제목 검증 및 정제"""
        if not v or not v.strip():
            raise ValueError('기사 제목은 필수입니다')

        # HTML 태그 제거
        v = re.sub(r'<[^>]+>', '', v)

        # 특수문자 정규화
        v = re.sub(r'[\r\n\t]+', ' ', v)
        v = re.sub(r'\s+', ' ', v)
        v = v.strip()

        return v

    @validator('content')
    def validate_content(cls, v):
        """기사 본문 검증 및 정제"""
        if not v or len(v.strip()) < 50:
            raise ValueError('기사 본문은 최소 50자 이상이어야 합니다')

        # HTML 태그 제거 (본문은 일부 태그 보존 가능)
        # 여기서는 단순화를 위해 모든 태그 제거
        v = re.sub(r'<[^>]+>', '', v)

        # 연속된 공백과 줄바꿈 정규화
        v = re.sub(r'\n\s*\n', '\n\n', v)  # 연속된 빈 줄을 두 줄로 제한
        v = re.sub(r'[ \t]+', ' ', v)  # 연속된 공백을 하나로

        return v.strip()

    @validator('tags')
    def validate_tags(cls, v):
        """태그 검증 및 정제"""
        if v is None:
            return v

        # 빈 태그 제거 및 정제
        cleaned_tags = []
        for tag in v:
            if isinstance(tag, str):
                tag = tag.strip()
                if tag and len(tag) <= 50:  # 태그 길이 제한
                    cleaned_tags.append(tag)

        # 중복 제거
        return list(set(cleaned_tags))

    @validator('published_at')
    def validate_published_at(cls, v):
        """발행일시 검증"""
        if v is None:
            raise ValueError('기사 발행일시는 필수입니다')

        # 미래 날짜 검증
        now = datetime.now(timezone.utc)
        if v > now:
            raise ValueError('기사 발행일시는 현재 시점보다 미래일 수 없습니다')

        return v

    @validator('original_url')
    def validate_url(cls, v):
        """URL 검증"""
        if not v:
            raise ValueError('원문 URL은 필수입니다')

        # URL 구조 검증
        parsed = urlparse(str(v))
        if not parsed.netloc:
            raise ValueError('유효한 URL 형식이 아닙니다')

        return v

    def to_db_dict(self) -> Dict[str, Any]:
        """데이터베이스 저장용 딕셔너리로 변환"""
        return {
            'external_id': self.external_id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'source_name': self.source_name,
            'source_category': self.source_category,
            'original_url': str(self.original_url),
            'published_at': self.published_at,
            'category': self.category,
            'tags': self.tags,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'share_count': self.share_count,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label.value if self.sentiment_label else None,
            'sentiment_confidence': self.sentiment_confidence,
            'crawl_method': self.crawl_method.value if self.crawl_method else None,
            'crawl_success': self.crawl_success,
            'crawl_error_message': self.crawl_error_message,
            'crawled_at': self.crawled_at or datetime.now(timezone.utc),
            'status': self.status.value
        }


class KeywordData(BaseModel):
    """
    키워드 데이터 검증 모델

    기사에서 추출된 키워드의 유효성을 검증하고
    중요도 점수를 정규화합니다.
    """

    # 필수 필드
    keyword: constr(min_length=1, max_length=200) = Field(..., description="키워드")
    importance_score: confloat(ge=0.0, le=1.0) = Field(..., description="중요도 점수")
    frequency: conint(ge=1) = Field(1, description="등장 빈도")

    # 선택 필드
    keyword_type: Optional[str] = Field(None, description="키워드 타입")
    tf_idf_score: Optional[float] = Field(None, description="TF-IDF 점수")
    sentiment_contribution: Optional[confloat(ge=-1.0, le=1.0)] = Field(None, description="감성 기여도")
    first_position: Optional[conint(ge=0)] = Field(None, description="첫 등장 위치")
    positions: Optional[List[int]] = Field(None, description="모든 등장 위치")
    extraction_method: Optional[str] = Field(None, description="추출 방법")
    confidence: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="추출 신뢰도")

    @validator('keyword')
    def validate_keyword(cls, v):
        """키워드 검증 및 정제"""
        if not v or not v.strip():
            raise ValueError('키워드는 필수입니다')

        # 앞뒤 공백 제거 및 정규화
        v = v.strip().lower()

        # 특수문자 제한 검증
        if not re.match(r'^[가-힣a-zA-Z0-9\s\-_.]+$', v):
            raise ValueError('키워드에 허용되지 않는 특수문자가 포함되어 있습니다')

        return v

    @validator('positions')
    def validate_positions(cls, v):
        """등장 위치 검증"""
        if v is not None:
            # 중복 제거 및 정렬
            v = sorted(list(set(v)))

            # 음수 위치 제거
            v = [pos for pos in v if pos >= 0]

        return v

    def to_db_dict(self) -> Dict[str, Any]:
        """데이터베이스 저장용 딕셔너리로 변환"""
        return {
            'keyword': self.keyword,
            'keyword_type': self.keyword_type,
            'importance_score': self.importance_score,
            'tf_idf_score': self.tf_idf_score,
            'frequency': self.frequency,
            'sentiment_contribution': self.sentiment_contribution,
            'first_position': self.first_position,
            'positions': self.positions,
            'extraction_method': self.extraction_method,
            'confidence': self.confidence
        }


class CrawlingRequest(BaseModel):
    """
    크롤링 요청 데이터 모델

    크롤링 작업 요청을 위한 매개변수를 검증합니다.
    """

    # 필수 필드
    target_url: HttpUrl = Field(..., description="크롤링 대상 URL")
    crawl_method: CrawlMethod = Field(CrawlMethod.PLAYWRIGHT, description="크롤링 방법")

    # 선택 필드
    max_pages: conint(ge=1, le=1000) = Field(10, description="최대 크롤링 페이지 수")
    delay_seconds: confloat(ge=0.0, le=60.0) = Field(1.0, description="페이지 간 지연 시간")
    include_comments: bool = Field(True, description="댓글 포함 여부")
    include_images: bool = Field(False, description="이미지 포함 여부")

    # 필터링 옵션
    date_from: Optional[datetime] = Field(None, description="시작 날짜")
    date_to: Optional[datetime] = Field(None, description="종료 날짜")
    keywords: Optional[List[str]] = Field(None, description="필터링 키워드")

    # 고급 옵션
    user_agent: Optional[str] = Field(None, description="사용자 정의 User-Agent")
    headers: Optional[Dict[str, str]] = Field(None, description="추가 HTTP 헤더")
    cookies: Optional[Dict[str, str]] = Field(None, description="쿠키")

    @validator('date_from', 'date_to')
    def validate_dates(cls, v):
        """날짜 검증"""
        if v is not None:
            now = datetime.now(timezone.utc)
            if v > now:
                raise ValueError('날짜는 현재 시점보다 미래일 수 없습니다')
        return v

    @root_validator
    def validate_date_range(cls, values):
        """날짜 범위 검증"""
        date_from = values.get('date_from')
        date_to = values.get('date_to')

        if date_from is not None and date_to is not None:
            if date_from >= date_to:
                raise ValueError('시작 날짜는 종료 날짜보다 이전이어야 합니다')

        return values


class BatchValidationResult(BaseModel):
    """
    배치 검증 결과 모델

    여러 데이터의 일괄 검증 결과를 담는 모델입니다.
    """

    total_count: int = Field(..., description="전체 데이터 수")
    valid_count: int = Field(..., description="유효한 데이터 수")
    invalid_count: int = Field(..., description="무효한 데이터 수")

    valid_data: List[Any] = Field(..., description="유효한 데이터 목록")
    invalid_data: List[Dict[str, Any]] = Field(..., description="무효한 데이터 및 오류 정보")

    success_rate: float = Field(..., description="성공률 (0.0 ~ 1.0)")

    @validator('success_rate', pre=True, always=True)
    def calculate_success_rate(cls, v, values):
        """성공률 자동 계산"""
        total = values.get('total_count', 0)
        valid = values.get('valid_count', 0)

        if total == 0:
            return 0.0

        return valid / total


# 유틸리티 함수들
def validate_comments_batch(comments_data: List[Dict[str, Any]]) -> BatchValidationResult:
    """
    댓글 데이터 일괄 검증

    Args:
        comments_data: 댓글 데이터 리스트

    Returns:
        BatchValidationResult: 검증 결과
    """
    valid_data = []
    invalid_data = []

    for i, comment_dict in enumerate(comments_data):
        try:
            comment = CommentData(**comment_dict)
            valid_data.append(comment)
        except Exception as e:
            invalid_data.append({
                'index': i,
                'data': comment_dict,
                'error': str(e)
            })

    return BatchValidationResult(
        total_count=len(comments_data),
        valid_count=len(valid_data),
        invalid_count=len(invalid_data),
        valid_data=valid_data,
        invalid_data=invalid_data,
        success_rate=0.0  # 자동 계산됨
    )


def validate_articles_batch(articles_data: List[Dict[str, Any]]) -> BatchValidationResult:
    """
    기사 데이터 일괄 검증

    Args:
        articles_data: 기사 데이터 리스트

    Returns:
        BatchValidationResult: 검증 결과
    """
    valid_data = []
    invalid_data = []

    for i, article_dict in enumerate(articles_data):
        try:
            article = ArticleData(**article_dict)
            valid_data.append(article)
        except Exception as e:
            invalid_data.append({
                'index': i,
                'data': article_dict,
                'error': str(e)
            })

    return BatchValidationResult(
        total_count=len(articles_data),
        valid_count=len(valid_data),
        invalid_count=len(invalid_data),
        valid_data=valid_data,
        invalid_data=invalid_data,
        success_rate=0.0  # 자동 계산됨
    )


def sanitize_html_content(content: str) -> str:
    """
    HTML 내용 정제

    Args:
        content: 원본 HTML 내용

    Returns:
        str: 정제된 텍스트
    """
    if not content:
        return ""

    # HTML 태그 제거
    content = re.sub(r'<[^>]+>', '', content)

    # HTML 엔티티 디코딩 (간단한 경우만)
    entity_map = {
        '&amp;': '&',
        '&lt;': '<', 
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' '
    }

    for entity, char in entity_map.items():
        content = content.replace(entity, char)

    # 연속된 공백 정규화
    content = re.sub(r'\s+', ' ', content)

    return content.strip()
