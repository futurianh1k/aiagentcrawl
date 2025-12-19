"""
3회차 실습 08: LangGraph Conditional Routing
페이지 21 - 댓글 수 기준 분기 라우팅

이 스크립트는 LangGraph의 조건부 라우팅을 구현합니다.
- 조건부 분기 (Conditional Edge)
- 댓글 수에 따른 배치/실시간 분석 선택
- 동적 워크플로우 제어
- 성능 최적화 전략
"""

import os
from typing import TypedDict, List, Dict, Any
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class ConditionalAgentState(TypedDict):
    """조건부 라우팅용 상태"""
    keyword: str
    articles: List[Dict[str, Any]]
    total_comments: int
    processing_mode: str  # "batch" 또는 "realtime"

    # 분석 결과
    analysis_results: List[Dict[str, Any]]
    processing_stats: Dict[str, Any]

    # 메타데이터
    workflow_path: List[str]  # 실행된 노드 경로
    decision_reasons: List[str]  # 분기 결정 이유
    errors: List[str]

def setup_llm():
    """LLM 초기화"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 환경 변수에 설정되지 않았습니다.")

    return ChatOpenAI(model="gpt-4", temperature=0.3, api_key=api_key)

def data_validator(state: ConditionalAgentState) -> ConditionalAgentState:
    """데이터 검증 Agent"""
    print("🔍 Data Validator 실행: 입력 데이터 검증")

    state["workflow_path"].append("validator")

    # 모의 기사 데이터 생성 (댓글 수가 다른 기사들)
    mock_articles = [
        {
            "title": f"{state['keyword']} 대규모 업데이트",
            "comments": [f"댓글 {i}" for i in range(150)]  # 150개 댓글
        },
        {
            "title": f"{state['keyword']} 소식", 
            "comments": [f"댓글 {i}" for i in range(5)]   # 5개 댓글
        },
        {
            "title": f"{state['keyword']} 분석",
            "comments": [f"댓글 {i}" for i in range(200)]  # 200개 댓글
        }
    ]

    state["articles"] = mock_articles

    # 총 댓글 수 계산
    total_comments = sum(len(article["comments"]) for article in state["articles"])
    state["total_comments"] = total_comments

    print(f"✅ 데이터 검증 완료: {len(state['articles'])}개 기사, {total_comments}개 댓글")

    return state

def should_use_batch_processing(state: ConditionalAgentState) -> str:
    """조건부 라우팅: 배치 처리 여부 결정"""

    threshold = 100  # 댓글 100개 기준
    total_comments = state["total_comments"]

    if total_comments > threshold:
        decision = "batch_analyzer"
        reason = f"총 {total_comments}개 댓글 > {threshold}개 기준, 배치 처리 선택"
        state["processing_mode"] = "batch"
    else:
        decision = "realtime_analyzer"
        reason = f"총 {total_comments}개 댓글 ≤ {threshold}개 기준, 실시간 처리 선택"
        state["processing_mode"] = "realtime"

    state["decision_reasons"].append(reason)

    print(f"🔀 라우팅 결정: {decision}")
    print(f"📋 결정 근거: {reason}")

    return decision

def realtime_analyzer(state: ConditionalAgentState) -> ConditionalAgentState:
    """실시간 감성 분석 Agent"""
    print("⚡ Realtime Analyzer 실행: 순차 처리")

    state["workflow_path"].append("realtime_analyzer")
    start_time = datetime.now()

    try:
        llm = setup_llm()
        analysis_results = []

        for article in state["articles"]:
            article_analysis = {
                "title": article["title"],
                "comment_count": len(article["comments"]),
                "sentiments": [],
                "processing_method": "realtime"
            }

            print(f"  📰 실시간 분석: {article['title']} ({len(article['comments'])}개 댓글)")

            # 각 댓글을 개별적으로 즉시 처리
            for i, comment in enumerate(article["comments"]):
                # 실시간 처리를 위한 간단한 규칙 기반 분석
                if any(word in comment.lower() for word in ["좋", "훌륭", "최고"]):
                    sentiment = "긍정"
                elif any(word in comment.lower() for word in ["나쁘", "최악", "실망"]):
                    sentiment = "부정"
                else:
                    sentiment = "중립"

                article_analysis["sentiments"].append({
                    "comment_index": i,
                    "sentiment": sentiment,
                    "processing_time": 0.001  # 빠른 처리
                })

            analysis_results.append(article_analysis)

        processing_time = (datetime.now() - start_time).total_seconds()

        state["analysis_results"] = analysis_results
        state["processing_stats"] = {
            "method": "realtime",
            "total_processing_time": processing_time,
            "comments_per_second": state["total_comments"] / processing_time if processing_time > 0 else 0,
            "advantages": ["즉시 결과 확인", "메모리 효율적", "중간 결과 활용 가능"]
        }

        print(f"✅ 실시간 분석 완료: {state['total_comments']}개 댓글, {processing_time:.2f}초")

    except Exception as e:
        print(f"❌ 실시간 분석 오류: {e}")
        state["errors"].append(f"Realtime Analyzer: {str(e)}")

    return state

def batch_analyzer(state: ConditionalAgentState) -> ConditionalAgentState:
    """배치 감성 분석 Agent"""
    print("📦 Batch Analyzer 실행: 배치 처리")

    state["workflow_path"].append("batch_analyzer")
    start_time = datetime.now()

    try:
        llm = setup_llm()
        analysis_results = []

        # 모든 댓글을 모아서 배치로 처리
        all_comments = []
        comment_mapping = []  # 댓글과 기사 매핑 정보

        for article_idx, article in enumerate(state["articles"]):
            for comment_idx, comment in enumerate(article["comments"]):
                all_comments.append(comment)
                comment_mapping.append({
                    "article_idx": article_idx,
                    "comment_idx": comment_idx,
                    "article_title": article["title"]
                })

        print(f"  📊 배치 분석 준비: 총 {len(all_comments)}개 댓글")

        # 배치 크기로 나누어 처리 (실제로는 LLM Batch API 사용)
        batch_size = 50
        batch_results = []

        for i in range(0, len(all_comments), batch_size):
            batch = all_comments[i:i + batch_size]
            print(f"    배치 {i//batch_size + 1}: {len(batch)}개 댓글 처리")

            # 배치 처리 시뮬레이션 (실제로는 더 복잡한 LLM 호출)
            for comment in batch:
                if any(word in comment.lower() for word in ["좋", "훌륭", "최고"]):
                    sentiment = "긍정"
                elif any(word in comment.lower() for word in ["나쁘", "최악", "실망"]):
                    sentiment = "부정" 
                else:
                    sentiment = "중립"

                batch_results.append({
                    "comment": comment,
                    "sentiment": sentiment,
                    "batch_processed": True
                })

        # 결과를 기사별로 재구성
        for article_idx, article in enumerate(state["articles"]):
            article_analysis = {
                "title": article["title"],
                "comment_count": len(article["comments"]),
                "sentiments": [],
                "processing_method": "batch"
            }

            # 해당 기사의 댓글 결과만 추출
            for mapping, result in zip(comment_mapping, batch_results):
                if mapping["article_idx"] == article_idx:
                    article_analysis["sentiments"].append({
                        "comment_index": mapping["comment_idx"],
                        "sentiment": result["sentiment"],
                        "batch_processed": True
                    })

            analysis_results.append(article_analysis)

        processing_time = (datetime.now() - start_time).total_seconds()

        state["analysis_results"] = analysis_results
        state["processing_stats"] = {
            "method": "batch",
            "total_processing_time": processing_time,
            "comments_per_second": state["total_comments"] / processing_time if processing_time > 0 else 0,
            "batch_size": batch_size,
            "total_batches": len(range(0, len(all_comments), batch_size)),
            "advantages": ["높은 처리량", "비용 효율적", "일관된 품질"]
        }

        print(f"✅ 배치 분석 완료: {state['total_comments']}개 댓글, {processing_time:.2f}초")

    except Exception as e:
        print(f"❌ 배치 분석 오류: {e}")
        state["errors"].append(f"Batch Analyzer: {str(e)}")

    return state

def results_aggregator(state: ConditionalAgentState) -> ConditionalAgentState:
    """결과 집계 Agent"""
    print("📈 Results Aggregator 실행: 결과 집계 및 요약")

    state["workflow_path"].append("aggregator")

    try:
        # 전체 감성 분포 계산
        all_sentiments = []
        for article_analysis in state["analysis_results"]:
            for sentiment_data in article_analysis["sentiments"]:
                all_sentiments.append(sentiment_data["sentiment"])

        sentiment_counts = {}
        for sentiment in all_sentiments:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

        # 처리 방식별 성능 비교
        processing_method = state["processing_stats"]["method"]
        processing_time = state["processing_stats"]["total_processing_time"]
        throughput = state["processing_stats"]["comments_per_second"]

        summary_report = f"""
