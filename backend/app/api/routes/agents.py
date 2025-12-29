"""
AI Agent 라우터
뉴스 분석 Agent 관련 엔드포인트
"""

import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.dependencies import get_agent_service, get_database_session
from app.schemas.requests import AnalysisRequest, AnalysisResponse
from app.services.agent_service import NewsAnalysisAgent
from app.models.database import AnalysisSession, Article, Comment, Keyword

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_news(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    agent_service: NewsAnalysisAgent = Depends(get_agent_service),
    db: Session = Depends(get_database_session)
):
    """뉴스 감정 분석 시작"""

    # 분석 세션 생성
    session = AnalysisSession(
        keyword=request.keyword,
        sources=json.dumps(request.sources),
        status="processing"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        # AI Agent 분석 실행
        analysis_result = await agent_service.analyze_news(
            keyword=request.keyword,
            sources=request.sources,
            max_articles=request.max_articles
        )

        # 데이터베이스에 결과 저장
        articles_data = []
        for article_data in analysis_result["articles"]:
            # 기사 저장
            article = Article(
                session_id=session.id,
                title=article_data["title"],
                content=article_data["content"],
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

            # 기사 데이터에 댓글 수 추가
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "url": article.url,
                "source": article.source,
                "published_at": article.published_at,
                "sentiment_score": article.sentiment_score,
                "sentiment_label": article.sentiment_label,
                "confidence": article.confidence,
                "comment_count": comment_count
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

        # 세션 상태 업데이트
        session.status = "completed"
        session.completed_at = datetime.now()
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
