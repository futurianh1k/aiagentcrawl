"""
데이터베이스 모델 정의
SQLAlchemy ORM 모델들
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """사용자 모델 - 한국 정부 IT 보안 규정 준수"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))

    # 계정 상태
    is_active = Column(Boolean, default=True)  # 계정 활성화 여부
    is_verified = Column(Boolean, default=False)  # 이메일 인증 여부
    is_superuser = Column(Boolean, default=False)  # 관리자 여부

    # 보안 관련
    failed_login_attempts = Column(Integer, default=0)  # 로그인 실패 횟수
    locked_until = Column(DateTime(timezone=True), nullable=True)  # 계정 잠금 시간
    last_login_at = Column(DateTime(timezone=True), nullable=True)  # 마지막 로그인 시간
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now())  # 비밀번호 변경 시간

    # 이메일 인증
    email_verification_token = Column(String(255), nullable=True)  # 이메일 인증 토큰
    email_verification_token_expires = Column(DateTime(timezone=True), nullable=True)  # 토큰 만료 시간

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 인덱스 추가 (보안 및 성능 향상)
    __table_args__ = (
        Index('idx_email_active', 'email', 'is_active'),
        Index('idx_locked_until', 'locked_until'),
    )

class AnalysisSession(Base):
    """분석 세션 모델"""
    __tablename__ = "analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # NULL = 비로그인 사용자
    keyword = Column(String(255), nullable=False, index=True)
    sources = Column(Text)  # JSON 문자열로 저장
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    overall_summary = Column(Text)  # 세션 전체 요약본

    # LLM 토큰 사용량 추적
    prompt_tokens = Column(Integer, default=0)  # 프롬프트 토큰
    completion_tokens = Column(Integer, default=0)  # 완료 토큰
    total_tokens = Column(Integer, default=0)  # 총 토큰
    estimated_cost = Column(Float, default=0.0)  # 예상 비용 (USD)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # 관계 설정
    user = relationship("User", backref="analysis_sessions")
    articles = relationship("Article", back_populates="session")

class Article(Base):
    """뉴스 기사 모델"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)  # AI 요약본
    url = Column(String(1000))
    source = Column(String(100))
    published_at = Column(DateTime(timezone=True))
    sentiment_score = Column(Float)  # -1 to 1
    sentiment_label = Column(String(20))  # positive, negative, neutral
    confidence = Column(Float)  # 0 to 1
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    session = relationship("AnalysisSession", back_populates="articles")
    comments = relationship("Comment", back_populates="article")
    media = relationship("ArticleMedia", back_populates="article")

class Comment(Base):
    """댓글 모델"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100))
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))
    confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    article = relationship("Article", back_populates="comments")

class Keyword(Base):
    """키워드 모델"""
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id"), nullable=False)
    keyword = Column(String(100), nullable=False)
    frequency = Column(Integer, default=1)
    sentiment_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SearchHistory(Base):
    """검색 히스토리 모델"""
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), nullable=False, index=True)
    sources = Column(Text)  # JSON 문자열로 저장
    max_articles = Column(Integer, default=10)
    search_count = Column(Integer, default=1)  # 동일 검색어 횟수
    last_searched_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ArticleMedia(Base):
    """기사 미디어 모델 (이미지, 인포그래픽, 테이블)"""
    __tablename__ = "article_media"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, index=True)
    
    # 미디어 타입: image, infographic, table
    media_type = Column(String(20), nullable=False)
    
    # 파일 저장 정보
    file_path = Column(String(500))  # 로컬 파일 경로
    original_url = Column(String(1000))  # 원본 URL
    
    # 메타데이터
    caption = Column(Text)  # 이미지 캡션 또는 테이블 제목
    alt_text = Column(String(500))  # 대체 텍스트
    width = Column(Integer)  # 이미지 너비
    height = Column(Integer)  # 이미지 높이
    file_size = Column(Integer)  # 파일 크기 (bytes)
    mime_type = Column(String(100))  # MIME 타입 (image/jpeg, text/html 등)
    
    # 테이블 전용: HTML 내용 저장
    table_html = Column(Text)  # 테이블의 경우 HTML 직접 저장
    
    # 순서 (기사 내 표시 순서)
    display_order = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    article = relationship("Article", back_populates="media")
