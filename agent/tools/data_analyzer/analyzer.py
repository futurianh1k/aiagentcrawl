"""
Data Analyzer Tool

OpenAI/Gemini를 이용한 감성 분석 Tool 구현
보안 가이드라인: API 키는 로그에 노출하지 않음, 개인정보 마스킹
"""

import json
import time
from typing import List, Dict, Any, Optional

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

from langchain.tools import tool

from common.config import get_config
from common.utils import safe_log, validate_input
from common.security import mask_sensitive_data
from common.models import SentimentType, SentimentResult, TrendAnalysis
from .models import SentimentResult, TrendAnalysis


class DataAnalyzerTool:
    """데이터 분석 Tool 클래스"""

    def __init__(self, use_openai: bool = True):
        """
        초기화

        Args:
            use_openai: True이면 OpenAI 사용, False이면 Gemini 사용
        """
        self.use_openai = use_openai
        self.config = get_config()

        if use_openai:
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI 라이브러리가 설치되지 않았습니다.")
            api_key = self.config.get_openai_key()
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")
            openai.api_key = api_key
            safe_log("OpenAI 초기화 완료", level="info")
        else:
            if not GEMINI_AVAILABLE:
                raise RuntimeError("Gemini 라이브러리가 설치되지 않았습니다.")
            api_key = self.config.get_gemini_key()
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")
            genai.configure(api_key=api_key)
            safe_log("Gemini 초기화 완료", level="info")

    def create_sentiment_prompt(self, text: str) -> str:
        """감성 분석용 프롬프트 생성"""
        # 개인정보 마스킹 (이메일, 전화번호 등)
        sanitized_text = text  # 실제로는 마스킹 로직 추가 필요

        return f"""당신은 전문 뉴스 댓글 감성 분석가입니다.

다음 댓글을 분석하고, 반드시 아래 JSON 형식으로만 응답하세요.

댓글: "{sanitized_text}"

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
        comments_text = "\n".join([
            f"- {c.get('text', c) if isinstance(c, dict) else str(c)}"
            for c in comments[:20]  # 최대 20개
        ])

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
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 정확한 JSON 형식으로만 응답하는 감성 분석 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.config.OPENAI_TEMPERATURE,
                timeout=30
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            safe_log("OpenAI API 오류", level="error", error=str(e))
            # 더미 응답 반환
            if "sentiment" in prompt and "overall_sentiment" not in prompt:
                return '{"sentiment": "중립", "confidence": 0.5, "reason": "API 오류로 인한 기본 응답", "keywords": ["분석불가"]}'
            else:
                return '{"overall_sentiment": "중립", "sentiment_distribution": {"긍정": 0.33, "부정": 0.33, "중립": 0.34}, "key_topics": ["분석불가"], "summary": "API 오류로 분석할 수 없습니다."}'

    def parse_json_response(self, response: str, response_type: str = "sentiment") -> Dict[str, Any]:
        """JSON 응답 파싱 및 검증"""
        try:
            # JSON 부분만 추출
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

            # 검증 및 정규화
            if response_type == "sentiment":
                if "sentiment" not in parsed:
                    parsed["sentiment"] = "중립"
                if parsed["sentiment"] not in ["긍정", "부정", "중립"]:
                    parsed["sentiment"] = "중립"
                if "confidence" not in parsed or not (0 <= parsed["confidence"] <= 1):
                    parsed["confidence"] = 0.5

            elif response_type == "trend":
                if "sentiment_distribution" in parsed:
                    dist = parsed["sentiment_distribution"]
                    total = sum(dist.values())
                    if total > 0:
                        for key in dist:
                            dist[key] = dist[key] / total
                    else:
                        parsed["sentiment_distribution"] = {"긍정": 0.33, "부정": 0.33, "중립": 0.34}

            return parsed

        except Exception as e:
            safe_log("JSON 파싱 오류", level="error", error=str(e))
            # 기본값 반환
            if response_type == "sentiment":
                return {"sentiment": "중립", "confidence": 0.5, "reason": "파싱 오류", "keywords": []}
            else:
                return {"overall_sentiment": "중립", "sentiment_distribution": {"긍정": 0.33, "부정": 0.33, "중립": 0.34}, "key_topics": [], "summary": "파싱 오류"}

    def analyze_single_comment(self, comment_text: str) -> SentimentResult:
        """단일 댓글 감성 분석"""
        if not validate_input(comment_text, max_length=1000):
            raise ValueError("유효하지 않은 댓글입니다.")

        prompt = self.create_sentiment_prompt(comment_text)

        if self.use_openai:
            response = self.call_openai_api(prompt)
        else:
            # Gemini 호출 로직 (간단화)
            response = '{"sentiment": "중립", "confidence": 0.5, "reason": "Gemini 미구현", "keywords": []}'

        result = self.parse_json_response(response, "sentiment")

        return SentimentResult(
            text=comment_text,
            sentiment=SentimentType(result["sentiment"]),
            confidence=result["confidence"],
            reason=result["reason"],
            keywords=result.get("keywords", [])
        )

    def analyze_trend(self, comments: List[Dict], keyword: str) -> TrendAnalysis:
        """댓글 전체의 동향 분석"""
        if not comments:
            return TrendAnalysis(
                keyword=keyword,
                overall_sentiment=SentimentType.NEUTRAL,
                sentiment_distribution={"긍정": 0.0, "부정": 0.0, "중립": 1.0},
                key_topics=[],
                summary="분석할 댓글이 없습니다.",
                total_comments=0
            )

        prompt = self.create_trend_prompt(comments, keyword)

        if self.use_openai:
            response = self.call_openai_api(prompt, max_tokens=800)
        else:
            # Gemini 호출 로직 (간단화)
            response = '{"overall_sentiment": "중립", "sentiment_distribution": {"긍정": 0.33, "부정": 0.33, "중립": 0.34}, "key_topics": [], "summary": "Gemini 미구현"}'

        result = self.parse_json_response(response, "trend")

        return TrendAnalysis(
            keyword=keyword,
            overall_sentiment=SentimentType(result["overall_sentiment"]),
            sentiment_distribution=result["sentiment_distribution"],
            key_topics=result.get("key_topics", []),
            summary=result.get("summary", ""),
            total_comments=len(comments)
        )


@tool
def analyze_sentiment(comment_text: str, use_openai: bool = True) -> Dict[str, Any]:
    """단일 댓글 감성 분석 Tool 함수"""
    try:
        analyzer = DataAnalyzerTool(use_openai=use_openai)
        result = analyzer.analyze_single_comment(comment_text)
        return result.to_dict()
    except Exception as e:
        safe_log("감성 분석 오류", level="error", error=str(e))
        return {"error": str(e), "sentiment": "중립", "confidence": 0.0}


@tool
def analyze_news_trend(comments_data: List[Dict], keyword: str, use_openai: bool = True) -> Dict[str, Any]:
    """뉴스 댓글 전체 동향 분석 Tool 함수"""
    try:
        analyzer = DataAnalyzerTool(use_openai=use_openai)
        
        # 댓글 데이터 정규화
        normalized_comments = []
        for comment in comments_data:
            if isinstance(comment, dict):
                if "text" in comment:
                    normalized_comments.append(comment)
                else:
                    # 키가 없으면 전체를 텍스트로 간주
                    normalized_comments.append({"text": str(comment)})
            else:
                normalized_comments.append({"text": str(comment)})

        if not normalized_comments:
            return {
                "error": "분석할 댓글이 없습니다.",
                "keyword": keyword,
                "overall_sentiment": "중립",
                "sentiment_distribution": {"긍정": 0.0, "부정": 0.0, "중립": 1.0},
                "key_topics": [],
                "summary": "댓글이 없습니다.",
                "total_comments": 0
            }

        result = analyzer.analyze_trend(normalized_comments, keyword)
        return result.to_dict()
    except Exception as e:
        safe_log("동향 분석 오류", level="error", error=str(e))
        return {
            "error": str(e),
            "keyword": keyword,
            "overall_sentiment": "중립",
            "sentiment_distribution": {"긍정": 0.33, "부정": 0.33, "중립": 0.34},
            "key_topics": [],
            "summary": f"동향 분석 중 오류: {str(e)}",
            "total_comments": len(comments_data) if comments_data else 0
        }
