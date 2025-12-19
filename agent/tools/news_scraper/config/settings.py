"""
설정 관리 모듈

2회차 강의: AI 에이전트 기반 뉴스 감성 분석 시스템
Pydantic BaseSettings를 활용한 중앙화된 설정 관리
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, validator
import os
from pathlib import Path


class DatabaseConfig(BaseSettings):
    """
    데이터베이스 설정 클래스

    MySQL 연결 정보와 SQLAlchemy 관련 설정을 관리합니다.
    환경 변수는 DB_ 접두사를 사용합니다.
    """

    # 기본 연결 정보
    host: str = Field(default="localhost", description="MySQL 서버 호스트")
    port: int = Field(default=3306, description="MySQL 서버 포트")
    user: str = Field(default="root", description="데이터베이스 사용자명")
    password: str = Field(default="", description="데이터베이스 비밀번호")
    database: str = Field(default="news_sentiment", description="데이터베이스 이름")

    # 커넥션 풀 설정
    pool_size: int = Field(default=10, description="커넥션 풀 크기")
    max_overflow: int = Field(default=20, description="최대 오버플로우 연결 수")
    pool_timeout: int = Field(default=30, description="커넥션 대기 시간(초)")
    pool_recycle: int = Field(default=3600, description="커넥션 재활용 시간(초)")

    # 성능 최적화 설정
    echo: bool = Field(default=False, description="SQL 쿼리 로깅 여부")
    echo_pool: bool = Field(default=False, description="커넥션 풀 로깅 여부")

    class Config:
        env_prefix = "DB_"
        case_sensitive = False

    @validator('password')
    def validate_password(cls, v):
        """비밀번호 검증: 프로덕션 환경에서는 필수"""
        if not v and os.getenv('ENVIRONMENT') == 'production':
            raise ValueError('프로덕션 환경에서는 데이터베이스 비밀번호가 필수입니다')
        return v

    def get_connection_url(self) -> str:
        """SQLAlchemy 연결 URL 생성"""
        return (
            f"mysql+pymysql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
            f"?charset=utf8mb4"
        )

    def get_engine_kwargs(self) -> Dict[str, Any]:
        """SQLAlchemy 엔진 생성을 위한 kwargs 반환"""
        return {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'echo': self.echo,
            'echo_pool': self.echo_pool,
        }


class CrawlerConfig(BaseSettings):
    """
    크롤러 설정 클래스

    Playwright 브라우저 설정과 크롤링 전략을 관리합니다.
    환경 변수는 CRAWLER_ 접두사를 사용합니다.
    """

    # 브라우저 설정
    browser_type: str = Field(default="chromium", description="사용할 브라우저 (chromium, firefox, webkit)")
    headless: bool = Field(default=True, description="헤드리스 모드 사용 여부")
    slow_mo: int = Field(default=0, description="액션 간 지연시간(ms)")

    # 뷰포트 설정
    viewport_width: int = Field(default=1920, description="뷰포트 너비")
    viewport_height: int = Field(default=1080, description="뷰포트 높이")
    device_scale_factor: float = Field(default=1.0, description="디바이스 스케일 팩터")

    # 타임아웃 설정
    page_timeout: int = Field(default=30000, description="페이지 로드 타임아웃(ms)")
    navigation_timeout: int = Field(default=30000, description="네비게이션 타임아웃(ms)")
    wait_timeout: int = Field(default=10000, description="요소 대기 타임아웃(ms)")

    # Stealth 모드 설정
    user_agent: Optional[str] = Field(default=None, description="사용자 정의 User-Agent")
    extra_http_headers: Dict[str, str] = Field(default_factory=dict, description="추가 HTTP 헤더")
    java_script_enabled: bool = Field(default=True, description="JavaScript 활성화")

    # 동시성 설정
    max_concurrent_pages: int = Field(default=5, description="최대 동시 페이지 수")
    max_concurrent_contexts: int = Field(default=3, description="최대 동시 컨텍스트 수")

    # 재시도 설정
    max_retries: int = Field(default=3, description="최대 재시도 횟수")
    retry_delay: float = Field(default=1.0, description="재시도 간격(초)")
    exponential_backoff: bool = Field(default=True, description="지수 백오프 사용 여부")

    class Config:
        env_prefix = "CRAWLER_"
        case_sensitive = False

    @validator('browser_type')
    def validate_browser_type(cls, v):
        """지원되는 브라우저 타입 검증"""
        supported_browsers = ['chromium', 'firefox', 'webkit']
        if v not in supported_browsers:
            raise ValueError(f'지원되는 브라우저: {supported_browsers}')
        return v

    def get_browser_args(self) -> List[str]:
        """브라우저 실행 인자 생성"""
        args = []
        if self.headless:
            args.append('--headless=new')
        args.extend([
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',  # 성능 최적화
        ])
        return args

    def get_viewport_config(self) -> Dict[str, Any]:
        """뷰포트 설정 반환"""
        return {
            'width': self.viewport_width,
            'height': self.viewport_height,
            'device_scale_factor': self.device_scale_factor,
        }


class AppConfig(BaseSettings):
    """
    애플리케이션 전체 설정 클래스

    로깅, 환경, API 키 등 전반적인 앱 설정을 관리합니다.
    환경 변수는 APP_ 접두사를 사용합니다.
    """

    # 환경 설정
    environment: str = Field(default="development", description="실행 환경 (development, staging, production)")
    debug: bool = Field(default=True, description="디버그 모드")
    log_level: str = Field(default="INFO", description="로그 레벨")

    # 로깅 설정
    log_file_path: Optional[str] = Field(default=None, description="로그 파일 경로")
    log_max_size: int = Field(default=10, description="로그 파일 최대 크기(MB)")
    log_backup_count: int = Field(default=5, description="로그 백업 파일 수")

    # API 키 설정
    firecrawl_api_key: Optional[str] = Field(default=None, description="Firecrawl API 키")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API 키")

    # 성능 설정
    batch_size: int = Field(default=1000, description="배치 처리 크기")
    worker_count: int = Field(default=4, description="워커 프로세스 수")
    memory_limit: int = Field(default=1024, description="메모리 제한(MB)")

    # 보안 설정
    secret_key: str = Field(default="your-secret-key-here", description="암호화 시크릿 키")
    allowed_hosts: List[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"], description="허용된 호스트")

    class Config:
        env_prefix = "APP_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator('environment')
    def validate_environment(cls, v):
        """환경 값 검증"""
        valid_envs = ['development', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f'유효한 환경: {valid_envs}')
        return v

    @validator('log_level')
    def validate_log_level(cls, v):
        """로그 레벨 검증"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'유효한 로그 레벨: {valid_levels}')
        return v.upper()

    def is_production(self) -> bool:
        """프로덕션 환경 여부 확인"""
        return self.environment == 'production'

    def get_log_config(self) -> Dict[str, Any]:
        """로깅 설정 딕셔너리 반환"""
        config = {
            'level': self.log_level,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        }

        if self.log_file_path:
            config.update({
                'filename': self.log_file_path,
                'maxBytes': self.log_max_size * 1024 * 1024,
                'backupCount': self.log_backup_count,
            })

        return config


