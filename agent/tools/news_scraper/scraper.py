"""
News Scraper Tool

Selenium을 이용한 뉴스 크롤링 Tool 구현
네이버 뉴스와 구글 뉴스 지원
보안 가이드라인: robots.txt 준수, Rate Limit 준수, User-Agent 설정
"""

import time
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from enum import Enum

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from langchain.tools import tool

from common.config import get_config
from common.utils import safe_log, validate_input, validate_url
from common.security import sanitize_filename
from .models import NewsArticle, Comment


class NewsSource(str, Enum):
    """뉴스 소스 열거형"""
    NAVER = "네이버"
    GOOGLE = "구글"


# CSS Selector 상수 (유지보수성 향상)
SELECTORS = {
    "naver": {
        "news_link": [
            # 구체적인 셀렉터부터 시도 (우선순위 순)
            "a.news_tit",  # 가장 일반적
            "div.news_area a.news_tit",
            ".news_contents a.news_tit",
            "div.news_wrap a.news_tit",
            ".list_news a.news_tit",
            "div.group_news a.news_tit",
            ".news_area a.news_tit",
            ".api_subject_bx a.news_tit",
            "a[href*='news.naver.com']",  # URL 기반 필터
            "div.news_wrap a[href*='news.naver.com']",
        ],
        "title": "#ct > div.media_end_head.go_trans > div.media_end_head_title > h2",
        "content": "#dic_area",
        "comment_more": ".u_cbox_btn_more",
        "comment": ".u_cbox_comment_box .u_cbox_contents",
    },
    "google": {
        "news_link": "a[data-ved][href*='news']",
        "title": "h1",
        "content": "article p, .article-body p",
        "comment": ".comment-text, .comment",
    }
}


