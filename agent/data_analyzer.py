"""
AI 에이전트 기반 뉴스 감성 분석 시스템 - 실습 3
==================================================
주제: DataAnalyzer Tool 구현 - OpenAI/Gemini 감성 분석

목표:
- OpenAI GPT 또는 Google Gemini를 이용한 감성 분석 구현
- 프롬프트 엔지니어링을 통한 일관된 JSON 응답 확보
- 댓글 단위 및 기사 단위 분석 기능 구현
- Tool로 패키징하여 Agent에서 사용 가능하도록 구현

필수 라이브러리:
pip install openai google-generativeai langchain python-dotenv
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import openai
import google.generativeai as genai
from langchain.tools import tool
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class SentimentType(Enum):
    """감성 유형 열거형"""
    POSITIVE = "긍정"
    NEGATIVE = "부정" 
    NEUTRAL = "중립"

@dataclass
class SentimentResult:
    """감성 분석 결과 데이터 클래스"""
    text: str
    sentiment: SentimentType
    confidence: float
    reason: str
    keywords: List[str]
    timestamp: Optional[str] = None

@dataclass  
class TrendAnalysis:
    """동향 분석 결과 데이터 클래스"""
    keyword: str
    overall_sentiment: SentimentType
    sentiment_distribution: Dict[str, float]
    key_topics: List[str]
    summary: str
    total_comments: int

class DataAnalyzerTool:
    """데이터 분석 Tool 클래스"""

    def __init__(self, use_openai: bool = True):
        """초기화

        Args:
            use_openai (bool): True이면 OpenAI 사용, False이면 Gemini 사용
        """
        self.use_openai = use_openai

        # API 키 설정
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if use_openai:
            if not self.openai_api_key:
                print("⚠️  경고: OPENAI_API_KEY가 설정되지 않았습니다.")
                self.openai_api_key = "sk-test-key"
            openai.api_key = self.openai_api_key
        else:
            if not self.gemini_api_key:
                print("⚠️  경고: GEMINI_API_KEY가 설정되지 않았습니다.")
                self.gemini_api_key = "test-key"
            genai.configure(api_key=self.gemini_api_key)

    def create_sentiment_prompt(self, text: str) -> str:
        """감성 분석용 프롬프트 생성"""
        return f"""당신은 전문 뉴스 댓글 감성 분석가입니다.

다음 댓글을 분석하고, 반드시 아래 JSON 형식으로만 응답하세요.

댓글: "{text}"

응답 형식 (다른 텍스트는 절대 포함하지 마세요):
{{
    "sentiment": "긍정|부정|중립",
    "confidence": 0.0-1.0 사이의 숫자,
    "reason": "감성 판단 근거를 한국어로 간단히 설명",
    "keywords": ["핵심", "키워드", "목록"]
}}

분석 기준:
- 긍정: 지지, 찬성, 호의적, 기대, 감사 등의 표현
- 부정: 반대, 비판, 우려, 실망, 분노 등의 표현  
- 중립: 객관적 사실, 질문, 애매한 표현

JSON 형식을 엄격히 지켜주세요."""

    def create_trend_prompt(self, comments: List[Dict], keyword: str) -> str:
        """동향 분석용 프롬프트 생성"""
        comments_text = "\n".join([f"- {c.get('text', '')}" for c in comments[:20]])  # 최대 20개

        return f"""당신은 전문 여론 동향 분석가입니다.

키워드: "{keyword}"에 대한 댓글들을 분석하여 전체적인 여론 동향을 파악하세요.

댓글들:
{comments_text}

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "overall_sentiment": "긍정|부정|중립",
    "sentiment_distribution": {{
        "긍정": 0.0-1.0,
        "부정": 0.0-1.0, 
        "중립": 0.0-1.0
    }},
    "key_topics": ["주요", "이슈", "목록"],
    "summary": "동향 요약을 2-3문장으로 설명"
}}

분석 기준:
- 전체 댓글의 감성 비율을 정확히 계산
- 합계가 1.0이 되도록 비율 조정
- 핵심 이슈나 관심사를 키워드로 추출
- 객관적이고 균형잡힌 요약 작성

