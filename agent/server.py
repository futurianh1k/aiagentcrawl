"""
Agent 서비스 서버

Agent를 독립적인 서비스로 실행하기 위한 간단한 HTTP 서버
주로 개발/테스트용이며, 프로덕션에서는 backend에서 직접 import하여 사용
"""

import asyncio
import json
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from common.config import get_config
from common.utils import safe_log, validate_input
from .news_agent import NewsAnalysisAgent

app = FastAPI(
    title="News Analysis Agent Service",
    description="뉴스 분석 Agent 서비스 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent 인스턴스 (전역)
agent_instance: NewsAnalysisAgent = None


class AnalyzeRequest(BaseModel):
    """분석 요청 모델"""
    keyword: str
    sources: List[str] = ["네이버"]
    max_articles: int = 10


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 Agent 초기화"""
    global agent_instance
    try:
        config = get_config()
        agent_instance = NewsAnalysisAgent(config.get_openai_key())
        safe_log("Agent 서비스 시작", level="info")
    except Exception as e:
        safe_log("Agent 초기화 실패", level="error", error=str(e))
        raise


@app.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": "agent",
        "agent_initialized": agent_instance is not None
    }


@app.post("/analyze")
async def analyze_news(request: AnalyzeRequest) -> Dict[str, Any]:
    """뉴스 분석 실행"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent가 초기화되지 않았습니다.")

    try:
        result = await agent_instance.analyze_news_async(
            keyword=request.keyword,
            sources=request.sources,
            max_articles=request.max_articles
        )
        return result
    except Exception as e:
        safe_log("뉴스 분석 오류", level="error", error=str(e))
        raise HTTPException(status_code=500, detail=f"분석 중 오류: {str(e)}")


@app.post("/analyze-sentiment")
async def analyze_sentiment_query(query: str) -> str:
    """자연어 질의를 통한 감성 분석"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent가 초기화되지 않았습니다.")

    try:
        if not validate_input(query, max_length=500):
            raise HTTPException(status_code=400, detail="유효하지 않은 질의입니다.")

        response = agent_instance.analyze_news_sentiment(query)
        return {"response": response}
    except HTTPException:
        raise
    except Exception as e:
        safe_log("감성 분석 오류", level="error", error=str(e))
        raise HTTPException(status_code=500, detail=f"분석 중 오류: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