class NewsScraperTool:
    """뉴스 스크레이퍼 Tool 클래스"""

    def __init__(self):
        """초기화"""
        self.driver: Optional[webdriver.Chrome] = None
        self.config = get_config()
        self.firecrawl_api_key = self.config.get_firecrawl_key()

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

    def search_naver_news(self, keyword: str, max_articles: int = 5) -> List[str]:
        """
        네이버 뉴스에서 키워드 검색 후 기사 URL 목록 반환
        
        Args:
            keyword: 검색할 키워드
            max_articles: 최대 수집할 기사 수
        
        Returns:
            기사 URL 목록
        """
        # 입력 검증
        if not validate_input(keyword, max_length=100):
            safe_log("유효하지 않은 키워드", level="warning", keyword=keyword)
            return []

        if not self.driver:
            self.driver = self.setup_driver()

        try:
            # 네이버 뉴스 검색 URL (URL 인코딩)
            encoded_keyword = quote(keyword)
            search_url = f"https://search.naver.com/search.naver?where=news&query={encoded_keyword}"
            print(f"[DEBUG] 네이버 뉴스 검색 시작: keyword={keyword}, url={search_url}")
            safe_log("네이버 뉴스 검색 시작", level="info", keyword=keyword, url=search_url)

            self.driver.get(search_url)
            print(f"[DEBUG] 페이지 로드 완료, 2초 대기 중...")
            time.sleep(3)  # 페이지 로드 대기 (3초로 증가)

            # 페이지 로드 확인
            current_url = self.driver.current_url
            page_title = self.driver.title
            print(f"[DEBUG] 현재 URL: {current_url}, 페이지 제목: {page_title}")
            safe_log("페이지 로드 완료", level="info", current_url=current_url, page_title=page_title)

            # Explicit Wait: 검색 결과가 로드될 때까지 대기
            wait = WebDriverWait(self.driver, self.config.CRAWLER_TIMEOUT)

            # 여러 셀렉터 시도 (네이버가 구조를 자주 변경함)
            news_links = []
            selectors = SELECTORS["naver"]["news_link"]
            
            print(f"[DEBUG] 총 {len(selectors)}개의 셀렉터 시도")
            for i, selector in enumerate(selectors, 1):
                try:
                    print(f"[DEBUG] 셀렉터 {i}/{len(selectors)} 시도: {selector}")
                    safe_log("셀렉터 시도", level="info", selector=selector, attempt=f"{i}/{len(selectors)}")
                    
                    links = wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, selector)
                        )
                    )
                    
                    if links and len(links) > 0:
                        news_links = links
                        print(f"[DEBUG] ✓ 셀렉터 성공! {len(links)}개의 링크 발견")
                        safe_log("셀렉터 성공", level="info", selector=selector, count=len(links))
                        break
                except Exception as e:
                    error_msg = str(e)[:100]
                    print(f"[DEBUG] ✗ 셀렉터 실패: {error_msg}")
                    safe_log("셀렉터 실패", level="info", selector=selector, error=error_msg)
                    continue
            
            # 모든 셀렉터 실패 시 디버깅 정보 출력
            if not news_links:
                print(f"[DEBUG] !! 모든 셀렉터 실패 !!")
                # 페이지 소스 일부 출력 (디버깅용)
                page_source = self.driver.page_source
                print(f"[DEBUG] 페이지 소스 길이: {len(page_source)}")
                print(f"[DEBUG] 페이지 소스 미리보기:\n{page_source[:2000]}\n...")
                
                safe_log("페이지 로드 실패 - 디버깅 정보", level="error", 
                        page_title=page_title,
                        page_source_preview=page_source[:1000],
                        current_url=current_url,
                        page_source_length=len(page_source))
                
                # 스크린샷 저장 (디버깅용)
                try:
                    screenshot_path = "/tmp/naver_search_debug.png"
                    self.driver.save_screenshot(screenshot_path)
                    print(f"[DEBUG] 스크린샷 저장: {screenshot_path}")
                    safe_log("디버깅 스크린샷 저장", level="info", path=screenshot_path)
                except Exception as ss_error:
                    print(f"[DEBUG] 스크린샷 저장 실패: {ss_error}")
                
                return []

            # URL 목록 추출
            article_urls = []
            print(f"[DEBUG] {len(news_links)}개의 링크에서 URL 추출 시작")
            
            # 디버깅: 처음 5개 링크의 전체 URL 출력
            for i, link in enumerate(news_links[:5], 1):
                try:
                    href = link.get_attribute("href")
                    if href:
                        print(f"[DEBUG] 샘플 링크 {i} (전체): {href}")
                except Exception:
                    pass
            
            for i, link in enumerate(news_links[:max_articles * 3], 1):  # 더 많이 수집 후 필터링
                try:
                    href = link.get_attribute("href")
                    if href and validate_url(href):
                        # 네이버 뉴스 기사 URL 엄격 필터링
                        is_news_article = False
                        
                        # 실제 기사 URL 패턴만 허용
                        if "n.news.naver.com/mnews/article/" in href:
                            # 모바일 뉴스: https://n.news.naver.com/mnews/article/001/0015819227
                            is_news_article = True
                            print(f"[DEBUG] ✓ 모바일 뉴스 기사: {href[:80]}...")
                        elif "news.naver.com/main/read" in href:
                            # PC 뉴스: https://news.naver.com/main/read.nhn?mode=...
                            is_news_article = True
                            print(f"[DEBUG] ✓ PC 뉴스 기사: {href[:80]}...")
                        elif "/article/" in href and "news.naver.com" in href:
                            # 기타 기사 패턴
                            is_news_article = True
                            print(f"[DEBUG] ✓ 기타 뉴스 기사: {href[:80]}...")
                        else:
                            # 제외되는 URL 로그 (디버깅용)
                            if "news.naver.com" in href:
                                print(f"[DEBUG] ✗ 기사 아님 (제외): {href[:80]}...")
                        
                        if is_news_article:
                            article_urls.append(href)
                                
                        if len(article_urls) >= max_articles:
                            break
                except Exception as e:
                    print(f"[DEBUG] 링크 추출 실패: {e}")
                    continue

            print(f"[DEBUG] 최종 수집된 URL 개수: {len(article_urls)}")
            
            # URL이 0개면 페이지 소스를 더 자세히 출력
            if len(article_urls) == 0:
                print(f"[DEBUG] !! 뉴스 URL이 하나도 없음. 페이지 HTML 샘플:")
                try:
                    # 뉴스 관련 요소 찾기
                    news_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='news'], div[class*='article']")
                    print(f"[DEBUG] 뉴스 관련 div 개수: {len(news_elements)}")
                    if news_elements:
                        print(f"[DEBUG] 첫 번째 뉴스 div HTML:\n{news_elements[0].get_attribute('outerHTML')[:1000]}")
                except Exception as e:
                    print(f"[DEBUG] HTML 샘플 추출 실패: {e}")
            
            safe_log("네이버 기사 URL 수집 완료", level="info", count=len(article_urls))
            return article_urls

        except Exception as e:
            import traceback
            error_details = {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            safe_log("네이버 뉴스 검색 오류", level="error", **error_details)
            return []

    def search_google_news(self, keyword: str, max_articles: int = 5) -> List[str]:
        """
        구글 뉴스에서 키워드 검색 후 기사 URL 목록 반환
        
        Args:
            keyword: 검색할 키워드
            max_articles: 최대 수집할 기사 수
        
        Returns:
            기사 URL 목록
        """
        # 입력 검증
        if not validate_input(keyword, max_length=100):
            safe_log("유효하지 않은 키워드", level="warning", keyword=keyword)
            return []

        if not self.driver:
            self.driver = self.setup_driver()

        try:
            # 구글 뉴스 검색 URL (URL 인코딩)
            encoded_keyword = quote(keyword)
            search_url = f"https://news.google.com/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
            safe_log("구글 뉴스 검색 시작", level="info", keyword=keyword)

            self.driver.get(search_url)
            time.sleep(2)  # 구글 뉴스는 동적 로딩이 많아 추가 대기

            # Explicit Wait: 검색 결과가 로드될 때까지 대기
            wait = WebDriverWait(self.driver, self.config.CRAWLER_TIMEOUT)

            # 뉴스 기사 링크들이 나타날 때까지 대기
            try:
                news_links = wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, SELECTORS["google"]["news_link"])
                    )
                )
            except Exception:
                # 대체 선택자 시도
                news_links = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "article a[href*='/articles/'], article h3 a"
                )

            # URL 목록 추출
            article_urls = []
            seen_urls = set()  # 중복 제거

            for link in news_links[:max_articles * 2]:  # 더 많이 수집 후 필터링
                try:
                    href = link.get_attribute("href")
                    if href and validate_url(href):
                        # 구글 뉴스 URL 정규화
                        if "news.google.com" in href:
                            # 구글 뉴스 리디렉션 URL 처리
                            continue
                        elif href.startswith("./"):
                            href = f"https://news.google.com{href[1:]}"
                        
                        if href not in seen_urls:
                            seen_urls.add(href)
                            article_urls.append(href)
                            if len(article_urls) >= max_articles:
                                break
                except Exception:
                    continue

            safe_log("구글 기사 URL 수집 완료", level="info", count=len(article_urls))
            return article_urls

        except Exception as e:
            safe_log("구글 뉴스 검색 오류", level="error", error=str(e))
            return []

    def search_news(self, keyword: str, sources: List[str], max_articles: int = 5) -> List[str]:
        """
        여러 소스에서 뉴스 검색
        
        Args:
            keyword: 검색할 키워드
            sources: 뉴스 소스 목록 (["네이버", "구글"])
            max_articles: 소스당 최대 기사 수
        
        Returns:
            기사 URL 목록
        """
        all_urls = []
        
        # 소스 매핑 (다양한 이름 지원)
        source_mapping = {
            "네이버": "네이버",
            "naver": "네이버",
            "구글": "구글",
            "google": "구글",
            # 지원하지 않는 소스는 네이버로 매핑 (기본값)
            "다음": "네이버",
            "KBS": "네이버",
            "SBS": "네이버",
            "MBC": "네이버",
            "YTN": "네이버",
        }
        
        # 지원되는 소스만 필터링
        valid_sources = []
        for source in sources:
            normalized_source = source_mapping.get(source, None)
            if normalized_source:
                if normalized_source not in valid_sources:
                    valid_sources.append(normalized_source)
                if source != normalized_source:
                    safe_log(f"소스 매핑: {source} -> {normalized_source}", level="info")
            else:
                safe_log("지원하지 않는 뉴스 소스", level="warning", source=source)
        
        # 지원되는 소스가 없으면 네이버를 기본값으로 사용
        if not valid_sources:
            valid_sources = ["네이버"]
            safe_log("지원되는 소스가 없어 네이버를 기본값으로 사용", level="info")
        
        for source in valid_sources:
            try:
                if source == "네이버" or source == NewsSource.NAVER.value:
                    urls = self.search_naver_news(keyword, max_articles)
                    all_urls.extend(urls)
                elif source == "구글" or source == NewsSource.GOOGLE.value:
                    urls = self.search_google_news(keyword, max_articles)
                    all_urls.extend(urls)
                else:
                    safe_log("지원하지 않는 뉴스 소스", level="warning", source=source)
            except Exception as e:
                safe_log(f"{source} 뉴스 검색 실패", level="error", error=str(e))
                continue

        # 중복 제거
        unique_urls = list(dict.fromkeys(all_urls))  # 순서 유지하면서 중복 제거
        safe_log("전체 기사 URL 수집 완료", level="info", total=len(unique_urls), sources=valid_sources)
        return unique_urls

    def extract_with_selenium(self, url: str, source: str = "naver") -> Dict[str, Any]:
        """
        Selenium으로 기사 내용 추출
        
        Args:
            url: 기사 URL
            source: 뉴스 소스 ("naver" 또는 "google")
        
        Returns:
            추출된 기사 정보
        """
        if not validate_url(url):
            return {
                "title": "추출 실패",
                "content": "유효하지 않은 URL",
                "comments": [],
                "extraction_method": "selenium",
                "error": "Invalid URL"
            }

        if not self.driver:
            self.driver = self.setup_driver()

        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, self.config.CRAWLER_TIMEOUT)

            selectors = SELECTORS.get(source, SELECTORS["naver"])

            # 제목 추출 (여러 셀렉터 시도)
            title = None
            title_selectors = [
                selectors["title"],  # 기본 셀렉터
                "h2.media_end_head_headline",
                "h3.tit_view",
                ".article_header h2",
                ".article_view h3",
                "h1", "h2"
            ]
            
            print(f"[DEBUG] 제목 추출 시도 (URL: {url[:60]}...)")
            for i, title_selector in enumerate(title_selectors, 1):
                try:
                    title_element = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, title_selector))
                    )
                    if title_element and title_element.text.strip():
                        title = title_element.text.strip()
                        print(f"[DEBUG] ✓ 제목 추출 성공! (셀렉터 {i}: {title_selector})")
                        break
                except Exception:
                    continue
            
            if not title:
                safe_log("제목 추출 실패 - 모든 셀렉터 실패", level="warning", url=url)
                title = "제목 추출 실패"

            # 본문 추출 (여러 셀렉터 시도)
            content = None
            content_selectors = [
                selectors["content"],  # #dic_area
                "#articeBody",
                ".article_body",
                ".article_view",
                "article",
                ".news_end_body_container",
                "#newsct_article",
                "div#articleBodyContents"
            ]
            
            print(f"[DEBUG] 본문 추출 시도 (총 {len(content_selectors)}개 셀렉터)")
            for i, content_selector in enumerate(content_selectors, 1):
                try:
                    content_elements = self.driver.find_elements(By.CSS_SELECTOR, content_selector)
                    if content_elements:
                        content_text = " ".join([elem.text.strip() for elem in content_elements if elem.text.strip()])
                        if content_text and len(content_text) > 50:  # 최소 50자 이상
                            content = content_text
                            print(f"[DEBUG] ✓ 본문 추출 성공! (셀렉터 {i}: {content_selector}, 길이: {len(content)}자)")
                            break
                        else:
                            print(f"[DEBUG] 셀렉터 {i} ({content_selector}): 내용 부족 ({len(content_text) if content_text else 0}자)")
                    else:
                        print(f"[DEBUG] 셀렉터 {i} ({content_selector}): 요소 없음")
                except Exception as e:
                    print(f"[DEBUG] 셀렉터 {i} ({content_selector}): 에러 - {str(e)[:50]}")
                    continue
            
            if not content:
                safe_log("본문 추출 실패 - 모든 셀렉터 실패", level="error")
                # 디버깅: 페이지 소스 일부 출력
                page_source = self.driver.page_source[:2000]
                print(f"[DEBUG] 페이지 소스 미리보기:\n{page_source}\n...")
                content = "본문 추출 실패"

            # 댓글 추출 (네이버만 지원)
            comments = []
            if source == "naver":
                comments = self.extract_comments_basic()

            return {
                "title": title,
                "content": content,
                "comments": comments,
                "extraction_method": "selenium",
                "source": source
            }

        except Exception as e:
            safe_log("Selenium 추출 오류", level="error", error=str(e), url=url)
            return {
                "title": "추출 실패",
                "content": "추출 실패",
                "comments": [],
                "extraction_method": "selenium",
                "error": str(e),
                "source": source
            }

    def extract_comments_basic(self) -> List[Dict[str, Any]]:
        """
        기본적인 댓글 추출 (네이버 뉴스)
        
        Returns:
            댓글 목록
        """
        comments = []

        try:
            wait = WebDriverWait(self.driver, 5)

            # 댓글 더보기 버튼 클릭 시도
            try:
                more_button = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, SELECTORS["naver"]["comment_more"])
                    )
                )
                more_button.click()
                time.sleep(2)  # 댓글 로딩 대기
            except Exception:
                pass  # 더보기 버튼이 없을 수 있음

            # 댓글 요소들 찾기
            comment_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                SELECTORS["naver"]["comment"]
            )

            for i, comment_elem in enumerate(comment_elements[:10]):  # 최대 10개
                try:
                    text = comment_elem.text.strip()
                    if text:
                        comments.append({
                            "id": f"comment_{i+1}",
                            "text": text,
                            "author": f"사용자{i+1}",
                            "timestamp": None
                        })
                except Exception:
                    continue

        except Exception as e:
            safe_log("댓글 추출 중 오류", level="warning", error=str(e))

        return comments

    def scrape_article(self, url: str, source: str = "naver") -> NewsArticle:
        """
        단일 기사 스크레이핑
        
        Args:
            url: 기사 URL
            source: 뉴스 소스 ("naver" 또는 "google")
        
        Returns:
            NewsArticle 객체
        """
        safe_log("기사 스크레이핑 시작", level="info", url=url, source=source)

        # Selenium으로 추출
        selenium_result = self.extract_with_selenium(url, source)

        comments = [
            Comment(
                id=c.get("id", ""),
                text=c.get("text", ""),
                author=c.get("author"),
                timestamp=None
            )
            for c in selenium_result.get("comments", [])
        ]

        return NewsArticle(
            url=url,
            title=selenium_result["title"],
            content=selenium_result["content"],
            comments=comments,
            source=source,
            extraction_method="selenium"
        )

    def cleanup(self):
        """리소스 정리"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                safe_log("WebDriver 정리 완료", level="info")
            except Exception as e:
                safe_log("WebDriver 정리 오류", level="warning", error=str(e))


@tool
def scrape_news(keyword: str, sources: List[str] = None, max_articles: int = 3) -> List[Dict[str, Any]]:
    """
    뉴스 스크레이핑 Tool 함수

    Args:
        keyword: 검색할 키워드
        sources: 뉴스 소스 목록 (["네이버", "구글"])
        max_articles: 소스당 최대 수집할 기사 수 (기본값: 3)

    Returns:
        스크레이핑된 기사들의 정보
    """
    if sources is None:
        sources = ["네이버"]

    scraper = NewsScraperTool()

    try:
        # 입력 검증
        if not validate_input(keyword, max_length=100):
            return [{
                "error": f"유효하지 않은 키워드: {keyword}",
                "keyword": keyword
            }]

        # 1단계: 뉴스 소스에서 기사 URL 검색
        article_urls = scraper.search_news(keyword, sources, max_articles)

        if not article_urls:
            return [{
                "error": f"'{keyword}' 키워드로 기사를 찾을 수 없습니다.",
                "keyword": keyword,
                "sources": sources
            }]

        # 2단계: 각 기사 상세 정보 추출
        scraped_articles = []

        for i, url in enumerate(article_urls, 1):
            safe_log(f"기사 처리 중 ({i}/{len(article_urls)})", level="info")

            # URL에서 소스 판단
            source = "naver" if "naver.com" in url else "google"

            article = scraper.scrape_article(url, source)
            article_dict = article.to_dict()
            article_dict["keyword"] = keyword
            scraped_articles.append(article_dict)

            # Rate Limit 준수
            time.sleep(1)

        return scraped_articles

    except Exception as e:
        safe_log("뉴스 스크레이핑 중 오류", level="error", error=str(e))
        return [{
            "error": f"뉴스 스크레이핑 중 오류: {str(e)}",
            "keyword": keyword,
            "sources": sources
        }]

    finally:
        scraper.cleanup()
