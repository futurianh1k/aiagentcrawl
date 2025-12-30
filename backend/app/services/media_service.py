"""
미디어 저장 서비스
이미지, 테이블 등 미디어 파일 저장 및 관리
"""

import os
import uuid
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

# 미디어 저장 디렉토리
MEDIA_BASE_DIR = os.getenv("MEDIA_DIR", "/app/media")


class MediaService:
    """미디어 파일 저장 서비스"""
    
    def __init__(self):
        """초기화"""
        self.base_dir = Path(MEDIA_BASE_DIR)
        self.images_dir = self.base_dir / "images"
        self.tables_dir = self.base_dir / "tables"
        self._initialized = False
    
    def _ensure_directories(self):
        """디렉토리 생성 (지연 초기화)"""
        if self._initialized:
            return True
        
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            self.images_dir.mkdir(parents=True, exist_ok=True)
            self.tables_dir.mkdir(parents=True, exist_ok=True)
            self._initialized = True
            return True
        except PermissionError as e:
            print(f"[WARN] 미디어 디렉토리 생성 실패 (권한 문제): {e}")
            return False
        except Exception as e:
            print(f"[WARN] 미디어 디렉토리 생성 실패: {e}")
            return False
    
    async def save_article_media(
        self, 
        article_id: int, 
        images: List[Dict], 
        tables: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        기사의 이미지와 테이블 저장
        
        Args:
            article_id: 기사 ID
            images: 이미지 정보 리스트 [{url, alt, caption, ...}]
            tables: 테이블 정보 리스트 [{html, caption, ...}]
        
        Returns:
            저장된 미디어 정보
        """
        saved_images = []
        saved_tables = []
        
        # 기본 디렉토리 확인
        if not self._ensure_directories():
            # 디렉토리 생성 실패 시 원본 URL만 반환
            for img in images:
                saved_images.append({
                    "media_type": "image",
                    "file_path": None,
                    "original_url": img.get("url"),
                    "caption": img.get("caption", ""),
                    "alt_text": img.get("alt", ""),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "file_size": None,
                    "mime_type": None,
                    "display_order": img.get("order", 0),
                })
            return {"images": saved_images, "tables": []}
        
        # 기사별 디렉토리 생성
        article_images_dir = self.images_dir / str(article_id)
        article_tables_dir = self.tables_dir / str(article_id)
        
        try:
            article_images_dir.mkdir(parents=True, exist_ok=True)
            article_tables_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[WARN] 기사별 디렉토리 생성 실패: {e}")
            # 원본 URL만 반환
            for img in images:
                saved_images.append({
                    "media_type": "image",
                    "file_path": None,
                    "original_url": img.get("url"),
                    "caption": img.get("caption", ""),
                    "alt_text": img.get("alt", ""),
                    "display_order": img.get("order", 0),
                })
            return {"images": saved_images, "tables": []}
        
        # 이미지 저장 (비동기 병렬)
        if images:
            image_tasks = [
                self._download_and_save_image(img, article_images_dir, i)
                for i, img in enumerate(images)
            ]
            saved_images = await asyncio.gather(*image_tasks, return_exceptions=True)
            saved_images = [img for img in saved_images if img and not isinstance(img, Exception)]
        
        # 테이블 저장
        for i, table in enumerate(tables):
            saved_table = self._save_table(table, article_tables_dir, i)
            if saved_table:
                saved_tables.append(saved_table)
        
        return {
            "images": saved_images,
            "tables": saved_tables
        }
    
    async def _download_and_save_image(
        self, 
        image_info: Dict, 
        save_dir: Path, 
        order: int
    ) -> Optional[Dict]:
        """
        이미지 다운로드 및 저장
        
        Args:
            image_info: 이미지 정보 {url, alt, caption, ...}
            save_dir: 저장 디렉토리
            order: 표시 순서
        
        Returns:
            저장된 이미지 정보
        """
        url = image_info.get("url")
        if not url:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                # MIME 타입 확인
                content_type = response.headers.get("content-type", "image/jpeg")
                
                # 확장자 결정
                ext_map = {
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                    "image/webp": ".webp",
                    "image/gif": ".gif",
                }
                ext = ext_map.get(content_type.split(";")[0], ".jpg")
                
                # 파일명 생성
                filename = f"{uuid.uuid4().hex}{ext}"
                file_path = save_dir / filename
                
                # 파일 저장
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                # 상대 경로 계산 (API에서 제공할 경로)
                relative_path = f"images/{save_dir.name}/{filename}"
                
                return {
                    "media_type": "image",
                    "file_path": relative_path,
                    "original_url": url,
                    "caption": image_info.get("caption", ""),
                    "alt_text": image_info.get("alt", ""),
                    "width": image_info.get("width"),
                    "height": image_info.get("height"),
                    "file_size": len(response.content),
                    "mime_type": content_type.split(";")[0],
                    "display_order": order,
                }
        except Exception as e:
            print(f"[WARN] 이미지 다운로드 실패: {url[:50]}... - {str(e)}")
            # 다운로드 실패 시 원본 URL만 저장
            return {
                "media_type": "image",
                "file_path": None,
                "original_url": url,
                "caption": image_info.get("caption", ""),
                "alt_text": image_info.get("alt", ""),
                "width": image_info.get("width"),
                "height": image_info.get("height"),
                "file_size": None,
                "mime_type": None,
                "display_order": order,
            }
    
    def _save_table(
        self, 
        table_info: Dict, 
        save_dir: Path, 
        order: int
    ) -> Optional[Dict]:
        """
        테이블 HTML 저장
        
        Args:
            table_info: 테이블 정보 {html, caption, rows, cols, ...}
            save_dir: 저장 디렉토리
            order: 표시 순서
        
        Returns:
            저장된 테이블 정보
        """
        html = table_info.get("html")
        if not html:
            return None
        
        try:
            # 파일명 생성
            filename = f"{uuid.uuid4().hex}.html"
            file_path = save_dir / filename
            
            # HTML 파일로 저장 (스타일 추가)
            styled_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
</head>
<body>
    <table>{html}</table>
</body>
</html>
"""
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(styled_html)
            
            # 상대 경로 계산
            relative_path = f"tables/{save_dir.name}/{filename}"
            
            return {
                "media_type": "table",
                "file_path": relative_path,
                "original_url": None,
                "caption": table_info.get("caption", ""),
                "table_html": html[:5000],  # DB에도 저장 (5000자 제한)
                "width": table_info.get("cols"),
                "height": table_info.get("rows"),
                "file_size": len(styled_html.encode("utf-8")),
                "mime_type": "text/html",
                "display_order": order,
            }
        except Exception as e:
            print(f"[WARN] 테이블 저장 실패: {str(e)}")
            return None
    
    def delete_article_media(self, article_id: int) -> bool:
        """
        기사의 미디어 파일 삭제
        
        Args:
            article_id: 기사 ID
        
        Returns:
            삭제 성공 여부
        """
        import shutil
        
        try:
            article_images_dir = self.images_dir / str(article_id)
            article_tables_dir = self.tables_dir / str(article_id)
            
            if article_images_dir.exists():
                shutil.rmtree(article_images_dir)
            if article_tables_dir.exists():
                shutil.rmtree(article_tables_dir)
            
            return True
        except Exception as e:
            print(f"[ERROR] 미디어 삭제 실패: {str(e)}")
            return False
    
    def get_media_url(self, file_path: str) -> str:
        """
        미디어 파일의 접근 URL 반환
        
        Args:
            file_path: 상대 파일 경로
        
        Returns:
            접근 가능한 URL
        """
        return f"/api/media/{file_path}"


# 싱글톤 인스턴스
media_service = MediaService()
