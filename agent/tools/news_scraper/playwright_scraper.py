"""
Playwright News Scraper - 병렬처리 지원

Playwright 기반 비동기 병렬 뉴스 크롤러
네이버와 구글을 동시에 크롤링하여 속도 2-3배 향상

사용 예시:
    scraper = PlaywrightNewsScraper()
    articles = await scraper.scrape_all(keyword="AI", sources=["네이버", "구글"], max_articles=5)
    await scraper.cleanup()
"""

import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from common.utils import safe_log, validate_input
from .playwright_naver import PlaywrightNaverScraper
from .playwright_google import PlaywrightGoogleScraper


class PlaywrightNewsScraper:
    """
    Playwright 기반 병렬 뉴스 크롤러
    
    특징:
    - 네이버/구글 동시 검색 (병렬 처리)
    - 기사 추출도 병렬 처리
    - 기존 대비 2-3배 빠른 속도
    """
    
    def __init__(self):
        """초기화"""
        self.naver_scraper = PlaywrightNaverScraper()
        self.google_scraper = PlaywrightGoogleScraper()
    
    async def search_news_parallel(
        self, 
        keyword: str, 
        sources: List[str], 
        max_articles: int = 5
    ) -> Dict[str, List[str]]:
        """
        여러 소스에서 병렬로 뉴스 검색
        
        Args:
            keyword: 검색 키워드
            sources: 뉴스 소스 목록 (["네이버", "구글"])
            max_articles: 소스당 최대 기사 수
        
        Returns:
            소스별 기사 URL 딕셔너리
        """
        results = {"네이버": [], "구글": []}
        tasks = []
        
        # 소스 매핑
        source_mapping = {
            "네이버": "네이버", "naver": "네이버",
            "구글": "구글", "google": "구글",
        }
        
        valid_sources = []
        for source in sources:
            normalized = source_mapping.get(source)
            if normalized and normalized not in valid_sources:
                valid_sources.append(normalized)
        
        if not valid_sources:
            valid_sources = ["네이버"]
        
        print(f"[DEBUG] 병렬 뉴스 검색 시작: {keyword}, 소스: {valid_sources}")
        safe_log("병렬 뉴스 검색 시작", level="info", keyword=keyword, sources=valid_sources)
        
        # 병렬로 검색 태스크 생성
        if "네이버" in valid_sources:
            tasks.append(("네이버", self.naver_scraper.search_news(keyword, max_articles)))
        if "구글" in valid_sources:
            tasks.append(("구글", self.google_scraper.search_news(keyword, max_articles)))
        
        # 병렬 실행
        if tasks:
            task_results = await asyncio.gather(
                *[task[1] for task in tasks],
                return_exceptions=True
            )
            
            for i, (source, _) in enumerate(tasks):
                if isinstance(task_results[i], Exception):
                    safe_log(f"{source} 검색 실패", level="error", error=str(task_results[i]))
                    results[source] = []
                else:
                    results[source] = task_results[i]
        
        total_urls = sum(len(urls) for urls in results.values())
        print(f"[DEBUG] ✓ 병렬 검색 완료: 총 {total_urls}개 URL")
        safe_log("병렬 검색 완료", level="info", total_urls=total_urls)
        
        return results
    
    async def extract_articles_parallel(
        self, 
        url_map: Dict[str, List[str]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        여러 기사를 병렬로 추출
        
        Args:
            url_map: 소스별 URL 딕셔너리 {"네이버": [...], "구글": [...]}
            max_concurrent: 최대 동시 처리 수
        
        Returns:
            기사 정보 목록
        """
        articles = []
        tasks = []
        
        # 모든 URL에 대해 태스크 생성
        for source, urls in url_map.items():
            scraper = self.naver_scraper if source == "네이버" else self.google_scraper
            for url in urls:
                tasks.append((source, url, scraper.extract_article(url)))
        
        print(f"[DEBUG] 병렬 기사 추출 시작: {len(tasks)}개 기사")
        safe_log("병렬 기사 추출 시작", level="info", count=len(tasks))
        
        # 세마포어로 동시 처리 수 제한
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_with_semaphore(source: str, url: str, coro):
            async with semaphore:
                try:
                    result = await coro
                    return result
                except Exception as e:
                    safe_log("기사 추출 실패", level="warning", error=str(e), url=url)
                    return None
        
        # 병렬 실행
        results = await asyncio.gather(
            *[extract_with_semaphore(s, u, c) for s, u, c in tasks],
            return_exceptions=True
        )
        
        # 결과 필터링 (None과 Exception 제외)
        for result in results:
            if result and not isinstance(result, Exception):
                articles.append(result)
        
        print(f"[DEBUG] ✓ 병렬 기사 추출 완료: {len(articles)}개 성공")
        safe_log("병렬 기사 추출 완료", level="info", success_count=len(articles))
        
        return articles
    
    async def scrape_all(
        self, 
        keyword: str, 
        sources: List[str], 
        max_articles: int = 5
    ) -> List[Dict[str, Any]]:
        """
        전체 크롤링 파이프라인 (검색 + 추출, 모두 병렬)
        
        Args:
            keyword: 검색 키워드
            sources: 뉴스 소스 목록
            max_articles: 소스당 최대 기사 수
        
        Returns:
            기사 정보 목록
        """
        # 1. 병렬 검색
        url_map = await self.search_news_parallel(keyword, sources, max_articles)
        
        # 2. 병렬 추출
        articles = await self.extract_articles_parallel(url_map)
        
        return articles
    
    async def cleanup(self):
        """리소스 정리"""
        await asyncio.gather(
            self.naver_scraper.cleanup(),
            self.google_scraper.cleanup(),
            return_exceptions=True
        )


# 동기 래퍼 (기존 코드 호환성)
class PlaywrightNewsScraperSync:
    """
    동기 래퍼 클래스 (기존 코드 호환성 유지)
    
    기존 동기 코드에서 Playwright 비동기 스크래퍼를 사용할 수 있게 해줍니다.
    """
    
    def __init__(self):
        self._scraper = PlaywrightNewsScraper()
        self._loop = None
    
    def _get_loop(self):
        """이벤트 루프 가져오기"""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
            return self._loop
    
    def search_news(self, keyword: str, sources: List[str], max_articles: int = 5) -> List[str]:
        """동기 방식 뉴스 검색"""
        async def _search():
            result = await self._scraper.search_news_parallel(keyword, sources, max_articles)
            # 모든 URL을 하나의 리스트로 합침
            all_urls = []
            for urls in result.values():
                all_urls.extend(urls)
            return all_urls
        
        loop = self._get_loop()
        return loop.run_until_complete(_search())
    
    def scrape_article(self, url: str, source: str = "네이버") -> Optional[Dict[str, Any]]:
        """동기 방식 기사 추출"""
        async def _extract():
            if source == "네이버":
                return await self._scraper.naver_scraper.extract_article(url)
            else:
                return await self._scraper.google_scraper.extract_article(url)
        
        loop = self._get_loop()
        return loop.run_until_complete(_extract())
    
    def cleanup(self):
        """리소스 정리"""
        async def _cleanup():
            await self._scraper.cleanup()
        
        loop = self._get_loop()
        loop.run_until_complete(_cleanup())
        if self._loop:
            self._loop.close()
            self._loop = None

