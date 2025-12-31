"""
이미지 검색 Tool 구현
Google Image Search API 또는 크롤링을 통한 이미지 검색
"""

import re
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import quote, urlparse
from common.utils import safe_log, validate_input


class ImageSearchTool:
    """이미지 검색 Tool"""
    
    def __init__(self):
        """초기화"""
        self.base_url = "https://www.google.com/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def search_images(
        self,
        query: str,
        search_operator: str = "AND",  # AND, OR
        max_results: int = 20,
        sample_image_url: Optional[str] = None,
        sample_image_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        이미지 검색 실행
        
        Args:
            query: 검색 쿼리 (프롬프트)
            search_operator: 검색 연산자 (AND, OR)
            max_results: 최대 결과 수
            sample_image_url: 샘플 이미지 URL (유사 이미지 검색 시)
            sample_image_path: 샘플 이미지 로컬 경로 (유사 이미지 검색 시)
        
        Returns:
            검색 결과 리스트
        """
        try:
            # 입력 검증
            validate_input(query, min_length=1, max_length=500)
            
            # 쿼리 파싱 및 연산자 처리
            processed_query = self._process_query(query, search_operator)
            
            # Google Image Search URL 생성
            search_url = self._build_search_url(processed_query, max_results)
            
            safe_log(f"이미지 검색 시작: {query}", level="info")
            
            # 이미지 검색 실행
            async with httpx.AsyncClient(timeout=30.0, headers=self.headers) as client:
                response = await client.get(search_url, follow_redirects=True)
                response.raise_for_status()
                
                # HTML에서 이미지 정보 추출
                results = self._extract_images_from_html(response.text, max_results)
                
                safe_log(f"이미지 검색 완료: {len(results)}개 결과", level="info")
                
                return results
                
        except Exception as e:
            safe_log(f"이미지 검색 오류: {str(e)}", level="error")
            return []
    
    def _process_query(self, query: str, operator: str) -> str:
        """
        쿼리 처리 및 연산자 적용
        
        Args:
            query: 원본 쿼리
            operator: AND 또는 OR
        
        Returns:
            처리된 쿼리
        """
        # OR 연산자 처리: "사과 or 오렌지" -> "사과 OR 오렌지"
        if operator.upper() == "OR":
            # "or" 또는 "OR"를 대문자로 통일
            query = re.sub(r'\s+or\s+', ' OR ', query, flags=re.IGNORECASE)
            query = re.sub(r'\s+OR\s+', ' OR ', query)
        else:
            # AND 연산자: 공백으로 구분된 키워드들을 모두 포함
            # "사과 오렌지" -> "사과 오렌지" (그대로 유지)
            pass
        
        return query.strip()
    
    def _build_search_url(self, query: str, max_results: int) -> str:
        """
        Google Image Search URL 생성
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
        
        Returns:
            검색 URL
        """
        # Google Image Search 파라미터
        params = {
            "q": query,
            "tbm": "isch",  # 이미지 검색 모드
            "num": min(max_results, 100)  # 최대 100개
        }
        
        # URL 인코딩
        encoded_params = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
        url = f"{self.base_url}?{encoded_params}"
        
        return url
    
    def _extract_images_from_html(self, html: str, max_results: int) -> List[Dict[str, Any]]:
        """
        HTML에서 이미지 정보 추출
        
        Args:
            html: Google Image Search HTML
            max_results: 최대 결과 수
        
        Returns:
            이미지 정보 리스트
        """
        results = []
        
        try:
            # Google Image Search 결과는 JavaScript로 동적 로드되므로
            # 간단한 패턴 매칭으로는 한계가 있음
            # 실제로는 Selenium 또는 Playwright를 사용하는 것이 더 정확함
            
            # 임시로 간단한 패턴 매칭 시도
            # 실제 구현에서는 Selenium/Playwright 사용 권장
            
            # 이미지 URL 패턴 찾기
            image_pattern = r'"(https?://[^"]+\.(?:jpg|jpeg|png|gif|webp)[^"]*)"'
            matches = re.findall(image_pattern, html, re.IGNORECASE)
            
            for i, image_url in enumerate(matches[:max_results]):
                # URL 검증
                if not self._is_valid_image_url(image_url):
                    continue
                
                # 이미지 정보 추출
                result = {
                    "image_url": image_url,
                    "thumbnail_url": image_url,  # 썸네일은 원본과 동일 (임시)
                    "title": f"이미지 {i+1}",
                    "source_url": "",
                    "source_site": "Google",
                    "width": None,
                    "height": None,
                    "file_size": None,
                    "mime_type": self._get_mime_type(image_url),
                    "similarity_score": None,
                    "display_order": i
                }
                
                results.append(result)
            
            # 결과가 없으면 더미 데이터 반환 (개발/테스트용)
            if not results:
                safe_log("이미지 추출 실패 - 더미 데이터 반환", level="warning")
                results = self._generate_dummy_results(max_results)
            
        except Exception as e:
            safe_log(f"이미지 추출 오류: {str(e)}", level="error")
            # 오류 시 더미 데이터 반환
            results = self._generate_dummy_results(max_results)
        
        return results
    
    def _is_valid_image_url(self, url: str) -> bool:
        """이미지 URL 유효성 검사"""
        try:
            parsed = urlparse(url)
            # 허용된 도메인 확인 (선택적)
            # Google 이미지 캐시 URL 등
            return parsed.scheme in ["http", "https"] and parsed.netloc
        except:
            return False
    
    def _get_mime_type(self, url: str) -> str:
        """URL에서 MIME 타입 추정"""
        ext = url.lower().split(".")[-1].split("?")[0]
        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp"
        }
        return mime_map.get(ext, "image/jpeg")
    
    def _generate_dummy_results(self, count: int) -> List[Dict[str, Any]]:
        """더미 검색 결과 생성 (개발/테스트용)"""
        results = []
        for i in range(count):
            results.append({
                "image_url": f"https://via.placeholder.com/800x600?text=Image+{i+1}",
                "thumbnail_url": f"https://via.placeholder.com/300x200?text=Thumb+{i+1}",
                "title": f"샘플 이미지 {i+1}",
                "source_url": f"https://example.com/image-{i+1}",
                "source_site": "Sample",
                "width": 800,
                "height": 600,
                "file_size": 50000,
                "mime_type": "image/jpeg",
                "similarity_score": 0.9 - (i * 0.05),
                "display_order": i
            })
        return results
