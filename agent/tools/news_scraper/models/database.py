"""
데이터베이스 모델 모듈

2회차 강의: AI 에이전트 기반 뉴스 감성 분석 시스템
SQLAlchemy ORM을 활용한 데이터 모델 정의 및 관리
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
from contextlib import contextmanager
import json

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, 
    Boolean, Float, ForeignKey, Index, UniqueConstraint,
    JSON, BigInteger, SmallInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.dialects.mysql import MEDIUMTEXT, LONGTEXT

from config.settings import settings

Base = declarative_base()


class Article(Base):
    """
    뉴스 기사 테이블

    각 뉴스 기사의 메타데이터와 내용을 저장합니다.
    감성 분석 결과와 크롤링 메타데이터도 포함합니다.
    """

    __tablename__ = 'articles'

    # 기본 키 및 식별자
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='기사 고유 ID')
    external_id = Column(String(255), unique=True, nullable=False, comment='외부 시스템 기사 ID')

    # 기사 메타데이터
    title = Column(Text, nullable=False, comment='기사 제목')
    content = Column(LONGTEXT, nullable=False, comment='기사 본문')
    summary = Column(MEDIUMTEXT, nullable=True, comment='기사 요약')

    # 출처 및 URL 정보
    source_name = Column(String(100), nullable=False, comment='언론사명')
    source_category = Column(String(50), nullable=True, comment='언론사 카테고리')
    original_url = Column(Text, nullable=False, comment='원문 URL')

    # 시간 정보
    published_at = Column(DateTime(timezone=True), nullable=False, comment='기사 발행일시')
    crawled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment='크롤링 일시')

    # 분류 정보
    category = Column(String(50), nullable=True, comment='기사 카테고리')
    tags = Column(JSON, nullable=True, comment='태그 목록 (JSON 배열)')

    # 감성 분석 결과
    sentiment_score = Column(Float, nullable=True, comment='감성 점수 (-1.0 ~ 1.0)')
    sentiment_label = Column(String(20), nullable=True, comment='감성 라벨 (positive, negative, neutral)')
    sentiment_confidence = Column(Float, nullable=True, comment='감성 분석 신뢰도 (0.0 ~ 1.0)')

    # 크롤링 메타데이터
    crawl_method = Column(String(50), nullable=True, comment='크롤링 방법 (playwright, firecrawl 등)')
    crawl_success = Column(Boolean, default=True, comment='크롤링 성공 여부')
    crawl_error_message = Column(Text, nullable=True, comment='크롤링 오류 메시지')

    # 통계 정보
    view_count = Column(Integer, default=0, comment='조회수')
    like_count = Column(Integer, default=0, comment='좋아요 수')
    share_count = Column(Integer, default=0, comment='공유 수')

    # 상태 관리
    status = Column(String(20), default='active', comment='기사 상태 (active, deleted, hidden)')
    is_processed = Column(Boolean, default=False, comment='감성 분석 처리 완료 여부')

    # 생성/수정 시간
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment='레코드 생성일시')
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment='레코드 수정일시')

    # 관계 정의
    comments = relationship("Comment", back_populates="article", cascade="all, delete-orphan")
    keywords = relationship("Keyword", back_populates="article", cascade="all, delete-orphan")

    # 인덱스 정의
    __table_args__ = (
        Index('idx_external_id', 'external_id'),
        Index('idx_published_at', 'published_at'),
        Index('idx_source_name', 'source_name'),
        Index('idx_category', 'category'),
        Index('idx_sentiment_label', 'sentiment_label'),
        Index('idx_crawled_at', 'crawled_at'),
        Index('idx_status', 'status'),
        Index('idx_is_processed', 'is_processed'),
        Index('idx_source_published', 'source_name', 'published_at'),  # 복합 인덱스
        {'comment': '뉴스 기사 테이블 - 감성 분석 대상 기사 저장'}
    )

    def to_dict(self) -> Dict[str, Any]:
        """모델 인스턴스를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'external_id': self.external_id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'source_name': self.source_name,
            'original_url': self.original_url,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'category': self.category,
            'tags': self.tags,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'sentiment_confidence': self.sentiment_confidence,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'share_count': self.share_count,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def update_sentiment(self, score: float, label: str, confidence: float):
        """감성 분석 결과 업데이트"""
        self.sentiment_score = score
        self.sentiment_label = label
        self.sentiment_confidence = confidence
        self.is_processed = True
        self.updated_at = datetime.now(timezone.utc)

    def add_tags(self, new_tags: List[str]):
        """태그 추가"""
        if self.tags is None:
            self.tags = []

        # 기존 태그와 중복되지 않는 태그만 추가
        existing_tags = set(self.tags)
        unique_new_tags = [tag for tag in new_tags if tag not in existing_tags]
        self.tags.extend(unique_new_tags)
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', source='{self.source_name}')>"


