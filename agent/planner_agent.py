"""
AI 에이전트 기반 뉴스 감성 분석 시스템 - 실습 4
==================================================
주제: Planner Agent 구현 - Tools 등록 및 실행

목표:
- 여러 Tools를 통합하는 Planner Agent 구현
- 자연어 의도 파악 및 Tool 순차 실행
- 사용자 질의에 따른 동적 Tool 선택
- 전체 End-to-End 파이프라인 구축

필수 라이브러리:
pip install langchain openai python-dotenv
"""

import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import AgentAction, AgentFinish

# 이전 실습들에서 구현한 Tool들 import (실제 환경에서는 별도 파일에서)
from lab2_news_scraper import NewsScraperTool
from lab3_data_analyzer import DataAnalyzerTool

# 환경 변수 로드
load_dotenv()

class NewsAnalysisAgent:
    """뉴스 감성 분석을 위한 통합 AI Agent"""

    def __init__(self):
        """Agent 초기화"""

        # OpenAI API 키 설정
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("⚠️  경고: OPENAI_API_KEY가 설정되지 않았습니다.")
            self.openai_api_key = "sk-test-key-replace-with-real-key"

        # LLM 초기화
        self.llm = OpenAI(
            temperature=0.1,  # 낮은 temperature로 일관된 응답
            openai_api_key=self.openai_api_key,
            max_tokens=1000,
            verbose=True
        )

        # 메모리 설정 (대화 컨텍스트 유지)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
            output_key="output"
        )

        # Tools 등록
        self.tools = [
            self.scrape_news_tool,
            self.analyze_sentiment_tool,
            self.analyze_trend_tool,
            self.summarize_results_tool
        ]

        # Agent 초기화
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            max_iterations=5,  # 최대 반복 횟수 제한
            early_stopping_method="generate"  # 조기 종료 설정
        )

        print("🤖 뉴스 감성 분석 Agent가 초기화되었습니다!")
        print(f"📚 등록된 Tools: {len(self.tools)}개")

    @tool
    def scrape_news_tool(keyword: str, max_articles: int = 3) -> str:
        """뉴스 기사 및 댓글 수집 도구

        Args:
            keyword (str): 검색할 키워드
            max_articles (int): 최대 수집할 기사 수

        Returns:
            str: 수집된 뉴스 데이터 (JSON 형식)
        """
        print(f"🔍 뉴스 검색 시작: {keyword}")

        # 실제로는 NewsScraperTool.scrape_news 호출
        # 여기서는 테스트용 더미 데이터 반환
        dummy_data = {
            "keyword": keyword,
            "articles": [
                {
                    "title": f"{keyword} 관련 주요 뉴스 1",
                    "url": "https://news.example.com/1",
                    "content": f"{keyword}에 대한 긍정적인 전망이 제시되었습니다.",
                    "comments": [
                        {"text": "좋은 소식이네요!", "author": "사용자1"},
                        {"text": "기대됩니다.", "author": "사용자2"},
                        {"text": "신중하게 지켜봐야겠어요.", "author": "사용자3"}
                    ]
                },
                {
                    "title": f"{keyword} 관련 주요 뉴스 2", 
                    "url": "https://news.example.com/2",
                    "content": f"{keyword}에 대한 우려의 목소리도 나오고 있습니다.",
                    "comments": [
                        {"text": "걱정이 됩니다.", "author": "사용자4"},
                        {"text": "더 신중해야 할 것 같아요.", "author": "사용자5"},
                        {"text": "장단점을 모두 고려해야죠.", "author": "사용자6"}
                    ]
                }
            ],
            "total_articles": 2,
            "total_comments": 6
        }

        return json.dumps(dummy_data, ensure_ascii=False)

    @tool
    def analyze_sentiment_tool(comment_text: str) -> str:
        """단일 댓글 감성 분석 도구

        Args:
            comment_text (str): 분석할 댓글 텍스트

        Returns:
            str: 감성 분석 결과 (JSON 형식)
        """
        print(f"📝 댓글 감성 분석: {comment_text[:30]}...")

        # 간단한 키워드 기반 감성 분석 (실제로는 DataAnalyzerTool 사용)
        positive_words = ["좋", "훌륭", "기대", "찬성", "지지", "만족", "훌륭"]
        negative_words = ["나쁘", "걱정", "우려", "반대", "실망", "문제", "위험"]

        text_lower = comment_text.lower()

        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)

        if positive_score > negative_score:
            sentiment = "긍정"
            confidence = min(0.9, 0.6 + positive_score * 0.1)
        elif negative_score > positive_score:
            sentiment = "부정"
            confidence = min(0.9, 0.6 + negative_score * 0.1)
        else:
            sentiment = "중립"
            confidence = 0.5

        result = {
            "text": comment_text,
            "sentiment": sentiment,
            "confidence": confidence,
            "reason": f"{'긍정' if positive_score > 0 else '부정' if negative_score > 0 else '중립적'} 표현 감지",
            "keywords": positive_words[:2] if positive_score > 0 else negative_words[:2] if negative_score > 0 else ["중립"]
        }

        return json.dumps(result, ensure_ascii=False)

    @tool
    def analyze_trend_tool(comments_json: str, keyword: str) -> str:
        """댓글들의 전체 동향 분석 도구

        Args:
            comments_json (str): 댓글 데이터 JSON 문자열
            keyword (str): 분석 대상 키워드

        Returns:
            str: 동향 분석 결과 (JSON 형격)
        """
        print(f"📊 '{keyword}' 동향 분석 중...")

        try:
            # JSON 파싱
            data = json.loads(comments_json) if isinstance(comments_json, str) else comments_json

            # 모든 댓글 수집
            all_comments = []
            if "articles" in data:
                for article in data["articles"]:
                    if "comments" in article:
                        all_comments.extend(article["comments"])

            if not all_comments:
                return json.dumps({
                    "error": "분석할 댓글이 없습니다.",
                    "keyword": keyword
                }, ensure_ascii=False)

            # 각 댓글의 감성 분석
            sentiment_counts = {"긍정": 0, "부정": 0, "중립": 0}

            for comment in all_comments:
                if isinstance(comment, dict) and "text" in comment:
                    # analyze_sentiment_tool 호출
                    sentiment_result = json.loads(NewsAnalysisAgent.analyze_sentiment_tool(comment["text"]))
                    sentiment_counts[sentiment_result["sentiment"]] += 1

            total = sum(sentiment_counts.values())
            if total == 0:
                return json.dumps({
                    "error": "댓글 분석에 실패했습니다.",
                    "keyword": keyword
                }, ensure_ascii=False)

            # 비율 계산
            distribution = {
                sentiment: count / total 
                for sentiment, count in sentiment_counts.items()
            }

            # 전체 감성 결정
            max_sentiment = max(distribution.keys(), key=lambda k: distribution[k])

            # 주요 주제 추출 (간단한 키워드 추출)
            all_text = " ".join([c.get("text", "") for c in all_comments if isinstance(c, dict)])
            common_words = ["정책", "경제", "기술", "사회", "정부", "기업", "시장", "투자"]
            key_topics = [word for word in common_words if word in all_text][:3]

            result = {
                "keyword": keyword,
                "overall_sentiment": max_sentiment,
                "sentiment_distribution": distribution,
                "key_topics": key_topics or [keyword],
                "summary": f"'{keyword}'에 대한 여론은 전반적으로 {max_sentiment}적입니다. 총 {total}개의 댓글을 분석한 결과입니다.",
                "total_comments": total
            }

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "error": f"동향 분석 중 오류: {str(e)}",
                "keyword": keyword
            }, ensure_ascii=False)

    @tool
    def summarize_results_tool(trend_json: str) -> str:
        """분석 결과 요약 및 인사이트 제공 도구

        Args:
            trend_json (str): 동향 분석 결과 JSON

        Returns:
            str: 최종 요약 및 인사이트
        """
        print("📋 결과 요약 중...")

        try:
            data = json.loads(trend_json) if isinstance(trend_json, str) else trend_json

            if "error" in data:
                return f"❌ 분석 실패: {data['error']}"

            keyword = data.get("keyword", "대상")
            overall_sentiment = data.get("overall_sentiment", "중립")
            distribution = data.get("sentiment_distribution", {})
            key_topics = data.get("key_topics", [])
            total_comments = data.get("total_comments", 0)

            # 퍼센트로 변환
            percent_dist = {k: f"{v:.1%}" for k, v in distribution.items()}

            summary = f"""
🎯 **'{keyword}' 감성 분석 결과**

📊 **전체 동향**: {overall_sentiment}
📈 **감성 분포**:
   • 긍정: {percent_dist.get('긍정', '0.0%')}
   • 부정: {percent_dist.get('부정', '0.0%')}  
   • 중립: {percent_dist.get('중립', '0.0%')}

🔍 **주요 키워드**: {', '.join(key_topics) if key_topics else '없음'}
📝 **분석 댓글 수**: {total_comments}개

💡 **인사이트**:
""".strip()

            # 인사이트 생성
            if overall_sentiment == "긍정":
                summary += f"\n• {keyword}에 대한 여론이 전반적으로 긍정적입니다."
                summary += f"\n• 긍정 비율이 {percent_dist.get('긍정', '0%')}로 높은 지지를 받고 있습니다."
            elif overall_sentiment == "부정":
                summary += f"\n• {keyword}에 대한 우려의 목소리가 높습니다."
                summary += f"\n• 부정 비율이 {percent_dist.get('부정', '0%')}로 신중한 접근이 필요합니다."
            else:
                summary += f"\n• {keyword}에 대한 여론이 분산되어 있습니다."
                summary += f"\n• 다양한 관점에서 의견이 나뉘고 있어 균형잡힌 접근이 중요합니다."

            return summary

        except Exception as e:
            return f"❌ 요약 생성 중 오류: {str(e)}"

    def analyze_news_sentiment(self, user_query: str) -> str:
        """사용자 질의를 받아 뉴스 감성 분석을 수행하는 메인 메서드"""
        print(f"\n🤖 사용자 질의: {user_query}")
        print("=" * 60)

        try:
            # Agent 실행
            response = self.agent.run(input=user_query)

            print("=" * 60)
            print(f"✅ 최종 응답:")
            print(response)

            return response

        except Exception as e:
            error_msg = f"❌ Agent 실행 중 오류: {str(e)}"
            print(error_msg)
            return error_msg

    def get_conversation_history(self) -> List[Dict]:
        """대화 히스토리 반환"""
        return self.memory.chat_memory.messages

