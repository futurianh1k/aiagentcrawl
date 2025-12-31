"""
FastAPI 메인 애플리케이션 모듈
AI Agent 기반 뉴스 감정 분석 시스템의 진입점
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.models.database import Base, ImageSearchSession, ImageSearchResult
from app.api.routes import agents, analysis, media, image_search
from sqlalchemy import inspect

# 데이터베이스 테이블 생성 (테이블이 존재하지 않는 경우에만)
try:
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # 존재하지 않는 테이블만 생성
    for table in Base.metadata.tables.values():
        if table.name not in existing_tables:
            table.create(bind=engine, checkfirst=True)
except Exception as e:
    print(f"테이블 생성 중 경고: {e}")

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
app.include_router(media.router, prefix="/api/media", tags=["media"])
app.include_router(image_search.router, prefix="/api/image-search", tags=["image-search"])

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
