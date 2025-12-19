"""
3회차 실습 04: Pydantic 기반 구조화된 출력
페이지 10 - Structured Output (OpenAI)

이 스크립트는 OpenAI의 Structured Output 기능을 다룹니다.
- Pydantic 모델을 이용한 Type-safe 출력
- 자동 검증 및 변환
- 파싱 실패 최소화
- 프로덕션급 안정성 확보
"""

import os
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from dotenv import load_dotenv
import json

# 환경 변수 로드
load_dotenv()

class SentimentAnalysis(BaseModel):
    """감성 분석 결과 모델"""
    sentiment: Literal["긍정", "부정", "중립"] = Field(
        description="댓글의 감성 분류"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="분류 신뢰도 (0.0-1.0)"
    )
    reason: str = Field(
        min_length=5, max_length=200,
        description="감성 분류 근거"
    )
    keywords: List[str] = Field(
        description="감성을 나타내는 핵심 키워드",
        max_items=5
    )
    is_sarcasm: Optional[bool] = Field(
        default=None,
        description="반어법/비꼬는 표현 여부"
    )

class BatchSentimentAnalysis(BaseModel):
    """배치 감성 분석 결과 모델"""
    total_comments: int = Field(description="전체 댓글 수")
    results: List[SentimentAnalysis] = Field(description="개별 분석 결과")
    summary: dict = Field(description="요약 통계")

