"""
데이터베이스 연결 및 세션 관리 모듈
SQLAlchemy를 이용한 MySQL 연결
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
