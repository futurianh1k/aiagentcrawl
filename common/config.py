"""
설정 관리 모듈

환경 변수 및 설정을 중앙에서 관리합니다.
보안 가이드라인: API 키는 환경 변수에서만 읽고, 로그에 노출하지 않습니다.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Config:
    """애플리케이션 설정 클래스"""

    # OpenAI 설정
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))

    # Google Gemini 설정
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-pro")

    # Firecrawl 설정
    FIRECRAWL_API_KEY: Optional[str] = os.getenv("FIRECRAWL_API_KEY")

    # 데이터베이스 설정
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME", "news_analysis")

    # 크롤링 설정
    CRAWLER_USER_AGENT: str = os.getenv(
        "CRAWLER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    CRAWLER_TIMEOUT: int = int(os.getenv("CRAWLER_TIMEOUT", "30"))
    CRAWLER_MAX_RETRIES: int = int(os.getenv("CRAWLER_MAX_RETRIES", "3"))

    # 보안 설정
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def validate(cls) -> bool:
        """필수 설정값 검증"""
        errors = []

        # OpenAI API 키는 선택사항 (일부 Lab에서만 필요)
        # if not cls.OPENAI_API_KEY:
        #     errors.append("OPENAI_API_KEY가 설정되지 않았습니다.")

        if errors:
            print("⚠️  설정 오류:")
            for error in errors:
                print(f"   - {error}")
            return False

        return True

    @classmethod
    def get_openai_key(cls) -> Optional[str]:
        """OpenAI API 키 반환 (보안: 로그에 노출하지 않음)"""
        return cls.OPENAI_API_KEY

    @classmethod
    def get_gemini_key(cls) -> Optional[str]:
        """Gemini API 키 반환 (보안: 로그에 노출하지 않음)"""
        return cls.GEMINI_API_KEY

    @classmethod
    def get_firecrawl_key(cls) -> Optional[str]:
        """Firecrawl API 키 반환 (보안: 로그에 노출하지 않음)"""
        return cls.FIRECRAWL_API_KEY


def get_config() -> Config:
    """설정 인스턴스 반환"""
    return Config()

