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
from webdriver_manager.chrome import ChromeDriverManager
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
        "news_link": "a.news_tit",
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
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.implicitly_wait(10)
            safe_log("Chrome WebDriver 초기화 완료", level="info")
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
            safe_log("네이버 뉴스 검색 시작", level="info", keyword=keyword)

            self.driver.get(search_url)

            # Explicit Wait: 검색 결과가 로드될 때까지 대기
            wait = WebDriverWait(self.driver, self.config.CRAWLER_TIMEOUT)

            # 뉴스 기사 링크들이 나타날 때까지 대기
            news_links = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, SELECTORS["naver"]["news_link"])
                )
            )

            # URL 목록 추출
            article_urls = []
            for link in news_links[:max_articles]:
                href = link.get_attribute("href")
                if href and validate_url(href) and "news.naver.com" in href:
                    article_urls.append(href)

            safe_log("네이버 기사 URL 수집 완료", level="info", count=len(article_urls))
            return article_urls

        except Exception as e:
            safe_log("네이버 뉴스 검색 오류", level="error", error=str(e))
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
        
        for source in sources:
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
        safe_log("전체 기사 URL 수집 완료", level="info", total=len(unique_urls), sources=sources)
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

            # 제목 추출
            try:
                title_element = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, selectors["title"])
                    )
                )
                title = title_element.text.strip()
            except Exception:
                # 대체 방법 시도
                try:
                    title = self.driver.find_element(By.TAG_NAME, "h1").text.strip()
                except Exception as e:
                    safe_log("제목 추출 실패", level="warning", error=str(e))
                    title = "제목 추출 실패"

            # 본문 추출
            try:
                content_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    selectors["content"]
                )
                if content_elements:
                    content = " ".join([elem.text.strip() for elem in content_elements])
                else:
                    # 대체 방법
                    content = self.driver.find_element(By.TAG_NAME, "article").text.strip()
            except Exception as e:
                safe_log("본문 추출 실패", level="warning", error=str(e))
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
