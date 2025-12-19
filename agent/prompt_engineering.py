"""
3회차 실습 03: 프롬프트 엔지니어링 기초
페이지 8 - 나쁜/좋은 프롬프트 비교

이 스크립트는 프롬프트 엔지니어링의 핵심 원칙을 다룹니다.
- 나쁜 프롬프트 vs 좋은 프롬프트 비교
- 일관성 확보를 위한 체크리스트
- 실제 감성 분석 프롬프트 개선
- 출력 형식 제어 방법
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import json

# 환경 변수 로드
load_dotenv()

def setup_openai_client():
    """OpenAI 클라이언트 초기화"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 환경 변수에 설정되지 않았습니다.")

    return OpenAI(api_key=api_key)

# 나쁜 프롬프트 예제
BAD_PROMPT = "이 댓글의 감성을 분석해줘: {comment}"

# 좋은 프롬프트 예제
GOOD_PROMPT = """당신은 전문 뉴스 댓글 감성 분석가입니다.

다음 댓글의 감성을 분석하고, 반드시 JSON 형식으로 응답하세요.

댓글: {comment}

분류 기준:
- 긍정: 지지, 칭찬, 기대감, 만족감
- 부정: 비판, 분노, 실망, 우려
- 중립: 단순 사실 전달, 질문, 균형잡힌 의견

응답 형식 (JSON):
{{
  "sentiment": "긍정|부정|중립",
  "confidence": 0.0-1.0,
  "reason": "분석 근거 (한 문장)",
  "keywords": ["핵심", "키워드", "목록"]
}}

주의사항:
- 감정적 단어에 주목하세요
- 문맥을 고려하세요
- 확신이 없으면 confidence를 낮게 설정하세요"""

def test_bad_prompt(client, comment):
    """나쁜 프롬프트로 테스트"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": BAD_PROMPT.format(comment=comment)}],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"오류: {e}"

def test_good_prompt(client, comment):
    """좋은 프롬프트로 테스트"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": GOOD_PROMPT.format(comment=comment)}],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"오류: {e}"

def compare_prompts(client, test_comments):
    """프롬프트 비교 실행"""
    results = []

    for comment in test_comments:
        print(f"\n📝 테스트 댓글: \"{comment}\"")
        print("=" * 60)

        # 나쁜 프롬프트 테스트
        print("❌ 나쁜 프롬프트 결과:")
        bad_result = test_bad_prompt(client, comment)
        print(bad_result)

        # 좋은 프롬프트 테스트
        print("\n✅ 좋은 프롬프트 결과:")
        good_result = test_good_prompt(client, comment)
        print(good_result)

        results.append({
            "comment": comment,
            "bad_result": bad_result,
            "good_result": good_result
        })

        print("\n" + "-" * 60)

    return results

def analyze_json_parsing(result_text):
    """JSON 파싱 성공률 확인"""
    try:
        # JSON 추출 시도
        if '{' in result_text and '}' in result_text:
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            json_str = result_text[start:end]
            parsed = json.loads(json_str)
            return True, parsed
        else:
            return False, "JSON 형식 없음"
    except json.JSONDecodeError as e:
        return False, f"JSON 파싱 오류: {e}"

def prompt_engineering_checklist():
    """프롬프트 엔지니어링 체크리스트"""
    checklist = """
    ✅ 프롬프트 엔지니어링 체크리스트:

    1. 📋 역할 정의 (페르소나)
       ✅ "당신은 전문 감성 분석가입니다"
       ❌ 역할 없음

    2. 🎯 명확한 태스크 정의
       ✅ "다음 댓글의 감성을 분석하고"
       ❌ "분석해줘"

    3. 📏 분류 기준 제시
       ✅ 긍정/부정/중립의 구체적 기준
       ❌ 기준 없음

    4. 🔧 출력 형식 강제
       ✅ JSON 스키마 명시
       ❌ 자유 형식

    5. 📚 예시 제공 (Few-shot)
       ✅ 입력-출력 예제 1-3개
       ❌ 예시 없음

    6. 🚫 제약사항 명시
       ✅ 금지어, 주의사항
       ❌ 제약 없음

    7. 🎚️ 온도 조절
       ✅ 일관성: 0.0-0.3
       ✅ 창의성: 0.7-1.0
    """
    return checklist

