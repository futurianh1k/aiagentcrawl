"""
3회차 실습 06: DataAnalyzer Tool 완전 구현
페이지 12 - 프로덕션급 감성 분석 Tool

이 스크립트는 프로덕션 환경에서 사용 가능한 DataAnalyzer Tool을 구현합니다.
- 재시도(Retry) 로직
- 배치 분석 (Batch API)
- 캐싱 및 중복 방지
- 에러 핸들링 및 로깅
"""

import os
import logging
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from openai import OpenAI
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SentimentResult(BaseModel):
    """감성 분석 결과 모델"""
    sentiment: str = Field(description="감성 분류")
    confidence: float = Field(ge=0.0, le=1.0, description="신뢰도")
    reason: str = Field(description="분석 근거")
    keywords: List[str] = Field(description="핵심 키워드")
    processing_time: float = Field(description="처리 시간(초)")
    timestamp: str = Field(description="분석 시각")

@dataclass
class CacheEntry:
    """캐시 엔트리"""
    result: SentimentResult
    created_at: datetime
    ttl_hours: int = 24

class DataAnalyzer:
    """프로덕션급 감성 분석 Tool"""

    def __init__(self, api_key: str, enable_cache: bool = True, cache_ttl_hours: int = 24):
        self.client = OpenAI(api_key=api_key)
        self.enable_cache = enable_cache
        self.cache_ttl_hours = cache_ttl_hours
        self.cache: Dict[str, CacheEntry] = {}

        # 통계 추적
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "api_errors": 0,
            "retries": 0
        }

        logger.info("DataAnalyzer 초기화 완료")

    def _generate_cache_key(self, comment: str, model: str = "gpt-4") -> str:
        """캐시 키 생성"""
        content = f"{comment}:{model}".encode('utf-8')
        return hashlib.md5(content).hexdigest()

    def _is_cache_valid(self, entry: CacheEntry) -> bool:
        """캐시 유효성 검증"""
        age = datetime.now() - entry.created_at
        return age < timedelta(hours=entry.ttl_hours)

    def _get_from_cache(self, cache_key: str) -> Optional[SentimentResult]:
        """캐시에서 결과 조회"""
        if not self.enable_cache or cache_key not in self.cache:
            self.stats["cache_misses"] += 1
            return None

        entry = self.cache[cache_key]
        if self._is_cache_valid(entry):
            self.stats["cache_hits"] += 1
            logger.debug(f"캐시 히트: {cache_key[:8]}...")
            return entry.result
        else:
            # 만료된 캐시 삭제
            del self.cache[cache_key]
            self.stats["cache_misses"] += 1
            return None

    def _save_to_cache(self, cache_key: str, result: SentimentResult):
        """결과를 캐시에 저장"""
        if self.enable_cache:
            entry = CacheEntry(
                result=result,
                created_at=datetime.now(),
                ttl_hours=self.cache_ttl_hours
            )
            self.cache[cache_key] = entry
            logger.debug(f"캐시 저장: {cache_key[:8]}...")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    def _call_openai_api(self, comment: str, model: str = "gpt-4") -> Dict[str, Any]:
        """OpenAI API 호출 (재시도 포함)"""
        self.stats["retries"] += 1

        system_prompt = """당신은 전문 뉴스 댓글 감성 분석가입니다.
        주어진 댓글을 분석하여 JSON 형식으로 응답하세요.

        분류 기준:
        - 긍정: 지지, 칭찬, 기대감, 만족
        - 부정: 비판, 분노, 실망, 우려
        - 중립: 사실 전달, 질문, 균형 의견

        응답 형식:
        {"sentiment": "긍정|부정|중립", "confidence": 0.0-1.0, "reason": "근거", "keywords": ["키워드"]}"""

        try:
            start_time = datetime.now()

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"댓글: {comment}"}
                ],
                temperature=0.3,
                max_tokens=300
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            # JSON 파싱
            content = response.choices[0].message.content
            if '{' in content and '}' in content:
                import json
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                json_str = content[start_idx:end_idx]
                result = json.loads(json_str)

                # 결과에 메타데이터 추가
                result["processing_time"] = processing_time
                result["timestamp"] = datetime.now().isoformat()

                return result
            else:
                raise ValueError("JSON 형식의 응답을 받지 못했습니다")

        except Exception as e:
            self.stats["api_errors"] += 1
            logger.error(f"OpenAI API 호출 실패: {e}")
            raise

    def analyze_sentiment(self, comment: str, model: str = "gpt-4") -> SentimentResult:
        """단일 댓글 감성 분석"""
        self.stats["total_requests"] += 1

        # 빈 댓글 체크
        if not comment or not comment.strip():
            return SentimentResult(
                sentiment="중립",
                confidence=0.0,
                reason="빈 댓글",
                keywords=[],
                processing_time=0.0,
                timestamp=datetime.now().isoformat()
            )

        # 캐시 확인
        cache_key = self._generate_cache_key(comment, model)
        cached_result = self._get_from_cache(cache_key)

        if cached_result:
            return cached_result

        try:
            # API 호출
            raw_result = self._call_openai_api(comment, model)

            # Pydantic 모델로 검증
            result = SentimentResult(**raw_result)

            # 캐시에 저장
            self._save_to_cache(cache_key, result)

            logger.info(f"감성 분석 완료: {result.sentiment} ({result.confidence:.2f})")
            return result

        except Exception as e:
            logger.error(f"감성 분석 실패: {e}")

            # 폴백 결과 반환
            return SentimentResult(
                sentiment="중립",
                confidence=0.0,
                reason=f"분석 실패: {str(e)}",
                keywords=[],
                processing_time=0.0,
                timestamp=datetime.now().isoformat()
            )

    def batch_analyze(self, comments: List[str], model: str = "gpt-4", 
                     batch_size: int = 10) -> List[SentimentResult]:
        """배치 감성 분석"""
        logger.info(f"배치 분석 시작: {len(comments)}개 댓글")

        results = []

        # 배치 단위로 처리
        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]
            logger.info(f"배치 {i//batch_size + 1} 처리 중 ({len(batch)}개)")

            batch_results = []
            for comment in batch:
                result = self.analyze_sentiment(comment, model)
                batch_results.append(result)

            results.extend(batch_results)

        logger.info(f"배치 분석 완료: {len(results)}개 결과")
        return results

    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 조회"""
        cache_hit_rate = 0.0
        if self.stats["total_requests"] > 0:
            cache_hit_rate = self.stats["cache_hits"] / (self.stats["cache_hits"] + self.stats["cache_misses"])

        return {
            "total_requests": self.stats["total_requests"],
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_hit_rate": cache_hit_rate,
            "api_errors": self.stats["api_errors"],
            "retries": self.stats["retries"],
            "cache_size": len(self.cache)
        }

    def clear_cache(self):
        """캐시 클리어"""
        self.cache.clear()
        logger.info("캐시가 클리어되었습니다")

if __name__ == "__main__":
    print("🚀 DataAnalyzer Tool 완전 구현 실습을 시작합니다!")
    print("=" * 70)

    try:
        # 1. DataAnalyzer 초기화
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY를 설정해주세요")

        analyzer = DataAnalyzer(api_key=api_key, enable_cache=True)

        # 2. 단일 분석 테스트
        print("\n1️⃣ 단일 댓글 분석")
        print("-" * 40)

        test_comment = "이 새로운 정책은 정말 훌륭합니다! 적극 지지합니다."
        result = analyzer.analyze_sentiment(test_comment)

        print(f"📝 댓글: {test_comment}")
        print(f"🎯 결과: {result.sentiment} (신뢰도: {result.confidence:.2f})")
        print(f"📊 근거: {result.reason}")
        print(f"🔑 키워드: {result.keywords}")
        print(f"⏱️  처리시간: {result.processing_time:.3f}초")

        # 3. 캐시 테스트 (동일 댓글 재분석)
        print("\n2️⃣ 캐시 기능 테스트")
        print("-" * 40)

        print("동일 댓글 재분석 (캐시에서 가져오기)...")
        cached_result = analyzer.analyze_sentiment(test_comment)
        print(f"🎯 캐시된 결과: {cached_result.sentiment}")

        # 4. 배치 분석 테스트
        print("\n3️⃣ 배치 분석 테스트")
        print("-" * 40)

        test_comments = [
            "정말 좋은 아이디어네요!",
            "이건 완전 최악이에요.",
            "내일 날씨는 어떨까요?",
            "새로운 기술이 기대됩니다.",
            "문제가 너무 많아요."
        ]

        batch_results = analyzer.batch_analyze(test_comments, batch_size=2)

        for i, (comment, result) in enumerate(zip(test_comments, batch_results), 1):
            print(f"{i}. {comment[:20]}... → {result.sentiment} ({result.confidence:.2f})")

        # 5. 통계 정보 출력
        print("\n4️⃣ 성능 통계")
        print("-" * 40)

        stats = analyzer.get_statistics()
        for key, value in stats.items():
            if key == "cache_hit_rate":
                print(f"{key}: {value:.1%}")
            else:
                print(f"{key}: {value}")

        print("\n✅ DataAnalyzer Tool 실습 완료!")
        print("\n💡 핵심 기능:")
        print("   1. 자동 재시도 (Exponential Backoff)")
        print("   2. 인텔리전트 캐싱 (중복 방지)")
        print("   3. 배치 처리 (효율성 향상)")
        print("   4. 에러 복구 (폴백 결과)")
        print("   5. 성능 모니터링 (통계 수집)")
        print("\n📚 다음 단계:")
        print("   - 07_langgraph_sequential.py: Multi-Agent 워크플로우")
        print("   - 08_langgraph_conditional.py: 조건부 라우팅")

    except Exception as e:
        print(f"❌ 실습 오류: {e}")
        print("\n🔧 해결 방법:")
        print("   1. OpenAI API 키 확인")
        print("   2. pip install tenacity pydantic")
        print("   3. 네트워크 연결 확인")
