"""
이미지 검색 Tool 구현
duckduckgo-search 라이브러리를 사용한 실제 키워드 기반 이미지 검색
"""

import os
import re
import asyncio
from typing import List, Dict, Any, Optional
from common.utils import safe_log, validate_input

# duckduckgo-search 라이브러리 임포트
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    safe_log("duckduckgo-search 라이브러리가 설치되지 않음", level="warning")


class ImageSearchTool:
    """이미지 검색 Tool - DuckDuckGo Search 라이브러리 사용"""
    
    def __init__(self):
        """초기화"""
        self.ddgs = DDGS() if DDGS_AVAILABLE else None
    
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
            
            # 쿼리 처리
            processed_query = self._process_query(query, search_operator)
            
            safe_log(f"이미지 검색 시작: {processed_query}", level="info")
            
            if not DDGS_AVAILABLE or not self.ddgs:
                safe_log("DuckDuckGo Search 라이브러리를 사용할 수 없음", level="error")
                return []
            
            # 동기 함수를 비동기로 실행
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                self._search_sync, 
                processed_query, 
                max_results
            )
            
            safe_log(f"이미지 검색 완료: {len(results)}개 결과", level="info")
            return results
                
        except Exception as e:
            safe_log(f"이미지 검색 오류: {str(e)}", level="error")
            return []
    
    def _search_sync(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """동기 이미지 검색 (별도 스레드에서 실행)"""
        results = []
        
        try:
            # DuckDuckGo 이미지 검색
            ddgs_results = self.ddgs.images(
                keywords=query,
                region="kr-kr",  # 한국 지역
                safesearch="moderate",
                size=None,  # 모든 크기
                type_image=None,  # 모든 타입
                layout=None,  # 모든 레이아웃
                license_image=None,  # 모든 라이선스
                max_results=max_results
            )
            
            for i, img in enumerate(ddgs_results):
                results.append({
                    "image_url": img.get("image", ""),
                    "thumbnail_url": img.get("thumbnail", "") or img.get("image", ""),
                    "title": img.get("title", f"이미지 {i+1}"),
                    "source_url": img.get("url", ""),
                    "source_site": img.get("source", "DuckDuckGo"),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "file_size": None,
                    "mime_type": self._get_mime_type(img.get("image", "")),
                    "similarity_score": None,
                    "display_order": i
                })
                
        except Exception as e:
            safe_log(f"DuckDuckGo 검색 오류: {str(e)}", level="error")
            
        return results
    
    def _process_query(self, query: str, operator: str) -> str:
        """
        쿼리 처리 및 연산자 적용
        
        Args:
            query: 원본 쿼리
            operator: AND 또는 OR
        
        Returns:
            처리된 쿼리
        """
        if operator.upper() == "OR":
            # OR 연산자: "사과 or 오렌지" -> "사과 OR 오렌지"
            query = re.sub(r'\s+or\s+', ' OR ', query, flags=re.IGNORECASE)
        # AND는 기본 동작 (공백으로 구분된 키워드)
        
        return query.strip()
    
    def _get_mime_type(self, url: str) -> str:
        """URL에서 MIME 타입 추정"""
        url_lower = url.lower()
        if ".png" in url_lower:
            return "image/png"
        elif ".gif" in url_lower:
            return "image/gif"
        elif ".webp" in url_lower:
            return "image/webp"
        elif ".svg" in url_lower:
            return "image/svg+xml"
        else:
            return "image/jpeg"
