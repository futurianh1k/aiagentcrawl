"""
News Analysis Agent

뉴스 감성 분석을 위한 통합 AI Agent
네이버 뉴스와 구글 뉴스를 지원하며, 실제 Tools를 사용합니다.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

# LangChain import (최신 버전 1.2.0 호환)
try:
    # LangGraph 기반 ReAct Agent (최신 방식)
    from langgraph.prebuilt import create_react_agent
    from langchain_openai import ChatOpenAI
    from langchain_core.chat_history import InMemoryChatMessageHistory
    from langchain_core.messages import HumanMessage, AIMessage
    AGENT_AVAILABLE = True
    USE_LANGGRAPH = True
except ImportError:
    try:
        # 대체: LangChain의 다른 방식 시도
        from langchain_openai import ChatOpenAI
        from langchain_core.chat_history import InMemoryChatMessageHistory
        AGENT_AVAILABLE = True
        USE_LANGGRAPH = False
    except ImportError:
        AGENT_AVAILABLE = False
        USE_LANGGRAPH = False

from common.config import get_config
from common.utils import safe_log, validate_input
from agent.tools import scrape_news, analyze_sentiment, analyze_sentiment_func, analyze_news_trend, analyze_news_trend_func
from agent.tools.news_scraper import NewsScraperTool


class NewsAnalysisAgent:
    """뉴스 감성 분석을 위한 통합 AI Agent"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Agent 초기화

        Args:
            api_key: OpenAI API 키 (None이면 환경 변수에서 읽음)
        """
        config = get_config()
        self.openai_api_key = api_key or config.get_openai_key()

        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY가 필요합니다.")

        # LangChain Agent는 선택적 (analyze_news_sentiment에서만 사용)
        # analyze_news_async는 LangChain 없이도 작동
        self.agent = None
        self.llm = None
        self.memory = None

        if AGENT_AVAILABLE:
            try:
                # LLM 초기화
                self.llm = ChatOpenAI(
                    temperature=0.1,
                    openai_api_key=self.openai_api_key,
                    max_tokens=2000,
                    model="gpt-4o-mini"
                )

                # 메모리 설정 (최신 방식)
                try:
                    self.memory = InMemoryChatMessageHistory()
                except Exception as e:
                    safe_log("메모리 초기화 실패", level="warning", error=str(e))
                    self.memory = None

                # Tools 등록 (실제 Tools 사용)
                self.tools = [
                    scrape_news,
                    analyze_sentiment,
                    analyze_news_trend,
                ]

                # Agent 초기화 (LangGraph 방식)
                if USE_LANGGRAPH and create_react_agent:
                    try:
                        # create_react_agent는 model과 tools만 필요
                        self.agent = create_react_agent(
                            model=self.llm,
                            tools=self.tools
                        )
                        safe_log("NewsAnalysisAgent 초기화 완료 (LangGraph Agent 포함)", level="info", tools_count=len(self.tools))
                    except Exception as e:
                        safe_log("LangGraph Agent 초기화 실패 (계속 진행)", level="warning", error=str(e))
                        self.agent = None
                else:
                    safe_log("LangGraph를 사용할 수 없음 (analyze_news_async만 사용 가능)", level="warning")
                    self.agent = None

            except Exception as e:
                safe_log("LangChain 초기화 실패 (계속 진행)", level="warning", error=str(e))
                # LangChain 없이도 analyze_news_async는 작동 가능
        else:
            safe_log("LangChain이 설치되지 않음 (analyze_news_async만 사용 가능)", level="warning")

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
            # scrape_news가 @tool 데코레이터로 장식되어 있어 직접 호출 불가
            # NewsScraperTool을 직접 사용
            scraper = NewsScraperTool()
            articles_data = []
            
            try:
                # 소스 필터링 및 매핑 (다양한 소스 이름 지원)
                source_mapping = {
                    "네이버": "네이버",
                    "naver": "네이버",
                    "구글": "구글",
                    "google": "구글",
                }
                
                # 지원하지 않는 소스 목록 (명확한 에러 메시지용)
                unsupported_sources = ["다음", "Daum", "KBS", "SBS", "MBC", "YTN", "JTBC", "연합뉴스"]
                
                valid_sources = []
                rejected_sources = []  # 지원하지 않는 소스 추적
                
                for source in (sources or ["네이버"]):
                    # 지원하지 않는 소스 확인
                    if source in unsupported_sources:
                        rejected_sources.append(source)
                        safe_log("지원하지 않는 뉴스 소스", level="warning", source=source)
                        continue
                    
                    normalized_source = source_mapping.get(source, None)
                    if normalized_source:
                        if normalized_source not in valid_sources:
                            valid_sources.append(normalized_source)
                        if source != normalized_source:
                            safe_log(f"소스 매핑: {source} -> {normalized_source}", level="info")
                    else:
                        # 알 수 없는 소스
                        rejected_sources.append(source)
                        safe_log("알 수 없는 뉴스 소스", level="warning", source=source)
                
                # 지원하지 않는 소스만 선택한 경우 에러 반환
                if not valid_sources and rejected_sources:
                    return {
                        "error": f"선택한 뉴스 소스({', '.join(rejected_sources)})는 현재 지원하지 않습니다. 네이버 또는 구글을 선택해주세요.",
                        "keyword": keyword,
                        "rejected_sources": rejected_sources,
                        "supported_sources": ["네이버", "구글"]
                    }
                
                if not valid_sources:
                    valid_sources = ["네이버"]  # 기본값
                
                # 뉴스 검색 및 크롤링 (타임아웃 설정)
                import asyncio
                try:
                    # 전체 크롤링에 최대 2분 제한 (각 소스별로 60초)
                    article_urls = await asyncio.wait_for(
                        asyncio.to_thread(scraper.search_news, keyword, valid_sources, max_articles),
                        timeout=120  # 2분
                    )
                except asyncio.TimeoutError:
                    safe_log("뉴스 검색 타임아웃 (2분 초과)", level="warning", keyword=keyword, sources=valid_sources)
                    return {
                        "error": f"'{keyword}' 키워드로 기사 검색 중 시간 초과가 발생했습니다.",
                        "keyword": keyword,
                        "sources": valid_sources
                    }
                
                if not article_urls:
                    return {
                        "error": f"'{keyword}' 키워드로 기사를 찾을 수 없습니다.",
                        "keyword": keyword,
                        "sources": valid_sources
                    }
                
                # 각 기사 상세 정보 추출
                for i, url in enumerate(article_urls, 1):
                    safe_log(f"기사 처리 중 ({i}/{len(article_urls)})", level="info")
                    
                    # URL에서 소스 판단
                    source = "naver" if "naver.com" in url else "google"
                    
                    try:
                        article = scraper.scrape_article(url, source)
                        article_dict = article.to_dict()
                        article_dict["keyword"] = keyword
                        article_dict["source"] = "네이버" if source == "naver" else "구글"
                        articles_data.append(article_dict)
                    except Exception as e:
                        safe_log(f"기사 크롤링 실패: {url}", level="warning", error=str(e))
                        continue
                    
                    # Rate Limit 준수
                    import time
                    time.sleep(1)
                    
            finally:
                scraper.cleanup()

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
                    safe_log("기사 스킵 (에러 포함)", level="warning", error=article.get("error"))
                    continue

                # 기사 본문 감성 분석
                article_text = f"{article.get('title', '')} {article.get('content', '')}"
                
                try:
                    # analyze_sentiment_func 사용 (직접 호출 가능한 함수)
                    article_sentiment = analyze_sentiment_func(article_text[:500])  # 최대 500자
                except Exception as e:
                    safe_log("기사 감성 분석 실패", level="error", error=str(e))
                    article_sentiment = {
                        "sentiment": "중립",
                        "sentiment_score": 0.0,
                        "sentiment_label": "neutral",
                        "confidence": 0.0
                    }

                # 댓글 감성 분석
                article_comments = article.get("comments", [])
                analyzed_comments = []

                for comment in article_comments[:10]:  # 최대 10개 댓글
                    comment_text = comment.get("text", "") if isinstance(comment, dict) else str(comment)
                    if comment_text:
                        try:
                            # analyze_sentiment_func 사용 (직접 호출 가능한 함수)
                            comment_sentiment = analyze_sentiment_func(comment_text)
                            # 댓글 데이터와 감성 분석 결과 병합
                            comment_data = comment if isinstance(comment, dict) else {"text": comment}
                            analyzed_comments.append({
                                **comment_data,
                                **comment_sentiment
                            })
                            all_comments.append(comment_text)
                        except Exception as e:
                            safe_log("댓글 감성 분석 실패", level="warning", error=str(e))
                            continue

                analyzed_articles.append({
                    **article,
                    **article_sentiment,
                    "comments": analyzed_comments,
                    "comment_count": len(analyzed_comments)
                })

            # 3단계: 전체 동향 분석
            if all_comments:
                # analyze_news_trend_func 사용 (직접 호출 가능한 함수)
                trend_result = analyze_news_trend_func(
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
        if not self.agent:
            return "LangChain Agent가 초기화되지 않았습니다. analyze_news_async를 사용하세요."

        if not validate_input(user_query, max_length=500):
            return "유효하지 않은 질의입니다."

        safe_log("Agent 실행 시작", level="info", query=user_query[:50])

        try:
            # LangGraph Agent 실행 (최신 방식)
            if USE_LANGGRAPH:
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=user_query)]
                if self.memory:
                    messages = list(self.memory.messages) + messages
                
                response = self.agent.invoke({"messages": messages})
                
                # 메모리에 응답 저장
                if self.memory:
                    self.memory.add_message(HumanMessage(content=user_query))
                    if isinstance(response, dict) and "messages" in response:
                        self.memory.add_messages(response["messages"][-1:])
                
                # 응답 추출
                if isinstance(response, dict) and "messages" in response:
                    last_message = response["messages"][-1]
                    result = last_message.content if hasattr(last_message, "content") else str(last_message)
                else:
                    result = str(response)
            else:
                # 대체 방식 (없으면 에러)
                result = "LangGraph Agent를 사용할 수 없습니다."
            
            safe_log("Agent 실행 완료", level="info")
            return result
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
            return [{"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} for m in self.memory.messages]
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
        if agent.agent:
            print("\n📝 자연어 질의 테스트:")
            response = agent.analyze_news_sentiment("AI 기술에 대한 최근 뉴스의 여론을 분석해줘")
            print(f"✅ 응답: {response[:200]}...")

    except Exception as e:
        print(f"❌ 오류: {e}")


if __name__ == "__main__":
    asyncio.run(main())