class Comment(Base):
    """
    댓글 테이블

    기사에 달린 댓글과 대댓글을 저장합니다.
    감성 분석과 스팸 필터링 결과도 포함합니다.
    """

    __tablename__ = 'comments'

    # 기본 키 및 식별자
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='댓글 고유 ID')
    external_id = Column(String(255), nullable=False, comment='외부 시스템 댓글 ID')

    # 관계 정보
    article_id = Column(BigInteger, ForeignKey('articles.id', ondelete='CASCADE'), nullable=False, comment='소속 기사 ID')
    parent_id = Column(BigInteger, ForeignKey('comments.id', ondelete='CASCADE'), nullable=True, comment='상위 댓글 ID (대댓글의 경우)')

    # 댓글 내용
    content = Column(MEDIUMTEXT, nullable=False, comment='댓글 내용')
    author_name = Column(String(100), nullable=True, comment='작성자명')
    author_id = Column(String(100), nullable=True, comment='작성자 ID')

    # 감성 분석 결과
    sentiment_score = Column(Float, nullable=True, comment='감성 점수 (-1.0 ~ 1.0)')
    sentiment_label = Column(String(20), nullable=True, comment='감성 라벨 (positive, negative, neutral)')
    sentiment_confidence = Column(Float, nullable=True, comment='감성 분석 신뢰도')

    # 스팸 및 품질 관리
    is_spam = Column(Boolean, default=False, comment='스팸 여부')
    spam_confidence = Column(Float, nullable=True, comment='스팸 판정 신뢰도')
    toxicity_score = Column(Float, nullable=True, comment='독성 점수 (0.0 ~ 1.0)')

    # 통계 정보
    like_count = Column(Integer, default=0, comment='좋아요 수')
    dislike_count = Column(Integer, default=0, comment='싫어요 수')
    reply_count = Column(Integer, default=0, comment='답글 수')

    # 시간 정보
    posted_at = Column(DateTime(timezone=True), nullable=False, comment='댓글 작성일시')
    crawled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment='크롤링 일시')

    # 상태 관리
    status = Column(String(20), default='active', comment='댓글 상태')
    is_processed = Column(Boolean, default=False, comment='감성 분석 처리 여부')

    # 생성/수정 시간
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment='레코드 생성일시')
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment='레코드 수정일시')

    # 관계 정의
    article = relationship("Article", back_populates="comments")
    replies = relationship("Comment", cascade="all, delete-orphan", remote_side=[id])

    # 인덱스 정의
    __table_args__ = (
        Index('idx_article_id', 'article_id'),
        Index('idx_parent_id', 'parent_id'),
        Index('idx_posted_at', 'posted_at'),
        Index('idx_sentiment_label', 'sentiment_label'),
        Index('idx_is_spam', 'is_spam'),
        Index('idx_status', 'status'),
        Index('idx_article_posted', 'article_id', 'posted_at'),  # 복합 인덱스
        UniqueConstraint('external_id', 'article_id', name='uq_external_article'),
        {'comment': '댓글 테이블 - 기사별 댓글 및 감성 분석 결과 저장'}
    )

    def to_dict(self) -> Dict[str, Any]:
        """모델 인스턴스를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'external_id': self.external_id,
            'article_id': self.article_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'author_name': self.author_name,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'is_spam': self.is_spam,
            'like_count': self.like_count,
            'reply_count': self.reply_count,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'status': self.status
        }

    def update_sentiment(self, score: float, label: str, confidence: float):
        """감성 분석 결과 업데이트"""
        self.sentiment_score = score
        self.sentiment_label = label
        self.sentiment_confidence = confidence
        self.is_processed = True
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_spam(self, confidence: float = 1.0):
        """스팸으로 표시"""
        self.is_spam = True
        self.spam_confidence = confidence
        self.status = 'hidden'
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<Comment(id={self.id}, article_id={self.article_id}, content='{self.content[:30]}...')>"


class Keyword(Base):
    """
    키워드 테이블

    기사에서 추출된 키워드와 그 중요도를 저장합니다.
    NLP 분석 결과와 트렌드 분석에 활용됩니다.
    """

    __tablename__ = 'keywords'

    # 기본 키 및 식별자
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='키워드 고유 ID')

    # 관계 정보
    article_id = Column(BigInteger, ForeignKey('articles.id', ondelete='CASCADE'), nullable=False, comment='소속 기사 ID')

    # 키워드 정보
    keyword = Column(String(200), nullable=False, comment='키워드')
    keyword_type = Column(String(50), nullable=True, comment='키워드 타입 (entity, topic, emotion 등)')

    # 중요도 및 점수
    importance_score = Column(Float, nullable=False, default=0.0, comment='중요도 점수 (0.0 ~ 1.0)')
    tf_idf_score = Column(Float, nullable=True, comment='TF-IDF 점수')
    frequency = Column(Integer, nullable=False, default=1, comment='기사 내 등장 빈도')

    # 감성 정보
    sentiment_contribution = Column(Float, nullable=True, comment='감성에 대한 기여도')

    # 위치 정보
    first_position = Column(Integer, nullable=True, comment='첫 번째 등장 위치')
    positions = Column(JSON, nullable=True, comment='모든 등장 위치 (JSON 배열)')

    # 메타데이터
    extraction_method = Column(String(50), nullable=True, comment='추출 방법 (regex, nlp, manual)')
    confidence = Column(Float, nullable=True, comment='추출 신뢰도')

    # 생성/수정 시간
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment='레코드 생성일시')
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment='레코드 수정일시')

    # 관계 정의
    article = relationship("Article", back_populates="keywords")

    # 인덱스 정의
    __table_args__ = (
        Index('idx_article_id', 'article_id'),
        Index('idx_keyword', 'keyword'),
        Index('idx_keyword_type', 'keyword_type'),
        Index('idx_importance_score', 'importance_score'),
        Index('idx_article_keyword', 'article_id', 'keyword'),  # 복합 인덱스
        UniqueConstraint('article_id', 'keyword', name='uq_article_keyword'),
        {'comment': '키워드 테이블 - 기사별 추출 키워드 및 중요도 저장'}
    )

    def to_dict(self) -> Dict[str, Any]:
        """모델 인스턴스를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'article_id': self.article_id,
            'keyword': self.keyword,
            'keyword_type': self.keyword_type,
            'importance_score': self.importance_score,
            'tf_idf_score': self.tf_idf_score,
            'frequency': self.frequency,
            'sentiment_contribution': self.sentiment_contribution,
            'extraction_method': self.extraction_method,
            'confidence': self.confidence
        }

    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword='{self.keyword}', importance={self.importance_score})>"


