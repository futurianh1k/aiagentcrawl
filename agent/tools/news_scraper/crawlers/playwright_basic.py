"""
Playwright 기초 크롤러 모듈

2회차 강의: AI 에이전트 기반 뉴스 감성 분석 시스템
Playwright MCP를 활용한 고급 웹 크롤링 - Contexts와 Pages 관리
"""

from typing import Optional, List, Dict, Any, Union, Callable
import asyncio
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging

from playwright.async_api import (
    async_playwright, Browser, BrowserContext, Page, 
    Playwright, BrowserType, Error as PlaywrightError
)

from config.settings import settings

logger = logging.getLogger(__name__)


class PlaywrightManager:
    """
    Playwright 브라우저 관리자

    브라우저 인스턴스와 컨텍스트를 효율적으로 관리하고
    리소스 정리를 자동화합니다.
    """

    def __init__(self):
        """PlaywrightManager 초기화"""
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.contexts: List[BrowserContext] = []
        self._initialized = False

    async def initialize(self) -> None:
        """
        Playwright 및 브라우저 초기화

        설정에 따라 브라우저를 실행하고 기본 설정을 적용합니다.
        """
        if self._initialized:
            return

        try:
            # Playwright 인스턴스 생성
            self.playwright = await async_playwright().start()

            # 브라우저 타입 선택
            browser_type: BrowserType = getattr(
                self.playwright, 
                settings.crawler.browser_type
            )

            # 브라우저 실행 옵션 설정
            launch_options = {
                'headless': settings.crawler.headless,
                'args': settings.crawler.get_browser_args(),
                'slow_mo': settings.crawler.slow_mo
            }

            # 브라우저 실행
            self.browser = await browser_type.launch(**launch_options)

            self._initialized = True
            logger.info(
                f"Playwright 브라우저가 성공적으로 초기화되었습니다: "
                f"{settings.crawler.browser_type} (헤드리스: {settings.crawler.headless})"
            )

        except Exception as e:
            logger.error(f"Playwright 초기화 실패: {e}")
            await self.cleanup()
            raise

    async def create_context(self, **context_options) -> BrowserContext:
        """
        새로운 브라우저 컨텍스트 생성

        Args:
            **context_options: 컨텍스트 생성 옵션

        Returns:
            BrowserContext: 생성된 컨텍스트
        """
        if not self._initialized:
            await self.initialize()

        # 기본 컨텍스트 옵션 설정
        default_options = {
            'viewport': settings.crawler.get_viewport_config(),
            'user_agent': settings.crawler.user_agent or None,
            'extra_http_headers': settings.crawler.extra_http_headers,
            'java_script_enabled': settings.crawler.java_script_enabled,
        }

        # 사용자 옵션과 병합
        final_options = {**default_options, **context_options}

        # None 값 제거
        final_options = {k: v for k, v in final_options.items() if v is not None}

        try:
            context = await self.browser.new_context(**final_options)

            # 타임아웃 설정
            context.set_default_timeout(settings.crawler.page_timeout)
            context.set_default_navigation_timeout(settings.crawler.navigation_timeout)

            self.contexts.append(context)

            logger.info(f"새로운 브라우저 컨텍스트가 생성되었습니다 (총 {len(self.contexts)}개)")

            return context

        except Exception as e:
            logger.error(f"컨텍스트 생성 실패: {e}")
            raise

    async def create_stealth_context(self) -> BrowserContext:
        """
        봇 감지를 우회하는 스텔스 컨텍스트 생성

        Returns:
            BrowserContext: 스텔스 설정이 적용된 컨텍스트
        """
        # 랜덤 뷰포트 설정
        viewport = {
            'width': random.randint(1200, 1920),
            'height': random.randint(800, 1080),
        }

        # 랜덤 User-Agent 설정 (간단한 예시)
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]

        context_options = {
            'viewport': viewport,
            'user_agent': random.choice(user_agents),
            'extra_http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        }

        context = await self.create_context(**context_options)

        # 추가 스텔스 설정
        await context.add_init_script("""
            // WebDriver 속성 숨기기
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // Chrome 객체 추가
            window.chrome = {
                runtime: {},
            };

            // Permissions API 오버라이드
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        logger.info("스텔스 모드 컨텍스트가 생성되었습니다")

        return context

    async def cleanup_context(self, context: BrowserContext) -> None:
        """
        특정 컨텍스트 정리

        Args:
            context: 정리할 컨텍스트
        """
        try:
            if context in self.contexts:
                self.contexts.remove(context)

            await context.close()

            logger.info(f"컨텍스트가 정리되었습니다 (남은 컨텍스트: {len(self.contexts)}개)")

        except Exception as e:
            logger.warning(f"컨텍스트 정리 중 오류: {e}")

    async def cleanup(self) -> None:
        """모든 리소스 정리"""
        try:
            # 모든 컨텍스트 정리
            for context in self.contexts[:]:  # 복사본을 만들어 순회
                await self.cleanup_context(context)

            # 브라우저 종료
            if self.browser:
                await self.browser.close()
                self.browser = None

            # Playwright 종료
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            self._initialized = False

            logger.info("Playwright 리소스가 모두 정리되었습니다")

        except Exception as e:
            logger.error(f"리소스 정리 중 오류: {e}")

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.cleanup()


class ContextualCrawler:
    """
    컨텍스트 기반 크롤러

    여러 브라우저 컨텍스트를 사용하여 
    병렬 크롤링과 세션 격리를 제공합니다.
    """

    def __init__(self, manager: Optional[PlaywrightManager] = None):
        """
        ContextualCrawler 초기화

        Args:
            manager: Playwright 매니저 (None일 경우 자동 생성)
        """
        self.manager = manager or PlaywrightManager()
        self.active_contexts: Dict[str, BrowserContext] = {}
        self._own_manager = manager is None

    async def initialize(self) -> None:
        """크롤러 초기화"""
        if not self.manager._initialized:
            await self.manager.initialize()

    @asynccontextmanager
    async def get_context(self, context_id: str = "default", **context_options):
        """
        컨텍스트 컨텍스트 매니저

        Args:
            context_id: 컨텍스트 식별자
            **context_options: 컨텍스트 생성 옵션

        Yields:
            BrowserContext: 브라우저 컨텍스트
        """
        context = None
        try:
            # 기존 컨텍스트가 있으면 재사용
            if context_id in self.active_contexts:
                context = self.active_contexts[context_id]
            else:
                # 새 컨텍스트 생성
                await self.initialize()
                context = await self.manager.create_context(**context_options)
                self.active_contexts[context_id] = context

            yield context

        except Exception as e:
            logger.error(f"컨텍스트 '{context_id}' 사용 중 오류: {e}")
            raise
        finally:
            # 컨텍스트 정리는 명시적으로 호출해야 함
            pass

    @asynccontextmanager
    async def get_page(self, context_id: str = "default", **page_options) -> Page:
        """
        페이지 컨텍스트 매니저

        Args:
            context_id: 컨텍스트 식별자
            **page_options: 페이지 생성 옵션

        Yields:
            Page: 브라우저 페이지
        """
        page = None
        try:
            async with self.get_context(context_id) as context:
                page = await context.new_page()

                # 페이지별 타임아웃 설정
                page.set_default_timeout(settings.crawler.wait_timeout)

                yield page

        except Exception as e:
            logger.error(f"페이지 사용 중 오류: {e}")
            raise
        finally:
            if page:
                try:
                    await page.close()
                except Exception as e:
                    logger.warning(f"페이지 정리 중 오류: {e}")

    async def crawl_url(
        self, 
        url: str, 
        context_id: str = "default",
        wait_for_selector: Optional[str] = None,
        wait_for_load_state: str = "domcontentloaded"
    ) -> Dict[str, Any]:
        """
        단일 URL 크롤링

        Args:
            url: 크롤링할 URL
            context_id: 사용할 컨텍스트 ID
            wait_for_selector: 대기할 셀렉터
            wait_for_load_state: 페이지 로드 상태 대기

        Returns:
            Dict: 크롤링 결과 (title, content, url, timestamp)
        """
        async with self.get_page(context_id) as page:
            try:
                # 페이지 이동
                response = await page.goto(url, wait_until=wait_for_load_state)

                if not response or response.status >= 400:
                    raise Exception(f"페이지 로드 실패: HTTP {response.status if response else 'No response'}")

                # 특정 셀렉터 대기
                if wait_for_selector:
                    await page.wait_for_selector(wait_for_selector)

                # 기본 정보 추출
                title = await page.title()
                content = await page.content()
                final_url = page.url

                # 스크린샷 (디버깅용)
                screenshot_path = None
                if settings.app.debug:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = f"/tmp/screenshot_{context_id}_{timestamp}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)

                return {
                    'success': True,
                    'url': final_url,
                    'original_url': url,
                    'title': title,
                    'content': content,
                    'timestamp': datetime.now(timezone.utc),
                    'context_id': context_id,
                    'screenshot_path': screenshot_path,
                    'response_status': response.status if response else None
                }

            except PlaywrightError as e:
                logger.error(f"Playwright 오류 (URL: {url}): {e}")
                return {
                    'success': False,
                    'url': url,
                    'error': f"Playwright 오류: {str(e)}",
                    'error_type': 'playwright_error',
                    'timestamp': datetime.now(timezone.utc),
                    'context_id': context_id
                }

            except Exception as e:
                logger.error(f"크롤링 오류 (URL: {url}): {e}")
                return {
                    'success': False,
                    'url': url,
                    'error': str(e),
                    'error_type': 'general_error',
                    'timestamp': datetime.now(timezone.utc),
                    'context_id': context_id
                }

    async def crawl_multiple_urls(
        self, 
        urls: List[str], 
        max_concurrent: Optional[int] = None,
        delay_between_requests: float = 1.0,
        **crawl_options
    ) -> List[Dict[str, Any]]:
        """
        여러 URL 병렬 크롤링

        Args:
            urls: 크롤링할 URL 리스트
            max_concurrent: 최대 동시 실행 수
            delay_between_requests: 요청 간 지연 시간
            **crawl_options: crawl_url에 전달할 추가 옵션

        Returns:
            List[Dict]: 크롤링 결과 리스트
        """
        if not urls:
            return []

        max_concurrent = max_concurrent or settings.crawler.max_concurrent_pages

        # 세마포어를 사용한 동시성 제어
        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_with_semaphore(url: str, index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    # 순서대로 지연 적용
                    if delay_between_requests > 0:
                        await asyncio.sleep(delay_between_requests * index)

                    # 컨텍스트 ID를 인덱스 기반으로 생성 (컨텍스트 재사용)
                    context_id = f"context_{index % settings.crawler.max_concurrent_contexts}"

                    result = await self.crawl_url(url, context_id=context_id, **crawl_options)
                    result['index'] = index

                    return result

                except Exception as e:
                    logger.error(f"URL 크롤링 실패 (인덱스 {index}, URL: {url}): {e}")
                    return {
                        'success': False,
                        'url': url,
                        'error': str(e),
                        'error_type': 'async_error',
                        'index': index,
                        'timestamp': datetime.now(timezone.utc)
                    }

        # 모든 URL에 대해 비동기 태스크 생성
        tasks = [
            crawl_with_semaphore(url, i) 
            for i, url in enumerate(urls)
        ]

        # 모든 태스크 실행 및 결과 수집
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 예외 처리된 결과 정리
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'url': urls[i] if i < len(urls) else 'unknown',
                    'error': str(result),
                    'error_type': 'exception',
                    'index': i,
                    'timestamp': datetime.now(timezone.utc)
                })
            else:
                processed_results.append(result)

        # 결과를 원래 순서대로 정렬
        processed_results.sort(key=lambda x: x.get('index', 0))

        logger.info(f"{len(urls)}개 URL 크롤링 완료: 성공 {sum(1 for r in processed_results if r.get('success', False))}개")

        return processed_results

    async def close_context(self, context_id: str) -> None:
        """
        특정 컨텍스트 종료

        Args:
            context_id: 종료할 컨텍스트 ID
        """
        if context_id in self.active_contexts:
            context = self.active_contexts.pop(context_id)
            await self.manager.cleanup_context(context)
            logger.info(f"컨텍스트 '{context_id}'가 종료되었습니다")

    async def cleanup(self) -> None:
        """모든 리소스 정리"""
        try:
            # 모든 활성 컨텍스트 정리
            for context_id in list(self.active_contexts.keys()):
                await self.close_context(context_id)

            # 매니저가 자체 생성된 경우에만 정리
            if self._own_manager:
                await self.manager.cleanup()

            logger.info("ContextualCrawler 리소스가 정리되었습니다")

        except Exception as e:
            logger.error(f"ContextualCrawler 정리 중 오류: {e}")

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.cleanup()


# 편의 함수들
async def quick_crawl(url: str, **options) -> Dict[str, Any]:
    """
    단일 URL 빠른 크롤링

    Args:
        url: 크롤링할 URL
        **options: 추가 크롤링 옵션

    Returns:
        Dict: 크롤링 결과
    """
    async with ContextualCrawler() as crawler:
        return await crawler.crawl_url(url, **options)


async def quick_crawl_multiple(urls: List[str], **options) -> List[Dict[str, Any]]:
    """
    여러 URL 빠른 크롤링

    Args:
        urls: 크롤링할 URL 리스트
        **options: 추가 크롤링 옵션

    Returns:
        List[Dict]: 크롤링 결과 리스트
    """
    async with ContextualCrawler() as crawler:
        return await crawler.crawl_multiple_urls(urls, **options)


# 동기 래퍼 함수들 (기존 코드와의 호환성을 위해)
def sync_crawl(url: str, **options) -> Dict[str, Any]:
    """
    동기적 단일 URL 크롤링

    Args:
        url: 크롤링할 URL
        **options: 추가 크롤링 옵션

    Returns:
        Dict: 크롤링 결과
    """
    return asyncio.run(quick_crawl(url, **options))


def sync_crawl_multiple(urls: List[str], **options) -> List[Dict[str, Any]]:
    """
    동기적 여러 URL 크롤링

    Args:
        urls: 크롤링할 URL 리스트
        **options: 추가 크롤링 옵션

    Returns:
        List[Dict]: 크롤링 결과 리스트
    """
    return asyncio.run(quick_crawl_multiple(urls, **options))
