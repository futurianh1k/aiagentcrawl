"""
3회차 실습 05: Function Calling 패턴
페이지 11 - Tool 정의 및 자동 호출

이 스크립트는 OpenAI Function Calling 기능을 다룹니다.
- Tool 정의 및 스키마 작성
- LLM이 적절한 Tool 자동 선택
- 복잡한 워크플로우의 자동화
- 다중 Tool 체인 실행
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any

# 환경 변수 로드
load_dotenv()

def setup_openai_client():
    """OpenAI 클라이언트 초기화"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 환경 변수에 설정되지 않았습니다.")

    return OpenAI(api_key=api_key)

# Tool 함수들 정의
def analyze_sentiment(comment: str, language: str = "ko") -> Dict[str, Any]:
    """감성 분석 Tool 함수"""
    # 실제로는 더 복잡한 분석 로직이 들어감
    positive_words = ["좋다", "훌륭하다", "최고", "추천", "만족", "기대"]
    negative_words = ["최악", "실망", "화나다", "짜증", "문제", "불만"]

    sentiment = "중립"
    confidence = 0.5
    keywords = []

    comment_lower = comment.lower()

    pos_count = sum(1 for word in positive_words if word in comment_lower)
    neg_count = sum(1 for word in negative_words if word in comment_lower)

    if pos_count > neg_count:
        sentiment = "긍정"
        confidence = min(0.9, 0.6 + pos_count * 0.1)
        keywords = [word for word in positive_words if word in comment_lower]
    elif neg_count > pos_count:
        sentiment = "부정"  
        confidence = min(0.9, 0.6 + neg_count * 0.1)
        keywords = [word for word in negative_words if word in comment_lower]

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "keywords": keywords[:3],  # 최대 3개만
        "method": "keyword_based_analysis"
    }

def search_news(keyword: str, max_results: int = 5) -> Dict[str, Any]:
    """뉴스 검색 Tool 함수 (모의)"""
    # 실제로는 뉴스 API 호출
    mock_articles = [
        {"title": f"{keyword} 관련 최신 뉴스 1", "url": "https://news1.com", "summary": "긍정적 전망"},
        {"title": f"{keyword} 시장 동향 분석", "url": "https://news2.com", "summary": "중립적 분석"},
        {"title": f"{keyword} 논란 확산", "url": "https://news3.com", "summary": "부정적 의견"},
    ]

    return {
        "keyword": keyword,
        "articles": mock_articles[:max_results],
        "total_found": len(mock_articles),
        "search_timestamp": "2024-12-18T10:00:00Z"
    }

def summarize_sentiment_trends(analysis_results: list) -> Dict[str, Any]:
    """감성 분석 결과 요약 Tool 함수"""
    if not analysis_results:
        return {"error": "분석 결과가 없습니다"}

    sentiments = [result.get("sentiment", "중립") for result in analysis_results]
    confidences = [result.get("confidence", 0.5) for result in analysis_results]

    sentiment_counts = {}
    for sentiment in sentiments:
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

    total = len(sentiments)
    sentiment_percentages = {k: (v/total)*100 for k, v in sentiment_counts.items()}

    avg_confidence = sum(confidences) / len(confidences)

    # 전체적인 경향 판단
    if sentiment_percentages.get("긍정", 0) > 50:
        overall_trend = "긍정적"
    elif sentiment_percentages.get("부정", 0) > 50:
        overall_trend = "부정적"
    else:
        overall_trend = "중립적"

    return {
        "total_analyzed": total,
        "sentiment_distribution": sentiment_percentages,
        "average_confidence": avg_confidence,
        "overall_trend": overall_trend,
        "recommendation": f"전반적으로 {overall_trend} 반응을 보이고 있습니다."
    }

# Function Calling용 Tool 스키마 정의
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_sentiment",
            "description": "주어진 댓글이나 텍스트의 감성을 분석합니다",
            "parameters": {
                "type": "object",
                "properties": {
                    "comment": {
                        "type": "string",
                        "description": "분석할 댓글이나 텍스트"
                    },
                    "language": {
                        "type": "string", 
                        "enum": ["ko", "en"],
                        "description": "텍스트 언어 (기본값: ko)",
                        "default": "ko"
                    }
                },
                "required": ["comment"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_news",
            "description": "특정 키워드로 뉴스 기사를 검색합니다",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "검색할 키워드"
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "최대 검색 결과 수 (기본값: 5)",
                        "default": 5
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "summarize_sentiment_trends",
            "description": "여러 감성 분석 결과를 종합하여 전체적인 경향을 요약합니다",
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_results": {
                        "type": "array",
                        "items": {
                            "type": "object"
                        },
                        "description": "감성 분석 결과들의 배열"
                    }
                },
                "required": ["analysis_results"]
            }
        }
    }
]

# Tool 함수 매핑
AVAILABLE_FUNCTIONS = {
    "analyze_sentiment": analyze_sentiment,
    "search_news": search_news, 
    "summarize_sentiment_trends": summarize_sentiment_trends
}

def execute_function_call(function_name: str, arguments: str) -> Any:
    """Function Call 실행"""
    try:
        # JSON 파싱
        args = json.loads(arguments)

        # 함수 실행
        if function_name in AVAILABLE_FUNCTIONS:
            function = AVAILABLE_FUNCTIONS[function_name]
            result = function(**args)
            print(f"🔧 {function_name} 실행 완료")
            return result
        else:
            return {"error": f"Unknown function: {function_name}"}

    except json.JSONDecodeError as e:
        return {"error": f"JSON parsing error: {e}"}
    except Exception as e:
        return {"error": f"Function execution error: {e}"}

