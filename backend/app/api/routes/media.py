"""
미디어 라우터
이미지, 테이블 등 미디어 파일 제공
"""

import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.dependencies import get_database_session
from app.models.database import ArticleMedia, Article

router = APIRouter()

# 미디어 저장 디렉토리
MEDIA_BASE_DIR = os.getenv("MEDIA_DIR", "/app/media")


@router.get("/images/{article_id}/{filename}")
async def get_image(article_id: int, filename: str):
    """이미지 파일 제공"""
    file_path = Path(MEDIA_BASE_DIR) / "images" / str(article_id) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")
    
    # MIME 타입 결정
    ext = file_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    media_type = media_types.get(ext, "application/octet-stream")
    
    return FileResponse(file_path, media_type=media_type)


@router.get("/tables/{article_id}/{filename}")
async def get_table(article_id: int, filename: str):
    """테이블 HTML 파일 제공"""
    file_path = Path(MEDIA_BASE_DIR) / "tables" / str(article_id) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="테이블을 찾을 수 없습니다")
    
    return FileResponse(file_path, media_type="text/html; charset=utf-8")


@router.get("/article/{article_id}")
async def get_article_media(
    article_id: int,
    db: Session = Depends(get_database_session)
):
    """기사의 미디어 목록 조회"""
    
    # 기사 확인
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다")
    
    # 미디어 조회
    media_list = db.query(ArticleMedia).filter(
        ArticleMedia.article_id == article_id
    ).order_by(ArticleMedia.display_order).all()
    
    images = []
    tables = []
    
    for media in media_list:
        media_data = {
            "id": media.id,
            "file_path": media.file_path,
            "original_url": media.original_url,
            "caption": media.caption,
            "alt_text": media.alt_text,
            "width": media.width,
            "height": media.height,
            "display_order": media.display_order,
        }
        
        # 접근 URL 생성
        if media.file_path:
            media_data["url"] = f"/api/media/{media.file_path}"
        elif media.original_url:
            media_data["url"] = media.original_url
        else:
            media_data["url"] = None
        
        if media.media_type == "image":
            images.append(media_data)
        elif media.media_type == "table":
            media_data["table_html"] = media.table_html
            media_data["rows"] = media.height
            media_data["cols"] = media.width
            tables.append(media_data)
    
    return {
        "article_id": article_id,
        "article_title": article.title,
        "images": images,
        "tables": tables,
        "total_images": len(images),
        "total_tables": len(tables),
    }


@router.get("/session/{session_id}")
async def get_session_media(
    session_id: int,
    db: Session = Depends(get_database_session)
):
    """세션의 모든 미디어 목록 조회"""
    
    # 세션의 모든 기사 ID 조회
    articles = db.query(Article).filter(Article.session_id == session_id).all()
    
    if not articles:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    article_ids = [a.id for a in articles]
    
    # 미디어 조회
    media_list = db.query(ArticleMedia).filter(
        ArticleMedia.article_id.in_(article_ids)
    ).order_by(ArticleMedia.article_id, ArticleMedia.display_order).all()
    
    # 기사별로 그룹화
    result = []
    for article in articles:
        article_media = [m for m in media_list if m.article_id == article.id]
        
        images = []
        tables = []
        
        for media in article_media:
            media_data = {
                "id": media.id,
                "url": f"/api/media/{media.file_path}" if media.file_path else media.original_url,
                "caption": media.caption,
            }
            
            if media.media_type == "image":
                images.append(media_data)
            elif media.media_type == "table":
                tables.append(media_data)
        
        if images or tables:
            result.append({
                "article_id": article.id,
                "article_title": article.title[:50],
                "images": images,
                "tables": tables,
            })
    
    return {
        "session_id": session_id,
        "articles_with_media": len(result),
        "total_images": sum(len(r["images"]) for r in result),
        "total_tables": sum(len(r["tables"]) for r in result),
        "articles": result,
    }
