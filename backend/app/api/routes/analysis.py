"""
분석 결과 라우터
저장된 분석 결과 조회 엔드포인트
"""

import csv
import io
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func  # SQLAlchemy func 추가
from app.api.dependencies import get_database_session
from app.schemas.requests import AnalysisResponse, SessionListResponse
from app.models.database import AnalysisSession, Article, Comment, Keyword, SearchHistory, ArticleMedia

router = APIRouter()


@router.get("/search-history")
async def get_search_history(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_database_session)
):
    """검색 히스토리 조회 (최근 검색어)"""
    
    history = db.query(SearchHistory).order_by(
        SearchHistory.last_searched_at.desc()
    ).limit(limit).all()
    
    return {
        "history": [
            {
                "id": h.id,
                "keyword": h.keyword,
                "sources": json.loads(h.sources) if h.sources else [],
                "max_articles": h.max_articles,
                "search_count": h.search_count,
                "last_searched_at": h.last_searched_at
            }
            for h in history
        ]
    }


@router.delete("/search-history/{history_id}")
async def delete_search_history(
    history_id: int,
    db: Session = Depends(get_database_session)
):
    """검색 히스토리 삭제"""
    
    history = db.query(SearchHistory).filter(SearchHistory.id == history_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="히스토리를 찾을 수 없습니다")
    
    db.delete(history)
    db.commit()
    
    return {"message": "검색 히스토리가 삭제되었습니다"}


@router.delete("/search-history")
async def clear_search_history(
    db: Session = Depends(get_database_session)
):
    """모든 검색 히스토리 삭제"""
    
    db.query(SearchHistory).delete()
    db.commit()
    
    return {"message": "모든 검색 히스토리가 삭제되었습니다"}


@router.get("/export/{session_id}/csv")
async def export_session_csv(
    session_id: int,
    db: Session = Depends(get_database_session)
):
    """세션 데이터를 CSV로 내보내기"""
    from urllib.parse import quote
    
    # 세션 조회
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="분석 세션을 찾을 수 없습니다")
    
    # 기사 조회
    articles = db.query(Article).filter(Article.session_id == session_id).all()
    
    # CSV 생성
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 헤더
    writer.writerow([
        "번호", "제목", "요약", "소스", "URL", "감성", "감성점수", "신뢰도", "작성일"
    ])
    
    # 데이터
    for i, article in enumerate(articles, 1):
        writer.writerow([
            i,
            article.title,
            article.summary or "",
            article.source or "",
            article.url or "",
            article.sentiment_label or "",
            article.sentiment_score or 0,
            article.confidence or 0,
            article.published_at.strftime("%Y-%m-%d %H:%M") if article.published_at else ""
        ])
    
    output.seek(0)
    
    # UTF-8 BOM 추가 (Excel 한글 호환)
    bom = '\ufeff'
    csv_content = bom + output.getvalue()
    
    # 파일명 인코딩 (한글 지원)
    filename = f"analysis_{session_id}.csv"
    filename_encoded = quote(f"분석결과_{session_id}_{session.keyword}.csv")
    
    return StreamingResponse(
        io.BytesIO(csv_content.encode('utf-8')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}; filename*=UTF-8''{filename_encoded}"
        }
    )


