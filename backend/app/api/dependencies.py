"""
FastAPI 의존성 주입 모듈
데이터베이스 세션 및 서비스 의존성 관리
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.agent_service import NewsAnalysisAgent

def get_agent_service() -> NewsAnalysisAgent:
    """AI Agent 서비스 인스턴스 반환"""
    return NewsAnalysisAgent()

def get_database_session(db: Session = Depends(get_db)) -> Session:
    """데이터베이스 세션 반환"""
    return db