JSON 형식을 엄격히 지켜주세요."""

    def call_openai_api(self, prompt: str, max_tokens: int = 500) -> str:
        """OpenAI API 호출"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 정확한 JSON 형식으로만 응답하는 감성 분석 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3,
                timeout=30
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"❌ OpenAI API 오류: {str(e)}")
            # 더미 응답 반환
            if "sentiment" in prompt:
                return '{"sentiment": "중립", "confidence": 0.5, "reason": "API 오류로 인한 기본 응답", "keywords": ["분석불가"]}'
            else:
                return '{"overall_sentiment": "중립", "sentiment_distribution": {"긍정": 0.33, "부정": 0.33, "중립": 0.34}, "key_topics": ["분석불가"], "summary": "API 오류로 분석할 수 없습니다."}'

    def call_gemini_api(self, prompt: str) -> str:
        """Google Gemini API 호출"""
        try:
            model = genai.GenerativeModel('gemini-pro')

            generation_config = genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=500,
                top_p=0.8
            )

            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )

            return response.text.strip()

        except Exception as e:
            print(f"❌ Gemini API 오류: {str(e)}")
            # 더미 응답 반환
            if "sentiment" in prompt:
                return '{"sentiment": "중립", "confidence": 0.5, "reason": "API 오류로 인한 기본 응답", "keywords": ["분석불가"]}'
            else:
                return '{"overall_sentiment": "중립", "sentiment_distribution": {"긍정": 0.33, "부정": 0.33, "중립": 0.34}, "key_topics": ["분석불가"], "summary": "API 오류로 분석할 수 없습니다."}'

    def parse_json_response(self, response: str, response_type: str = "sentiment") -> Dict[str, Any]:
        """JSON 응답 파싱 및 검증"""
        try:
            # JSON 부분만 추출 (markdown 코드 블록 제거)
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_text = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_text = response[json_start:json_end]
            else:
                raise ValueError("JSON 형식을 찾을 수 없습니다")

            parsed = json.loads(json_text)

            # 감성 분석 응답 검증
            if response_type == "sentiment":
                required_keys = ["sentiment", "confidence", "reason", "keywords"]
                for key in required_keys:
                    if key not in parsed:
                        raise ValueError(f"필수 키 '{key}'가 없습니다")

                # 감성 값 정규화
                if parsed["sentiment"] not in ["긍정", "부정", "중립"]:
                    parsed["sentiment"] = "중립"

                # 신뢰도 값 검증
                if not (0 <= parsed["confidence"] <= 1):
                    parsed["confidence"] = 0.5

            # 동향 분석 응답 검증
            elif response_type == "trend":
                required_keys = ["overall_sentiment", "sentiment_distribution", "key_topics", "summary"]
                for key in required_keys:
                    if key not in parsed:
                        raise ValueError(f"필수 키 '{key}'가 없습니다")

                # 비율 정규화
                dist = parsed["sentiment_distribution"]
                total = sum(dist.values())
                if total > 0:
                    for key in dist:
                        dist[key] = dist[key] / total
                else:
                    parsed["sentiment_distribution"] = {"긍정": 0.33, "부정": 0.33, "중립": 0.34}

            return parsed

        except Exception as e:
            print(f"❌ JSON 파싱 오류: {str(e)}")
            print(f"원본 응답: {response}")

            # 기본값 반환
            if response_type == "sentiment":
                return {
                    "sentiment": "중립",
                    "confidence": 0.5,
                    "reason": "파싱 오류로 인한 기본 응답",
                    "keywords": ["분석불가"]
                }
            else:
                return {
                    "overall_sentiment": "중립",
                    "sentiment_distribution": {"긍정": 0.33, "부정": 0.33, "중립": 0.34},
                    "key_topics": ["분석불가"],
                    "summary": "파싱 오류로 분석할 수 없습니다."
                }

    def analyze_single_comment(self, comment_text: str) -> SentimentResult:
        """단일 댓글 감성 분석"""
        print(f"📝 댓글 분석 중: {comment_text[:50]}...")

        prompt = self.create_sentiment_prompt(comment_text)

        # API 호출
        if self.use_openai:
            response = self.call_openai_api(prompt)
        else:
            response = self.call_gemini_api(prompt)

        # 응답 파싱
        result = self.parse_json_response(response, "sentiment")

        return SentimentResult(
            text=comment_text,
            sentiment=SentimentType(result["sentiment"]),
            confidence=result["confidence"],
            reason=result["reason"],
            keywords=result["keywords"]
        )

    def analyze_trend(self, comments: List[Dict], keyword: str) -> TrendAnalysis:
        """댓글 전체의 동향 분석"""
        print(f"📊 '{keyword}' 키워드 동향 분석 중... (댓글 {len(comments)}개)")

        prompt = self.create_trend_prompt(comments, keyword)

        # API 호출
        if self.use_openai:
            response = self.call_openai_api(prompt, max_tokens=800)
        else:
            response = self.call_gemini_api(prompt)

        # 응답 파싱
        result = self.parse_json_response(response, "trend")

        return TrendAnalysis(
            keyword=keyword,
            overall_sentiment=SentimentType(result["overall_sentiment"]),
            sentiment_distribution=result["sentiment_distribution"],
            key_topics=result["key_topics"],
            summary=result["summary"],
            total_comments=len(comments)
        )

    @tool
    def analyze_sentiment(comment_text: str, use_openai: bool = True) -> Dict[str, Any]:
        """단일 댓글 감성 분석 Tool 함수

        Args:
            comment_text (str): 분석할 댓글 텍스트
            use_openai (bool): True이면 OpenAI 사용, False이면 Gemini 사용

        Returns:
            Dict: 감성 분석 결과
        """
        analyzer = DataAnalyzerTool(use_openai=use_openai)

        try:
            result = analyzer.analyze_single_comment(comment_text)

            return {
                "text": result.text,
                "sentiment": result.sentiment.value,
                "confidence": result.confidence,
                "reason": result.reason,
                "keywords": result.keywords,
                "api_used": "OpenAI" if use_openai else "Gemini"
            }

        except Exception as e:
            return {
                "error": f"감성 분석 중 오류: {str(e)}",
                "text": comment_text,
                "sentiment": "중립",
                "confidence": 0.0
            }

    @tool
    def analyze_news_trend(comments_data: List[Dict], keyword: str, use_openai: bool = True) -> Dict[str, Any]:
        """뉴스 댓글 전체 동향 분석 Tool 함수

        Args:
            comments_data (List[Dict]): 댓글 데이터 리스트
            keyword (str): 분석 대상 키워드
            use_openai (bool): True이면 OpenAI 사용, False이면 Gemini 사용

        Returns:
            Dict: 동향 분석 결과
        """
        analyzer = DataAnalyzerTool(use_openai=use_openai)

        try:
            # 댓글 텍스트만 추출
            comments = []
            for comment in comments_data:
                if isinstance(comment, dict) and 'text' in comment:
                    comments.append(comment)
                elif isinstance(comment, str):
                    comments.append({'text': comment})

            if not comments:
                return {
                    "error": "분석할 댓글이 없습니다.",
                    "keyword": keyword
                }

            result = analyzer.analyze_trend(comments, keyword)

            return {
                "keyword": result.keyword,
                "overall_sentiment": result.overall_sentiment.value,
                "sentiment_distribution": result.sentiment_distribution,
                "key_topics": result.key_topics,
                "summary": result.summary,
                "total_comments": result.total_comments,
                "api_used": "OpenAI" if use_openai else "Gemini"
            }

        except Exception as e:
            return {
                "error": f"동향 분석 중 오류: {str(e)}",
                "keyword": keyword,
                "overall_sentiment": "중립"
            }

