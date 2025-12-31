"""
이미지 검색 라우터
이미지 검색 관련 엔드포인트
"""

import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.api.dependencies import get_database_session
from app.schemas.requests import ImageSearchRequest, ImageSearchResponse, ImageSearchResultData
from app.services.image_search_service import ImageSearchService
from app.models.database import ImageSearchSession, ImageSearchResult
from app.services.media_service import media_service
import os
import uuid
from pathlib import Path

router = APIRouter()


def get_image_search_service() -> ImageSearchService:
    """이미지 검색 서비스 인스턴스 반환"""
    return ImageSearchService()


@router.post("/search", response_model=ImageSearchResponse)
async def search_images(
    request: ImageSearchRequest,
    background_tasks: BackgroundTasks,
    image_search_service: ImageSearchService = Depends(get_image_search_service),
    db: Session = Depends(get_database_session)
):
    """이미지 검색 시작"""
    
    # 이미지 검색 세션 생성
    session = ImageSearchSession(
        query=request.query,
        query_type=request.query_type,
        search_operator=request.search_operator,
        status="processing",
        sample_image_url=request.sample_image_url,
        sample_image_path=request.sample_image_path
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        # 이미지 검색 서비스 호출
        search_result = await image_search_service.search_images(
            query=request.query,
            query_type=request.query_type,
            search_operator=request.search_operator,
            max_results=request.max_results,
            sample_image_url=request.sample_image_url,
            sample_image_path=request.sample_image_path
        )

        # 검색 결과 저장
        results_data = search_result.get("results", [])
        for i, result_data in enumerate(results_data):
            image_result = ImageSearchResult(
                session_id=session.id,
                image_url=result_data.get("image_url", ""),
                thumbnail_url=result_data.get("thumbnail_url"),
                image_path=result_data.get("image_path"),
                title=result_data.get("title"),
                source_url=result_data.get("source_url"),
                source_site=result_data.get("source_site"),
                width=result_data.get("width"),
                height=result_data.get("height"),
                file_size=result_data.get("file_size"),
                mime_type=result_data.get("mime_type"),
                similarity_score=result_data.get("similarity_score"),
                display_order=i
            )
            db.add(image_result)

        # 세션 업데이트
        session.status = "completed"
        session.total_results = len(results_data)
        session.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(session)

        # 결과 조회
        results = db.query(ImageSearchResult).filter(
            ImageSearchResult.session_id == session.id
        ).order_by(ImageSearchResult.display_order).all()

        return ImageSearchResponse(
            session_id=session.id,
            query=session.query,
            query_type=session.query_type,
            search_operator=session.search_operator,
            status=session.status,
            total_results=session.total_results,
            results=[
                ImageSearchResultData(
                    id=r.id,
                    image_url=r.image_url,
                    thumbnail_url=r.thumbnail_url,
                    image_path=r.image_path,
                    title=r.title,
                    source_url=r.source_url,
                    source_site=r.source_site,
                    width=r.width,
                    height=r.height,
                    file_size=r.file_size,
                    mime_type=r.mime_type,
                    similarity_score=r.similarity_score,
                    display_order=r.display_order
                )
                for r in results
            ],
            created_at=session.created_at,
            completed_at=session.completed_at
        )

    except Exception as e:
        # 에러 처리
        session.status = "failed"
        session.error_message = str(e)
        session.completed_at = datetime.utcnow()
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"이미지 검색 실패: {str(e)}")


