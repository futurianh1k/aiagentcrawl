"""
Base News Scraper

모든 뉴스 크롤러의 공통 기능을 제공하는 베이스 클래스
WebDriver 설정, 리소스 관리 등 공통 기능 포함
"""

from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from common.config import get_config
from common.utils import safe_log


class BaseNewsScraper:
    """뉴스 크롤러 베이스 클래스"""
    
    def __init__(self):
        """초기화"""
        self.driver: Optional[webdriver.Chrome] = None
        self.config = get_config()
    
    def setup_driver(self) -> webdriver.Chrome:
        """
        Chrome WebDriver 설정 및 초기화
        
        보안 가이드라인: User-Agent 설정, robots.txt 준수
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 브라우저 창 숨김
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-agent={self.config.CRAWLER_USER_AGENT}")

        # ChromeDriver 자동 설치 및 설정
        # ChromeDriverManager의 경로 문제를 근본적으로 해결
        # 모듈 경로를 기준으로 경로를 결정하는 문제를 해결하기 위해
        # sys.modules를 조작하거나 직접 다운로드
        try:
            import os
            import sys
            import subprocess
            import shutil
            import zipfile
            import urllib.request
            
            # 방법 1: 시스템에 설치된 ChromeDriver 사용 시도
            chromedriver_paths = [
                "/usr/local/bin/chromedriver",
                "/usr/bin/chromedriver",
                "/opt/chromedriver/chromedriver",
            ]
            
            driver_path = None
            for path in chromedriver_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    driver_path = path
                    safe_log("시스템 ChromeDriver 사용", level="info", path=driver_path)
                    break
            
            # 방법 2: ChromeDriverManager 사용 (경로 강제 지정)
            # ChromeDriverManager가 모듈 경로를 기준으로 경로를 결정하는 문제를 해결
            if not driver_path:
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    import inspect
                    
                    # 임시 디렉토리 사용
                    temp_dir = "/tmp"
                    wdm_dir = os.path.join(temp_dir, ".wdm")
                    os.makedirs(wdm_dir, exist_ok=True)
                    
                    # 모든 환경 변수 설정 (ChromeDriverManager가 확인하는 모든 경로)
                    env_vars = {
                        'WDM_LOCAL': '1',
                        'WDM_LOG_LEVEL': '0',
                        'HOME': temp_dir,
                        'WDM_PATH': wdm_dir,
                        'USERPROFILE': temp_dir,
                        'XDG_CACHE_HOME': wdm_dir,
                        'XDG_DATA_HOME': wdm_dir,
                        'XDG_CONFIG_HOME': wdm_dir,
                    }
                    for key, value in env_vars.items():
                        os.environ[key] = value
                    
                    # 현재 작업 디렉토리 백업
                    original_cwd = os.getcwd()
                    
                    try:
                        # 임시 디렉토리로 작업 디렉토리 변경
                        os.chdir(temp_dir)
                        
                        # ChromeDriverManager 초기화 및 설치
                        # 모듈 파일 경로를 임시로 변경하여 영향 최소화
                        manager = None
                        try:
                            # path 인자 사용 시도
                            manager = ChromeDriverManager(path=wdm_dir)
                            driver_path = manager.install()
                        except (TypeError, AttributeError) as e:
                            # path 인자 미지원 시 환경 변수만 사용
                            manager = ChromeDriverManager()
                            driver_path = manager.install()
                        
                        # 다운로드된 경로 확인 및 수정
                        if driver_path:
                            # /app/agent/.wdm 경로가 포함되어 있으면 /tmp/.wdm로 복사
                            if '/app/agent/.wdm' in driver_path or '/app/agent' in driver_path:
                                old_path = driver_path
                                if os.path.exists(old_path):
                                    # 상대 경로 추출
                                    if '.wdm' in old_path:
                                        relative_path = old_path.split('.wdm', 1)[1].lstrip('/')
                                    else:
                                        relative_path = os.path.basename(old_path)
                                    
                                    # 새 경로 생성
                                    new_driver_path = os.path.join(wdm_dir, relative_path)
                                    os.makedirs(os.path.dirname(new_driver_path), exist_ok=True)
                                    
                                    # 파일 복사
                                    shutil.copy2(old_path, new_driver_path)
                                    os.chmod(new_driver_path, 0o755)
                                    driver_path = new_driver_path
                                    safe_log("ChromeDriver 경로 수정 완료", level="info", 
                                            old_path=old_path, new_path=new_driver_path)
                                else:
                                    safe_log("원본 ChromeDriver 파일을 찾을 수 없음, 재시도", level="warning", path=old_path)
                                    # 파일이 없으면 다시 시도 (경로 명시)
                                    try:
                                        manager = ChromeDriverManager(path=wdm_dir)
                                        driver_path = manager.install()
                                    except (TypeError, AttributeError):
                                        manager = ChromeDriverManager()
                                        driver_path = manager.install()
                        
                    finally:
                        # 원래 상태로 복원
                        try:
                            os.chdir(original_cwd)
                        except Exception:
                            pass
                            
                except ImportError:
                    safe_log("webdriver-manager를 사용할 수 없음", level="warning")
                    raise RuntimeError("ChromeDriver를 찾을 수 없습니다. webdriver-manager가 필요합니다.")
            
            # ChromeDriver 파일 존재 및 실행 권한 확인
            if not driver_path or not os.path.exists(driver_path):
                raise RuntimeError(f"ChromeDriver를 찾을 수 없습니다: {driver_path}")
            
            # 실행 권한 확인 및 설정
            if not os.access(driver_path, os.X_OK):
                os.chmod(driver_path, 0o755)
            
            # Service 생성 및 WebDriver 초기화
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.implicitly_wait(10)
            safe_log("Chrome WebDriver 초기화 완료", level="info", driver_path=driver_path)
            return driver
        except Exception as e:
            safe_log("Chrome WebDriver 초기화 실패", level="error", error=str(e))
            raise RuntimeError(f"WebDriver 초기화 실패: {e}")

    def cleanup(self):
        """리소스 정리"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                safe_log("WebDriver 정리 완료", level="info")
            except Exception as e:
                safe_log("WebDriver 정리 오류", level="warning", error=str(e))


