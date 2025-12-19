"""
3회차 실습 02: Google Gemini API 기초
페이지 7 - Gemini Pro 사용법

이 스크립트는 Google Gemini API의 기본 사용법을 다룹니다.
- Gemini API 키 설정
- Gemini Pro 모델 사용
- OpenAI API와의 비교
- 멀티모달 기능 소개
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def setup_gemini_client():
    """Gemini API 클라이언트 초기화"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 환경 변수에 설정되지 않았습니다. .env 파일을 확인하세요.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    print("✅ Gemini Pro 클라이언트 초기화 완료")
    return model

def basic_gemini_generation(model, prompt):
    """기본 Gemini 텍스트 생성"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ Gemini API 호출 오류: {e}")
        return None

def gemini_sentiment_analysis(model, comment):
    """Gemini를 이용한 감성 분석"""
    prompt = f"""당신은 전문 뉴스 댓글 감성 분석가입니다.

    다음 댓글의 감성을 분석하고 JSON 형식으로 응답해주세요:
    댓글: "{comment}"

    응답 형식:
    {{
        "sentiment": "긍정|부정|중립",
        "confidence": 0.0-1.0,
        "reason": "분석 근거"
    }}"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ Gemini 감성 분석 오류: {e}")
        return None

def compare_gemini_features():
    """Gemini의 특징 설명"""
    features = {
        "장점": [
            "🌍 멀티모달 지원 (텍스트, 이미지, 오디오, 비디오)",
            "📄 긴 컨텍스트 윈도우 (32K tokens, 일부 모델은 1M+ tokens)",
            "💰 경쟁력 있는 가격 (OpenAI 대비 저렴)",
            "⚡ 빠른 응답 속도",
            "🔒 Google의 안전성 필터링"
        ],
        "OpenAI vs Gemini": {
            "OpenAI GPT-4": {
                "장점": "성숙한 생태계, 프롬프트 엔지니어링 자료 풍부",
                "단점": "높은 비용, 컨텍스트 제한"
            },
            "Google Gemini": {
                "장점": "멀티모달, 긴 컨텍스트, 저렴한 비용",
                "단점": "상대적으로 새로운 플랫폼, 적은 자료"
            }
        }
    }
    return features

def multi_modal_example_info():
    """멀티모달 기능 예제 정보 (실제 이미지 없이 설명만)"""
    info = """
    🖼️ Gemini 멀티모달 기능 예제 (참고용):

    # 이미지 분석 예제 (실제 이미지가 있을 때)
    import PIL.Image

    # 이미지 로드
    img = PIL.Image.open('screenshot.jpg')

    # 이미지와 텍스트를 함께 분석
    response = model.generate_content([
        "이 스크린샷에서 UI 요소들을 분석하고 개선점을 제안해주세요.",
        img
    ])

    print(response.text)

    🎯 활용 사례:
    - 뉴스 기사 이미지의 텍스트 추출
    - 차트/그래프 데이터 분석
    - UI/UX 스크린샷 분석
    - 문서 이미지에서 정보 추출
    """
    return info

def gemini_prompt_engineering_tips():
    """Gemini 프롬프트 엔지니어링 팁"""
    tips = """
    💡 Gemini 프롬프트 엔지니어링 팁:

    1. 명확한 지시사항:
       - "JSON 형식으로 응답해주세요" ✅
       - "결과를 알려주세요" ❌

    2. 예시 제공:
       - Few-shot 프롬프트 효과적
       - 원하는 출력 형식 명시

    3. 컨텍스트 활용:
       - 긴 문서 처리에 강점
       - 전체 맥락을 고려한 분석 가능

    4. 안전 필터링:
       - Google의 엄격한 안전 정책
       - 민감한 내용 필터링됨
    """
    return tips

if __name__ == "__main__":
    print("🚀 Google Gemini API 기초 실습을 시작합니다!")
    print("=" * 60)

    try:
        # 1. Gemini 클라이언트 초기화
        model = setup_gemini_client()

        # 2. 기본 텍스트 생성 예제
        print("\n1️⃣ 기본 텍스트 생성 예제")
        print("-" * 40)
        basic_prompt = "AI 에이전트의 정의와 주요 구성 요소를 간단히 설명해주세요."
        basic_response = basic_gemini_generation(model, basic_prompt)
        if basic_response:
            print(f"📝 질문: {basic_prompt}")
            print(f"🤖 Gemini: {basic_response}")

        # 3. 감성 분석 예제
        print("\n2️⃣ Gemini 감성 분석 예제")
        print("-" * 40)
        test_comment = "새로운 AI 기술이 정말 혁신적이네요! 앞으로가 기대됩니다."
        sentiment_result = gemini_sentiment_analysis(model, test_comment)
        if sentiment_result:
            print(f"💬 댓글: {test_comment}")
            print(f"📊 분석 결과:\n{sentiment_result}")

        # 4. Gemini 특징 비교
        print("\n3️⃣ Gemini vs OpenAI 특징 비교")
        print("-" * 40)
        features = compare_gemini_features()

        print("🔥 Gemini의 주요 장점:")
        for advantage in features["장점"]:
            print(f"   {advantage}")

        print("\n⚖️ 플랫폼 비교:")
        for platform, details in features["OpenAI vs Gemini"].items():
            print(f"\n📱 {platform}:")
            for key, value in details.items():
                print(f"   {key}: {value}")

        # 5. 멀티모달 기능 소개
        print("\n4️⃣ 멀티모달 기능 소개")
        print("-" * 40)
        multimodal_info = multi_modal_example_info()
        print(multimodal_info)

        # 6. 프롬프트 엔지니어링 팁
        print("\n5️⃣ 프롬프트 엔지니어링 팁")
        print("-" * 40)
        tips = gemini_prompt_engineering_tips()
        print(tips)

        print("\n✅ Gemini API 실습 완료!")
        print("\n💡 다음 단계:")
        print("   - 03_prompt_engineering.py: 프롬프트 엔지니어링 심화")
        print("   - OpenAI와 Gemini 결과 비교해보기")

    except Exception as e:
        print(f"❌ 전체 실습 오류: {e}")
        print("\n🔧 해결 방법:")
        print("   1. .env 파일에 GEMINI_API_KEY 설정 확인")
        print("   2. pip install google-generativeai")
        print("   3. Google AI Studio에서 API 키 발급")
        print("   4. https://makersuite.google.com/app/apikey")
