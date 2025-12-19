"""
Session 3 - Lab 09: LangChain ConversationBufferMemory
페이지 29: 대화 기억 관리 및 컨텍스트 유지

LangChain의 ConversationBufferMemory를 사용하여 
대화 컨텍스트를 관리하는 AI 에이전트 구현

학습 목표:
- ConversationBufferMemory 기본 사용법
- 대화 히스토리 관리
- 메모리 제한 및 최적화
- 감정 분석과 메모리 통합
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.llms.openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate


class MemoryManager:
    """대화 메모리 관리 클래스"""

    def __init__(self, memory_type: str = "buffer", max_token_limit: int = 2000):
        """
        메모리 관리자 초기화

        Args:
            memory_type: 메모리 타입 ("buffer" 또는 "window")
            max_token_limit: 최대 토큰 제한
        """
        self.memory_type = memory_type
        self.max_token_limit = max_token_limit

        # 메모리 타입에 따른 메모리 객체 생성
        if memory_type == "buffer":
            self.memory = ConversationBufferMemory(
                memory_key="history",
                return_messages=True,
                max_token_limit=max_token_limit
            )
        elif memory_type == "window":
            self.memory = ConversationBufferWindowMemory(
                memory_key="history",
                k=5,  # 최근 5개 대화만 유지
                return_messages=True
            )
        else:
            raise ValueError("memory_type must be 'buffer' or 'window'")

        # 대화 통계
        self.conversation_count = 0
        self.total_tokens_used = 0

        print(f"✅ {memory_type.upper()} 메모리 관리자 초기화 완료")
        print(f"📊 토큰 제한: {max_token_limit}")

    def add_conversation(self, user_input: str, ai_response: str) -> None:
        """대화를 메모리에 추가"""
        try:
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(ai_response)

            self.conversation_count += 1

            # 대략적인 토큰 수 계산 (1토큰 ≈ 4글자)
            tokens_used = len(user_input + ai_response) // 4
            self.total_tokens_used += tokens_used

            print(f"💬 대화 추가됨 (#{self.conversation_count})")
            print(f"📝 사용자: {user_input[:50]}...")
            print(f"🤖 AI: {ai_response[:50]}...")
            print(f"🎯 예상 토큰: {tokens_used}")

        except Exception as e:
            print(f"❌ 대화 추가 실패: {e}")

    def get_conversation_history(self) -> List[BaseMessage]:
        """대화 히스토리 반환"""
        return self.memory.chat_memory.messages

    def clear_memory(self) -> None:
        """메모리 초기화"""
        self.memory.clear()
        self.conversation_count = 0
        self.total_tokens_used = 0
        print("🗑️ 메모리가 초기화되었습니다")

    def get_memory_stats(self) -> Dict[str, Any]:
        """메모리 사용 통계 반환"""
        messages = self.get_conversation_history()

        return {
            "memory_type": self.memory_type,
            "conversation_count": self.conversation_count,
            "total_messages": len(messages),
            "estimated_tokens": self.total_tokens_used,
            "token_limit": self.max_token_limit,
            "memory_usage_percent": round((self.total_tokens_used / self.max_token_limit) * 100, 2)
        }

    def export_conversations(self, filename: str) -> None:
        """대화 내용을 파일로 내보내기"""
        try:
            messages = self.get_conversation_history()
            conversations = []

            for i in range(0, len(messages), 2):
                if i + 1 < len(messages):
                    user_msg = messages[i]
                    ai_msg = messages[i + 1]

                    conversations.append({
                        "timestamp": datetime.now().isoformat(),
                        "user": user_msg.content,
                        "ai": ai_msg.content
                    })

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(conversations, f, ensure_ascii=False, indent=2)

            print(f"💾 대화 내용이 {filename}에 저장되었습니다")

        except Exception as e:
            print(f"❌ 내보내기 실패: {e}")


class SentimentMemoryAgent:
    """감정 분석과 메모리를 통합한 AI 에이전트"""

    def __init__(self, openai_api_key: str, memory_type: str = "buffer"):
        """
        감정 분석 메모리 에이전트 초기화

        Args:
            openai_api_key: OpenAI API 키
            memory_type: 메모리 타입
        """
        self.api_key = openai_api_key
        self.memory_manager = MemoryManager(memory_type)

        # OpenAI 채팅 모델 초기화
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name="gpt-3.5-turbo",
            temperature=0.7
        )

        # 프롬프트 템플릿 정의
        self.prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""당신은 감정을 이해하고 공감하는 AI 어시스턴트입니다. 
사용자의 감정을 분석하고, 이전 대화 내용을 참고하여 적절한 응답을 제공하세요.

이전 대화:
{history}

현재 입력: {input}

응답 시 다음을 포함하세요:
1. 감정 분석 결과 (긍정/부정/중립)
2. 이전 대화와의 연관성
3. 공감적이고 도움이 되는 응답

응답:"""
        )

        # 대화 체인 생성
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory_manager.memory,
            prompt=self.prompt,
            verbose=True
        )

        print("🤖 감정 분석 메모리 에이전트 초기화 완료")

    def analyze_and_respond(self, user_input: str) -> str:
        """사용자 입력 분석 및 응답 생성"""
        try:
            print(f"\n🔍 분석 중: {user_input}")

            # 대화 체인을 통한 응답 생성
            response = self.conversation.predict(input=user_input)

            print(f"💭 AI 응답: {response}")

            return response

        except Exception as e:
            print(f"❌ 응답 생성 실패: {e}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."

    def get_conversation_summary(self) -> str:
        """대화 요약 생성"""
        try:
            history = self.memory_manager.get_conversation_history()

            if not history:
                return "아직 대화 내역이 없습니다."

            # 대화 내용을 문자열로 변환
            conversation_text = "\n".join([
                f"{'사용자' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}"
                for msg in history
            ])

            # 요약 프롬프트
            summary_prompt = f"""다음 대화를 간단히 요약해주세요:

{conversation_text}

요약:"""

            summary_response = self.llm.predict(summary_prompt)
            return summary_response

        except Exception as e:
            print(f"❌ 요약 생성 실패: {e}")
            return "요약을 생성할 수 없습니다."


def demonstrate_basic_memory():
    """기본 메모리 사용법 시연"""
    print("\n" + "="*60)
    print("🧠 기본 메모리 사용법 시연")
    print("="*60)

    # Buffer Memory 시연
    buffer_memory = MemoryManager("buffer", max_token_limit=1000)

    # 샘플 대화 추가
    conversations = [
        ("안녕하세요!", "안녕하세요! 어떻게 도와드릴까요?"),
        ("오늘 기분이 좋지 않아요", "그렇군요. 무슨 일이 있었나요?"),
        ("회사에서 프레젠테이션이 잘 안됐어요", "힘들었겠네요. 다음엔 더 잘할 수 있을 거예요."),
        ("조언 고마워요", "언제든지 도움이 필요하면 말씀하세요!")
    ]

    for user, ai in conversations:
        buffer_memory.add_conversation(user, ai)

    # 메모리 통계 출력
    stats = buffer_memory.get_memory_stats()
    print(f"\n📊 메모리 통계:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Window Memory 시연
    print(f"\n🪟 Window Memory 비교 (최근 5개만 유지)")
    window_memory = MemoryManager("window")

    # 더 많은 대화 추가
    for i in range(10):
        window_memory.add_conversation(
            f"질문 {i+1}: 테스트 질문입니다",
            f"답변 {i+1}: 테스트 답변입니다"
        )

    window_stats = window_memory.get_memory_stats()
    print(f"\n📊 Window Memory 통계:")
    for key, value in window_stats.items():
        print(f"   {key}: {value}")


def demonstrate_sentiment_memory_agent():
    """감정 분석 메모리 에이전트 시연"""
    print("\n" + "="*60)
    print("💝 감정 분석 메모리 에이전트 시연")
    print("="*60)

    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("📝 데모용 모의 응답을 사용합니다.")

        # 모의 메모리 관리자로 시연
        memory_demo = MemoryManager("buffer")

        demo_conversations = [
            ("오늘 정말 힘든 하루였어요", "[감정: 부정] 힘든 하루를 보내셨군요. 무슨 일이 있었는지 들어보겠습니다."),
            ("프로젝트 마감이 내일인데 아직 못 끝냈어요", "[감정: 스트레스] 마감 압박이 크시겠네요. 우선순위를 정해서 차근차근 진행해보세요."),
            ("그래도 팀원들이 도와줘서 다행이에요", "[감정: 감사/안도] 이전에 힘들다고 하셨는데, 팀원들의 도움으로 상황이 나아지고 있다니 다행입니다!"),
            ("네, 덕분에 기분이 나아졌어요", "[감정: 긍정] 처음 힘들다고 하셨던 것과 비교하면 많이 회복되신 것 같아 기쁩니다.")
        ]

        for user, ai in demo_conversations:
            memory_demo.add_conversation(user, ai)

        print("\n📋 시연용 대화 내역:")
        messages = memory_demo.get_conversation_history()
        for i, msg in enumerate(messages):
            role = "🧑 사용자" if i % 2 == 0 else "🤖 AI"
            print(f"{role}: {msg.content}")

        return

    # 실제 API를 사용한 에이전트
    try:
        agent = SentimentMemoryAgent(api_key)

        # 대화형 시연
        test_inputs = [
            "안녕하세요! 오늘 새로운 프로젝트를 시작했어요",
            "하지만 조금 걱정이 되네요. 너무 복잡해 보여요",
            "아까 걱정된다고 했는데, 어떻게 극복할 수 있을까요?"
        ]

        for user_input in test_inputs:
            print(f"\n" + "-"*50)
            response = agent.analyze_and_respond(user_input)

        # 대화 요약
        print(f"\n📄 대화 요약:")
        summary = agent.get_conversation_summary()
        print(summary)

        # 메모리 통계
        stats = agent.memory_manager.get_memory_stats()
        print(f"\n📊 최종 메모리 통계:")
        for key, value in stats.items():
            print(f"   {key}: {value}")

    except Exception as e:
        print(f"❌ API 에이전트 시연 실패: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 Session 3 - Lab 09: LangChain ConversationBufferMemory")
    print("=" * 70)

    try:
        # 1. 기본 메모리 사용법 시연
        demonstrate_basic_memory()

        # 2. 감정 분석 메모리 에이전트 시연
        demonstrate_sentiment_memory_agent()

        print(f"\n✅ 모든 시연이 완료되었습니다!")
        print(f"\n📚 핵심 학습 내용:")
        print(f"   1. ConversationBufferMemory vs ConversationBufferWindowMemory")
        print(f"   2. 대화 컨텍스트 관리 및 토큰 제한")
        print(f"   3. 감정 분석과 메모리 통합")
        print(f"   4. 메모리 통계 및 모니터링")
        print(f"   5. 대화 내용 내보내기")

    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    main()
