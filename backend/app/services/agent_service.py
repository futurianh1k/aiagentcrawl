"""
AI Agent 서비스 모듈
Agent 서비스(포트 8001)를 호출하여 실제 뉴스 크롤링 및 감정 분석 수행
"""

import os
from datetime import datetime
from typing import List, Dict, Any
import httpx
from app.core.config import settings


class NewsAnalysisAgent:
    """뉴스 감정 분석 Agent - Agent 서비스 HTTP API 호출"""

    def __init__(self):
        """Agent 초기화"""
        # Agent 서비스 URL (Docker Compose 네트워크 내부)
        self.agent_service_url = os.getenv(
            "AGENT_SERVICE_URL", 
            "http://agent:8001"  # Docker Compose 서비스 이름 사용
        )

    async def analyze_news(
        self,
        keyword: str,
        sources: List[str],
        max_articles: int = 20
    ) -> Dict[str, Any]:
        """
        뉴스 감정 분석 실행 - Agent 서비스 호출

        Args:
            keyword: 검색 키워드
            sources: 뉴스 소스 목록
            max_articles: 최대 기사 수

        Returns:
            분석 결과 딕셔너리
        """
        try:
            # Agent 서비스의 /analyze 엔드포인트 호출
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5분 타임아웃
                response = await client.post(
                    f"{self.agent_service_url}/analyze",
                    json={
                        "keyword": keyword,
                        "sources": sources,
                        "max_articles": max_articles
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Agent 서비스 응답 형식을 백엔드 형식에 맞게 변환
                return self._format_agent_response(result, keyword, sources)
                
        except httpx.TimeoutException:
            raise Exception("Agent 서비스 응답 시간 초과 (5분 이상 소요)")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Agent 서비스 오류: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Agent 서비스 호출 실패: {str(e)}")

    def _format_agent_response(
        self, 
        agent_result: Dict[str, Any],
        keyword: str,
        sources: List[str]
    ) -> Dict[str, Any]:
        """
        Agent 서비스 응답을 백엔드 형식에 맞게 변환
        
        Agent 서비스 응답 형식:
        {
            "keyword": str,
            "sources": List[str],
            "total_articles": int,
            "articles": List[Dict],  # 각 기사는 title, content, url, source, sentiment, comments 등 포함
            "sentiment_distribution": Dict,  # {"긍정": int, "부정": int, "중립": int} 또는 {"positive": int, ...}
            "keywords": List[Dict],  # [{"keyword": str, "frequency": int, "sentiment_score": float}]
            "analyzed_at": str
        }
        
        백엔드 기대 형식:
        {
            "keyword": str,
            "sources": List[str],
            "total_articles": int,
            "articles": List[Dict],  # sentiment_label, sentiment_score, confidence 포함
            "sentiment_distribution": {"positive": int, "negative": int, "neutral": int},
            "keywords": List[Dict],
            "analyzed_at": str
        }
        """
        # 에러 응답 처리
        if "error" in agent_result:
            raise Exception(agent_result.get("error", "Agent 서비스 오류"))
        
        # 감정 분포 변환 (한국어 -> 영어)
        sentiment_dist = agent_result.get("sentiment_distribution", {})
        if isinstance(sentiment_dist, dict):
            # 한국어 키가 있으면 영어로 변환
            normalized_dist = {
                "positive": sentiment_dist.get("긍정", sentiment_dist.get("positive", 0)),
                "negative": sentiment_dist.get("부정", sentiment_dist.get("negative", 0)),
                "neutral": sentiment_dist.get("중립", sentiment_dist.get("neutral", 0))
            }
        else:
            normalized_dist = {"positive": 0, "negative": 0, "neutral": 0}
        
        # 기사 데이터 형식 변환
        formatted_articles = []
        for article in agent_result.get("articles", []):
            # Agent 서비스의 기사 형식: title, content, url, source, sentiment, comments 등
            sentiment = article.get("sentiment", "중립")
            confidence = article.get("confidence", article.get("sentiment_confidence", 0.5))
            
            # 한국어 감정 레이블을 영어로 변환
            sentiment_label = sentiment
            if sentiment == "긍정" or sentiment == "긍정적":
                sentiment_label = "긍정"  # DB에는 한국어로 저장
            elif sentiment == "부정" or sentiment == "부정적":
                sentiment_label = "부정"
            else:
                sentiment_label = "중립"
            
            # 감정 점수 계산
            sentiment_score = article.get("sentiment_score")
            if sentiment_score is None:
                if sentiment_label == "긍정":
                    sentiment_score = 0.7
                elif sentiment_label == "부정":
                    sentiment_score = -0.7
                else:
                    sentiment_score = 0.0
            
            formatted_article = {
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "url": article.get("url"),
                "source": article.get("source"),
                "published_at": article.get("published_at"),
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "confidence": confidence,
                "comments": []
            }
            
            # 댓글 형식 변환
            for comment in article.get("comments", []):
                comment_sentiment = comment.get("sentiment", "중립")
                comment_confidence = comment.get("confidence", comment.get("sentiment_confidence", 0.5))
                
                # 댓글 감정 점수
                comment_score = comment.get("sentiment_score")
                if comment_score is None:
                    if comment_sentiment == "긍정":
                        comment_score = 0.7
                    elif comment_sentiment == "부정":
                        comment_score = -0.7
                    else:
                        comment_score = 0.0
                
                formatted_comment = {
                    "content": comment.get("text", comment.get("content", "")),
                    "author": comment.get("author", comment.get("author_name")),
                    "sentiment_score": comment_score,
                    "sentiment_label": comment_sentiment,
                    "confidence": comment_confidence
                }
                formatted_article["comments"].append(formatted_comment)
            
            formatted_articles.append(formatted_article)
        
        # 키워드 형식 확인 및 변환
        keywords = agent_result.get("keywords", [])
        if not keywords or len(keywords) == 0:
            # 키워드가 없으면 기본 키워드 생성
            keywords = [{
                "keyword": keyword,
                "frequency": len(formatted_articles),
                "sentiment_score": 0.0
            }]
        
        return {
            "keyword": agent_result.get("keyword", keyword),
            "sources": agent_result.get("sources", sources),
            "total_articles": len(formatted_articles),
            "articles": formatted_articles,
            "sentiment_distribution": normalized_dist,
            "keywords": keywords,
            "analyzed_at": agent_result.get("analyzed_at", datetime.now().isoformat())
        }
