"""
AI Agent 라우터
뉴스 분석 Agent 관련 엔드포인트
"""

import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.dependencies import get_agent_service, get_database_session, get_current_user_optional
from app.schemas.requests import AnalysisRequest, AnalysisResponse
from app.services.agent_service import NewsAnalysisAgent
from app.models.database import AnalysisSession, Article, Comment, Keyword, SearchHistory, ArticleMedia, User
from app.services.media_service import media_service

router = APIRouter()

# Freemium 설정
MAX_ARTICLES_FREE = 3  # 비로그인 사용자 최대 기사 수
MAX_ARTICLES_PREMIUM = 50  # 로그인 사용자 최대 기사 수

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_news(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user_optional),
    agent_service: NewsAnalysisAgent = Depends(get_agent_service),
    db: Session = Depends(get_database_session)
):
    """
    뉴스 감정 분석 시작

    Freemium 모델:
    - 비로그인: 최대 3개 기사
    - 로그인: 최대 50개 기사 + 검색 이력 저장
    """

    # Freemium 로직: 비로그인 사용자 제한
    actual_max_articles = request.max_articles
    is_premium_user = current_user is not None

    if not is_premium_user:
        # 비로그인 사용자는 최대 3개로 제한
        if actual_max_articles > MAX_ARTICLES_FREE:
            actual_max_articles = MAX_ARTICLES_FREE
    else:
        # 로그인 사용자는 최대 50개로 제한
        if actual_max_articles > MAX_ARTICLES_PREMIUM:
            actual_max_articles = MAX_ARTICLES_PREMIUM

    # 검색 히스토리 저장/업데이트 (로그인 사용자만)
    if is_premium_user:
        existing_history = db.query(SearchHistory).filter(
            SearchHistory.keyword == request.keyword
        ).first()

        if existing_history:
            existing_history.search_count += 1
            existing_history.sources = json.dumps(request.sources)
            existing_history.max_articles = actual_max_articles
        else:
            new_history = SearchHistory(
                keyword=request.keyword,
                sources=json.dumps(request.sources),
                max_articles=actual_max_articles
            )
            db.add(new_history)

    # 분석 세션 생성
    session = AnalysisSession(
        user_id=current_user.id if current_user else None,  # 로그인 사용자 ID 저장
        keyword=request.keyword,
        sources=json.dumps(request.sources),
        status="processing"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        # AI Agent 분석 실행 (실제 제한된 개수로)
        analysis_result = await agent_service.analyze_news(
            keyword=request.keyword,
            sources=request.sources,
            max_articles=actual_max_articles
        )

        # 데이터베이스에 결과 저장
        articles_data = []
        for article_data in analysis_result["articles"]:
            # 기사 저장 (요약 포함)
            article = Article(
                session_id=session.id,
                title=article_data["title"],
                content=article_data["content"],
                summary=article_data.get("summary", ""),  # 기사 요약 저장
                url=article_data.get("url"),
                source=article_data.get("source"),
                published_at=article_data.get("published_at"),
                sentiment_score=article_data.get("sentiment_score"),
                sentiment_label=article_data.get("sentiment_label"),
                confidence=article_data.get("confidence")
            )
            db.add(article)
            db.flush()  # ID 생성을 위해 flush

            # 댓글 저장
            comment_count = 0
            for comment_data in article_data.get("comments", []):
                comment = Comment(
                    article_id=article.id,
                    content=comment_data["content"],
                    author=comment_data.get("author"),
                    sentiment_score=comment_data.get("sentiment_score"),
                    sentiment_label=comment_data.get("sentiment_label"),
                    confidence=comment_data.get("confidence")
                )
                db.add(comment)
                comment_count += 1

            # 미디어 저장 (이미지, 테이블)
            media_count = {"images": 0, "tables": 0}
            raw_images = article_data.get("images", [])
            raw_tables = article_data.get("tables", [])
            
            if raw_images or raw_tables:
                try:
                    # 미디어 파일 저장 (비동기)
                    saved_media = await media_service.save_article_media(
                        article.id, raw_images, raw_tables
                    )
                    
                    # DB에 미디어 메타데이터 저장
                    for img_data in saved_media.get("images", []):
                        media_record = ArticleMedia(
                            article_id=article.id,
                            media_type="image",
                            file_path=img_data.get("file_path"),
                            original_url=img_data.get("original_url"),
                            caption=img_data.get("caption", ""),
                            alt_text=img_data.get("alt_text", ""),
                            width=img_data.get("width"),
                            height=img_data.get("height"),
                            file_size=img_data.get("file_size"),
                            mime_type=img_data.get("mime_type"),
                            display_order=img_data.get("display_order", 0),
                        )
                        db.add(media_record)
                        media_count["images"] += 1
                    
                    for tbl_data in saved_media.get("tables", []):
                        media_record = ArticleMedia(
                            article_id=article.id,
                            media_type="table",
                            file_path=tbl_data.get("file_path"),
                            caption=tbl_data.get("caption", ""),
                            width=tbl_data.get("width"),  # cols
                            height=tbl_data.get("height"),  # rows
                            file_size=tbl_data.get("file_size"),
                            mime_type="text/html",
                            table_html=tbl_data.get("table_html"),
                            display_order=tbl_data.get("display_order", 0),
                        )
                        db.add(media_record)
                        media_count["tables"] += 1
                        
                except Exception as media_err:
                    print(f"[WARN] 미디어 저장 오류 (계속 진행): {str(media_err)}")

            # 기사 데이터에 요약 및 댓글 수 추가
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "summary": article.summary or "",  # 기사 요약
                "url": article.url,
                "source": article.source,
                "published_at": article.published_at,
                "sentiment_score": article.sentiment_score,
                "sentiment_label": article.sentiment_label,
                "confidence": article.confidence,
                "comment_count": comment_count,
                "image_count": media_count["images"],
                "table_count": media_count["tables"],
            })

        # 키워드 저장
        keywords_data = []
        for keyword_data in analysis_result.get("keywords", []):
            # sentiment_score가 없을 경우 기본값 0.0 사용
            sentiment_score = keyword_data.get("sentiment_score", 0.0)
            keyword = Keyword(
                session_id=session.id,
                keyword=keyword_data.get("keyword", ""),
                frequency=keyword_data.get("frequency", 1),
                sentiment_score=sentiment_score
            )
            db.add(keyword)
            keywords_data.append({
                "keyword": keyword_data.get("keyword", ""),
                "frequency": keyword_data.get("frequency", 1),
                "sentiment_score": sentiment_score
            })

        # 세션 상태 및 종합 요약 업데이트
        session.status = "completed"
        session.completed_at = datetime.now()
        session.overall_summary = analysis_result.get("overall_summary", "")  # 종합 요약 저장
        
        # 토큰 사용량 저장
        token_usage = analysis_result.get("token_usage", {})
        session.prompt_tokens = token_usage.get("prompt_tokens", 0)
        session.completion_tokens = token_usage.get("completion_tokens", 0)
        session.total_tokens = token_usage.get("total_tokens", 0)
        session.estimated_cost = token_usage.get("estimated_cost", 0.0)
        
        db.commit()

        # 응답 데이터 구성
        return AnalysisResponse(
            session_id=session.id,
            keyword=session.keyword,
            status=session.status,
            total_articles=len(articles_data),
            sentiment_distribution=analysis_result["sentiment_distribution"],
            keywords=keywords_data,
            articles=articles_data,
            overall_summary=session.overall_summary or "",  # 종합 요약
            timing=analysis_result.get("timing"),  # 성능 측정 정보
            token_usage=analysis_result.get("token_usage"),  # LLM 토큰 사용량
            created_at=session.created_at,
            completed_at=session.completed_at
        )

    except Exception as e:
        # 에러 발생시 세션 상태 업데이트
        session.status = "failed"
        db.commit()

        # 에러 로깅 (상세 정보)
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR in analyze_news: {str(e)}")
        print(f"Traceback: {error_detail}")

        raise HTTPException(
            status_code=500,
            detail=f"뉴스 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/status/{session_id}")
async def get_analysis_status(
    session_id: int,
    db: Session = Depends(get_database_session)
):
    """분석 상태 조회"""
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="분석 세션을 찾을 수 없습니다")

    return {
        "session_id": session.id,
        "keyword": session.keyword,
        "status": session.status,
        "created_at": session.created_at,
        "completed_at": session.completed_at
    }
