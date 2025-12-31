"""
이미지 검색 서비스 모듈
Agent 서비스를 호출하여 이미지 검색 수행
"""

import os
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings


class ImageSearchService:
    """이미지 검색 서비스 - Agent 서비스 HTTP API 호출"""

    def __init__(self):
        """서비스 초기화"""
        # Agent 서비스 URL (Docker Compose 네트워크 내부)
        self.agent_service_url = os.getenv(
            "AGENT_SERVICE_URL", 
            "http://agent:8001"  # Docker Compose 서비스 이름 사용
        )

    async def search_images(
        self,
        query: str,
        query_type: str = "text",  # text, image, mixed
        search_operator: str = "AND",  # AND, OR
        max_results: int = 20,
        sample_image_url: Optional[str] = None,
        sample_image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        이미지 검색 실행 - Agent 서비스 호출

        Args:
            query: 검색 쿼리 (프롬프트)
            query_type: 검색 타입 (text, image, mixed)
            search_operator: 검색 연산자 (AND, OR)
            max_results: 최대 결과 수
            sample_image_url: 샘플 이미지 URL (이미지 검색 시)
            sample_image_path: 샘플 이미지 로컬 경로 (이미지 검색 시)

        Returns:
            검색 결과 딕셔너리
        """
        try:
            # Agent 서비스의 /search-images 엔드포인트 호출
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5분 타임아웃
                payload = {
                    "query": query,
                    "query_type": query_type,
                    "search_operator": search_operator,
                    "max_results": max_results
                }
                
                # 샘플 이미지 정보 추가 (있는 경우)
                if sample_image_url:
                    payload["sample_image_url"] = sample_image_url
                if sample_image_path:
                    payload["sample_image_path"] = sample_image_path
                
                response = await client.post(
                    f"{self.agent_service_url}/search-images",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                return result
                
        except httpx.TimeoutException:
            raise Exception("이미지 검색 서비스 응답 시간 초과 (5분 이상 소요)")
        except httpx.HTTPStatusError as e:
            raise Exception(f"이미지 검색 서비스 오류: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"이미지 검색 서비스 호출 실패: {str(e)}")