def common_prompt_mistakes():
    """흔한 프롬프트 실수들"""
    mistakes = """
    ❌ 흔한 프롬프트 실수들:

    1. 모호한 지시사항
       나쁜 예: "이것을 분석해줘"
       좋은 예: "이 댓글의 감성을 긍정/부정/중립으로 분류해주세요"

    2. 형식 불일치
       나쁜 예: 매번 다른 출력 형식
       좋은 예: JSON 스키마 강제

    3. 컨텍스트 부족
       나쁜 예: 단순 텍스트만 제공
       좋은 예: 배경 설명, 목적 명시

    4. 예외 처리 부족
       나쁜 예: 확신 없는 경우 처리 안함
       좋은 예: confidence 점수, 기본값 제공

    5. 과도한 복잡성
       나쁜 예: 10개 이상의 분류, 복잡한 조건
       좋은 예: 3-5개 분류, 명확한 기준
    """
    return mistakes

if __name__ == "__main__":
    print("🚀 프롬프트 엔지니어링 기초 실습을 시작합니다!")
    print("=" * 70)

    # 테스트용 댓글들
    test_comments = [
        "정부 정책이 정말 최악이다. 완전히 실망했어요.",
        "새로운 기술이 혁신적이네요! 기대가 됩니다.",
        "오늘 날씨가 흐리고 비가 올 것 같습니다.",
        "이 제품 가격은 얼마인가요? 구매를 고려 중입니다.",
        "정말 훌륭한 서비스입니다. 강력 추천합니다!"
    ]

    try:
        # 1. OpenAI 클라이언트 초기화
        client = setup_openai_client()
        print("✅ OpenAI 클라이언트 초기화 완료")

        # 2. 프롬프트 엔지니어링 체크리스트 출력
        print("\n1️⃣ 프롬프트 엔지니어링 체크리스트")
        checklist = prompt_engineering_checklist()
        print(checklist)

        # 3. 흔한 실수들 소개
        print("\n2️⃣ 흔한 프롬프트 실수들")
        mistakes = common_prompt_mistakes()
        print(mistakes)

        # 4. 실제 비교 테스트
        print("\n3️⃣ 나쁜 프롬프트 vs 좋은 프롬프트 비교")
        print("\n🔍 프롬프트 비교:")
        print(f"❌ 나쁜 프롬프트: \"{BAD_PROMPT}\"")
        print(f"✅ 좋은 프롬프트: (구조화된 형식, {len(GOOD_PROMPT.split())}단어)")

        # 비교 실행 (첫 번째 댓글만 예시로)
        print(f"\n📊 테스트 결과 (예시):")
        test_comment = test_comments[0]
        results = compare_prompts(client, [test_comment])

        # 5. JSON 파싱 성공률 확인
        if results:
            result = results[0]
            print("\n4️⃣ JSON 파싱 성공률 비교")

            # 나쁜 프롬프트 JSON 파싱
            bad_success, bad_parsed = analyze_json_parsing(result["bad_result"])
            print(f"❌ 나쁜 프롬프트 JSON 파싱: {'성공' if bad_success else '실패'}")
            if not bad_success:
                print(f"   사유: {bad_parsed}")

            # 좋은 프롬프트 JSON 파싱
            good_success, good_parsed = analyze_json_parsing(result["good_result"])
            print(f"✅ 좋은 프롬프트 JSON 파싱: {'성공' if good_success else '실패'}")
            if good_success:
                print(f"   파싱된 데이터: {good_parsed}")

        print("\n✅ 프롬프트 엔지니어링 실습 완료!")
        print("\n💡 핵심 교훈:")
        print("   1. 명확한 역할과 지시사항 제공")
        print("   2. 출력 형식을 JSON으로 강제")
        print("   3. 분류 기준을 구체적으로 명시")
        print("   4. 온도 설정으로 일관성 확보")
        print("\n📚 다음 단계:")
        print("   - 04_structured_output.py: Pydantic 기반 Type-safe 출력")
        print("   - 05_function_calling.py: Function Calling 패턴")

    except Exception as e:
        print(f"❌ 실습 오류: {e}")
        print("\n🔧 해결 방법:")
        print("   1. API 키 설정 확인")
        print("   2. 네트워크 연결 확인")
        print("   3. API 크레딧 잔액 확인")
