"""
News Analysis Agent

뉴스 감성 분석을 위한 통합 AI Agent
네이버 뉴스와 구글 뉴스를 지원하며, 실제 Tools를 사용합니다.
"""

import json
import asyncio
import time
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

# OpenAI 요약 기능을 위한 import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Playwright 스크래퍼 (병렬처리 지원)
try:
    from agent.tools.news_scraper.playwright_scraper import PlaywrightNewsScraper
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    safe_log("Playwright 사용 불가 - Selenium 폴백", level="warning")


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

    def _parse_keyword_operators(self, keyword: str) -> Dict[str, Any]:
        """
        키워드에서 검색 연산자 파싱 (OR, AND)
        
        지원하는 형식:
        - "삼성전자 || LG전자" → OR 검색
        - "삼성전자 OR LG전자" → OR 검색
        - "삼성전자 LG전자" → AND 검색 (공백으로 구분)
        
        Returns:
            {"type": "or" | "and" | "single", "keywords": ["키워드1", "키워드2", ...]}
        """
        import re
        
        # 앞뒤 공백 제거
        keyword = keyword.strip()
        
        # OR 검색 체크 (|| 또는 OR)
        or_pattern = r'\s*(?:\|\||OR)\s*'
        if re.search(or_pattern, keyword, re.IGNORECASE):
            keywords = [k.strip() for k in re.split(or_pattern, keyword, flags=re.IGNORECASE) if k.strip()]
            return {"type": "or", "keywords": keywords}
        
        # 단일 키워드 (공백 포함 가능 - AND 검색)
        return {"type": "single", "keywords": [keyword]}

    async def analyze_news_async(
        self,
        keyword: str,
        sources: List[str] = None,
        max_articles: int = 10
    ) -> Dict[str, Any]:
        """
        비동기 뉴스 분석 실행

        Args:
            keyword: 검색할 키워드 (OR 연산자 지원: "삼성전자 || LG전자")
            sources: 뉴스 소스 목록 (["네이버", "구글"])
            max_articles: 최대 기사 수

        Returns:
            분석 결과 딕셔너리
        """
        if sources is None:
            sources = ["네이버"]

        # 입력 검증
        if not validate_input(keyword, max_length=200):
            raise ValueError("유효하지 않은 키워드입니다.")
        
        # OR 검색 파싱
        parsed = self._parse_keyword_operators(keyword)
        
        if parsed["type"] == "or" and len(parsed["keywords"]) > 1:
            # OR 검색: 각 키워드별로 분석 후 병합
            safe_log("OR 검색 감지", level="info", keywords=parsed["keywords"])
            return await self._analyze_multiple_keywords_or(
                parsed["keywords"], sources, max_articles
            )

        safe_log("뉴스 분석 시작", level="info", keyword=keyword, sources=sources)

        # 성능 측정을 위한 시간 기록
        timing_info = {
            "crawling_time": 0.0,
            "sentiment_time": 0.0,
            "summary_time": 0.0,
            "total_time": 0.0
        }
        
        # LLM 토큰 사용량 추적
        token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0  # USD
        }
        
        total_start_time = time.time()

        try:
            # 1단계: 뉴스 수집 (Playwright 병렬처리 또는 Selenium 폴백)
            crawling_start = time.time()
            articles_data = []
            
            # 소스 필터링 및 매핑
            source_mapping = {
                "네이버": "네이버", "naver": "네이버",
                "구글": "구글", "google": "구글",
            }
            unsupported_sources = ["다음", "Daum", "KBS", "SBS", "MBC", "YTN", "JTBC", "연합뉴스"]
            
            valid_sources = []
            rejected_sources = []
            
            for source in (sources or ["네이버"]):
                if source in unsupported_sources:
                    rejected_sources.append(source)
                    safe_log("지원하지 않는 뉴스 소스", level="warning", source=source)
                    continue
                
                normalized_source = source_mapping.get(source)
                if normalized_source:
                    if normalized_source not in valid_sources:
                        valid_sources.append(normalized_source)
                else:
                    rejected_sources.append(source)
            
            if not valid_sources and rejected_sources:
                return {
                    "error": f"선택한 뉴스 소스({', '.join(rejected_sources)})는 지원하지 않습니다. 네이버 또는 구글을 선택해주세요.",
                    "keyword": keyword,
                    "rejected_sources": rejected_sources,
                    "supported_sources": ["네이버", "구글"]
                }
            
            if not valid_sources:
                valid_sources = ["네이버"]
            
            # Playwright 병렬처리 사용 (가능한 경우)
            if PLAYWRIGHT_AVAILABLE:
                safe_log("Playwright 병렬 크롤링 시작", level="info", keyword=keyword, sources=valid_sources)
                print(f"[DEBUG] 🚀 Playwright 병렬처리 사용 - 소스: {valid_sources}")
                
                playwright_scraper = PlaywrightNewsScraper()
                try:
                    # 병렬로 모든 기사 수집 및 추출 (검색 + 추출 모두 병렬)
                    articles_data = await asyncio.wait_for(
                        playwright_scraper.scrape_all(keyword, valid_sources, max_articles),
                        timeout=180  # 3분 (병렬처리로 충분)
                    )
                    
                    # 키워드 추가
                    for article in articles_data:
                        article["keyword"] = keyword
                        
                except asyncio.TimeoutError:
                    safe_log("Playwright 타임아웃 (3분 초과)", level="warning")
                    return {
                        "error": f"'{keyword}' 키워드로 기사 검색 중 시간 초과가 발생했습니다.",
                        "keyword": keyword,
                        "sources": valid_sources
                    }
                finally:
                    await playwright_scraper.cleanup()
            else:
                # Selenium 폴백 (기존 방식)
                safe_log("Selenium 순차 크롤링 시작 (Playwright 불가)", level="info")
                print(f"[DEBUG] ⚠️ Selenium 순차처리 폴백")
                
                scraper = NewsScraperTool()
                try:
                    article_urls = await asyncio.wait_for(
                        asyncio.to_thread(scraper.search_news, keyword, valid_sources, max_articles),
                        timeout=120
                    )
                    
                    if not article_urls:
                        return {
                            "error": f"'{keyword}' 키워드로 기사를 찾을 수 없습니다.",
                            "keyword": keyword,
                            "sources": valid_sources
                        }
                    
                    # 순차 추출
                    for url in article_urls:
                        source = "naver" if "naver.com" in url else "google"
                        try:
                            article = scraper.scrape_article(url, source)
                            article_dict = article.to_dict()
                            article_dict["keyword"] = keyword
                            article_dict["source"] = "네이버" if source == "naver" else "구글"
                            articles_data.append(article_dict)
                        except Exception as e:
                            safe_log(f"기사 크롤링 실패: {url}", level="warning", error=str(e))
                        time.sleep(1)
                        
                except asyncio.TimeoutError:
                    return {
                        "error": f"'{keyword}' 키워드로 기사 검색 중 시간 초과가 발생했습니다.",
                        "keyword": keyword,
                        "sources": valid_sources
                    }
                finally:
                    scraper.cleanup()

            if not articles_data or (len(articles_data) == 1 and "error" in articles_data[0]):
                return {
                    "error": articles_data[0].get("error", "뉴스 수집 실패") if articles_data else "뉴스 수집 실패",
                    "keyword": keyword,
                    "sources": sources
                }

            # 크롤링 시간 기록
            timing_info["crawling_time"] = round(time.time() - crawling_start, 2)
            safe_log(f"크롤링 완료: {timing_info['crawling_time']}초", level="info")

            # 2단계: 각 기사 및 댓글 감성 분석
            sentiment_start = time.time()
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
                    "summary": "",  # 요약은 별도 단계에서 처리
                    "comments": analyzed_comments,
                    "comment_count": len(analyzed_comments)
                })

            # 감성 분석 시간 기록
            timing_info["sentiment_time"] = round(time.time() - sentiment_start, 2)
            safe_log(f"감성 분석 완료: {timing_info['sentiment_time']}초", level="info")

            # 기사 요약 생성 (별도 단계로 분리)
            summary_start = time.time()
            for i, analyzed_article in enumerate(analyzed_articles):
                summary_result = self._summarize_article(
                    analyzed_article.get('title', ''),
                    analyzed_article.get('content', '')
                )
                analyzed_articles[i]["summary"] = summary_result["summary"]
                
                # 토큰 사용량 누적
                usage = summary_result.get("usage", {})
                token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                token_usage["total_tokens"] += usage.get("total_tokens", 0)

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

            # 6단계: 전체 종합 요약 생성
            overall_result = self._generate_overall_summary(
                analyzed_articles, 
                keyword, 
                sentiment_distribution
            )
            overall_summary = overall_result["summary"]
            
            # 종합 요약 토큰 사용량 추가
            overall_usage = overall_result.get("usage", {})
            token_usage["prompt_tokens"] += overall_usage.get("prompt_tokens", 0)
            token_usage["completion_tokens"] += overall_usage.get("completion_tokens", 0)
            token_usage["total_tokens"] += overall_usage.get("total_tokens", 0)
            
            # 예상 비용 계산 (gpt-4o-mini 가격 기준: input $0.15/1M, output $0.6/1M)
            token_usage["estimated_cost"] = round(
                (token_usage["prompt_tokens"] * 0.15 / 1_000_000) +
                (token_usage["completion_tokens"] * 0.6 / 1_000_000),
                6
            )

            # 요약 시간 기록 (기사 요약 + 종합 요약)
            timing_info["summary_time"] = round(time.time() - summary_start, 2)
            safe_log(f"요약 생성 완료: {timing_info['summary_time']}초, 토큰: {token_usage['total_tokens']}", level="info")

            # 총 소요 시간
            timing_info["total_time"] = round(time.time() - total_start_time, 2)

            result = {
                "keyword": keyword,
                "sources": sources,
                "total_articles": len(analyzed_articles),
                "articles": analyzed_articles,
                "sentiment_distribution": sentiment_distribution,
                "trend_analysis": trend_result,
                "keywords": keywords,
                "overall_summary": overall_summary,
                "timing": timing_info,  # 성능 측정 정보 추가
                "token_usage": token_usage,  # LLM 토큰 사용량 추가
                "analyzed_at": datetime.now().isoformat()
            }

            safe_log(f"뉴스 분석 완료 (총 {timing_info['total_time']}초, 토큰: {token_usage['total_tokens']})", level="info", total_articles=len(analyzed_articles))
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

    async def _analyze_multiple_keywords_or(
        self,
        keywords: List[str],
        sources: List[str],
        max_articles: int
    ) -> Dict[str, Any]:
        """
        OR 검색: 여러 키워드를 각각 분석 후 결과 병합
        
        Args:
            keywords: 검색 키워드 목록
            sources: 뉴스 소스 목록
            max_articles: 키워드당 최대 기사 수
        
        Returns:
            병합된 분석 결과
        """
        total_start_time = time.time()
        timing_info = {
            "crawling_time": 0.0,
            "sentiment_time": 0.0,
            "summary_time": 0.0,
            "total_time": 0.0
        }
        token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0
        }
        
        all_articles = []
        all_keywords_data = []
        combined_sentiment = {"positive": 0, "negative": 0, "neutral": 0}
        keyword_results = []
        
        # 각 키워드별로 분석 실행
        articles_per_keyword = max(3, max_articles // len(keywords))  # 키워드당 기사 수 분배
        
        for kw in keywords:
            safe_log(f"OR 검색 - '{kw}' 분석 시작", level="info")
            
            try:
                # 단일 키워드 분석 (재귀 호출 방지를 위해 직접 분석 로직 사용)
                result = await self._analyze_single_keyword(
                    kw, sources, articles_per_keyword
                )
                
                if "error" not in result:
                    keyword_results.append({
                        "keyword": kw,
                        "article_count": result.get("total_articles", 0),
                        "sentiment": result.get("sentiment_distribution", {})
                    })
                    
                    # 기사 병합
                    for article in result.get("articles", []):
                        article["search_keyword"] = kw  # 어떤 키워드로 찾았는지 표시
                        all_articles.append(article)
                    
                    # 감정 분포 합산
                    for key in combined_sentiment:
                        combined_sentiment[key] += result.get("sentiment_distribution", {}).get(key, 0)
                    
                    # 타이밍 정보 합산
                    result_timing = result.get("timing", {})
                    timing_info["crawling_time"] += result_timing.get("crawling_time", 0)
                    timing_info["sentiment_time"] += result_timing.get("sentiment_time", 0)
                    timing_info["summary_time"] += result_timing.get("summary_time", 0)
                    
                    # 토큰 사용량 합산
                    result_tokens = result.get("token_usage", {})
                    token_usage["prompt_tokens"] += result_tokens.get("prompt_tokens", 0)
                    token_usage["completion_tokens"] += result_tokens.get("completion_tokens", 0)
                    token_usage["total_tokens"] += result_tokens.get("total_tokens", 0)
                    
                    # 키워드 데이터 병합
                    all_keywords_data.extend(result.get("keywords", []))
                    
            except Exception as e:
                safe_log(f"OR 검색 - '{kw}' 분석 실패", level="warning", error=str(e))
                continue
        
        if not all_articles:
            return {
                "error": f"'{' || '.join(keywords)}' 키워드로 기사를 찾을 수 없습니다.",
                "keyword": " || ".join(keywords),
                "sources": sources
            }
        
        # 전체 종합 요약 생성
        summary_start = time.time()
        overall_result = self._generate_overall_summary(
            all_articles,
            " || ".join(keywords),
            combined_sentiment
        )
        overall_summary = overall_result["summary"]
        
        # 종합 요약 토큰 사용량 추가
        overall_usage = overall_result.get("usage", {})
        token_usage["prompt_tokens"] += overall_usage.get("prompt_tokens", 0)
        token_usage["completion_tokens"] += overall_usage.get("completion_tokens", 0)
        token_usage["total_tokens"] += overall_usage.get("total_tokens", 0)
        
        # 예상 비용 계산
        token_usage["estimated_cost"] = round(
            (token_usage["prompt_tokens"] * 0.15 / 1_000_000) +
            (token_usage["completion_tokens"] * 0.6 / 1_000_000),
            6
        )
        
        timing_info["summary_time"] += round(time.time() - summary_start, 2)
        timing_info["total_time"] = round(time.time() - total_start_time, 2)
        
        # 결과 조합
        return {
            "keyword": " || ".join(keywords),
            "search_type": "or",
            "keyword_results": keyword_results,
            "sources": sources,
            "total_articles": len(all_articles),
            "articles": all_articles,
            "sentiment_distribution": combined_sentiment,
            "keywords": all_keywords_data[:20],  # 상위 20개
            "overall_summary": overall_summary,
            "timing": timing_info,
            "token_usage": token_usage,
            "analyzed_at": datetime.now().isoformat()
        }

    async def _analyze_single_keyword(
        self,
        keyword: str,
        sources: List[str],
        max_articles: int
    ) -> Dict[str, Any]:
        """단일 키워드 분석 (내부 사용)"""
        # 기존 analyze_news_async 로직의 핵심 부분을 분리
        timing_info = {
            "crawling_time": 0.0,
            "sentiment_time": 0.0,
            "summary_time": 0.0,
            "total_time": 0.0
        }
        token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0
        }
        total_start_time = time.time()
        
        try:
            # 1단계: 뉴스 수집
            crawling_start = time.time()
            articles_data = []
            
            source_mapping = {
                "네이버": "네이버", "naver": "네이버",
                "구글": "구글", "google": "구글",
            }
            
            valid_sources = []
            for source in sources:
                normalized_source = source_mapping.get(source)
                if normalized_source and normalized_source not in valid_sources:
                    valid_sources.append(normalized_source)
            
            if not valid_sources:
                valid_sources = ["네이버"]
            
            if PLAYWRIGHT_AVAILABLE:
                playwright_scraper = PlaywrightNewsScraper()
                try:
                    articles_data = await asyncio.wait_for(
                        playwright_scraper.scrape_all(keyword, valid_sources, max_articles),
                        timeout=120
                    )
                    for article in articles_data:
                        article["keyword"] = keyword
                except asyncio.TimeoutError:
                    return {"error": f"'{keyword}' 검색 시간 초과"}
                finally:
                    await playwright_scraper.cleanup()
            else:
                scraper = NewsScraperTool()
                try:
                    article_urls = await asyncio.wait_for(
                        asyncio.to_thread(scraper.search_news, keyword, valid_sources, max_articles),
                        timeout=120
                    )
                    for url in (article_urls or []):
                        source = "naver" if "naver.com" in url else "google"
                        try:
                            article = scraper.scrape_article(url, source)
                            article_dict = article.to_dict()
                            article_dict["keyword"] = keyword
                            articles_data.append(article_dict)
                        except:
                            pass
                        time.sleep(0.5)
                finally:
                    scraper.cleanup()
            
            timing_info["crawling_time"] = round(time.time() - crawling_start, 2)
            
            if not articles_data:
                return {"error": f"'{keyword}' 기사 없음", "keyword": keyword}
            
            # 2단계: 감성 분석
            sentiment_start = time.time()
            analyzed_articles = []
            
            for article in articles_data:
                if "error" in article:
                    continue
                    
                article_text = f"{article.get('title', '')} {article.get('content', '')}"
                try:
                    article_sentiment = analyze_sentiment_func(article_text[:500])
                except:
                    article_sentiment = {"sentiment": "중립", "sentiment_score": 0.0, "sentiment_label": "neutral", "confidence": 0.0}
                
                analyzed_articles.append({
                    **article,
                    **article_sentiment,
                    "summary": "",
                    "comments": [],
                    "comment_count": 0
                })
            
            timing_info["sentiment_time"] = round(time.time() - sentiment_start, 2)
            
            # 3단계: 요약 생성
            summary_start = time.time()
            for i, analyzed_article in enumerate(analyzed_articles):
                summary_result = self._summarize_article(
                    analyzed_article.get('title', ''),
                    analyzed_article.get('content', '')
                )
                analyzed_articles[i]["summary"] = summary_result["summary"]
                
                # 토큰 사용량 누적
                usage = summary_result.get("usage", {})
                token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                token_usage["total_tokens"] += usage.get("total_tokens", 0)
            
            # 예상 비용 계산
            token_usage["estimated_cost"] = round(
                (token_usage["prompt_tokens"] * 0.15 / 1_000_000) +
                (token_usage["completion_tokens"] * 0.6 / 1_000_000),
                6
            )
            
            sentiment_distribution = self._calculate_sentiment_distribution(analyzed_articles)
            keywords_data = self._extract_keywords(analyzed_articles, keyword)
            
            timing_info["summary_time"] = round(time.time() - summary_start, 2)
            timing_info["total_time"] = round(time.time() - total_start_time, 2)
            
            return {
                "keyword": keyword,
                "total_articles": len(analyzed_articles),
                "articles": analyzed_articles,
                "sentiment_distribution": sentiment_distribution,
                "keywords": keywords_data,
                "timing": timing_info,
                "token_usage": token_usage
            }
            
        except Exception as e:
            return {"error": str(e), "keyword": keyword}

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

    def _summarize_article(self, title: str, content: str) -> Dict[str, Any]:
        """
        OpenAI를 사용하여 기사 내용 요약
        
        Returns:
            {"summary": "요약 텍스트", "usage": {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}}
        """
        result = {"summary": "", "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
        
        if not OPENAI_AVAILABLE or not self.openai_api_key:
            return result
        
        try:
            client = OpenAI(api_key=self.openai_api_key)
            
            # 내용이 너무 길면 잘라내기
            text = f"제목: {title}\n\n내용: {content[:3000]}"
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 뉴스 기사 요약 전문가입니다. 주어진 뉴스 기사를 3-4문장으로 핵심 내용만 간결하게 요약해주세요. 한국어로 답변하세요."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            result["summary"] = response.choices[0].message.content.strip()
            
            # 토큰 사용량 추출
            if response.usage:
                result["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return result
        except Exception as e:
            safe_log("기사 요약 실패", level="warning", error=str(e))
            return result

    def _generate_overall_summary(self, articles: List[Dict], keyword: str, sentiment_distribution: Dict) -> Dict[str, Any]:
        """
        전체 기사에 대한 종합 요약 생성
        
        Returns:
            {"summary": "요약 텍스트", "usage": {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}}
        """
        result = {"summary": "", "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
        
        if not OPENAI_AVAILABLE or not self.openai_api_key:
            return result
        
        try:
            client = OpenAI(api_key=self.openai_api_key)
            
            # 기사 제목과 요약 수집
            article_summaries = []
            for i, article in enumerate(articles[:10], 1):  # 최대 10개 기사
                title = article.get('title', '')
                summary = article.get('summary', '')
                sentiment = article.get('sentiment', '중립')
                if title:
                    article_summaries.append(f"{i}. [{sentiment}] {title}")
                    if summary:
                        article_summaries.append(f"   요약: {summary[:100]}...")
            
            articles_text = "\n".join(article_summaries)
            
            # 감정 분포 정보
            total = sum(sentiment_distribution.values())
            sentiment_info = f"""
감정 분포:
- 긍정: {sentiment_distribution.get('positive', 0)}개 ({sentiment_distribution.get('positive', 0)/total*100:.1f}% if total > 0 else 0)
- 부정: {sentiment_distribution.get('negative', 0)}개 ({sentiment_distribution.get('negative', 0)/total*100:.1f}% if total > 0 else 0)
- 중립: {sentiment_distribution.get('neutral', 0)}개 ({sentiment_distribution.get('neutral', 0)/total*100:.1f}% if total > 0 else 0)
"""
            
            prompt = f"""'{keyword}' 키워드에 대한 뉴스 분석 결과를 종합 요약해주세요.

수집된 기사 수: {len(articles)}개

{sentiment_info}

주요 기사 목록:
{articles_text}

위 정보를 바탕으로:
1. 전반적인 여론 동향 (긍정/부정/중립)
2. 주요 쟁점 및 이슈
3. 향후 전망 또는 시사점

을 5-7문장으로 종합 요약해주세요. 한국어로 답변하세요."""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 뉴스 분석 전문가입니다. 여러 뉴스 기사를 분석하여 종합적인 인사이트를 제공합니다."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            result["summary"] = response.choices[0].message.content.strip()
            
            # 토큰 사용량 추출
            if response.usage:
                result["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return result
        except Exception as e:
            safe_log("종합 요약 생성 실패", level="warning", error=str(e))
            return result

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
