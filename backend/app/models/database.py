"""
데이터베이스 모델 정의
SQLAlchemy ORM 모델들
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class AnalysisSession(Base):
    """분석 세션 모델"""
    __tablename__ = "analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), nullable=False, index=True)
    sources = Column(Text)  # JSON 문자열로 저장
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # 관계 설정
    articles = relationship("Article", back_populates="session")

class Article(Base):
    """뉴스 기사 모델"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
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
