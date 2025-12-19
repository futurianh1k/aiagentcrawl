"""
3회차 실습 07: LangGraph Sequential 워크플로우
페이지 20 - Crawler → Analyzer → Reporter

이 스크립트는 LangGraph를 이용한 순차적 Multi-Agent 워크플로우를 구현합니다.
- StateGraph 기반 상태 관리
- Agent 간 데이터 흐름
- 순차 실행 패턴
- 에러 핸들링 및 로깅
"""

import os
import json
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class AgentState(TypedDict):
    """Multi-Agent 공유 상태"""
    # 입력 데이터
    keyword: str
    max_articles: int

    # Crawler Agent 결과
    articles: List[Dict[str, Any]]
    crawler_status: str
    crawler_timestamp: str

    # Analyzer Agent 결과  
    analysis_results: List[Dict[str, Any]]
    analyzer_status: str
    analyzer_timestamp: str

    # Reporter Agent 결과
    final_report: str
    summary_stats: Dict[str, Any]
    reporter_status: str
    reporter_timestamp: str

    # 메타데이터
    workflow_id: str
    total_processing_time: float
    errors: List[str]

def setup_llm():
    """LLM 초기화"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 환경 변수에 설정되지 않았습니다.")

    return ChatOpenAI(
        model="gpt-4",
        temperature=0.3,
        api_key=api_key
    )

def crawler_agent(state: AgentState) -> AgentState:
    """뉴스 크롤링 Agent (모의)"""
    print(f"🕷️ Crawler Agent 실행: '{state['keyword']}' 검색")

    try:
        start_time = datetime.now()

        # 실제 환경에서는 여기서 Selenium, Playwright, Firecrawl 사용
        mock_articles = [
            {
                "title": f"{state['keyword']} 관련 최신 동향",
                "url": "https://news1.example.com/article1",
                "summary": "긍정적인 전망을 제시하는 기사입니다.",
                "comments": [
                    "정말 좋은 소식이네요!",
                    "드디어 개선되는군요.", 
                    "기대하고 있었습니다."
                ],
                "crawl_timestamp": datetime.now().isoformat()
            },
            {
                "title": f"{state['keyword']} 논란 확산",
                "url": "https://news2.example.com/article2", 
                "summary": "일부 부정적 의견이 제기되고 있습니다.",
                "comments": [
                    "이건 문제가 있어 보여요.",
                    "왜 이런 결정을 했을까요?",
                    "실망스럽네요."
                ],
                "crawl_timestamp": datetime.now().isoformat()
            },
            {
                "title": f"{state['keyword']} 중립적 분석 리포트",
                "url": "https://news3.example.com/article3",
                "summary": "객관적인 분석을 제공하는 기사입니다.", 
                "comments": [
                    "자세한 분석 감사합니다.",
                    "더 지켜봐야 할 것 같네요.",
                    "균형잡힌 시각이군요."
                ],
                "crawl_timestamp": datetime.now().isoformat()
            }
        ]

        # 요청된 수만큼만 반환
        articles = mock_articles[:state['max_articles']]

        processing_time = (datetime.now() - start_time).total_seconds()

        # 상태 업데이트
        state["articles"] = articles
        state["crawler_status"] = "completed"
        state["crawler_timestamp"] = datetime.now().isoformat()

        print(f"✅ Crawler 완료: {len(articles)}개 기사 수집 ({processing_time:.2f}초)")

        return state

    except Exception as e:
        print(f"❌ Crawler 오류: {e}")
        state["crawler_status"] = "error"
        state["errors"].append(f"Crawler: {str(e)}")
        state["articles"] = []
        return state

def analyzer_agent(state: AgentState) -> AgentState:
    """감성 분석 Agent"""
    print("🔍 Analyzer Agent 실행: 댓글 감성 분석")

    try:
        start_time = datetime.now()
        llm = setup_llm()

        analysis_results = []

        for article in state["articles"]:
            article_analysis = {
                "article_title": article["title"],
                "article_url": article["url"],
                "comment_analyses": []
            }

            print(f"  📰 분석 중: {article['title'][:30]}...")

            # 각 댓글 분석
            for comment in article["comments"]:
                prompt = f"""다음 댓글의 감성을 분석하고 JSON으로 응답하세요:

                댓글: "{comment}"

                응답 형식:
                {{
                    "sentiment": "긍정|부정|중립",
                    "confidence": 0.0-1.0,
                    "keywords": ["키워드1", "키워드2"]
                }}"""

                try:
                    response = llm.invoke([HumanMessage(content=prompt)])
                    content = response.content

                    # JSON 파싱
                    if '{' in content and '}' in content:
                        start_idx = content.find('{')
                        end_idx = content.rfind('}') + 1
                        json_str = content[start_idx:end_idx]
                        sentiment_data = json.loads(json_str)

                        comment_analysis = {
                            "comment": comment,
                            "sentiment": sentiment_data.get("sentiment", "중립"),
                            "confidence": sentiment_data.get("confidence", 0.5),
                            "keywords": sentiment_data.get("keywords", [])
                        }
                    else:
                        # 폴백
                        comment_analysis = {
                            "comment": comment,
                            "sentiment": "중립",
                            "confidence": 0.0,
                            "keywords": []
                        }

                    article_analysis["comment_analyses"].append(comment_analysis)

                except Exception as e:
                    print(f"    ⚠️ 댓글 분석 실패: {e}")
                    # 에러 시 기본값
                    article_analysis["comment_analyses"].append({
                        "comment": comment,
                        "sentiment": "중립", 
                        "confidence": 0.0,
                        "keywords": [],
                        "error": str(e)
                    })

            analysis_results.append(article_analysis)

        processing_time = (datetime.now() - start_time).total_seconds()

        # 상태 업데이트
        state["analysis_results"] = analysis_results
        state["analyzer_status"] = "completed"
        state["analyzer_timestamp"] = datetime.now().isoformat()

        total_comments = sum(len(article["comments"]) for article in state["articles"])
        print(f"✅ Analyzer 완료: {total_comments}개 댓글 분석 ({processing_time:.2f}초)")

        return state

    except Exception as e:
        print(f"❌ Analyzer 오류: {e}")
        state["analyzer_status"] = "error"
        state["errors"].append(f"Analyzer: {str(e)}")
        state["analysis_results"] = []
        return state

def reporter_agent(state: AgentState) -> AgentState:
    """리포트 생성 Agent"""
    print("📊 Reporter Agent 실행: 최종 리포트 생성")

    try:
        start_time = datetime.now()

        # 통계 계산
        all_sentiments = []
        all_confidences = []

        for article_analysis in state["analysis_results"]:
            for comment_analysis in article_analysis["comment_analyses"]:
                all_sentiments.append(comment_analysis["sentiment"])
                all_confidences.append(comment_analysis["confidence"])

        # 감성 분포 계산
        sentiment_counts = {}
        for sentiment in all_sentiments:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

        total_comments = len(all_sentiments)
        sentiment_percentages = {}
        if total_comments > 0:
            for sentiment, count in sentiment_counts.items():
                sentiment_percentages[sentiment] = (count / total_comments) * 100

        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        # 전체 경향 판단
        positive_pct = sentiment_percentages.get("긍정", 0)
        negative_pct = sentiment_percentages.get("부정", 0)
        neutral_pct = sentiment_percentages.get("중립", 0)

        if positive_pct > negative_pct and positive_pct > neutral_pct:
            overall_trend = "긍정적"
        elif negative_pct > positive_pct and negative_pct > neutral_pct:
            overall_trend = "부정적"
        else:
            overall_trend = "중립적"

        # 요약 통계
        summary_stats = {
            "total_articles": len(state["articles"]),
            "total_comments": total_comments,
            "sentiment_distribution": sentiment_percentages,
            "average_confidence": avg_confidence,
            "overall_trend": overall_trend
        }

        # 최종 리포트 생성
        report = f"""
