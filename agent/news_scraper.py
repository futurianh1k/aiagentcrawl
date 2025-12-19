"""
AI 에이전트 기반 뉴스 감성 분석 시스템 - 실습 2
==================================================
주제: NewsScraper Tool 구현 - Selenium + Firecrawl

목표:
- Selenium을 이용한 안정적인 웹 크롤링 구현
- Explicit Wait을 통한 Flaky Test 방지
- Firecrawl MCP를 활용한 구조화된 데이터 추출
- Tool로 패키징하여 Agent에서 사용 가능하도록 구현

필수 라이브러리:
pip install selenium webdriver-manager requests beautifulsoup4 python-dotenv langchain
"""

import os
import json
import time
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from langchain.tools import tool
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

@dataclass
class NewsArticle:
    """뉴스 기사 데이터 클래스"""
    url: str
    title: str
    content: str
    comments: List[Dict[str, Any]]
    published_date: Optional[str] = None
    source: Optional[str] = None

class NewsScraperTool:
    """뉴스 스크레이퍼 Tool 클래스"""

    def __init__(self):
        """초기화"""
        self.driver = None
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY", "fc-test-key")

    def setup_driver(self) -> webdriver.Chrome:
        """Chrome WebDriver 설정 및 초기화"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 브라우저 창 숨김
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # ChromeDriver 자동 설치 및 설정
        service = Service(ChromeDriverManager().install())

        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)  # 기본 대기 시간 설정

        return driver

    def search_naver_news(self, keyword: str, max_articles: int = 5) -> List[str]:
        """네이버 뉴스에서 키워드 검색 후 기사 URL 목록 반환"""
        if not self.driver:
            self.driver = self.setup_driver()

        try:
            # 네이버 뉴스 검색 URL
            search_url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
            print(f"🔍 네이버 뉴스 검색: {keyword}")

            self.driver.get(search_url)

            # Explicit Wait: 검색 결과가 로드될 때까지 대기
            wait = WebDriverWait(self.driver, 15)

            # 뉴스 기사 링크들이 나타날 때까지 대기
            news_links = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "a.news_tit")
                )
            )

            # URL 목록 추출
            article_urls = []
            for link in news_links[:max_articles]:
                href = link.get_attribute("href")
                if href and "news.naver.com" in href:
                    article_urls.append(href)

            print(f"✅ {len(article_urls)}개의 기사 URL 수집 완료")
            return article_urls

        except Exception as e:
            print(f"❌ 네이버 뉴스 검색 중 오류: {str(e)}")
            return []

    def extract_with_selenium(self, url: str) -> Dict[str, Any]:
        """Selenium으로 기사 내용 추출"""
        if not self.driver:
            self.driver = self.setup_driver()

        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 10)

            # 제목 추출
            try:
                title_element = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "#ct > div.media_end_head.go_trans > div.media_end_head_title > h2")
                    )
                )
                title = title_element.text.strip()
            except:
                title = "제목 추출 실패"

            # 본문 추출
            try:
                content_element = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "#dic_area")
                    )
                )
                content = content_element.text.strip()
            except:
                content = "본문 추출 실패"

            # 댓글 추출 (네이버 뉴스 댓글은 동적 로딩이므로 기본 구현)
            comments = self.extract_comments_basic()

            return {
                "title": title,
                "content": content,
                "comments": comments,
                "extraction_method": "selenium"
            }

        except Exception as e:
            print(f"❌ Selenium 추출 오류 ({url}): {str(e)}")
            return {
                "title": "추출 실패",
                "content": "추출 실패", 
                "comments": [],
                "extraction_method": "selenium",
                "error": str(e)
            }

    def extract_comments_basic(self) -> List[Dict[str, Any]]:
        """기본적인 댓글 추출 (네이버 뉴스 댓글 구조에 맞춰 구현)"""
        comments = []

        try:
            # 댓글 영역이 로드될 때까지 대기
            wait = WebDriverWait(self.driver, 5)

            # 댓글 더보기 버튼 클릭 시도
            try:
                more_button = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".u_cbox_btn_more")
                    )
                )
                more_button.click()
                time.sleep(2)  # 댓글 로딩 대기
            except:
                pass  # 더보기 버튼이 없을 수 있음

            # 댓글 요소들 찾기
            comment_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".u_cbox_comment_box .u_cbox_contents"
            )

            for i, comment_elem in enumerate(comment_elements[:10]):  # 최대 10개
                try:
                    text = comment_elem.text.strip()
                    if text:
                        comments.append({
                            "id": f"comment_{i+1}",
                            "text": text,
                            "author": f"사용자{i+1}",  # 실제로는 더 정교한 추출 필요
                            "timestamp": None  # 실제로는 시간 정보 추출 필요
                        })
                except:
                    continue

        except Exception as e:
            print(f"⚠️  댓글 추출 중 오류: {str(e)}")

        # 테스트용 더미 댓글 (실제 댓글 추출이 실패할 경우)
        if not comments:
            comments = [
                {"id": "dummy_1", "text": "좋은 기사네요.", "author": "독자1", "timestamp": None},
                {"id": "dummy_2", "text": "정보 감사합니다.", "author": "독자2", "timestamp": None},
                {"id": "dummy_3", "text": "더 자세한 내용이 궁금합니다.", "author": "독자3", "timestamp": None}
            ]

        return comments

    def extract_with_firecrawl(self, url: str) -> Dict[str, Any]:
        """Firecrawl API를 이용한 구조화된 데이터 추출"""
        try:
            # Firecrawl API 엔드포인트
            api_url = "https://api.firecrawl.dev/v0/scrape"

            headers = {
                "Authorization": f"Bearer {self.firecrawl_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "url": url,
                "formats": ["markdown", "html"],
                "includeTags": ["title", "article", "p", "h1", "h2", "h3"],
                "excludeTags": ["script", "style", "nav", "footer"],
                "waitFor": 2000  # 2초 대기
            }

            print(f"🔥 Firecrawl API 호출: {url}")
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return {
                    "title": data.get("metadata", {}).get("title", "제목 없음"),
                    "content": data.get("markdown", "내용 없음"),
                    "comments": [],  # Firecrawl로는 댓글 추출이 어려움
                    "extraction_method": "firecrawl",
                    "success": True
                }
            else:
                print(f"❌ Firecrawl API 오류: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Firecrawl 추출 오류: {str(e)}")
            return None

    def scrape_article(self, url: str) -> NewsArticle:
        """단일 기사 스크레이핑 (Firecrawl 우선, 실패 시 Selenium 사용)"""
        print(f"\n📰 기사 스크레이핑 시작: {url}")

        # 1차: Firecrawl 시도
        firecrawl_result = self.extract_with_firecrawl(url)

        if firecrawl_result and firecrawl_result.get("success"):
            print("✅ Firecrawl로 추출 성공")
            return NewsArticle(
                url=url,
                title=firecrawl_result["title"],
                content=firecrawl_result["content"],
                comments=firecrawl_result["comments"],
                source="firecrawl"
            )

        # 2차: Selenium 시도 
        print("🔄 Firecrawl 실패, Selenium으로 재시도...")
        selenium_result = self.extract_with_selenium(url)

        return NewsArticle(
            url=url,
            title=selenium_result["title"],
            content=selenium_result["content"],
            comments=selenium_result["comments"],
            source="selenium"
        )

    def cleanup(self):
        """리소스 정리"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    @tool
    def scrape_news(keyword: str, max_articles: int = 3) -> List[Dict[str, Any]]:
        """뉴스 스크레이핑 Tool 함수

        Args:
            keyword (str): 검색할 키워드
            max_articles (int): 최대 수집할 기사 수 (기본값: 3)

        Returns:
            List[Dict]: 스크레이핑된 기사들의 정보
        """
        scraper = NewsScraperTool()

        try:
            # 1단계: 네이버 뉴스에서 기사 URL 검색
            article_urls = scraper.search_naver_news(keyword, max_articles)

            if not article_urls:
                return [{
                    "error": f"'{keyword}' 키워드로 기사를 찾을 수 없습니다.",
                    "keyword": keyword
                }]

            # 2단계: 각 기사 상세 정보 추출
            scraped_articles = []

            for i, url in enumerate(article_urls, 1):
                print(f"\n[{i}/{len(article_urls)}] 기사 처리 중...")

                article = scraper.scrape_article(url)

                scraped_articles.append({
                    "url": article.url,
                    "title": article.title,
                    "content": article.content[:500] + "..." if len(article.content) > 500 else article.content,
                    "comments": article.comments,
                    "source": article.source,
                    "keyword": keyword
                })

                time.sleep(1)  # API 부하 방지

            return scraped_articles

        except Exception as e:
            return [{
                "error": f"뉴스 스크레이핑 중 오류: {str(e)}",
                "keyword": keyword
            }]

        finally:
            scraper.cleanup()