def main():
    """메인 실행 함수"""
    print("🚀 DataAnalyzer Tool 실습 시작")
    print("=" * 60)

    # 테스트 댓글들
    test_comments = [
        "정말 좋은 정책이네요! 적극 지지합니다.",
        "이런 식으로 하면 안 된다고 생각합니다.",
        "더 자세한 설명이 필요할 것 같아요.",
        "찬성합니다. 빨리 시행되었으면 좋겠어요.",
        "반대합니다. 너무 성급한 결정인 것 같네요.",
        "장단점을 더 살펴봐야 할 것 같습니다."
    ]

    # 실습 1: 단일 댓글 감성 분석
    print("\n📝 [실습 1] 단일 댓글 감성 분석")
    print("-" * 40)

    for i, comment in enumerate(test_comments[:3], 1):
        print(f"\n[댓글 {i}] {comment}")
        result = DataAnalyzerTool.analyze_sentiment(comment, use_openai=True)

        if "error" in result:
            print(f"❌ 오류: {result['error']}")
        else:
            print(f"✅ 감성: {result['sentiment']} (신뢰도: {result['confidence']:.2f})")
            print(f"   근거: {result['reason']}")
            print(f"   키워드: {result['keywords']}")

    # 실습 2: 전체 동향 분석
    print("\n\n📊 [실습 2] 전체 동향 분석")
    print("-" * 40)

    comments_dict = [{"text": comment} for comment in test_comments]
    trend_result = DataAnalyzerTool.analyze_news_trend(
        comments_dict, 
        keyword="정부 정책", 
        use_openai=True
    )

    if "error" in trend_result:
        print(f"❌ 오류: {trend_result['error']}")
    else:
        print(f"🎯 키워드: {trend_result['keyword']}")
        print(f"📈 전체 감성: {trend_result['overall_sentiment']}")
        print(f"📊 감성 분포:")
        for sentiment, ratio in trend_result['sentiment_distribution'].items():
            print(f"   {sentiment}: {ratio:.1%}")
        print(f"🔍 주요 주제: {', '.join(trend_result['key_topics'])}")
        print(f"📋 요약: {trend_result['summary']}")
        print(f"📝 총 댓글: {trend_result['total_comments']}개")

    print("\n🎯 주요 학습 포인트:")
    print("1. 프롬프트 엔지니어링으로 일관된 JSON 응답 확보")
    print("2. OpenAI와 Gemini API의 차이점 및 선택 방법")
    print("3. JSON 파싱 및 예외 처리로 안정적인 데이터 추출")
    print("4. 감성 분석과 동향 분석의 구분 및 활용")
    print("5. @tool 데코레이터로 Agent에서 사용 가능한 Tool로 변환")

    print("\n⚠️  주의사항:")
    print("- OPENAI_API_KEY 또는 GEMINI_API_KEY 환경 변수 설정 필요")
    print("- API 사용량 제한 및 비용 고려")
    print("- JSON 형식 응답이 보장되지 않을 수 있음 (파싱 로직 필요)")
    print("- Rate Limit 대응을 위한 재시도 로직 구현 권장")

if __name__ == "__main__":
    main()
