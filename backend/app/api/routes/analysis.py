"""
분석 결과 라우터
저장된 분석 결과 조회 엔드포인트
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.dependencies import get_database_session
from app.schemas.requests import AnalysisResponse, SessionListResponse
from app.models.database import AnalysisSession, Article, Comment, Keyword

router = APIRouter()

@router.get("/{session_id}", response_model=AnalysisResponse)
async def get_analysis_result(
    session_id: int,
    db: Session = Depends(get_database_session)
):
    """분석 결과 조회"""

    # 세션 조회
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="분석 세션을 찾을 수 없습니다")

    # 기사 조회
    articles = db.query(Article).filter(Article.session_id == session_id).all()
    articles_data = []

    for article in articles:
        # 댓글 수 계산
        comment_count = db.query(Comment).filter(Comment.article_id == article.id).count()

        articles_data.append({
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "url": article.url,
            "source": article.source,
            "published_at": article.published_at,
            "sentiment_score": article.sentiment_score or 0.0,
            "sentiment_label": article.sentiment_label,  # 나중에 정규화됨
            "confidence": article.confidence or 0.0,
            "comment_count": comment_count
        })

    # 키워드 조회
    keywords = db.query(Keyword).filter(Keyword.session_id == session_id).all()
    keywords_data = [
        {
            "keyword": keyword.keyword,
            "frequency": keyword.frequency,
            "sentiment_score": keyword.sentiment_score or 0.0
        }
        for keyword in keywords
    ]
    
    # 키워드가 없으면 기본 키워드 생성 (검색 키워드 포함)
    if not keywords_data and articles_data:
        keywords_data = [
            {
                "keyword": session.keyword,
                "frequency": len(articles_data),
                "sentiment_score": 0.0
            }
        ]

    # 감정 분포 계산 (한국어/영어 레이블 모두 처리)
    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    
    # 한국어 레이블을 영어로 매핑하는 함수
    def normalize_sentiment_label(label: str) -> str:
        if not label:
            return "neutral"
        label_lower = label.lower()
        # 한국어 레이블 처리
        if label == "긍정" or "positive" in label_lower or "긍정적" in label:
            return "positive"
        elif label == "부정" or "negative" in label_lower or "부정적" in label:
            return "negative"
        elif label == "중립" or "neutral" in label_lower or "중립적" in label:
            return "neutral"
        # 이미 영어인 경우
        elif label_lower in ["positive", "negative", "neutral"]:
            return label_lower
        else:
            return "neutral"
    
    # 기사 데이터에 정규화된 감정 레이블 추가 및 감정 분포 계산
    for article_data in articles_data:
        original_label = article_data.get("sentiment_label")
        normalized_label = normalize_sentiment_label(original_label)
        article_data["sentiment_label"] = normalized_label  # 영어로 변환된 레이블로 업데이트
        sentiment_distribution[normalized_label] = sentiment_distribution.get(normalized_label, 0) + 1

    return AnalysisResponse(
        session_id=session.id,
        keyword=session.keyword,
        status=session.status,
        total_articles=len(articles_data),
        sentiment_distribution=sentiment_distribution,
        keywords=keywords_data,
        articles=articles_data,
        created_at=session.created_at,
        completed_at=session.completed_at
    )

@router.get("/sessions", response_model=SessionListResponse)
async def get_analysis_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_database_session)
):
    """분석 세션 목록 조회"""

    # 쿼리 구성
    query = db.query(AnalysisSession)

    if keyword:
        query = query.filter(AnalysisSession.keyword.contains(keyword))

    # 전체 개수
    total = query.count()

    # 페이지네이션
    offset = (page - 1) * per_page
    sessions = query.order_by(AnalysisSession.created_at.desc()).offset(offset).limit(per_page).all()

    sessions_data = []
    for session in sessions:
        article_count = db.query(Article).filter(Article.session_id == session.id).count()

        sessions_data.append({
            "id": session.id,
            "keyword": session.keyword,
            "status": session.status,
            "article_count": article_count,
            "created_at": session.created_at,
            "completed_at": session.completed_at
        })

    return SessionListResponse(
        sessions=sessions_data,
        total=total,
        page=page,
        per_page=per_page
    )

@router.delete("/{session_id}")
async def delete_analysis_session(
    session_id: int,
    db: Session = Depends(get_database_session)
):
    """분석 세션 삭제"""

    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="분석 세션을 찾을 수 없습니다")

    # 관련 데이터 삭제 (CASCADE로 자동 삭제되지만 명시적으로 처리)
    db.query(Comment).filter(Comment.article_id.in_(
        db.query(Article.id).filter(Article.session_id == session_id)
    )).delete(synchronize_session=False)

    db.query(Article).filter(Article.session_id == session_id).delete()
    db.query(Keyword).filter(Keyword.session_id == session_id).delete()
    db.delete(session)
    db.commit()

    return {"message": "분석 세션이 삭제되었습니다"}

@router.get("/stats/summary")
async def get_statistics_summary(
    db: Session = Depends(get_database_session)
):
    """전체 통계 요약"""
    
    # 전체 세션 수
    total_sessions = db.query(AnalysisSession).count()
    completed_sessions = db.query(AnalysisSession).filter(AnalysisSession.status == "completed").count()
    processing_sessions = db.query(AnalysisSession).filter(AnalysisSession.status == "processing").count()
    failed_sessions = db.query(AnalysisSession).filter(AnalysisSession.status == "failed").count()
    
    # 전체 기사 수
    total_articles = db.query(Article).count()
    
    # 전체 댓글 수
    total_comments = db.query(Comment).count()
    
    # 전체 키워드 수
    total_keywords = db.query(Keyword).count()
    
    # 감정 분포
    sentiment_stats = db.query(
        Article.sentiment_label,
        db.func.count(Article.id).label('count')
    ).group_by(Article.sentiment_label).all()
    
    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    for label, count in sentiment_stats:
        if label:
            # 한국어 레이블을 영어로 변환
            if label == "긍정":
                sentiment_distribution["positive"] = count
            elif label == "부정":
                sentiment_distribution["negative"] = count
            elif label == "중립":
                sentiment_distribution["neutral"] = count
            else:
                sentiment_distribution[label] = count
    
    # 최근 분석된 키워드 (상위 10개)
    recent_keywords = db.query(
        AnalysisSession.keyword,
        db.func.count(AnalysisSession.id).label('count')
    ).group_by(AnalysisSession.keyword).order_by(
        db.func.max(AnalysisSession.created_at).desc()
    ).limit(10).all()
    
    return {
        "sessions": {
            "total": total_sessions,
            "completed": completed_sessions,
            "processing": processing_sessions,
            "failed": failed_sessions
        },
        "articles": {
            "total": total_articles
        },
        "comments": {
            "total": total_comments
        },
        "keywords": {
            "total": total_keywords
        },
        "sentiment_distribution": sentiment_distribution,
        "recent_keywords": [
            {"keyword": kw, "count": cnt}
            for kw, cnt in recent_keywords
        ]
    }
