"""
AI Agent 서비스 모듈
LangChain을 이용한 뉴스 수집 및 감정 분석 에이전트
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# LangChain import (최신 버전 호환)
try:
    from langchain.agents import Tool, AgentExecutor
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.tools import Tool
        from langchain.agents import AgentExecutor
        from langchain_openai import ChatOpenAI
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        Tool = None
        AgentExecutor = None
        ChatOpenAI = None
        LANGCHAIN_AVAILABLE = False

from app.core.config import settings


class MockNewsScraper:
    """Mock 뉴스 스크래퍼 (실제 구현시 Selenium/API 대체)"""

    async def scrape_news(self, keyword: str, sources: List[str], max_articles: int = 20) -> List[Dict]:
        """뉴스 기사 수집 시뮬레이션"""
        await asyncio.sleep(1)  # 실제 스크래핑 시뮬레이션

        articles = []
        for i in range(min(max_articles, 15)):
            article = {
                "title": f"{keyword} 관련 뉴스 기사 {i+1}",
                "content": f"{keyword}에 대한 상세한 뉴스 내용입니다. " * random.randint(5, 20),
                "url": f"https://news.example.com/{keyword}-{i+1}",
                "source": random.choice(sources),
                "published_at": datetime.now() - timedelta(hours=random.randint(1, 48)),
                "comments": [
                    {
                        "text": f"댓글 {j+1}: {keyword}에 대한 의견입니다.",
                        "author": f"사용자{j+1}",
                        "sentiment": random.choice(["긍정", "부정", "중립"])
                    }
                    for j in range(random.randint(0, 5))
                ]
            }
            articles.append(article)

        return articles


class SentimentAnalyzer:
    """감정 분석기 (OpenAI API 사용)"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        if LANGCHAIN_AVAILABLE and ChatOpenAI:
            try:
                self.llm = ChatOpenAI(
                    temperature=0.3,
                    openai_api_key=api_key,
                    model_name=settings.SENTIMENT_ANALYSIS_MODEL
                )
            except Exception:
                self.llm = None
        else:
            self.llm = None

    async def analyze(self, text: str) -> Dict[str, Any]:
        """텍스트 감정 분석"""
        if not self.llm:
            # LLM이 없으면 기본 응답
            return {
                "sentiment": random.choice(["긍정", "부정", "중립"]),
                "confidence": random.uniform(0.6, 0.9),
                "reason": "기본 분석 결과"
            }

        try:
            prompt = f"""다음 텍스트의 감정을 분석하세요. JSON 형식으로 응답하세요.

텍스트: {text[:500]}

응답 형식:
{{
    "sentiment": "긍정|부정|중립",
    "confidence": 0.0-1.0,
    "reason": "분석 근거"
}}"""

            response = await self.llm.ainvoke(prompt)
            result = json.loads(response.content)
            return result
        except Exception:
            return {
                "sentiment": random.choice(["긍정", "부정", "중립"]),
                "confidence": 0.7,
                "reason": "분석 실패"
            }


class NewsAnalysisAgent:
    """뉴스 감정 분석 Agent"""

    def __init__(self):
        """Agent 초기화"""
        self.scraper = MockNewsScraper()
        self.analyzer = SentimentAnalyzer(settings.OPENAI_API_KEY)

    async def analyze_news(
        self,
        keyword: str,
        sources: List[str],
        max_articles: int = 20
    ) -> Dict[str, Any]:
        """
        뉴스 감정 분석 실행

        Args:
            keyword: 검색 키워드
            sources: 뉴스 소스 목록
            max_articles: 최대 기사 수

        Returns:
            분석 결과 딕셔너리
        """
        # 1. 뉴스 수집
        articles = await self.scraper.scrape_news(keyword, sources, max_articles)

        # 2. 감정 분석
        analyzed_articles = []
        sentiment_counts = {"긍정": 0, "부정": 0, "중립": 0}

        for article in articles:
            # 기사 본문 감정 분석
            article_text = f"{article['title']} {article['content']}"
            article_sentiment = await self.analyzer.analyze(article_text[:500])

            # 댓글 감정 분석
            analyzed_comments = []
            for comment in article.get("comments", []):
                comment_sentiment = await self.analyzer.analyze(comment.get("text", ""))
                analyzed_comments.append({
                    **comment,
                    **comment_sentiment
                })
                sentiment_counts[comment_sentiment.get("sentiment", "중립")] += 1

            analyzed_articles.append({
                **article,
                **article_sentiment,
                "comments": analyzed_comments
            })

            sentiment_counts[article_sentiment.get("sentiment", "중립")] += 1

        # 3. 결과 정리
        total = sum(sentiment_counts.values())
        sentiment_distribution = {
            "positive": sentiment_counts.get("긍정", 0),
            "negative": sentiment_counts.get("부정", 0),
            "neutral": sentiment_counts.get("중립", 0)
        }

        # 4. 기사 데이터 형식 변환 (agents.py에서 기대하는 형식)
        formatted_articles = []
        for article in analyzed_articles:
            sentiment = article.get("sentiment", "중립")
            confidence = article.get("confidence", 0.5)
            
            formatted_article = {
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "url": article.get("url"),
                "source": article.get("source"),
                "published_at": article.get("published_at"),
                "sentiment_score": 0.7 if sentiment == "긍정" else (-0.7 if sentiment == "부정" else 0.0),
                "sentiment_label": sentiment,
                "confidence": confidence,
                "comments": []
            }
            
            # 댓글 형식 변환
            for comment in article.get("comments", []):
                comment_sentiment = comment.get("sentiment", "중립")
                comment_confidence = comment.get("confidence", 0.5)
                
                formatted_comment = {
                    "content": comment.get("text", ""),
                    "author": comment.get("author"),
                    "sentiment_score": 0.7 if comment_sentiment == "긍정" else (-0.7 if comment_sentiment == "부정" else 0.0),
                    "sentiment_label": comment_sentiment,
                    "confidence": comment_confidence
                }
                formatted_article["comments"].append(formatted_comment)
            
            formatted_articles.append(formatted_article)

        # 5. 키워드 추출 (간단한 버전)
        keywords = []
        keyword_freq = {}
        for article in formatted_articles:
            text = f"{article['title']} {article['content']}"
            words = text.split()
            for word in words:
                if len(word) > 1 and word != keyword:
                    keyword_freq[word] = keyword_freq.get(word, 0) + 1
        
        # 상위 10개 키워드
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords = [
            {
                "keyword": kw,
                "frequency": freq,
                "sentiment_score": 0.0  # 기본값
            }
            for kw, freq in sorted_keywords
        ]

        return {
            "keyword": keyword,
            "sources": sources,
            "total_articles": len(formatted_articles),
            "articles": formatted_articles,
            "sentiment_distribution": sentiment_distribution,
            "keywords": keywords,
            "analyzed_at": datetime.now().isoformat()
        }