@router.get("/export/{session_id}/json")
async def export_session_json(
    session_id: int,
    db: Session = Depends(get_database_session)
):
    """세션 데이터를 JSON으로 내보내기"""
    
    # 세션 조회
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="분석 세션을 찾을 수 없습니다")
    
    # 기사 조회
    articles = db.query(Article).filter(Article.session_id == session_id).all()
    
    # 키워드 조회
    keywords = db.query(Keyword).filter(Keyword.session_id == session_id).all()
    
    # 감정 분포 계산
    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    
    articles_data = []
    for article in articles:
        # 댓글 조회
        comments = db.query(Comment).filter(Comment.article_id == article.id).all()
        
        label = article.sentiment_label or "neutral"
        if label == "긍정":
            sentiment_distribution["positive"] += 1
        elif label == "부정":
            sentiment_distribution["negative"] += 1
        else:
            sentiment_distribution["neutral"] += 1
        
        articles_data.append({
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "summary": article.summary or "",
            "url": article.url,
            "source": article.source,
            "sentiment_label": article.sentiment_label,
            "sentiment_score": article.sentiment_score,
            "confidence": article.confidence,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "comments": [
                {
                    "content": c.content,
                    "author": c.author,
                    "sentiment_label": c.sentiment_label,
                    "sentiment_score": c.sentiment_score
                }
                for c in comments
            ]
        })
    
    export_data = {
        "session": {
            "id": session.id,
            "keyword": session.keyword,
            "sources": json.loads(session.sources) if session.sources else [],
            "status": session.status,
            "overall_summary": session.overall_summary,
            "created_at": session.created_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        },
        "sentiment_distribution": sentiment_distribution,
        "keywords": [
            {
                "keyword": k.keyword,
                "frequency": k.frequency,
                "sentiment_score": k.sentiment_score
            }
            for k in keywords
        ],
        "articles": articles_data,
        "total_articles": len(articles_data)
    }
    
    json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    # 파일명 인코딩 (한글 지원)
    from urllib.parse import quote
    filename = f"analysis_{session_id}.json"
    filename_encoded = quote(f"분석결과_{session_id}_{session.keyword}.json")
    
    return StreamingResponse(
        io.BytesIO(json_content.encode('utf-8')),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}; filename*=UTF-8''{filename_encoded}"
        }
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
            "overall_summary": session.overall_summary or "",  # 종합 요약 미리보기
            # 토큰 사용량 정보
            "prompt_tokens": session.prompt_tokens or 0,
            "completion_tokens": session.completion_tokens or 0,
            "total_tokens": session.total_tokens or 0,
            "estimated_cost": session.estimated_cost or 0.0,
            "created_at": session.created_at,
            "completed_at": session.completed_at
        })

    return SessionListResponse(
        sessions=sessions_data,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/stats/usage")
async def get_llm_usage_stats(
    db: Session = Depends(get_database_session)
):
    """LLM 토큰 사용량 통계"""
    
    # 완료된 세션의 토큰 사용량 합계
    usage_stats = db.query(
        func.count(AnalysisSession.id).label('total_sessions'),
        func.sum(AnalysisSession.prompt_tokens).label('total_prompt_tokens'),
        func.sum(AnalysisSession.completion_tokens).label('total_completion_tokens'),
        func.sum(AnalysisSession.total_tokens).label('total_tokens'),
        func.sum(AnalysisSession.estimated_cost).label('total_cost')
    ).filter(AnalysisSession.status == "completed").first()
    
    total_sessions = usage_stats.total_sessions or 0
    total_prompt_tokens = usage_stats.total_prompt_tokens or 0
    total_completion_tokens = usage_stats.total_completion_tokens or 0
    total_tokens = usage_stats.total_tokens or 0
    total_cost = float(usage_stats.total_cost or 0.0)
    
    # Free tier 한도 (OpenAI 기본 $5.00, 설정 가능)
    free_credit_limit = 5.0
    remaining_credit = max(0, free_credit_limit - total_cost)
    usage_percentage = min(100, (total_cost / free_credit_limit * 100)) if free_credit_limit > 0 else 0
    
    # 사람이 읽기 쉬운 형식
    def format_tokens(n: int) -> str:
        if n >= 1_000_000:
            return f"{n/1_000_000:.2f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)
    
    # 최근 5개 세션 사용량
    recent_sessions = db.query(
        AnalysisSession.id,
        AnalysisSession.keyword,
        AnalysisSession.total_tokens,
        AnalysisSession.estimated_cost,
        AnalysisSession.created_at
    ).filter(
        AnalysisSession.status == "completed",
        AnalysisSession.total_tokens > 0
    ).order_by(
        AnalysisSession.created_at.desc()
    ).limit(5).all()
    
    return {
        "total_sessions": total_sessions,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "total_estimated_cost": round(total_cost, 6),
        
        # 사람이 읽기 쉬운 형식
        "total_tokens_formatted": format_tokens(total_tokens),
        "total_cost_formatted": f"${total_cost:.4f}",
        
        # Free tier 정보
        "free_credit_limit": free_credit_limit,
        "remaining_credit": round(remaining_credit, 4),
        "usage_percentage": round(usage_percentage, 2),
        
        # 최근 세션별 사용량
        "recent_usage": [
            {
                "session_id": s.id,
                "keyword": s.keyword,
                "tokens": s.total_tokens,
                "tokens_formatted": format_tokens(s.total_tokens or 0),
                "cost": round(s.estimated_cost or 0, 6),
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in recent_sessions
        ],
        
        # 가격 정보 (gpt-4o-mini 기준)
        "pricing_info": {
            "model": "gpt-4o-mini",
            "input_price_per_1m": 0.15,
            "output_price_per_1m": 0.6,
            "currency": "USD"
        }
    }


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
        func.count(Article.id).label('count')
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
        func.count(AnalysisSession.id).label('count')
    ).group_by(AnalysisSession.keyword).order_by(
        func.max(AnalysisSession.created_at).desc()
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
            "summary": article.summary or "",  # 기사 요약
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

    # 토큰 사용량 정보
    token_usage = None
    if session.total_tokens and session.total_tokens > 0:
        token_usage = {
            "prompt_tokens": session.prompt_tokens or 0,
            "completion_tokens": session.completion_tokens or 0,
            "total_tokens": session.total_tokens or 0,
            "estimated_cost": session.estimated_cost or 0.0
        }
    
    return AnalysisResponse(
        session_id=session.id,
        keyword=session.keyword,
        status=session.status,
        total_articles=len(articles_data),
        sentiment_distribution=sentiment_distribution,
        keywords=keywords_data,
        articles=articles_data,
        overall_summary=session.overall_summary or "",  # 종합 요약
        token_usage=token_usage,  # 토큰 사용량
        created_at=session.created_at,
        completed_at=session.completed_at
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

    try:
        # 관련 데이터 삭제 (외래키 제약조건을 고려한 올바른 순서)
        # 먼저 해당 세션의 모든 기사 ID 조회
        articles = db.query(Article).filter(Article.session_id == session_id).all()
        article_ids = [article.id for article in articles]
        
        if article_ids:
            # 1. ArticleMedia 삭제 (Article을 참조하는 자식 테이블)
            db.query(ArticleMedia).filter(ArticleMedia.article_id.in_(article_ids)).delete(synchronize_session=False)
            
            # 2. Comment 삭제 (Article을 참조하는 자식 테이블)
            db.query(Comment).filter(Comment.article_id.in_(article_ids)).delete(synchronize_session=False)
        
        # 3. Article 삭제
        db.query(Article).filter(Article.session_id == session_id).delete(synchronize_session=False)
        
        # 4. Keyword 삭제
        db.query(Keyword).filter(Keyword.session_id == session_id).delete(synchronize_session=False)
        
        # 5. AnalysisSession 삭제
        db.delete(session)
        db.commit()
        
        return {"message": "분석 세션이 삭제되었습니다"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"세션 삭제 중 오류가 발생했습니다: {str(e)}")
