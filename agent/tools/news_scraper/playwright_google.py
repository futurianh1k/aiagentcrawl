"""
Playwright Google News Scraper

Playwright 기반 구글 뉴스 비동기 크롤러
RSS 피드 + Playwright 하이브리드 방식
"""

import asyncio
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from html import unescape

from common.utils import safe_log, validate_input, validate_url
from .playwright_base import PlaywrightBaseScraper


# 다양한 뉴스 사이트에서 동작하는 범용 셀렉터
ARTICLE_SELECTORS = {
    "title": [
        "h1",
        "h2.headline",
        ".article-title",
        ".post-title",
        "article h1",
        ".entry-title",
        "#article-title",
        ".title",
    ],
    "content": [
        "article",
        ".article-body",
        ".article-content",
        ".post-content",
        ".entry-content",
        "#article-body",
        ".story-body",
        "main",
        ".content",
        "#content",
        "[itemprop='articleBody']",
    ],
}


class PlaywrightGoogleScraper(PlaywrightBaseScraper):
    """Playwright 기반 구글 뉴스 크롤러"""
    
    async def search_news(self, keyword: str, max_articles: int = 5) -> List[str]:
        """
        구글 뉴스 RSS 피드에서 검색 (Selenium 불필요)
        
        Args:
            keyword: 검색 키워드
            max_articles: 최대 기사 수
        
        Returns:
            기사 URL 목록
        """
        if not validate_input(keyword, max_length=100):
            return []
        
        article_urls = []
        
        try:
            # 구글 뉴스 RSS 피드
            encoded_keyword = quote(keyword)
            rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
            
            print(f"[DEBUG] 구글 뉴스 RSS 피드 요청: {keyword}")
            safe_log("구글 뉴스 RSS 피드 요청", level="info", keyword=keyword)
            
            # RSS 피드 요청 (비동기로 처리)
            response = await asyncio.to_thread(
                requests.get,
                rss_url,
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=30
            )
            response.raise_for_status()
            
            # XML 파싱
            root = ET.fromstring(response.content)
            channel = root.find('channel')
            
            if channel is None:
                return []
            
            # 뉴스 아이템 추출
            for item in channel.findall('item'):
                if len(article_urls) >= max_articles:
                    break
                
                link = item.find('link')
                if link is not None and link.text:
                    url = link.text.strip()
                    # 구글 리다이렉션 URL도 포함 (나중에 실제 URL로 변환)
                    if url and url not in article_urls:
                        article_urls.append(url)
            
            print(f"[DEBUG] ✓ 구글 뉴스 {len(article_urls)}개 URL 수집")
            safe_log("구글 뉴스 URL 수집 완료", level="info", count=len(article_urls))
            
        except Exception as e:
            safe_log("구글 뉴스 검색 오류", level="error", error=str(e))
        
        return article_urls[:max_articles]
    
    async def extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        기사 내용 추출 (구글 리다이렉션 URL 처리)
        
        Args:
            url: 기사 URL (구글 리다이렉션 또는 직접 URL)
        
        Returns:
            기사 정보 딕셔너리
        """
        await self.setup()
        page = await self.new_page()
        
        try:
            print(f"[DEBUG] 구글 기사 추출: {url[:60]}...")
            
            # 페이지 로드 (구글 리다이렉션 자동 처리)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1000)
            
            # 실제 URL 가져오기 (리다이렉션 후)
            actual_url = page.url
            
            # 제목 추출
            title = await self.extract_text_by_selectors(page, ARTICLE_SELECTORS["title"])
            if not title:
                title = await page.title()
                # 사이트명 제거
                if title and ' - ' in title:
                    title = title.split(' - ')[0].strip()
            
            # 본문 추출
            content = await self.extract_text_by_selectors(page, ARTICLE_SELECTORS["content"])
            
            if title and content and len(content) > 50:
                print(f"[DEBUG] ✓ 구글 기사 추출 성공: {title[:30]}...")
                return {
                    "title": title,
                    "content": content[:3000],  # 최대 3000자
                    "url": actual_url,
                    "source": "구글",
                }
            
        except Exception as e:
            safe_log("구글 기사 추출 오류", level="error", error=str(e), url=url)
        finally:
            await page.close()
        
        return None