@router.post("/search/upload", response_model=ImageSearchResponse)
async def search_images_with_upload(
    query: str = Form(..., description="검색 쿼리 (프롬프트)"),
    search_operator: str = Form(default="AND", description="검색 연산자: AND, OR"),
    max_results: int = Form(default=20, ge=1, le=100, description="최대 결과 수"),
    file: UploadFile = File(..., description="샘플 이미지 파일"),
    image_search_service: ImageSearchService = Depends(get_image_search_service),
    db: Session = Depends(get_database_session)
):
    """이미지 파일 업로드 후 유사 이미지 검색"""
    
    # 이미지 파일 저장
    MEDIA_BASE_DIR = os.getenv("MEDIA_DIR", "/app/media")
    images_dir = Path(MEDIA_BASE_DIR) / "image_search_samples"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # 파일 확장자 확인
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")
    
    # 파일 저장
    filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = images_dir / filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 상대 경로 생성
    relative_path = f"image_search_samples/{filename}"
    
    # 이미지 검색 세션 생성
    session = ImageSearchSession(
        query=query,
        query_type="image",
        search_operator=search_operator,
        status="processing",
        sample_image_path=str(relative_path)
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        # 이미지 검색 서비스 호출
        search_result = await image_search_service.search_images(
            query=query,
            query_type="image",
            search_operator=search_operator,
            max_results=max_results,
            sample_image_path=str(relative_path)
        )

        # 검색 결과 저장
        results_data = search_result.get("results", [])
        for i, result_data in enumerate(results_data):
            image_result = ImageSearchResult(
                session_id=session.id,
                image_url=result_data.get("image_url", ""),
                thumbnail_url=result_data.get("thumbnail_url"),
                image_path=result_data.get("image_path"),
                title=result_data.get("title"),
                source_url=result_data.get("source_url"),
                source_site=result_data.get("source_site"),
                width=result_data.get("width"),
                height=result_data.get("height"),
                file_size=result_data.get("file_size"),
                mime_type=result_data.get("mime_type"),
                similarity_score=result_data.get("similarity_score"),
                display_order=i
            )
            db.add(image_result)

        # 세션 업데이트
        session.status = "completed"
        session.total_results = len(results_data)
        session.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(session)

        # 결과 조회
        results = db.query(ImageSearchResult).filter(
            ImageSearchResult.session_id == session.id
        ).order_by(ImageSearchResult.display_order).all()

        return ImageSearchResponse(
            session_id=session.id,
            query=session.query,
            query_type=session.query_type,
            search_operator=session.search_operator,
            status=session.status,
            total_results=session.total_results,
            results=[
                ImageSearchResultData(
                    id=r.id,
                    image_url=r.image_url,
                    thumbnail_url=r.thumbnail_url,
                    image_path=r.image_path,
                    title=r.title,
                    source_url=r.source_url,
                    source_site=r.source_site,
                    width=r.width,
                    height=r.height,
                    file_size=r.file_size,
                    mime_type=r.mime_type,
                    similarity_score=r.similarity_score,
                    display_order=r.display_order
                )
                for r in results
            ],
            created_at=session.created_at,
            completed_at=session.completed_at
        )

    except Exception as e:
        # 에러 처리
        session.status = "failed"
        session.error_message = str(e)
        session.completed_at = datetime.utcnow()
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"이미지 검색 실패: {str(e)}")


@router.get("/sessions/{session_id}", response_model=ImageSearchResponse)
async def get_image_search_session(
    session_id: int,
    db: Session = Depends(get_database_session)
):
    """이미지 검색 세션 조회"""
    
    session = db.query(ImageSearchSession).filter(
        ImageSearchSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="이미지 검색 세션을 찾을 수 없습니다")
    
    # 결과 조회
    results = db.query(ImageSearchResult).filter(
        ImageSearchResult.session_id == session_id
    ).order_by(ImageSearchResult.display_order).all()
    
    return ImageSearchResponse(
        session_id=session.id,
        query=session.query,
        query_type=session.query_type,
        search_operator=session.search_operator,
        status=session.status,
        total_results=session.total_results,
        results=[
            ImageSearchResultData(
                id=r.id,
                image_url=r.image_url,
                thumbnail_url=r.thumbnail_url,
                image_path=r.image_path,
                title=r.title,
                source_url=r.source_url,
                source_site=r.source_site,
                width=r.width,
                height=r.height,
                file_size=r.file_size,
                mime_type=r.mime_type,
                similarity_score=r.similarity_score,
                display_order=r.display_order
            )
            for r in results
        ],
        created_at=session.created_at,
        completed_at=session.completed_at
    )


@router.get("/sessions")
async def list_image_search_sessions(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_database_session)
):
    """이미지 검색 세션 목록 조회"""
    
    offset = (page - 1) * per_page
    
    sessions = db.query(ImageSearchSession).order_by(
        ImageSearchSession.created_at.desc()
    ).offset(offset).limit(per_page).all()
    
    total = db.query(ImageSearchSession).count()
    
    return {
        "sessions": [
            {
                "id": s.id,
                "query": s.query,
                "query_type": s.query_type,
                "search_operator": s.search_operator,
                "status": s.status,
                "total_results": s.total_results,
                "created_at": s.created_at,
                "completed_at": s.completed_at
            }
            for s in sessions
        ],
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.delete("/sessions/{session_id}")
async def delete_image_search_session(
    session_id: int,
    db: Session = Depends(get_database_session)
):
    """이미지 검색 세션 삭제"""
    
    session = db.query(ImageSearchSession).filter(
        ImageSearchSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="이미지 검색 세션을 찾을 수 없습니다")
    
    # 세션 삭제 (CASCADE로 결과도 자동 삭제)
    db.delete(session)
    db.commit()
    
    return {"message": "이미지 검색 세션이 삭제되었습니다"}
