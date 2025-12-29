"""
Playwright Naver News Scraper

Playwright 기반 네이버 뉴스 비동기 크롤러
"""

import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import quote

from common.utils import safe_log, validate_input, validate_url
from .playwright_base import PlaywrightBaseScraper


# 네이버 뉴스 CSS Selector 상수 (2024년 12월 기준)
NAVER_SELECTORS = {
    "news_link": [
        "a.news_tit",
        "div.news_area a.news_tit",
        ".news_contents a.news_tit",
        ".list_news a.news_tit",
        ".news_tit",
        "a[href*='n.news.naver.com']",
        "a[href*='news.naver.com']",
    ],
    "title": [
        "#ct > div.media_end_head.go_trans > div.media_end_head_title > h2",
        "h2.media_end_head_headline",
        "#title_area span",
        ".media_end_head_headline",
        "h3.tit_view",
        ".article_header h2",
        "#articleTitle",
        "h1",
    ],
    "content": [
        "#dic_area",
        "#newsct_article",
        ".news_end_body_container",
        "#articeBody",
        ".article_body",
        ".article_view",
        "article",
        "#articleBody",
        ".news_end_body",
    ],
}


class PlaywrightNaverScraper(PlaywrightBaseScraper):
    """Playwright 기반 네이버 뉴스 크롤러"""
    
    async def search_news(self, keyword: str, max_articles: int = 5) -> List[str]:
        """
        네이버 뉴스 검색
        
        Args:
            keyword: 검색 키워드
            max_articles: 최대 기사 수
        
        Returns:
            기사 URL 목록
        """
        if not validate_input(keyword, max_length=100):
            return []
        
        await self.setup()
        page = await self.new_page()
        article_urls = []
        
        try:
            # 네이버 뉴스 검색 URL
            encoded_keyword = quote(keyword)
            search_url = f"https://search.naver.com/search.naver?where=news&query={encoded_keyword}&sort=1"
            
            print(f"[DEBUG] 네이버 뉴스 검색: {keyword}")
            safe_log("네이버 뉴스 검색 시작", level="info", keyword=keyword)
            
            # 페이지 로드
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1000)  # 동적 콘텐츠 로딩 대기
            
            # 뉴스 링크 추출
            for selector in NAVER_SELECTORS["news_link"]:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        href = await element.get_attribute('href')
                        if href and self._is_valid_naver_url(href):
                            if href not in article_urls:
                                article_urls.append(href)
                                if len(article_urls) >= max_articles:
                                    break
                    if article_urls:
                        break
                except Exception:
                    continue
            
            print(f"[DEBUG] ✓ 네이버 뉴스 {len(article_urls)}개 URL 수집")
            safe_log("네이버 뉴스 URL 수집 완료", level="info", count=len(article_urls))
            
        except Exception as e:
            safe_log("네이버 뉴스 검색 오류", level="error", error=str(e))
        finally:
            await page.close()
        
        return article_urls[:max_articles]
    
    async def extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        네이버 뉴스 기사 내용 추출
        
        Args:
            url: 기사 URL
        
        Returns:
            기사 정보 딕셔너리
        """
        if not validate_url(url):
            return None
        
        await self.setup()
        page = await self.new_page()
        
        try:
            print(f"[DEBUG] 네이버 기사 추출: {url[:60]}...")
            
            # 페이지 로드
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(500)
            
            # 제목 추출
            title = await self.extract_text_by_selectors(page, NAVER_SELECTORS["title"])
            if not title:
                title = await page.title()
            
            # 본문 추출
            content = await self.extract_text_by_selectors(page, NAVER_SELECTORS["content"])
            
            if title and content and len(content) > 50:
                print(f"[DEBUG] ✓ 네이버 기사 추출 성공: {title[:30]}...")
                return {
                    "title": title,
                    "content": content[:3000],  # 최대 3000자
                    "url": url,
                    "source": "네이버",
                }
            
        except Exception as e:
            safe_log("네이버 기사 추출 오류", level="error", error=str(e), url=url)
        finally:
            await page.close()
        
        return None
    
    def _is_valid_naver_url(self, url: str) -> bool:
        """유효한 네이버 뉴스 URL인지 확인"""
        valid_patterns = [
            "n.news.naver.com/mnews/article/",
            "news.naver.com/main/read",
            "n.news.naver.com/article/",
        ]
        return any(pattern in url for pattern in valid_patterns)