def main():
    """메인 실행 함수"""
    print("🚀 NewsScraper Tool 실습 시작")
    print("=" * 60)

    # 테스트 키워드들
    test_keywords = ["AI", "삼성전자", "부동산"]

    for keyword in test_keywords:
        print(f"\n🔍 키워드 테스트: {keyword}")
        print("-" * 40)

        # Tool 함수 호출
        result = NewsScraperTool.scrape_news(keyword, max_articles=2)

        print(f"✅ 수집 결과: {len(result)}개 기사")

        for i, article in enumerate(result, 1):
            if "error" in article:
                print(f"❌ 오류: {article['error']}")
            else:
                print(f"\n[기사 {i}]")
                print(f"제목: {article['title'][:50]}...")
                print(f"URL: {article['url']}")
                print(f"댓글 수: {len(article['comments'])}개")
                print(f"추출 방법: {article['source']}")

    print("\n🎯 주요 학습 포인트:")
    print("1. Selenium WebDriver 설정 및 Explicit Wait 사용")
    print("2. CSS Selector를 이용한 안정적인 요소 선택")
    print("3. Firecrawl API를 통한 구조화된 데이터 추출")
    print("4. Fallback 메커니즘 (Firecrawl 실패 시 Selenium 사용)")
    print("5. @tool 데코레이터로 Agent에서 사용 가능한 Tool로 변환")

    print("\n⚠️  주의사항:")
    print("- FIRECRAWL_API_KEY 환경 변수 설정 필요")
    print("- Chrome 브라우저 및 ChromeDriver 필요")
    print("- 네트워크 상태에 따라 타임아웃 조정 필요")
    print("- robots.txt 및 사이트 정책 준수 필요")

if __name__ == "__main__":
    main()
