"""
Google News Scraper

구글 뉴스 전용 크롤러
RSS 피드 기반으로 안정적인 뉴스 수집
Selenium 대신 XML 파싱 사용
"""

import time
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from urllib.parse import quote, unquote
from html import unescape
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from common.utils import safe_log, validate_input, validate_url
from .base_scraper import BaseNewsScraper
from .models import NewsArticle, Comment


class GoogleNewsScraper(BaseNewsScraper):
    """
    구글 뉴스 전용 크롤러
    
    RSS 피드 기반으로 안정적인 뉴스 URL 수집
    실제 기사 내용은 Selenium으로 추출
    """
    
    def search_news(self, keyword: str, max_articles: int = 5) -> List[str]:
        """
        구글 뉴스 RSS 피드에서 키워드 검색 후 기사 URL 목록 반환
        
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

        try:
            # 구글 뉴스 RSS 피드 URL
            encoded_keyword = quote(keyword)
            rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
            print(f"[DEBUG] 구글 뉴스 RSS 피드 요청: {rss_url}")
            safe_log("구글 뉴스 RSS 피드 요청", level="info", keyword=keyword, url=rss_url)

            # RSS 피드 요청
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(rss_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            print(f"[DEBUG] RSS 피드 응답 수신: {len(response.content)} bytes")
            
            # XML 파싱
            root = ET.fromstring(response.content)
            
            # RSS 네임스페이스 처리
            namespaces = {
                'media': 'http://search.yahoo.com/mrss/'
            }
            
            # 뉴스 아이템 찾기
            channel = root.find('channel')
            if channel is None:
                print(f"[DEBUG] RSS 피드에서 channel을 찾을 수 없음")
                safe_log("RSS 피드에서 channel을 찾을 수 없음", level="warning")
                return []
            
            items = channel.findall('item')
            print(f"[DEBUG] RSS 피드에서 {len(items)}개의 뉴스 아이템 발견")
            safe_log("RSS 피드 파싱 완료", level="info", item_count=len(items))
            
            # URL 추출
            article_urls = []
            for i, item in enumerate(items[:max_articles * 2], 1):  # 여유분으로 더 수집
                try:
                    # 링크 추출
                    link_elem = item.find('link')
                    if link_elem is not None and link_elem.text:
                        url = link_elem.text.strip()
                        
                        # 구글 뉴스 리디렉션 URL에서 실제 URL 추출
                        actual_url = self._extract_actual_url(url)
                        
                        if actual_url and validate_url(actual_url):
                            # 제목도 함께 로그
                            title_elem = item.find('title')
                            title = title_elem.text if title_elem is not None else "제목 없음"
                            
                            print(f"[DEBUG] ✓ 기사 {i}: {title[:50]}...")
                            print(f"[DEBUG]   URL: {actual_url[:80]}...")
                            
                            article_urls.append(actual_url)
                            
                            if len(article_urls) >= max_articles:
                                break
                except Exception as e:
                    print(f"[DEBUG] 아이템 {i} 처리 실패: {e}")
                    continue
            
            print(f"[DEBUG] 최종 수집된 URL 개수: {len(article_urls)}")
            safe_log("구글 기사 URL 수집 완료", level="info", count=len(article_urls))
            return article_urls

        except requests.RequestException as e:
            safe_log("구글 뉴스 RSS 피드 요청 실패", level="error", error=str(e))
            print(f"[DEBUG] RSS 피드 요청 실패: {e}")
            return []
        except ET.ParseError as e:
            safe_log("RSS 피드 XML 파싱 실패", level="error", error=str(e))
            print(f"[DEBUG] XML 파싱 실패: {e}")
            return []
        except Exception as e:
            import traceback
            error_details = {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            safe_log("구글 뉴스 검색 오류", level="error", **error_details)
            print(f"[DEBUG] 예외 발생: {e}")
            return []

    def _extract_actual_url(self, google_news_url: str) -> str:
        """
        구글 뉴스 리디렉션 URL에서 실제 기사 URL 추출
        
        Args:
            google_news_url: 구글 뉴스 URL
        
        Returns:
            실제 기사 URL
        """
        # 구글 뉴스 URL이 아니면 그대로 반환
        if "news.google.com" not in google_news_url:
            return google_news_url
        
        # 구글 뉴스 RSS에서 오는 URL은 보통 실제 기사 URL을 포함
        # 예: https://news.google.com/rss/articles/...
        # 이 URL을 요청하면 실제 기사로 리디렉션됨
        
        try:
            # 리디렉션을 따라가서 최종 URL 얻기
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.head(google_news_url, headers=headers, allow_redirects=True, timeout=10)
            final_url = response.url
            
            # 구글 뉴스가 아닌 실제 기사 URL인지 확인
            if "news.google.com" not in final_url:
                print(f"[DEBUG] 리디렉션 URL 추출 성공: {final_url[:60]}...")
                return final_url
            
            # 리디렉션이 안 되면 원본 URL 반환
            return google_news_url
            
        except Exception as e:
            print(f"[DEBUG] URL 리디렉션 추출 실패: {e}")
            # 실패하면 원본 URL 반환 (나중에 Selenium으로 처리)
            return google_news_url

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
            print(f"[DEBUG] 기사 내용 추출 시작: {url[:60]}...")
            self.driver.get(url)
            time.sleep(2)  # 페이지 로드 대기

            # 제목 추출 (여러 셀렉터 시도)
            title = None
            title_selectors = [
                "h1",
                "h2.article-title",
                ".article-title h1",
                "article h1",
                ".headline",
                "h1.title",
                ".tit_view",
                "#articleTitle",
                ".news_tit",
            ]
            
            for i, title_selector in enumerate(title_selectors, 1):
                try:
                    title_elements = self.driver.find_elements(By.CSS_SELECTOR, title_selector)
                    if title_elements:
                        for elem in title_elements:
                            text = elem.text.strip()
                            if text and len(text) > 5:  # 최소 5자 이상
                                title = text
                                print(f"[DEBUG] ✓ 제목 추출 성공 (셀렉터 {i}): {title[:50]}...")
                                break
                    if title:
                        break
                except Exception:
                    continue
            
            if not title:
                # 페이지 타이틀 사용
                title = self.driver.title
                if title:
                    # " - 뉴스 사이트명" 등 제거
                    title = re.sub(r'\s*[-|]\s*[^-|]+$', '', title)
                    print(f"[DEBUG] ✓ 페이지 타이틀 사용: {title[:50]}...")
                else:
                    title = "제목 추출 실패"

            # 본문 추출 (여러 셀렉터 시도)
            content = None
            content_selectors = [
                "article p",
                ".article-body p",
                ".article-content p",
                "#article-body p",
                ".story-body p",
                "div[itemprop='articleBody'] p",
                "#dic_area",  # 네이버 뉴스
                ".news_end_body_container",
                "#articeBody",
                ".article_body",
                "article",
                ".content",
                "#content",
                "main p",
            ]
            
            for i, content_selector in enumerate(content_selectors, 1):
                try:
                    content_elements = self.driver.find_elements(By.CSS_SELECTOR, content_selector)
                    if content_elements:
                        content_text = " ".join([elem.text.strip() for elem in content_elements if elem.text.strip()])
                        if content_text and len(content_text) > 50:  # 최소 50자 이상
                            content = content_text
                            print(f"[DEBUG] ✓ 본문 추출 성공 (셀렉터 {i}, 길이: {len(content)}자)")
                            break
                except Exception:
                    continue
            
            if not content:
                content = "본문 추출 실패"
                print(f"[DEBUG] ✗ 본문 추출 실패")

            return {
                "title": title,
                "content": content,
                "comments": [],  # 구글 뉴스는 댓글 추출 미지원
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
