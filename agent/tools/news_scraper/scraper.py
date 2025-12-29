"""
News Scraper Tool

Selenium을 이용한 뉴스 크롤링 Tool 구현
네이버 뉴스와 구글 뉴스 지원
보안 가이드라인: robots.txt 준수, Rate Limit 준수, User-Agent 설정

이 모듈은 분리된 크롤러(NaverNewsScraper, GoogleNewsScraper)를 사용하는
통합 인터페이스를 제공합니다.
"""

import time
from typing import List, Dict, Any, Optional
from enum import Enum

from langchain.tools import tool

from common.utils import safe_log, validate_input, validate_url
from .models import NewsArticle
from .naver_scraper import NaverNewsScraper
from .google_scraper import GoogleNewsScraper


class NewsSource(str, Enum):
    """뉴스 소스 열거형"""
    NAVER = "네이버"
    GOOGLE = "구글"


class NewsScraperTool:
    """
    뉴스 스크레이퍼 Tool 클래스 (통합 인터페이스)
    
    분리된 크롤러(NaverNewsScraper, GoogleNewsScraper)를 사용하여
    여러 뉴스 소스에서 뉴스를 수집합니다.
    """

    def __init__(self):
        """초기화"""
        self.naver_scraper: Optional[NaverNewsScraper] = None
        self.google_scraper: Optional[GoogleNewsScraper] = None

    def _get_naver_scraper(self) -> NaverNewsScraper:
        """네이버 크롤러 인스턴스 반환 (지연 초기화)"""
        if self.naver_scraper is None:
            self.naver_scraper = NaverNewsScraper()
        return self.naver_scraper

    def _get_google_scraper(self) -> GoogleNewsScraper:
        """구글 크롤러 인스턴스 반환 (지연 초기화)"""
        if self.google_scraper is None:
            self.google_scraper = GoogleNewsScraper()
        return self.google_scraper

    def search_naver_news(self, keyword: str, max_articles: int = 5) -> List[str]:
        """
        네이버 뉴스에서 키워드 검색 후 기사 URL 목록 반환
        
        Args:
            keyword: 검색할 키워드
            max_articles: 최대 수집할 기사 수
        
        Returns:
            기사 URL 목록
        """
        scraper = self._get_naver_scraper()
        return scraper.search_news(keyword, max_articles)

    def search_google_news(self, keyword: str, max_articles: int = 5) -> List[str]:
        """
        구글 뉴스에서 키워드 검색 후 기사 URL 목록 반환
        
        Args:
            keyword: 검색할 키워드
            max_articles: 최대 수집할 기사 수
        
        Returns:
            기사 URL 목록
        """
        scraper = self._get_google_scraper()
        return scraper.search_news(keyword, max_articles)

    def search_news(self, keyword: str, sources: List[str], max_articles: int = 5) -> List[str]:
        """
        여러 소스에서 뉴스 검색
        
        Args:
            keyword: 검색할 키워드
            sources: 뉴스 소스 목록 (["네이버", "구글"])
            max_articles: 소스당 최대 기사 수
        
        Returns:
            기사 URL 목록
        """
        all_urls = []
        
        # 소스 매핑 (다양한 이름 지원)
        source_mapping = {
            "네이버": "네이버",
            "naver": "네이버",
            "구글": "구글",
            "google": "구글",
        }
        
        # 지원되는 소스만 필터링
        valid_sources = []
        for source in sources:
            normalized_source = source_mapping.get(source, None)
            if normalized_source:
                if normalized_source not in valid_sources:
                    valid_sources.append(normalized_source)
                if source != normalized_source:
                    safe_log(f"소스 매핑: {source} -> {normalized_source}", level="info")
            else:
                safe_log("지원하지 않는 뉴스 소스", level="warning", source=source)
        
        # 지원되는 소스가 없으면 네이버를 기본값으로 사용
        if not valid_sources:
            valid_sources = ["네이버"]
            safe_log("지원되는 소스가 없어 네이버를 기본값으로 사용", level="info")
        
        for source in valid_sources:
            try:
                if source == "네이버" or source == NewsSource.NAVER.value:
                    urls = self.search_naver_news(keyword, max_articles)
                    all_urls.extend(urls)
                elif source == "구글" or source == NewsSource.GOOGLE.value:
                    urls = self.search_google_news(keyword, max_articles)
                    all_urls.extend(urls)
                else:
                    safe_log("지원하지 않는 뉴스 소스", level="warning", source=source)
            except Exception as e:
                safe_log(f"{source} 뉴스 검색 실패", level="error", error=str(e))
                continue

        # 중복 제거
        unique_urls = list(dict.fromkeys(all_urls))  # 순서 유지하면서 중복 제거
        safe_log("전체 기사 URL 수집 완료", level="info", total=len(unique_urls), sources=valid_sources)
        return unique_urls


    def scrape_article(self, url: str, source: str = "naver") -> NewsArticle:
        """
        단일 기사 스크레이핑
        
        Args:
            url: 기사 URL
            source: 뉴스 소스 ("naver" 또는 "google")
        
        Returns:
            NewsArticle 객체
        """
        safe_log("기사 스크레이핑 시작", level="info", url=url, source=source)

        # 소스에 따라 적절한 크롤러 사용
        if source == "naver":
            scraper = self._get_naver_scraper()
        elif source == "google":
            scraper = self._get_google_scraper()
        else:
            # 기본값으로 네이버 사용
            safe_log(f"알 수 없는 소스 '{source}', 네이버로 대체", level="warning")
            scraper = self._get_naver_scraper()

        return scraper.scrape_article(url)

    def cleanup(self):
        """리소스 정리"""
        if self.naver_scraper:
            try:
                self.naver_scraper.cleanup()
            except Exception as e:
                safe_log("네이버 크롤러 정리 오류", level="warning", error=str(e))
        
        if self.google_scraper:
            try:
                self.google_scraper.cleanup()
            except Exception as e:
                safe_log("구글 크롤러 정리 오류", level="warning", error=str(e))


