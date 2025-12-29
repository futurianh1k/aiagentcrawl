"""
News Scraper Tool 패키지

네이버 뉴스와 구글 뉴스를 크롤링하는 Tool
Selenium 및 Playwright 지원
"""

from .scraper import scrape_news, NewsScraperTool, NewsSource
from .models import NewsArticle, Comment

# Playwright 스크래퍼 (선택적)
try:
    from .playwright_scraper import PlaywrightNewsScraper, PlaywrightNewsScraperSync
    from .playwright_naver import PlaywrightNaverScraper
    from .playwright_google import PlaywrightGoogleScraper
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

__all__ = [
    # Selenium 기반
    "scrape_news",
    "NewsScraperTool",
    "NewsSource",
    "NewsArticle",
    "Comment",
    # Playwright 기반
    "PlaywrightNewsScraper",
    "PlaywrightNewsScraperSync",
    "PlaywrightNaverScraper",
    "PlaywrightGoogleScraper",
    "PLAYWRIGHT_AVAILABLE",
]