🎯 조건부 라우팅 분석 결과
{'=' * 50}

🔀 워크플로우 경로: {' → '.join(state['workflow_path'])}

📊 처리 통계:
- 선택된 방식: {processing_method.upper()}
- 총 댓글 수: {state['total_comments']}개
- 처리 시간: {processing_time:.2f}초
- 처리량: {throughput:.1f} 댓글/초

📋 분기 결정 과정:
"""

        for reason in state["decision_reasons"]:
            summary_report += f"- {reason}\n"

        summary_report += f"""
📈 감성 분포:
- 긍정: {sentiment_counts.get('긍정', 0)}개 ({sentiment_counts.get('긍정', 0)/len(all_sentiments)*100:.1f}%)
- 부정: {sentiment_counts.get('부정', 0)}개 ({sentiment_counts.get('부정', 0)/len(all_sentiments)*100:.1f}%)
- 중립: {sentiment_counts.get('중립', 0)}개 ({sentiment_counts.get('중립', 0)/len(all_sentiments)*100:.1f}%)

🚀 {processing_method.title()} 처리의 장점:
"""

        for advantage in state["processing_stats"]["advantages"]:
            summary_report += f"- {advantage}\n"

        state["processing_stats"]["summary_report"] = summary_report
        state["processing_stats"]["sentiment_distribution"] = sentiment_counts

        print(f"✅ 결과 집계 완료")

    except Exception as e:
        print(f"❌ 결과 집계 오류: {e}")
        state["errors"].append(f"Aggregator: {str(e)}")

    return state

def create_conditional_workflow():
    """조건부 라우팅 워크플로우 생성"""

    workflow = StateGraph(ConditionalAgentState)

    # 노드 추가
    workflow.add_node("validator", data_validator)
    workflow.add_node("realtime_analyzer", realtime_analyzer)
    workflow.add_node("batch_analyzer", batch_analyzer)
    workflow.add_node("aggregator", results_aggregator)

    # 시작점 설정
    workflow.set_entry_point("validator")

    # 조건부 분기 (핵심!)
    workflow.add_conditional_edges(
        "validator",                    # 분기 시작 노드
        should_use_batch_processing,    # 분기 결정 함수
        {
            "realtime_analyzer": "realtime_analyzer",  # 실시간 처리 경로
            "batch_analyzer": "batch_analyzer"         # 배치 처리 경로
        }
    )

    # 두 경로 모두 집계기로 수렴
    workflow.add_edge("realtime_analyzer", "aggregator")
    workflow.add_edge("batch_analyzer", "aggregator")
    workflow.add_edge("aggregator", END)

    return workflow.compile()

if __name__ == "__main__":
    print("🚀 LangGraph Conditional Routing 실습을 시작합니다!")
    print("=" * 70)

    try:
        # 1. 워크플로우 생성
        app = create_conditional_workflow()
        print("✅ 조건부 라우팅 워크플로우 생성 완료")

        # 2. 테스트 케이스들
        test_cases = [
            {"keyword": "AI기술", "description": "소량 댓글 (실시간 처리 예상)"},
            {"keyword": "경제정책", "description": "대량 댓글 (배치 처리 예상)"}
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*20} 테스트 케이스 {i} {'='*20}")
            print(f"🎯 키워드: {test_case['keyword']}")
            print(f"📝 설명: {test_case['description']}")

            # 초기 상태
            initial_state: ConditionalAgentState = {
                "keyword": test_case["keyword"],
                "articles": [],
                "total_comments": 0,
                "processing_mode": "",
                "analysis_results": [],
                "processing_stats": {},
                "workflow_path": [],
                "decision_reasons": [],
                "errors": []
            }

            # 워크플로우 실행
            final_state = app.invoke(initial_state)

            # 결과 출력
            print(f"\n📊 실행 결과:")
            print(f"   🔀 워크플로우 경로: {' → '.join(final_state['workflow_path'])}")
            print(f"   ⚙️ 선택된 처리 방식: {final_state['processing_mode']}")
            print(f"   💬 총 댓글 수: {final_state['total_comments']}개")

            if final_state["processing_stats"]:
                stats = final_state["processing_stats"]
                print(f"   ⏱️ 처리 시간: {stats.get('total_processing_time', 0):.2f}초")
                print(f"   🚀 처리량: {stats.get('comments_per_second', 0):.1f} 댓글/초")

            # 요약 리포트 출력
            if "summary_report" in final_state.get("processing_stats", {}):
                print(final_state["processing_stats"]["summary_report"])

        print("\n✅ LangGraph Conditional Routing 실습 완료!")
        print("\n💡 핵심 개념:")
        print("   1. Conditional Edge: 조건에 따른 동적 라우팅")
        print("   2. Decision Function: 분기 결정 로직") 
        print("   3. Multi-Path Convergence: 여러 경로가 하나로 수렴")
        print("   4. Performance Optimization: 상황별 최적 처리 방식")
        print("\n📚 다음 단계:")
        print("   - 09_langchain_memory.py: 대화 메모리 관리")
        print("   - 10_integrated_demo.py: 전체 기능 통합")

    except Exception as e:
        print(f"❌ 실습 오류: {e}")
        print("\n🔧 해결 방법:")
        print("   1. OpenAI API 키 확인")
        print("   2. pip install langgraph langchain-openai")
        print("   3. 조건 함수 반환값 확인")