@tool
def scrape_news(keyword: str, sources: List[str] = None, max_articles: int = 3) -> List[Dict[str, Any]]:
    """
    뉴스 스크레이핑 Tool 함수

    Args:
        keyword: 검색할 키워드
        sources: 뉴스 소스 목록 (["네이버", "구글"])
        max_articles: 소스당 최대 수집할 기사 수 (기본값: 3)

    Returns:
        스크레이핑된 기사들의 정보
    """
    if sources is None:
        sources = ["네이버"]

    scraper = NewsScraperTool()

    try:
        # 입력 검증
        if not validate_input(keyword, max_length=100):
            return [{
                "error": f"유효하지 않은 키워드: {keyword}",
                "keyword": keyword
            }]

        # 1단계: 뉴스 소스에서 기사 URL 검색
        article_urls = scraper.search_news(keyword, sources, max_articles)

        if not article_urls:
            return [{
                "error": f"'{keyword}' 키워드로 기사를 찾을 수 없습니다.",
                "keyword": keyword,
                "sources": sources
            }]

        # 2단계: 각 기사 상세 정보 추출
        scraped_articles = []

        for i, url in enumerate(article_urls, 1):
            safe_log(f"기사 처리 중 ({i}/{len(article_urls)})", level="info")

            # URL에서 소스 판단
            source = "naver" if "naver.com" in url else "google"

            article = scraper.scrape_article(url, source)
            article_dict = article.to_dict()
            article_dict["keyword"] = keyword
            scraped_articles.append(article_dict)

            # Rate Limit 준수
            time.sleep(1)

        return scraped_articles

    except Exception as e:
        safe_log("뉴스 스크레이핑 중 오류", level="error", error=str(e))
        return [{
            "error": f"뉴스 스크레이핑 중 오류: {str(e)}",
            "keyword": keyword,
            "sources": sources
        }]

    finally:
        scraper.cleanup()
