"""
Base News Scraper

모든 뉴스 크롤러의 공통 기능을 제공하는 베이스 클래스
WebDriver 설정, 리소스 관리 등 공통 기능 포함
"""

import os
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
        Dockerfile에서 /usr/local/bin/chromedriver에 설치됨
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 브라우저 창 숨김
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        chrome_options.add_argument(f"--user-agent={self.config.CRAWLER_USER_AGENT}")

        try:
            # Dockerfile에서 설치된 ChromeDriver 경로
            chromedriver_paths = [
                "/usr/local/bin/chromedriver",
                "/usr/bin/chromedriver",
            ]
            
            driver_path = None
            for path in chromedriver_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    driver_path = path
                    print(f"[DEBUG] ChromeDriver 경로: {driver_path}")
                    safe_log("ChromeDriver 사용", level="info", path=driver_path)
                    break
            
            if not driver_path:
                raise RuntimeError("ChromeDriver를 찾을 수 없습니다")
            
            # Service 생성 및 WebDriver 초기화
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # implicitly_wait를 짧게 설정 (3초)
            driver.implicitly_wait(3)
            
            print(f"[DEBUG] Chrome WebDriver 초기화 완료")
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
                print(f"[DEBUG] WebDriver 정리 완료")
                safe_log("WebDriver 정리 완료", level="info")
            except Exception as e:
                safe_log("WebDriver 정리 오류", level="warning", error=str(e))