🎯 {state['keyword']} 감성 분석 리포트
{'=' * 50}

📊 분석 개요:
- 분석 기사 수: {summary_stats['total_articles']}개
- 분석 댓글 수: {summary_stats['total_comments']}개
- 전체 경향: {overall_trend}
- 평균 신뢰도: {avg_confidence:.2f}

📈 감성 분포:
- 긍정: {positive_pct:.1f}%
- 부정: {negative_pct:.1f}%  
- 중립: {neutral_pct:.1f}%

📝 상세 분석:
"""

        for i, article_analysis in enumerate(state["analysis_results"], 1):
            report += f"\n{i}. {article_analysis['article_title']}\n"

            article_sentiments = [ca["sentiment"] for ca in article_analysis["comment_analyses"]]
            pos = article_sentiments.count("긍정")
            neg = article_sentiments.count("부정") 
            neu = article_sentiments.count("중립")

            report += f"   댓글 반응: 긍정 {pos}개, 부정 {neg}개, 중립 {neu}개\n"

        report += f"\n⏱️ 처리 시간: {datetime.now().isoformat()}"

        processing_time = (datetime.now() - start_time).total_seconds()

        # 상태 업데이트
        state["final_report"] = report
        state["summary_stats"] = summary_stats
        state["reporter_status"] = "completed"
        state["reporter_timestamp"] = datetime.now().isoformat()

        print(f"✅ Reporter 완료: 리포트 생성 ({processing_time:.2f}초)")

        return state

    except Exception as e:
        print(f"❌ Reporter 오류: {e}")
        state["reporter_status"] = "error"
        state["errors"].append(f"Reporter: {str(e)}")
        state["final_report"] = f"리포트 생성 실패: {str(e)}"
        state["summary_stats"] = {}
        return state

def create_workflow() -> StateGraph:
    """LangGraph 워크플로우 생성"""

    # StateGraph 초기화
    workflow = StateGraph(AgentState)

    # Agent 노드 추가
    workflow.add_node("crawler", crawler_agent)
    workflow.add_node("analyzer", analyzer_agent) 
    workflow.add_node("reporter", reporter_agent)

    # 순차적 흐름 정의
    workflow.add_edge("crawler", "analyzer")
    workflow.add_edge("analyzer", "reporter")
    workflow.add_edge("reporter", END)

    # 시작점 설정
    workflow.set_entry_point("crawler")

    return workflow.compile()

if __name__ == "__main__":
    print("🚀 LangGraph Sequential 워크플로우 실습을 시작합니다!")
    print("=" * 70)

    try:
        # 1. 워크플로우 생성
        app = create_workflow()
        print("✅ LangGraph 워크플로우 생성 완료")

        # 2. 초기 상태 설정
        initial_state: AgentState = {
            "keyword": "삼성전자",
            "max_articles": 3,
            "articles": [],
            "crawler_status": "pending",
            "crawler_timestamp": "",
            "analysis_results": [],
            "analyzer_status": "pending", 
            "analyzer_timestamp": "",
            "final_report": "",
            "summary_stats": {},
            "reporter_status": "pending",
            "reporter_timestamp": "",
            "workflow_id": f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "total_processing_time": 0.0,
            "errors": []
        }

        print(f"\n🎯 분석 키워드: {initial_state['keyword']}")
        print(f"📊 최대 기사 수: {initial_state['max_articles']}개")
        print(f"🆔 워크플로우 ID: {initial_state['workflow_id']}")

        # 3. 워크플로우 실행
        print("\n🔄 Multi-Agent 워크플로우 실행")
        print("-" * 50)

        overall_start = datetime.now()

        # LangGraph 실행
        final_state = app.invoke(initial_state)

        overall_time = (datetime.now() - overall_start).total_seconds()

        print("\n" + "=" * 70)
        print("🎉 워크플로우 실행 완료!")
        print("=" * 70)

        # 4. 결과 출력
        print(f"\n📋 실행 상태:")
        print(f"   🕷️ Crawler: {final_state['crawler_status']}")
        print(f"   🔍 Analyzer: {final_state['analyzer_status']}")  
        print(f"   📊 Reporter: {final_state['reporter_status']}")
        print(f"   ⏱️ 총 처리시간: {overall_time:.2f}초")

        if final_state["errors"]:
            print(f"\n⚠️ 오류 목록:")
            for error in final_state["errors"]:
                print(f"   - {error}")

        # 5. 최종 리포트 출력
        if final_state["final_report"]:
            print(f"\n{final_state['final_report']}")

        # 6. 요약 통계
        if final_state["summary_stats"]:
            stats = final_state["summary_stats"]
            print(f"\n📈 핵심 통계:")
            print(f"   전체 경향: {stats.get('overall_trend', 'N/A')}")
            print(f"   신뢰도: {stats.get('average_confidence', 0):.2f}")

            dist = stats.get('sentiment_distribution', {})
            for sentiment, pct in dist.items():
                print(f"   {sentiment}: {pct:.1f}%")

        print("\n✅ LangGraph Sequential 실습 완료!")
        print("\n💡 핵심 개념:")
        print("   1. StateGraph: 상태 기반 워크플로우")
        print("   2. Sequential Flow: A → B → C 순차 실행")
        print("   3. State Sharing: Agent 간 데이터 공유")
        print("   4. Error Handling: 개별 Agent 오류 처리")
        print("\n📚 다음 단계:")
        print("   - 08_langgraph_conditional.py: 조건부 라우팅")
        print("   - 09_langchain_memory.py: 대화 메모리 관리")

    except Exception as e:
        print(f"❌ 실습 오류: {e}")
        print("\n🔧 해결 방법:")
        print("   1. OpenAI API 키 확인")
        print("   2. pip install langgraph langchain-openai")
        print("   3. 네트워크 연결 확인")