class DatabaseManager:
    """
    데이터베이스 연결 및 세션 관리자

    SQLAlchemy 엔진과 세션을 관리하고,
    트랜잭션 처리와 연결 풀링을 담당합니다.
    """

    def __init__(self, connection_url: Optional[str] = None):
        """
        DatabaseManager 초기화

        Args:
            connection_url: 데이터베이스 연결 URL (None일 경우 설정에서 자동 생성)
        """
        self.connection_url = connection_url or settings.db.get_connection_url()
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._initialize()

    def _initialize(self):
        """엔진과 세션 팩토리 초기화"""
        try:
            # SQLAlchemy 엔진 생성
            self.engine = create_engine(
                self.connection_url,
                poolclass=QueuePool,
                **settings.db.get_engine_kwargs()
            )

            # 세션 팩토리 생성
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )

            print(f"데이터베이스 연결이 성공적으로 초기화되었습니다: {self.engine.url}")

        except Exception as e:
            print(f"데이터베이스 초기화 오류: {e}")
            raise

    def create_tables(self, drop_existing: bool = False):
        """
        데이터베이스 테이블 생성

        Args:
            drop_existing: 기존 테이블 삭제 후 생성 여부
        """
        try:
            if drop_existing:
                Base.metadata.drop_all(bind=self.engine)
                print("기존 테이블이 삭제되었습니다.")

            Base.metadata.create_all(bind=self.engine)
            print("데이터베이스 테이블이 성공적으로 생성되었습니다.")

        except Exception as e:
            print(f"테이블 생성 오류: {e}")
            raise

    @contextmanager
    def get_session(self):
        """
        데이터베이스 세션 컨텍스트 매니저

        자동으로 트랜잭션을 관리하고 세션을 정리합니다.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"데이터베이스 트랜잭션 오류: {e}")
            raise
        finally:
            session.close()

    def get_session_direct(self) -> Session:
        """
        직접 세션 객체 반환

        수동으로 세션을 관리해야 하는 경우 사용합니다.
        """
        return self.SessionLocal()

    def test_connection(self) -> bool:
        """
        데이터베이스 연결 테스트

        Returns:
            bool: 연결 성공 여부
        """
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
                print("데이터베이스 연결 테스트 성공")
                return True
        except Exception as e:
            print(f"데이터베이스 연결 테스트 실패: {e}")
            return False

    def get_table_info(self) -> Dict[str, Any]:
        """
        테이블 정보 조회

        Returns:
            Dict: 테이블별 레코드 수 및 메타데이터
        """
        info = {}
        try:
            with self.get_session() as session:
                # Article 테이블 정보
                article_count = session.query(Article).count()
                info['articles'] = {
                    'count': article_count,
                    'processed': session.query(Article).filter(Article.is_processed == True).count(),
                    'latest': session.query(Article.published_at).order_by(Article.published_at.desc()).first()
                }

                # Comment 테이블 정보
                comment_count = session.query(Comment).count()
                info['comments'] = {
                    'count': comment_count,
                    'processed': session.query(Comment).filter(Comment.is_processed == True).count(),
                    'spam': session.query(Comment).filter(Comment.is_spam == True).count()
                }

                # Keyword 테이블 정보
                keyword_count = session.query(Keyword).count()
                info['keywords'] = {
                    'count': keyword_count,
                    'unique_keywords': session.query(Keyword.keyword).distinct().count()
                }

        except Exception as e:
            print(f"테이블 정보 조회 오류: {e}")

        return info

    def close(self):
        """데이터베이스 연결 종료"""
        if self.engine:
            self.engine.dispose()
            print("데이터베이스 연결이 종료되었습니다.")


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()

# 하위 호환성을 위한 함수들
def get_session():
    """세션 컨텍스트 매니저 반환"""
    return db_manager.get_session()

def create_tables(drop_existing: bool = False):
    """테이블 생성"""
    return db_manager.create_tables(drop_existing)

def test_connection() -> bool:
    """연결 테스트"""
    return db_manager.test_connection()
