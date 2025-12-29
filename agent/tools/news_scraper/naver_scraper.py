"""
Naver News Scraper

네이버 뉴스 전용 크롤러
네이버 뉴스 검색 및 기사 내용 추출 기능 제공
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


# 네이버 뉴스 CSS Selector 상수
NAVER_SELECTORS = {
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
}


class NaverNewsScraper(BaseNewsScraper):
    """네이버 뉴스 전용 크롤러"""
    
    def search_news(self, keyword: str, max_articles: int = 5) -> List[str]:
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
            selectors = NAVER_SELECTORS["news_link"]
            
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

    def extract_article(self, url: str) -> Dict[str, Any]:
        """
        네이버 뉴스 기사 내용 추출
        
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
            title_selectors = [
                NAVER_SELECTORS["title"],  # 기본 셀렉터
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
                NAVER_SELECTORS["content"],  # #dic_area
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
            comments = self.extract_comments()

            return {
                "title": title,
                "content": content,
                "comments": comments,
                "extraction_method": "selenium",
                "source": "naver"
            }

        except Exception as e:
            safe_log("네이버 뉴스 추출 오류", level="error", error=str(e), url=url)
            return {
                "title": "추출 실패",
                "content": "추출 실패",
                "comments": [],
                "extraction_method": "selenium",
                "error": str(e),
                "source": "naver"
            }

    def extract_comments(self) -> List[Dict[str, Any]]:
        """
        네이버 뉴스 댓글 추출
        
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
                        (By.CSS_SELECTOR, NAVER_SELECTORS["comment_more"])
                    )
                )
                more_button.click()
                time.sleep(2)  # 댓글 로딩 대기
            except Exception:
                pass  # 더보기 버튼이 없을 수 있음

            # 댓글 요소들 찾기
            comment_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                NAVER_SELECTORS["comment"]
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

    def scrape_article(self, url: str) -> NewsArticle:
        """
        네이버 뉴스 기사 스크레이핑
        
        Args:
            url: 기사 URL
        
        Returns:
            NewsArticle 객체
        """
        safe_log("네이버 기사 스크레이핑 시작", level="info", url=url)

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
            source="naver",
            extraction_method="selenium"
        )


