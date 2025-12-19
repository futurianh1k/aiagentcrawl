"""
News Analysis Agent

뉴스 감성 분석을 위한 통합 AI Agent
네이버 뉴스와 구글 뉴스를 지원하며, 실제 Tools를 사용합니다.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from langchain.agents import initialize_agent, AgentType
    from langchain.llms import OpenAI
    from langchain.memory import ConversationBufferMemory
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

from common.config import get_config
from common.utils import safe_log, validate_input
from agent.tools import scrape_news, analyze_sentiment, analyze_news_trend


class NewsAnalysisAgent:
    """뉴스 감성 분석을 위한 통합 AI Agent"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Agent 초기화

        Args:
            api_key: OpenAI API 키 (None이면 환경 변수에서 읽음)
        """
        if not AGENT_AVAILABLE:
            raise RuntimeError(
                "LangChain Agent가 설치되지 않았습니다. "
                "'pip install langchain openai' 를 실행하세요."
            )

        config = get_config()
        self.openai_api_key = api_key or config.get_openai_key()

        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY가 필요합니다.")

        # LLM 초기화
        try:
            self.llm = OpenAI(
                temperature=0.1,
                openai_api_key=self.openai_api_key,
                max_tokens=2000,
                verbose=True
            )
        except Exception as e:
            safe_log("LLM 초기화 실패", level="error", error=str(e))
            raise RuntimeError(f"LLM 초기화 실패: {e}")

        # 메모리 설정
        try:
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                input_key="input",
                output_key="output"
            )
        except Exception as e:
            safe_log("메모리 초기화 실패", level="warning", error=str(e))
            self.memory = None

        # Tools 등록 (실제 Tools 사용)
        self.tools = [
            scrape_news,
            analyze_sentiment,
            analyze_news_trend,
        ]

        # Agent 초기화
        try:
            self.agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=True,
                max_iterations=10,
                early_stopping_method="generate"
            )
            safe_log("NewsAnalysisAgent 초기화 완료", level="info", tools_count=len(self.tools))
        except Exception as e:
            safe_log("Agent 초기화 실패", level="error", error=str(e))
            raise RuntimeError(f"Agent 초기화 실패: {e}")

    async def analyze_news_async(
        self,
        keyword: str,
        sources: List[str] = None,
        max_articles: int = 10
    ) -> Dict[str, Any]:
        """
        비동기 뉴스 분석 실행

        Args:
            keyword: 검색할 키워드
            sources: 뉴스 소스 목록 (["네이버", "구글"])
            max_articles: 최대 기사 수

        Returns:
            분석 결과 딕셔너리
        """
        if sources is None:
            sources = ["네이버"]

        # 입력 검증
        if not validate_input(keyword, max_length=100):
            raise ValueError("유효하지 않은 키워드입니다.")

        safe_log("뉴스 분석 시작", level="info", keyword=keyword, sources=sources)

        try:
            # 1단계: 뉴스 수집
            articles_data = scrape_news(keyword, sources, max_articles)

            if not articles_data or (len(articles_data) == 1 and "error" in articles_data[0]):
                return {
                    "error": articles_data[0].get("error", "뉴스 수집 실패") if articles_data else "뉴스 수집 실패",
                    "keyword": keyword,
                    "sources": sources
                }

            # 2단계: 각 기사 및 댓글 감성 분석
            analyzed_articles = []
            all_comments = []

            for article in articles_data:
                if "error" in article:
                    continue

                # 기사 본문 감성 분석
                article_text = f"{article.get('title', '')} {article.get('content', '')}"
                article_sentiment = analyze_sentiment(article_text[:500])  # 최대 500자

                # 댓글 감성 분석
                article_comments = article.get("comments", [])
                analyzed_comments = []

                for comment in article_comments[:10]:  # 최대 10개 댓글
                    comment_text = comment.get("text", "") if isinstance(comment, dict) else str(comment)
                    if comment_text:
                        comment_sentiment = analyze_sentiment(comment_text)
                        analyzed_comments.append({
                            **comment if isinstance(comment, dict) else {"text": comment},
                            **comment_sentiment
                        })
                        all_comments.append(comment_text)

                analyzed_articles.append({
                    **article,
                    **article_sentiment,
                    "comments": analyzed_comments,
                    "comment_count": len(analyzed_comments)
                })

            # 3단계: 전체 동향 분석
            if all_comments:
                trend_result = analyze_news_trend(
                    [{"text": c} for c in all_comments],
                    keyword
                )
            else:
                trend_result = {
                    "keyword": keyword,
                    "overall_sentiment": "중립",
                    "sentiment_distribution": {"긍정": 0.33, "부정": 0.33, "중립": 0.34},
                    "key_topics": [],
                    "summary": "댓글이 없어 동향 분석을 수행할 수 없습니다.",
                    "total_comments": 0
                }

            # 4단계: 감성 분포 계산
            sentiment_distribution = self._calculate_sentiment_distribution(analyzed_articles)

            # 5단계: 키워드 추출
            keywords = self._extract_keywords(analyzed_articles, keyword)

            result = {
                "keyword": keyword,
                "sources": sources,
                "total_articles": len(analyzed_articles),
                "articles": analyzed_articles,
                "sentiment_distribution": sentiment_distribution,
                "trend_analysis": trend_result,
                "keywords": keywords,
                "analyzed_at": datetime.now().isoformat()
            }

            safe_log("뉴스 분석 완료", level="info", total_articles=len(analyzed_articles))
            return result

        except Exception as e:
            safe_log("뉴스 분석 오류", level="error", error=str(e))
            return {
                "error": f"뉴스 분석 중 오류: {str(e)}",
                "keyword": keyword,
                "sources": sources
            }

    def analyze_news_sentiment(self, user_query: str) -> str:
        """
        자연어 질의를 받아 뉴스 감성 분석 수행

        Args:
            user_query: 사용자 질의 (예: "AI 기술에 대한 최근 뉴스의 여론을 분석해줘")

        Returns:
            Agent 응답 문자열
        """
        if not validate_input(user_query, max_length=500):
            return "유효하지 않은 질의입니다."

        safe_log("Agent 실행 시작", level="info", query=user_query[:50])

        try:
            response = self.agent.run(input=user_query)
            safe_log("Agent 실행 완료", level="info")
            return response
        except Exception as e:
            error_msg = f"Agent 실행 중 오류: {str(e)}"
            safe_log("Agent 실행 오류", level="error", error=str(e))
            return error_msg

    def _calculate_sentiment_distribution(self, articles: List[Dict]) -> Dict[str, int]:
        """감성 분포 계산"""
        distribution = {"positive": 0, "negative": 0, "neutral": 0}

        for article in articles:
            sentiment = article.get("sentiment", "중립")
            if sentiment == "긍정":
                distribution["positive"] += 1
            elif sentiment == "부정":
                distribution["negative"] += 1
            else:
                distribution["neutral"] += 1

        return distribution

    def _extract_keywords(self, articles: List[Dict], main_keyword: str) -> List[Dict]:
        """키워드 추출 및 빈도 계산"""
        keyword_freq = {}

        for article in articles:
            text = f"{article.get('title', '')} {article.get('content', '')}"
            words = text.split()

            for word in words:
                if len(word) > 1 and word != main_keyword:
                    keyword_freq[word] = keyword_freq.get(word, 0) + 1

        # 상위 10개 키워드 반환
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        return [
            {
                "keyword": keyword,
                "frequency": freq
            }
            for keyword, freq in sorted_keywords
        ]

    def get_conversation_history(self) -> List[Dict]:
        """대화 히스토리 반환"""
        if self.memory:
            return self.memory.chat_memory.messages
        return []


async def main():
    """메인 실행 함수 (비동기)"""
    print("🚀 News Analysis Agent 테스트 시작")
    print("=" * 60)

    try:
        config = get_config()
        agent = NewsAnalysisAgent(config.get_openai_key())

        # 테스트: 비동기 분석
        print("\n📝 비동기 뉴스 분석 테스트:")
        result = await agent.analyze_news_async(
            keyword="AI",
            sources=["네이버", "구글"],
            max_articles=5
        )

        if "error" in result:
            print(f"❌ 오류: {result['error']}")
        else:
            print(f"✅ 분석 완료:")
            print(f"   - 총 기사 수: {result['total_articles']}")
            print(f"   - 감성 분포: {result['sentiment_distribution']}")
            print(f"   - 키워드 수: {len(result['keywords'])}")

        # 테스트: 자연어 질의
        print("\n📝 자연어 질의 테스트:")
        response = agent.analyze_news_sentiment("AI 기술에 대한 최근 뉴스의 여론을 분석해줘")
        print(f"✅ 응답: {response[:200]}...")

    except Exception as e:
        print(f"❌ 오류: {e}")


if __name__ == "__main__":
    asyncio.run(main())

