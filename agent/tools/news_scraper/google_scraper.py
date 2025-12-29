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
# 구글 뉴스는 구조가 자주 변경되므로 다양한 셀렉터 시도
GOOGLE_SELECTORS = {
    "news_link": [
        # 최신 구글 뉴스 구조 (2024)
        "article a[href*='/articles/']",
        "article h3 a",
        "article h4 a",
        "article a[href^='./articles/']",
        "article a[href*='articles']",
        
        # 클래스 기반 셀렉터
        ".JtKRv a",
        ".VDXfz a",
        ".Yv5pGd a",
        ".gPFEn a",
        ".WwrzSb a",
        ".ipQwMb a",
        ".DY5T1d a",
        
        # data 속성 기반
        "a[data-ved][href*='news']",
        "a[data-ved][href*='articles']",
        "div[data-ved] a[href*='news']",
        "div[data-ved] a[href*='articles']",
        
        # 제목 태그 기반
        "h3 a[href*='news']",
        "h3 a[href*='articles']",
        "h4 a[href*='news']",
        "h4 a[href*='articles']",
        
        # 일반적인 article 내부 링크
        "article a",
        "article h3 a",
        "article h4 a",
        
        # 더 넓은 범위의 셀렉터
        "div[jsmodel] a[href*='articles']",
        "div[jscontroller] a[href*='articles']",
        "c-wiz a[href*='articles']",
        
        # 최후의 수단: 모든 article 내부의 모든 링크
        "article a[href]",
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
            time.sleep(3)  # 대기 시간 단축

            # 페이지 스크롤하여 동적 콘텐츠 로드 (간소화)
            try:
                print(f"[DEBUG] 페이지 스크롤 중...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)
            except Exception as e:
                print(f"[DEBUG] 스크롤 실패 (무시): {e}")

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
                    
                    # 먼저 요소가 존재하는지 확인 (presence_of_all_elements_located는 최소 1개 필요)
                    # find_elements를 사용하여 0개여도 에러가 나지 않도록
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if links and len(links) > 0:
                        # 실제로 href 속성이 있는 링크만 필터링
                        valid_links = [link for link in links if link.get_attribute("href")]
                        if valid_links:
                            news_links = valid_links
                            print(f"[DEBUG] ✓ 셀렉터 성공! {len(valid_links)}개의 유효한 링크 발견 (전체: {len(links)})")
                            safe_log("셀렉터 성공", level="info", selector=selector, count=len(valid_links), total=len(links))
                            break
                        else:
                            print(f"[DEBUG] ✗ 셀렉터 {i}: 요소는 있지만 href가 없음")
                    else:
                        print(f"[DEBUG] ✗ 셀렉터 {i}: 요소 없음")
                except Exception as e:
                    error_msg = str(e)[:100]
                    print(f"[DEBUG] ✗ 셀렉터 실패: {error_msg}")
                    safe_log("셀렉터 실패", level="info", selector=selector, error=error_msg)
                    continue
            
            # 모든 셀렉터 실패 시 추가 시도
            if not news_links:
                print(f"[DEBUG] !! 모든 셀렉터 실패, 추가 시도 중...")
                
                # 1. article 태그가 있는지 확인
                try:
                    articles = self.driver.find_elements(By.TAG_NAME, "article")
                    print(f"[DEBUG] article 태그 개수: {len(articles)}")
                    if articles:
                        # article 내부의 모든 링크 찾기
                        for article in articles[:30]:  # 처음 30개 확인
                            try:
                                links_in_article = article.find_elements(By.TAG_NAME, "a")
                                for link in links_in_article:
                                    href = link.get_attribute("href")
                                    if href:
                                        # 구글 뉴스 리디렉션 URL이 아닌 실제 외부 URL만 수집
                                        if "news.google.com" not in href or "/articles/" in href:
                                            if href not in [l.get_attribute("href") for l in news_links if l]:
                                                news_links.append(link)
                                                print(f"[DEBUG] ✓ article 내부에서 링크 발견: {href[:80]}...")
                            except Exception:
                                continue
                except Exception as e:
                    print(f"[DEBUG] article 태그 검색 실패: {e}")
                
                # 2. 모든 a 태그에서 href가 있는 것 찾기
                if not news_links:
                    print(f"[DEBUG] 모든 a 태그 검색 시도...")
                    try:
                        all_links = self.driver.find_elements(By.TAG_NAME, "a")
                        print(f"[DEBUG] 전체 a 태그 개수: {len(all_links)}")
                        for link in all_links[:100]:  # 처음 100개만 확인
                            try:
                                href = link.get_attribute("href")
                                if href and validate_url(href):
                                    # 구글 뉴스가 아닌 외부 사이트 URL만 수집
                                    if "news.google.com" not in href:
                                        # 중복 체크
                                        if href not in [l.get_attribute("href") for l in news_links if l]:
                                            news_links.append(link)
                                            print(f"[DEBUG] ✓ a 태그에서 링크 발견: {href[:80]}...")
                                            if len(news_links) >= max_articles:
                                                break
                            except Exception:
                                continue
                    except Exception as e:
                        print(f"[DEBUG] a 태그 검색 실패: {e}")
                
                # 여전히 실패하면 디버깅 정보 출력
                if not news_links:
                    print(f"[DEBUG] !! 최종 실패 - 디버깅 정보 수집 중...")
                    # 페이지 소스 일부 출력 (디버깅용)
                    page_source = self.driver.page_source
                    print(f"[DEBUG] 페이지 소스 길이: {len(page_source)}")
                    
                    # article 태그가 있는지 확인
                    try:
                        article_count = len(self.driver.find_elements(By.TAG_NAME, "article"))
                        print(f"[DEBUG] article 태그 개수: {article_count}")
                    except Exception:
                        pass
                    
                    # a 태그 개수 확인
                    try:
                        a_count = len(self.driver.find_elements(By.TAG_NAME, "a"))
                        print(f"[DEBUG] a 태그 개수: {a_count}")
                    except Exception:
                        pass
                    
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
            
            # 간소화된 URL 추출 (타임아웃 방지)
            for i, link in enumerate(news_links[:max_articles * 3], 1):
                try:
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    
                    if href and validate_url(href):
                        # 구글 뉴스 리디렉션 URL은 건너뛰기 (시간 소모 방지)
                        if "news.google.com" in href:
                            print(f"[DEBUG] ✗ 구글 뉴스 URL 건너뛰기: {href[:60]}...")
                            continue
                        
                        # 외부 사이트 URL만 수집
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