class Settings:
    """
    통합 설정 관리자

    모든 설정 클래스를 통합하여 관리하는 싱글톤 클래스입니다.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.db = DatabaseConfig()
            self.crawler = CrawlerConfig()
            self.app = AppConfig()
            self._initialized = True

    def reload(self):
        """설정 재로드"""
        self.db = DatabaseConfig()
        self.crawler = CrawlerConfig()
        self.app = AppConfig()
        print("설정이 성공적으로 재로드되었습니다.")

    def validate_all(self) -> Dict[str, bool]:
        """모든 설정 검증"""
        results = {}

        try:
            # 데이터베이스 설정 검증
            self.db.get_connection_url()
            results['database'] = True
        except Exception as e:
            results['database'] = False
            print(f"데이터베이스 설정 오류: {e}")

        try:
            # 크롤러 설정 검증
            self.crawler.get_browser_args()
            results['crawler'] = True
        except Exception as e:
            results['crawler'] = False
            print(f"크롤러 설정 오류: {e}")

        try:
            # 앱 설정 검증
            self.app.get_log_config()
            results['app'] = True
        except Exception as e:
            results['app'] = False
            print(f"앱 설정 오류: {e}")

        return results

    def print_config_summary(self):
        """설정 요약 출력"""
        print("\n=== 설정 요약 ===")
        print(f"환경: {self.app.environment}")
        print(f"디버그 모드: {self.app.debug}")
        print(f"데이터베이스: {self.db.host}:{self.db.port}/{self.db.database}")
        print(f"브라우저: {self.crawler.browser_type} (헤드리스: {self.crawler.headless})")
        print(f"최대 동시 페이지: {self.crawler.max_concurrent_pages}")
        print(f"배치 크기: {self.app.batch_size}")
        print("================\n")


# 전역 설정 인스턴스
settings = Settings()

# 하위 호환성을 위한 별칭
db_config = settings.db
crawler_config = settings.crawler  
app_config = settings.app
