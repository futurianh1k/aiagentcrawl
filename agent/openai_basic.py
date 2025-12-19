"""
3회차 실습 01: OpenAI API 기초
페이지 6 - Chat Completions API 사용법

이 스크립트는 OpenAI Chat Completions API의 기본 사용법을 다룹니다.
- API 키 설정
- 기본 Chat Completions 호출
- 모델 선택 (GPT-4 vs GPT-3.5-turbo)
- 온도, 맥스 토큰 등 파라미터 조정
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def setup_openai_client():
    """OpenAI 클라이언트 초기화"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 환경 변수에 설정되지 않았습니다. .env 파일을 확인하세요.")

    client = OpenAI(api_key=api_key)
    print("✅ OpenAI 클라이언트 초기화 완료")
    return client

def basic_chat_completion(client, user_message, model="gpt-4"):
    """기본 Chat Completions API 호출"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,  # 창의성 조절 (0.0-2.0)
            max_tokens=1000,  # 최대 토큰 수
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ API 호출 오류: {e}")
        return None

def sentiment_analysis_example(client):
    """감성 분석 예제"""
    comment = "이 정책은 정말 최악이에요. 완전히 실망했습니다."

    system_prompt = """당신은 전문 감성 분석가입니다. 
    주어진 텍스트의 감성을 '긍정', '부정', '중립' 중 하나로 분류하고 
    그 이유를 간략히 설명해주세요."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"다음 댓글을 분석해주세요: {comment}"}
            ],
            temperature=0.3,  # 일관성을 위해 낮은 온도
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ 감성 분석 오류: {e}")
        return None

def compare_models(client, prompt):
    """GPT-4와 GPT-3.5-turbo 비교"""
    models = ["gpt-4", "gpt-3.5-turbo"]
    results = {}

    for model in models:
        print(f"\n🔄 {model} 응답 생성 중...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )

            results[model] = response.choices[0].message.content

            # 토큰 사용량 표시 (가능한 경우)
            if hasattr(response, 'usage'):
                usage = response.usage
                print(f"  📊 토큰 사용량: {usage.prompt_tokens} + {usage.completion_tokens} = {usage.total_tokens}")

        except Exception as e:
            results[model] = f"오류: {e}"

    return results

if __name__ == "__main__":
    print("🚀 OpenAI API 기초 실습을 시작합니다!")
    print("=" * 50)

    try:
        # 1. OpenAI 클라이언트 초기화
        client = setup_openai_client()

        # 2. 기본 채팅 예제
        print("\n1️⃣ 기본 채팅 예제")
        print("-" * 30)
        user_input = "AI 에이전트란 무엇인가요?"
        response = basic_chat_completion(client, user_input)
        if response:
            print(f"👤 사용자: {user_input}")
            print(f"🤖 GPT-4: {response}")

        # 3. 감성 분석 예제
        print("\n2️⃣ 감성 분석 예제")
        print("-" * 30)
        sentiment_result = sentiment_analysis_example(client)
        if sentiment_result:
            print(f"📊 분석 결과:\n{sentiment_result}")

        # 4. 모델 비교 예제
        print("\n3️⃣ GPT-4 vs GPT-3.5-turbo 비교")
        print("-" * 30)
        comparison_prompt = "Multi-Agent 시스템의 장점을 3가지로 요약해주세요."
        comparison_results = compare_models(client, comparison_prompt)

        for model, result in comparison_results.items():
            print(f"\n🔹 {model.upper()}:")
            print(result)

        print("\n✅ 실습 완료!")
        print("\n💡 다음 단계:")
        print("   - 02_gemini_basic.py: Google Gemini API 실습")
        print("   - 03_prompt_engineering.py: 프롬프트 엔지니어링")

    except Exception as e:
        print(f"❌ 전체 실습 오류: {e}")
        print("\n🔧 해결 방법:")
        print("   1. .env 파일에 OPENAI_API_KEY 설정 확인")
        print("   2. pip install openai python-dotenv")
        print("   3. API 키 유효성 및 크레딧 잔액 확인")