def chat_with_function_calling(client, user_message, max_iterations=3):
    """Function Calling을 활용한 대화"""
    messages = [
        {"role": "system", "content": """당신은 뉴스 감성 분석 전문 AI입니다. 
        사용자의 요청을 분석하여 적절한 도구를 사용해 답변하세요.

        사용 가능한 도구:
        1. analyze_sentiment: 댓글/텍스트 감성 분석
        2. search_news: 키워드로 뉴스 검색
        3. summarize_sentiment_trends: 감성 분석 결과 종합

        복잡한 요청의 경우 여러 도구를 순차적으로 사용할 수 있습니다."""},
        {"role": "user", "content": user_message}
    ]

    print(f"👤 사용자: {user_message}")
    print("=" * 60)

    for iteration in range(max_iterations):
        print(f"\n🔄 반복 {iteration + 1}")

        # OpenAI API 호출 (Function Calling 포함)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",  # 자동으로 적절한 도구 선택
            temperature=0.3
        )

        response_message = response.choices[0].message

        # Tool 호출이 있는지 확인
        if response_message.tool_calls:
            print(f"🛠️  LLM이 {len(response_message.tool_calls)}개 도구 사용 결정")

            # 메시지 기록에 추가
            messages.append(response_message)

            # 각 Tool 호출 실행
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments

                print(f"   📞 호출: {function_name}({function_args})")

                # 함수 실행
                function_result = execute_function_call(function_name, function_args)

                # 결과를 메시지에 추가
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_result, ensure_ascii=False)
                })

                print(f"   ✅ 결과: {function_result}")
        else:
            # Tool 호출이 없으면 최종 답변
            print(f"🤖 최종 답변:")
            print(response_message.content)
            break

    return messages

def demonstrate_single_tool_call(client):
    """단일 Tool 호출 예제"""
    print("\n1️⃣ 단일 Tool 호출 예제")
    print("-" * 40)

    user_query = "'이 정책은 정말 훌륭합니다!' 이 댓글의 감성을 분석해주세요."
    chat_with_function_calling(client, user_query)

def demonstrate_multi_tool_workflow(client):
    """다중 Tool 워크플로우 예제"""
    print("\n2️⃣ 다중 Tool 워크플로우 예제")
    print("-" * 40)

    user_query = """삼성전자에 대한 뉴스를 검색하고, 다음 댓글들도 분석해주세요:
    1. '삼성전자 주가가 오르네요! 좋은 소식입니다.'
    2. '또 다른 문제가 터졌나요? 실망이에요.'
    그리고 전체적인 감성 동향을 요약해주세요."""

    chat_with_function_calling(client, user_query)

def demonstrate_tool_schema_validation():
    """Tool 스키마 검증 시연"""
    print("\n3️⃣ Tool 스키마 및 파라미터 검증")
    print("-" * 40)

    print("📋 정의된 Tools:")
    for i, tool in enumerate(TOOLS, 1):
        func_info = tool["function"]
        print(f"   {i}. {func_info['name']}")
        print(f"      설명: {func_info['description']}")
        print(f"      필수 파라미터: {func_info['parameters'].get('required', [])}")

    print("\n🔧 파라미터 검증 예제:")

    # 올바른 호출
    try:
        result = analyze_sentiment("테스트 댓글입니다")
        print(f"✅ 올바른 호출 성공: {result['sentiment']}")
    except Exception as e:
        print(f"❌ 올바른 호출 실패: {e}")

    # 잘못된 호출 (필수 파라미터 누락)
    try:
        result = analyze_sentiment()  # comment 파라미터 누락
        print(f"이 줄은 실행되면 안됩니다: {result}")
    except Exception as e:
        print(f"✅ 잘못된 호출 정상 감지: {type(e).__name__}")

if __name__ == "__main__":
    print("🚀 Function Calling 패턴 실습을 시작합니다!")
    print("=" * 70)

    try:
        # 1. OpenAI 클라이언트 초기화
        client = setup_openai_client()
        print("✅ OpenAI 클라이언트 초기화 완료")

        # 2. Tool 스키마 검증 시연
        demonstrate_tool_schema_validation()

        # 3. 단일 Tool 호출 예제
        demonstrate_single_tool_call(client)

        # 4. 다중 Tool 워크플로우 예제  
        demonstrate_multi_tool_workflow(client)

        print("\n✅ Function Calling 실습 완료!")
        print("\n💡 핵심 개념:")
        print("   1. LLM이 상황에 맞는 Tool을 자동 선택")
        print("   2. JSON 스키마로 파라미터 검증")
        print("   3. 복잡한 워크플로우의 자동 체이닝")
        print("   4. tool_choice로 호출 방식 제어")
        print("\n📚 다음 단계:")
        print("   - 06_data_analyzer_tool.py: 프로덕션급 감성 분석 Tool")
        print("   - 07_langgraph_sequential.py: Multi-Agent 워크플로우")

    except Exception as e:
        print(f"❌ 실습 오류: {e}")
        print("\n🔧 해결 방법:")
        print("   1. OpenAI API 키 확인")
        print("   2. Function Calling 지원 모델 사용 (gpt-4, gpt-3.5-turbo)")
        print("   3. API 크레딧 잔액 확인")
