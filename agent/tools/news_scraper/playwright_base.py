"""
Playwright Base Scraper

Playwright 기반 비동기 스크래퍼 베이스 클래스
Selenium 대비 2-3배 빠른 속도와 네이티브 비동기 지원
"""

import asyncio
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from common.config import get_config
from common.utils import safe_log


class PlaywrightBaseScraper(ABC):
    """
    Playwright 기반 비동기 스크래퍼 베이스 클래스
    
    특징:
    - 네이티브 비동기 지원
    - 자동 대기 (auto-waiting)
    - 더 낮은 메모리 사용량
    - 더 빠른 속도
    """
    
    def __init__(self):
        """초기화"""
        self.config = get_config()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._playwright = None
    
    async def setup(self) -> None:
        """브라우저 초기화"""
        if self.browser is not None:
            return
            
        try:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-extensions',
                    '--disable-background-networking',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--disable-translate',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--no-first-run',
                    '--safebrowsing-disable-auto-update',
                ]
            )
            self.context = await self.browser.new_context(
                user_agent=self.config.CRAWLER_USER_AGENT,
                viewport={'width': 1920, 'height': 1080},
                locale='ko-KR',
            )
            # 불필요한 리소스 차단 (이미지, 폰트, 스타일시트 - 속도 향상)
            await self.context.route("**/*.{png,jpg,jpeg,gif,svg,webp,ico}", lambda route: route.abort())
            await self.context.route("**/*.woff*", lambda route: route.abort())
            
            print(f"[DEBUG] Playwright 브라우저 초기화 완료")
            safe_log("Playwright 브라우저 초기화 완료", level="info")
            
        except Exception as e:
            safe_log("Playwright 브라우저 초기화 실패", level="error", error=str(e))
            raise RuntimeError(f"Playwright 초기화 실패: {e}")
    
    async def cleanup(self) -> None:
        """리소스 정리"""
        try:
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            print(f"[DEBUG] Playwright 리소스 정리 완료")
            safe_log("Playwright 리소스 정리 완료", level="info")
        except Exception as e:
            safe_log("Playwright 리소스 정리 오류", level="warning", error=str(e))
    
    async def new_page(self) -> Page:
        """새 페이지 생성"""
        if self.context is None:
            await self.setup()
        return await self.context.new_page()
    
    async def extract_text_by_selectors(
        self, 
        page: Page, 
        selectors: List[str], 
        timeout: int = 5000
    ) -> Optional[str]:
        """
        여러 CSS 셀렉터를 시도하여 텍스트 추출
        
        Args:
            page: Playwright 페이지
            selectors: 시도할 CSS 셀렉터 목록
            timeout: 대기 시간 (ms)
        
        Returns:
            추출된 텍스트 또는 None
        """
        for i, selector in enumerate(selectors, 1):
            try:
                element = await page.wait_for_selector(selector, timeout=timeout)
                if element:
                    text = await element.text_content()
                    if text:
                        stripped_text = text.strip()
                        if len(stripped_text) > 10:
                            preview = stripped_text[:50].replace('\n', ' ')
                            print(f"[DEBUG] ✓ 텍스트 추출 성공 (셀렉터 {i}): {preview}...")
                            return stripped_text
            except Exception:
                continue
        return None
    
    async def extract_links_by_selectors(
        self, 
        page: Page, 
        selectors: List[str],
        timeout: int = 5000
    ) -> List[str]:
        """
        여러 CSS 셀렉터를 시도하여 링크 추출
        
        Args:
            page: Playwright 페이지
            selectors: 시도할 CSS 셀렉터 목록
            timeout: 대기 시간 (ms)
        
        Returns:
            추출된 링크 목록
        """
        links = []
        for i, selector in enumerate(selectors, 1):
            try:
                await page.wait_for_selector(selector, timeout=timeout)
                elements = await page.query_selector_all(selector)
                for element in elements:
                    href = await element.get_attribute('href')
                    if href and href not in links:
                        links.append(href)
                if links:
                    print(f"[DEBUG] ✓ 링크 추출 성공 (셀렉터 {i}): {len(links)}개")
                    break
            except Exception:
                continue
        return links
    
    @abstractmethod
    async def search_news(self, keyword: str, max_articles: int = 5) -> List[str]:
        """뉴스 검색 (하위 클래스에서 구현)"""
        pass
    
    @abstractmethod
    async def extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """기사 내용 추출 (하위 클래스에서 구현)"""
        pass