def setup_openai_client():
    """OpenAI 클라이언트 초기화"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 환경 변수에 설정되지 않았습니다.")

    return OpenAI(api_key=api_key)

def analyze_with_structured_output(client, comment):
    """Structured Output을 사용한 감성 분석"""
    system_prompt = """당신은 전문 뉴스 댓글 감성 분석가입니다.
    주어진 댓글을 분석하여 감성, 신뢰도, 근거, 핵심 키워드를 제공하세요.

    분류 기준:
    - 긍정: 지지, 칭찬, 기대감, 만족
    - 부정: 비판, 분노, 실망, 우려  
    - 중립: 사실 전달, 질문, 균형 의견

    반어법이나 비꼬는 표현도 감지해주세요."""

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",  # Structured Output 지원 모델
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"다음 댓글을 분석하세요: {comment}"}
            ],
            response_format=SentimentAnalysis,
            temperature=0.3
        )

        return response.choices[0].message.parsed

    except Exception as e:
        print(f"❌ Structured Output 오류: {e}")
        return None

def compare_traditional_vs_structured(client, comment):
    """전통적 방식 vs Structured Output 비교"""

    # 1. 전통적 JSON 방식
    traditional_prompt = f"""댓글의 감성을 분석하고 JSON으로 응답하세요.
    댓글: {comment}

    JSON 형식:
    {{
        "sentiment": "긍정|부정|중립",
        "confidence": 0.0-1.0,
        "reason": "분석 근거"
    }}"""

    print("1️⃣ 전통적 JSON 방식")
    try:
        traditional_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": traditional_prompt}],
            temperature=0.3
        )
        traditional_text = traditional_response.choices[0].message.content
        print(f"📄 원본 응답: {traditional_text}")

        # JSON 파싱 시도
        try:
            if '{' in traditional_text:
                start = traditional_text.find('{')
                end = traditional_text.rfind('}') + 1
                json_str = traditional_text[start:end]
                traditional_parsed = json.loads(json_str)
                print(f"✅ 파싱 성공: {traditional_parsed}")
            else:
                print("❌ JSON 형식 없음")
                traditional_parsed = None
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            traditional_parsed = None

    except Exception as e:
        print(f"❌ 전통적 방식 오류: {e}")
        traditional_parsed = None

    print("\n" + "-" * 50)

    # 2. Structured Output 방식
    print("2️⃣ Structured Output 방식")
    structured_result = analyze_with_structured_output(client, comment)

    if structured_result:
        print(f"✅ Type-safe 결과:")
        print(f"   감성: {structured_result.sentiment}")
        print(f"   신뢰도: {structured_result.confidence:.2f}")
        print(f"   근거: {structured_result.reason}")
        print(f"   키워드: {structured_result.keywords}")
        print(f"   반어법: {structured_result.is_sarcasm}")

        # Pydantic 모델의 장점 시연
        print(f"\n🔧 Type-safe 접근:")
        print(f"   structured_result.sentiment: {structured_result.sentiment}")
        print(f"   type(structured_result.confidence): {type(structured_result.confidence)}")

    return traditional_parsed, structured_result

def batch_analysis_example(client, comments):
    """배치 분석 예제"""
    print("🔄 배치 감성 분석 실행 중...")

    results = []
    for i, comment in enumerate(comments, 1):
        print(f"   {i}/{len(comments)} 처리 중...")
        result = analyze_with_structured_output(client, comment)
        if result:
            results.append(result)

    # 요약 통계 계산
    if results:
        sentiment_counts = {}
        total_confidence = 0

        for result in results:
            sentiment = result.sentiment
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            total_confidence += result.confidence

        summary = {
            "sentiment_distribution": sentiment_counts,
            "average_confidence": total_confidence / len(results),
            "total_analyzed": len(results)
        }

        # BatchSentimentAnalysis 모델로 래핑
        batch_result = BatchSentimentAnalysis(
            total_comments=len(comments),
            results=results,
            summary=summary
        )

        return batch_result

    return None

def demonstrate_validation():
    """Pydantic 검증 기능 시연"""
    print("🔍 Pydantic 데이터 검증 시연")

    # 1. 올바른 데이터
    try:
        valid_data = SentimentAnalysis(
            sentiment="긍정",
            confidence=0.85,
            reason="긍정적인 표현이 많이 사용됨",
            keywords=["좋다", "훌륭하다"],
            is_sarcasm=False
        )
        print(f"✅ 유효한 데이터: {valid_data.sentiment}")
    except Exception as e:
        print(f"❌ 유효한 데이터 오류: {e}")

    # 2. 잘못된 데이터 (범위 초과)
    try:
        invalid_data = SentimentAnalysis(
            sentiment="긍정",
            confidence=1.5,  # 범위 초과
            reason="짧음",     # 너무 짧음
            keywords=["키워드1", "키워드2", "키워드3", "키워드4", "키워드5", "키워드6"]  # 너무 많음
        )
        print(f"이 줄은 실행되면 안됩니다: {invalid_data}")
    except Exception as e:
        print(f"✅ 검증 오류 정상 감지: {type(e).__name__}")

    # 3. 잘못된 감성 값
    try:
        invalid_sentiment = SentimentAnalysis(
            sentiment="매우좋음",  # Literal 타입에 없는 값
            confidence=0.8,
            reason="적절한 길이의 근거입니다",
            keywords=["키워드"]
        )
        print(f"이 줄은 실행되면 안됩니다: {invalid_sentiment}")
    except Exception as e:
        print(f"✅ Literal 타입 오류 정상 감지: {type(e).__name__}")

if __name__ == "__main__":
    print("🚀 Pydantic 기반 구조화된 출력 실습을 시작합니다!")
    print("=" * 70)

    # 테스트용 댓글들
    test_comments = [
        "정말 훌륭한 정책입니다! 적극 지지합니다.",
        "이건 정말 최악의 결정이네요. 실망입니다.",
        "내일 회의 시간이 언제인가요?"
    ]

    try:
        # 1. OpenAI 클라이언트 초기화
        client = setup_openai_client()
        print("✅ OpenAI 클라이언트 초기화 완료")

        # 2. Pydantic 검증 시연
        print("\n1️⃣ Pydantic 데이터 검증 시연")
        print("-" * 40)
        demonstrate_validation()

        # 3. 전통적 방식 vs Structured Output 비교
        print("\n2️⃣ 전통적 방식 vs Structured Output 비교")
        print("-" * 50)
        test_comment = test_comments[0]
        print(f"📝 테스트 댓글: \"{test_comment}\"")
        print()

        traditional, structured = compare_traditional_vs_structured(client, test_comment)

        # 4. 배치 분석 예제
        print("\n3️⃣ 배치 감성 분석")
        print("-" * 40)
        batch_result = batch_analysis_example(client, test_comments)

        if batch_result:
            print(f"\n📊 배치 분석 결과:")
            print(f"   전체 댓글: {batch_result.total_comments}개")
            print(f"   분석 완료: {batch_result.summary['total_analyzed']}개")
            print(f"   평균 신뢰도: {batch_result.summary['average_confidence']:.3f}")
            print(f"   감성 분포: {batch_result.summary['sentiment_distribution']}")

        print("\n✅ Structured Output 실습 완료!")
        print("\n💡 핵심 장점:")
        print("   1. Type-safe: 런타임 오류 방지")
        print("   2. 자동 검증: 데이터 무결성 보장")
        print("   3. IDE 지원: 자동완성, 타입 체크")
        print("   4. 파싱 실패 제거: JSON 오류 없음")
        print("\n📚 다음 단계:")
        print("   - 05_function_calling.py: Function Calling으로 Tool 자동 선택")
        print("   - 06_data_analyzer_tool.py: 프로덕션급 감성 분석 Tool")

    except Exception as e:
        print(f"❌ 실습 오류: {e}")
        print("\n🔧 해결 방법:")
        print("   1. OpenAI API 키 확인")
        print("   2. gpt-4o-2024-08-06 모델 액세스 확인")
        print("   3. pip install pydantic")
