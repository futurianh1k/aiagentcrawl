"""
Google News Scraper

구글 뉴스 전용 크롤러
구글 뉴스 검색 및 기사 내용 추출 기능 제공
"""

import time
from typing import List, Dict, Any
from urllib.parse import quote

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from common.utils import safe_log, validate_input, validate_url
from .base_scraper import BaseNewsScraper
from .models import NewsArticle, Comment


# 구글 뉴스 CSS Selector 상수
GOOGLE_SELECTORS = {
    "news_link": [
        "article a[href*='/articles/']",
        "article h3 a",
        "a[data-ved][href*='news']",
        "div[data-ved] a[href*='news']",
        ".JtKRv a",
        "h3 a[href*='news']",
    ],
    "title": [
        "h1",
        "h2.article-title",
        ".article-title h1",
        "article h1",
        ".headline",
    ],
    "content": [
        "article p",
        ".article-body p",
        ".article-content p",
        "#article-body p",
        ".story-body p",
        "div[itemprop='articleBody'] p",
    ],
}


class GoogleNewsScraper(BaseNewsScraper):
    """구글 뉴스 전용 크롤러"""
    
    def search_news(self, keyword: str, max_articles: int = 5) -> List[str]:
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
            print(f"[DEBUG] 구글 뉴스 검색 시작: keyword={keyword}, url={search_url}")
            safe_log("구글 뉴스 검색 시작", level="info", keyword=keyword, url=search_url)

            self.driver.get(search_url)
            print(f"[DEBUG] 페이지 로드 완료, 3초 대기 중...")
            time.sleep(3)  # 구글 뉴스는 동적 로딩이 많아 추가 대기

            # 페이지 로드 확인
            current_url = self.driver.current_url
            page_title = self.driver.title
            print(f"[DEBUG] 현재 URL: {current_url}, 페이지 제목: {page_title}")
            safe_log("페이지 로드 완료", level="info", current_url=current_url, page_title=page_title)

            # Explicit Wait: 검색 결과가 로드될 때까지 대기
            wait = WebDriverWait(self.driver, self.config.CRAWLER_TIMEOUT)

            # 여러 셀렉터 시도 (구글 뉴스 구조 변경 대응)
            news_links = []
            selectors = GOOGLE_SELECTORS["news_link"]
            
            print(f"[DEBUG] 총 {len(selectors)}개의 셀렉터 시도")
            for i, selector in enumerate(selectors, 1):
                try:
                    print(f"[DEBUG] 셀렉터 {i}/{len(selectors)} 시도: {selector}")
                    safe_log("셀렉터 시도", level="info", selector=selector, attempt=f"{i}/{len(selectors)}")
                    
                    # 요소가 나타날 때까지 대기
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
                
                safe_log("구글 뉴스 페이지 로드 실패 - 디버깅 정보", level="error", 
                        page_title=page_title,
                        page_source_preview=page_source[:1000],
                        current_url=current_url,
                        page_source_length=len(page_source))
                
                # 스크린샷 저장 (디버깅용)
                try:
                    screenshot_path = "/tmp/google_search_debug.png"
                    self.driver.save_screenshot(screenshot_path)
                    print(f"[DEBUG] 스크린샷 저장: {screenshot_path}")
                    safe_log("디버깅 스크린샷 저장", level="info", path=screenshot_path)
                except Exception as ss_error:
                    print(f"[DEBUG] 스크린샷 저장 실패: {ss_error}")
                
                return []

            # URL 목록 추출
            article_urls = []
            seen_urls = set()  # 중복 제거
            print(f"[DEBUG] {len(news_links)}개의 링크에서 URL 추출 시작")
            
            for i, link in enumerate(news_links[:max_articles * 5], 1):  # 더 많이 수집 후 필터링
                try:
                    # href 속성과 실제 링크 URL 모두 확인
                    href = link.get_attribute("href")
                    if not href:
                        # data-ved 속성이 있는 경우 클릭하여 실제 URL 얻기 시도
                        try:
                            link.click()
                            time.sleep(1)  # 리디렉션 대기
                            href = self.driver.current_url
                            # 뒤로 가기
                            self.driver.back()
                            time.sleep(0.5)
                        except Exception:
                            continue
                    
                    if href and validate_url(href):
                        # 구글 뉴스 URL 정규화
                        if href.startswith("./"):
                            # 상대 경로 처리
                            href = f"https://news.google.com{href[1:]}"
                        
                        # 구글 뉴스 리디렉션 URL 처리
                        # news.google.com/articles/... 형태는 실제 기사 URL로 리디렉션됨
                        # 클릭하여 실제 URL을 얻거나, data-ved 속성으로 실제 URL 추출 시도
                        if "news.google.com" in href and "/articles/" in href:
                            # 구글 뉴스 리디렉션 URL - 클릭하여 실제 URL 얻기
                            try:
                                # 링크를 새 탭에서 열기
                                original_url = self.driver.current_url
                                link.click()
                                time.sleep(2)  # 리디렉션 대기
                                actual_url = self.driver.current_url
                                
                                # 실제 기사 URL인지 확인 (구글 뉴스가 아닌 외부 사이트)
                                if "news.google.com" not in actual_url and actual_url != original_url:
                                    if actual_url not in seen_urls:
                                        seen_urls.add(actual_url)
                                        article_urls.append(actual_url)
                                        print(f"[DEBUG] ✓ 기사 URL 수집 (리디렉션): {actual_url[:80]}...")
                                        
                                        if len(article_urls) >= max_articles:
                                            break
                                
                                # 원래 페이지로 돌아가기
                                self.driver.back()
                                time.sleep(1)
                            except Exception as e:
                                print(f"[DEBUG] 리디렉션 URL 처리 실패: {e}")
                                continue
                        elif "news.google.com" not in href:
                            # 이미 외부 사이트 URL인 경우
                            if href not in seen_urls:
                                seen_urls.add(href)
                                article_urls.append(href)
                                print(f"[DEBUG] ✓ 기사 URL 수집: {href[:80]}...")
                                
                                if len(article_urls) >= max_articles:
                                    break
                except Exception as e:
                    print(f"[DEBUG] 링크 추출 실패: {e}")
                    continue

            print(f"[DEBUG] 최종 수집된 URL 개수: {len(article_urls)}")
            
            if len(article_urls) == 0:
                print(f"[DEBUG] !! 뉴스 URL이 하나도 없음. 페이지 HTML 샘플:")
                try:
                    # 뉴스 관련 요소 찾기
                    news_elements = self.driver.find_elements(By.CSS_SELECTOR, "article, div[class*='article']")
                    print(f"[DEBUG] 뉴스 관련 요소 개수: {len(news_elements)}")
                    if news_elements:
                        print(f"[DEBUG] 첫 번째 뉴스 요소 HTML:\n{news_elements[0].get_attribute('outerHTML')[:1000]}")
                except Exception as e:
                    print(f"[DEBUG] HTML 샘플 추출 실패: {e}")
            
            safe_log("구글 기사 URL 수집 완료", level="info", count=len(article_urls))
            return article_urls

        except Exception as e:
            import traceback
            error_details = {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            safe_log("구글 뉴스 검색 오류", level="error", **error_details)
            return []

    def extract_article(self, url: str) -> Dict[str, Any]:
        """
        구글 뉴스 기사 내용 추출
        
        Args:
            url: 기사 URL
        
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

            # 제목 추출 (여러 셀렉터 시도)
            title = None
            title_selectors = GOOGLE_SELECTORS["title"]
            
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
                # 대체 방법: 페이지 타이틀 사용
                title = self.driver.title
                if title:
                    print(f"[DEBUG] ✓ 페이지 타이틀 사용: {title[:50]}...")
                else:
                    safe_log("제목 추출 실패 - 모든 셀렉터 실패", level="warning", url=url)
                    title = "제목 추출 실패"

            # 본문 추출 (여러 셀렉터 시도)
            content = None
            content_selectors = GOOGLE_SELECTORS["content"]
            
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

            # 구글 뉴스는 댓글 추출 미지원
            comments = []

            return {
                "title": title,
                "content": content,
                "comments": comments,
                "extraction_method": "selenium",
                "source": "google"
            }

        except Exception as e:
            safe_log("구글 뉴스 추출 오류", level="error", error=str(e), url=url)
            return {
                "title": "추출 실패",
                "content": "추출 실패",
                "comments": [],
                "extraction_method": "selenium",
                "error": str(e),
                "source": "google"
            }

    def scrape_article(self, url: str) -> NewsArticle:
        """
        구글 뉴스 기사 스크레이핑
        
        Args:
            url: 기사 URL
        
        Returns:
            NewsArticle 객체
        """
        safe_log("구글 기사 스크레이핑 시작", level="info", url=url)

        # 기사 내용 추출
        result = self.extract_article(url)

        comments = [
            Comment(
                id=c.get("id", ""),
                text=c.get("text", ""),
                author=c.get("author"),
                timestamp=None
            )
            for c in result.get("comments", [])
        ]

        return NewsArticle(
            url=url,
            title=result["title"],
            content=result["content"],
            comments=comments,
            source="google",
            extraction_method="selenium"
        )

