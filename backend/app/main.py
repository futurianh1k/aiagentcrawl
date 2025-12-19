"""
FastAPI 메인 애플리케이션 모듈
AI Agent 기반 뉴스 감정 분석 시스템의 진입점
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.models.database import Base
from app.api.routes import agents, analysis

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="News Sentiment AI Agent System",
    description="LangChain 기반 뉴스 감정 분석 AI Agent API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "News Sentiment AI Agent System",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy"}
