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
    # 이미지 추출용 셀렉터
    "images": [
        "#dic_area img",
        "#newsct_article img",
        ".news_end_body_container img",
        ".article_body img",
        "article img",
        "#articleBody img",
    ],
    # 테이블 추출용 셀렉터
    "tables": [
        "#dic_area table",
        "#newsct_article table",
        ".news_end_body_container table",
        ".article_body table",
        "article table",
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
        네이버 뉴스 기사 내용 추출 (이미지, 테이블 포함)
        
        Args:
            url: 기사 URL
        
        Returns:
            기사 정보 딕셔너리 (images, tables 포함)
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
            
            # 이미지 추출
            images = await self._extract_images(page)
            
            # 테이블 추출
            tables = await self._extract_tables(page)
            
            if title and content and len(content) > 50:
                print(f"[DEBUG] ✓ 네이버 기사 추출 성공: {title[:30]}... (이미지: {len(images)}개, 테이블: {len(tables)}개)")
                return {
                    "title": title,
                    "content": content[:3000],  # 최대 3000자
                    "url": url,
                    "source": "네이버",
                    "images": images,
                    "tables": tables,
                }
            
        except Exception as e:
            safe_log("네이버 기사 추출 오류", level="error", error=str(e), url=url)
        finally:
            await page.close()
        
        return None
    
    async def _extract_images(self, page) -> List[Dict[str, Any]]:
        """
        기사 내 이미지 추출
        
        Returns:
            이미지 정보 리스트 [{url, alt, caption, width, height}, ...]
        """
        images = []
        
        try:
            for selector in NAVER_SELECTORS["images"]:
                try:
                    elements = await page.query_selector_all(selector)
                    for i, element in enumerate(elements):
                        if len(images) >= 10:  # 최대 10개 이미지
                            break
                        
                        img_src = await element.get_attribute('src')
                        if not img_src or not self._is_valid_image_url(img_src):
                            # data-src 속성 확인 (lazy loading)
                            img_src = await element.get_attribute('data-src')
                        
                        if img_src and self._is_valid_image_url(img_src):
                            # 상대 경로를 절대 경로로 변환
                            if img_src.startswith('//'):
                                img_src = 'https:' + img_src
                            elif img_src.startswith('/'):
                                img_src = 'https://n.news.naver.com' + img_src
                            
                            alt_text = await element.get_attribute('alt') or ""
                            
                            # 이미지 크기 추출
                            width = await element.get_attribute('width')
                            height = await element.get_attribute('height')
                            
                            # 캡션 추출 (부모 요소에서 찾기)
                            caption = ""
                            try:
                                parent = await element.evaluate_handle("el => el.parentElement")
                                caption_el = await parent.query_selector("em, span.img_desc, figcaption")
                                if caption_el:
                                    caption = await caption_el.inner_text()
                            except:
                                pass
                            
                            images.append({
                                "url": img_src,
                                "alt": alt_text,
                                "caption": caption,
                                "width": int(width) if width and width.isdigit() else None,
                                "height": int(height) if height and height.isdigit() else None,
                                "order": i,
                            })
                    
                    if images:
                        break
                except Exception:
                    continue
        except Exception as e:
            safe_log("이미지 추출 오류", level="warning", error=str(e))
        
        return images
    
    async def _extract_tables(self, page) -> List[Dict[str, Any]]:
        """
        기사 내 테이블(표) 추출
        
        Returns:
            테이블 정보 리스트 [{html, caption, rows, cols}, ...]
        """
        tables = []
        
        try:
            for selector in NAVER_SELECTORS["tables"]:
                try:
                    elements = await page.query_selector_all(selector)
                    for i, element in enumerate(elements):
                        if len(tables) >= 5:  # 최대 5개 테이블
                            break
                        
                        # 테이블 HTML 추출
                        table_html = await element.inner_html()
                        
                        # 테이블이 너무 작으면 스킵 (최소 2행)
                        row_count = await element.evaluate("el => el.querySelectorAll('tr').length")
                        if row_count < 2:
                            continue
                        
                        # 열 개수
                        col_count = await element.evaluate("""
                            el => {
                                const firstRow = el.querySelector('tr');
                                return firstRow ? firstRow.querySelectorAll('td, th').length : 0;
                            }
                        """)
                        
                        # 캡션 추출
                        caption = ""
                        try:
                            caption_el = await element.query_selector("caption")
                            if caption_el:
                                caption = await caption_el.inner_text()
                        except:
                            pass
                        
                        tables.append({
                            "html": table_html[:5000],  # 최대 5000자
                            "caption": caption,
                            "rows": row_count,
                            "cols": col_count,
                            "order": i,
                        })
                    
                    if tables:
                        break
                except Exception:
                    continue
        except Exception as e:
            safe_log("테이블 추출 오류", level="warning", error=str(e))
        
        return tables
    
    def _is_valid_image_url(self, url: str) -> bool:
        """유효한 이미지 URL인지 확인 (아이콘, 배너 등 제외)"""
        if not url:
            return False
        
        # 제외할 패턴 (광고, 아이콘, 로고 등)
        exclude_patterns = [
            "icon", "logo", "banner", "ad_", "advert",
            "btn_", "button", "sprite", "blank", "spacer",
            "1x1", "pixel", ".gif",  # 작은 투명 이미지
            "naver.pstatic.net/static",  # 네이버 정적 리소스
        ]
        
        url_lower = url.lower()
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        # 이미지 확장자 확인
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        has_valid_ext = any(ext in url_lower for ext in valid_extensions)
        
        # imgnews.pstatic.net (네이버 뉴스 이미지 서버)는 확장자 없이도 허용
        if 'imgnews.pstatic.net' in url_lower or 'image.news.naver.com' in url_lower:
            return True
        
        return has_valid_ext
    
    def _is_valid_naver_url(self, url: str) -> bool:
        """유효한 네이버 뉴스 URL인지 확인"""
        valid_patterns = [
            "n.news.naver.com/mnews/article/",
            "news.naver.com/main/read",
            "n.news.naver.com/article/",
        ]
        return any(pattern in url for pattern in valid_patterns)