def main():
    """메인 실행 함수"""
    print("🚀 Planner Agent 실습 시작")
    print("=" * 60)

    # Agent 초기화
    agent = NewsAnalysisAgent()

    # 테스트 질의들
    test_queries = [
        "삼성전자 주가에 대한 최근 뉴스의 여론을 분석해줘",
        "AI 기술 발전에 대한 사람들의 반응은 어때?",
        "부동산 시장 동향에 대한 댓글들을 분석해서 요약해줘"
    ]

    print("\n📝 테스트 질의 실행:")

    for i, query in enumerate(test_queries, 1):
        print(f"\n\n[테스트 {i}]")
        print("-" * 50)

        response = agent.analyze_news_sentiment(query)

        print("\n" + "="*40)
        print(f"[테스트 {i} 완료]\n")

        # 메모리에서 대화 히스토리 확인
        history = agent.get_conversation_history()
        print(f"📚 대화 히스토리 길이: {len(history)}")

    print("\n\n🎯 주요 학습 포인트:")
    print("1. 여러 Tools를 하나의 Agent에 통합 등록")
    print("2. 사용자 질의에 따른 동적 Tool 선택 및 실행")
    print("3. ConversationBufferMemory로 대화 컨텍스트 유지")
    print("4. Tool 간 데이터 전달 및 파이프라인 구축")
    print("5. Agent의 ReAct 패턴 (Reason + Act) 관찰")

    print("\n⚠️  주의사항:")
    print("- 모든 Tools가 정상 작동해야 Agent가 올바르게 실행됨")
    print("- max_iterations 설정으로 무한 루프 방지")
    print("- Tool 간 데이터 형식 일치 (JSON 문자열 전달)")
    print("- verbose=True로 Agent 추론 과정 관찰 가능")

    print("\n✨ 확장 가능한 기능:")
    print("- 데이터베이스 연동 Tool 추가")
    print("- 시각화 생성 Tool 추가") 
    print("- 이메일/슬랙 알림 Tool 추가")
    print("- 스케줄링 및 자동화 Tool 추가")

if __name__ == "__main__":
    main()
