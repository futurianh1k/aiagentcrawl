"""
애플리케이션 설정 모듈
환경 변수를 통한 설정 관리
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""

    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://newsuser:newspass123@localhost:3306/news_sentiment"
    )

    # OpenAI API 설정
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Redis 설정
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # 보안 설정
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

    # CORS 설정
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # 로깅 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # AI Agent 설정
    MAX_ARTICLES_PER_REQUEST: int = 50
    SENTIMENT_ANALYSIS_MODEL: str = "gpt-3.5-turbo"

    class Config:
        env_file = ".env"
        case_sensitive = True

# 전역 설정 인스턴스
settings = Settings()
