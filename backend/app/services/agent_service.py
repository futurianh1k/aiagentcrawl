"""
AI Agent 서비스 모듈
LangChain을 이용한 뉴스 수집 및 감정 분석 에이전트
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
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
                "comments": self._generate_mock_comments(random.randint(3, 10))
            }
            articles.append(article)

        return articles

    def _generate_mock_comments(self, count: int) -> List[Dict]:
        """Mock 댓글 생성"""
        comments = []
        sentiments = ["긍정적인", "부정적인", "중립적인"]

        for i in range(count):
            sentiment = random.choice(sentiments)
            comment = {
                "content": f"이 뉴스에 대한 {sentiment} 의견입니다.",
                "author": f"사용자{i+1}",
                "created_at": datetime.now() - timedelta(minutes=random.randint(1, 1440))
            }
            comments.append(comment)

        return comments

class SentimentAnalyzer:
    """감정 분석 에이전트"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.SENTIMENT_ANALYSIS_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """텍스트 감정 분석"""
        prompt = f"""
        다음 텍스트의 감정을 분석해주세요:

        텍스트: {text}

        다음 형식으로 JSON 응답을 제공해주세요:
        {{
            "sentiment_label": "positive|negative|neutral",
            "sentiment_score": -1.0~1.0 사이의 실수,
            "confidence": 0.0~1.0 사이의 신뢰도
        }}
        """

        try:
            response = await self.llm.ainvoke(prompt)
            result = json.loads(response.content)
            return result
        except Exception as e:
            # 실패시 기본값 반환
            return {
                "sentiment_label": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.5
            }

class NewsAnalysisAgent:
    """뉴스 분석 통합 에이전트"""

    def __init__(self):
        self.scraper = MockNewsScraper()
        self.sentiment_analyzer = SentimentAnalyzer()

        # LangChain Agent 설정
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.3
        )

        self.tools = [
            Tool(
                name="news_scraper",
                description="뉴스 기사를 수집합니다",
                func=self._scrape_wrapper
            ),
            Tool(
                name="sentiment_analyzer", 
                description="텍스트의 감정을 분석합니다",
                func=self._sentiment_wrapper
            )
        ]

    def _scrape_wrapper(self, input_str: str) -> str:
        """동기 래퍼"""
        return "뉴스 수집 완료"

    def _sentiment_wrapper(self, input_str: str) -> str:
        """동기 래퍼"""
        return "감정 분석 완료"

    async def analyze_news(self, keyword: str, sources: List[str], max_articles: int) -> Dict[str, Any]:
        """통합 뉴스 분석 실행"""

        # 1. 뉴스 수집
        articles = await self.scraper.scrape_news(keyword, sources, max_articles)

        # 2. 각 기사 감정 분석 (병렬 처리)
        analyzed_articles = []
        sentiment_tasks = []

        for article in articles:
            # 기사 본문 감정 분석
            article_task = self.sentiment_analyzer.analyze_sentiment(
                f"{article['title']} {article['content']}"
            )
            sentiment_tasks.append((article, article_task, 'article'))

            # 댓글 감정 분석
            for comment in article['comments']:
                comment_task = self.sentiment_analyzer.analyze_sentiment(comment['content'])
                sentiment_tasks.append((comment, comment_task, 'comment'))

        # 병렬 실행
        sentiment_results = await asyncio.gather(*[task for _, task, _ in sentiment_tasks])

        # 결과 매핑
        result_index = 0
        for i, article in enumerate(articles):
            # 기사 감정 분석 결과 적용
            article_sentiment = sentiment_results[result_index]
            result_index += 1

            article.update(article_sentiment)

            # 댓글 감정 분석 결과 적용
            for j, comment in enumerate(article['comments']):
                comment_sentiment = sentiment_results[result_index]
                result_index += 1
                comment.update(comment_sentiment)

            analyzed_articles.append(article)

        # 3. 키워드 추출 및 통계 계산
        keywords = self._extract_keywords(analyzed_articles, keyword)
        sentiment_distribution = self._calculate_sentiment_distribution(analyzed_articles)

        return {
            "articles": analyzed_articles,
            "keywords": keywords,
            "sentiment_distribution": sentiment_distribution,
            "total_articles": len(analyzed_articles)
        }

    def _extract_keywords(self, articles: List[Dict], main_keyword: str) -> List[Dict]:
        """키워드 추출 및 빈도 계산"""
        # 간단한 키워드 추출 로직 (실제로는 NLP 라이브러리 사용)
        keyword_freq = {}

        for article in articles:
            text = f"{article['title']} {article['content']}"
            words = text.split()

            for word in words:
                if len(word) > 1 and word != main_keyword:
                    keyword_freq[word] = keyword_freq.get(word, 0) + 1

        # 상위 10개 키워드 반환
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        return [
            {
                "keyword": keyword,
                "frequency": freq,
                "sentiment_score": random.uniform(-0.5, 0.5)  # Mock sentiment
            }
            for keyword, freq in sorted_keywords
        ]

    def _calculate_sentiment_distribution(self, articles: List[Dict]) -> Dict[str, int]:
        """감정 분포 계산"""
        distribution = {"positive": 0, "negative": 0, "neutral": 0}

        for article in articles:
            label = article.get('sentiment_label', 'neutral')
            distribution[label] = distribution.get(label, 0) + 1

        return distribution
