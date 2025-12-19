"""
Calculator Agent

LangChain을 사용한 기본 Calculator Agent 구현
"""

import os
from typing import Optional, List
from dotenv import load_dotenv

from common.config import Config, get_config
from common.utils import safe_log
from .tools import add_tool, multiply_tool, divide_tool

# 환경 변수 로드
load_dotenv()

# LangChain 관련 import (선택적)
try:
    from langchain.agents.factory import create_agent
    CREATE_AGENT_AVAILABLE = True
except ImportError:
    create_agent = None
    CREATE_AGENT_AVAILABLE = False

try:
    from langchain.chat_models import ChatOpenAI
    OPENAI_INTEGRATION_AVAILABLE = True
except ImportError:
    try:
        from langchain_openai import ChatOpenAI
        OPENAI_INTEGRATION_AVAILABLE = True
    except ImportError:
        ChatOpenAI = None
        OPENAI_INTEGRATION_AVAILABLE = False

try:
    from langchain.memory import ConversationBufferMemory
    MEMORY_AVAILABLE = True
except ImportError:
    ConversationBufferMemory = None
    MEMORY_AVAILABLE = False


class CalculatorAgent:
    """기본 Calculator Tool을 사용하는 LangChain Agent"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Agent 초기화

        Args:
            api_key: OpenAI API 키 (None이면 환경 변수에서 읽음)

        Raises:
            RuntimeError: 필수 설정이 없거나 초기화 실패 시
        """
        config = get_config()

        # API 키 설정
        self.api_key = api_key or config.get_openai_key()

        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY가 필요합니다. 환경변수 또는 인자로 제공하세요."
            )

        if not OPENAI_INTEGRATION_AVAILABLE:
            raise RuntimeError(
                "OpenAI 통합이 설치되어 있지 않습니다. "
                "'pip install -U langchain-openai' 를 실행하세요."
            )

        # LLM 초기화
        try:
            self.llm = ChatOpenAI(
                temperature=0,
                api_key=self.api_key,
                verbose=True
            )
        except Exception as e:
            safe_log("LLM 초기화 실패", level="error", error=str(e))
            raise RuntimeError(f"LLM 초기화 실패: {e}")

        # 메모리 설정 (대화 기록 보관)
        if MEMORY_AVAILABLE and ConversationBufferMemory is not None:
            try:
                self.memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
            except Exception as e:
                safe_log("메모리 초기화 실패", level="warning", error=str(e))
                self.memory = None
        else:
            self.memory = None

        # Agent 초기화
        if CREATE_AGENT_AVAILABLE and create_agent is not None:
            try:
                self.agent = create_agent(
                    model=self.llm,
                    tools=[add_tool, multiply_tool, divide_tool],
                    system_prompt="You are a helpful calculator. Use tools to compute when necessary.",
                    debug=True,
                    name="calculator_agent",
                )
                safe_log("Agent 초기화 완료", level="info")
            except Exception as e:
                safe_log("Agent 초기화 실패", level="error", error=str(e))
                raise RuntimeError(f"Agent 초기화 실패: {e}")
        else:
            raise RuntimeError(
                "create_agent를 사용할 수 없습니다. "
                "LangChain 버전을 확인하세요."
            )

    def run(self, query: str) -> str:
        """
        Agent 실행

        Args:
            query: 사용자 질의

        Returns:
            Agent 응답
        """
        try:
            safe_log("Agent 실행 시작", level="info", query_length=len(query))

            # 입력 검증
            if not query or not isinstance(query, str):
                raise ValueError("유효하지 않은 질의입니다.")

            # Agent 실행
            inputs = {"messages": [{"role": "user", "content": query}]}
            response = None

            if hasattr(self.agent, "run"):
                response = self.agent.run(inputs)
            elif hasattr(self.agent, "stream"):
                last = None
                for chunk in self.agent.stream(inputs, stream_mode="final"):
                    last = chunk
                response = last
            elif hasattr(self.agent, "__call__"):
                response = self.agent(inputs)
            else:
                raise RuntimeError("Agent 실행 방법을 찾을 수 없습니다.")

            safe_log("Agent 실행 완료", level="info")
            return str(response) if response else "응답을 생성하지 못했습니다."

        except Exception as e:
            error_msg = f"Agent 실행 중 오류: {str(e)}"
            safe_log("Agent 실행 오류", level="error", error=str(e))
            return error_msg

    def get_memory(self) -> Optional[object]:
        """메모리 객체 반환"""
        return self.memory


def main():
    """메인 실행 함수"""
    print("🚀 LangChain 기본 Agent 실습 시작")
    print("=" * 60)

    # Agent 초기화
    try:
        config = get_config()
        calculator = CalculatorAgent(config.get_openai_key())
    except RuntimeError as e:
        print(f"❌ {e}")
        print("터미널에서 실행하려면 OPENAI_API_KEY를 설정하세요.")
        return

    # 테스트 질의들
    test_queries = [
        "3과 5를 더해줘",
        "10에 7을 곱한 결과는?",
        "100을 4로 나누면?",
        "((2 + 3) * 4) / 2 를 계산해줘"
    ]

    print("\n📝 테스트 질의 실행:")
    for i, query in enumerate(test_queries, 1):
        print(f"\n[테스트 {i}]")
        result = calculator.run(query)
        print(f"✅ 결과: {result}")
        print("-" * 40)

    print("\n🎯 주요 학습 포인트:")
    print("1. @tool 데코레이터로 함수를 Tool로 변환")
    print("2. create_agent로 Agent와 Tools 연결")
    print("3. verbose=True로 Agent 사고 과정 관찰")
    print("4. ConversationBufferMemory로 대화 기록 관리")
    print("5. 에러 처리 및 로깅")

    print("\n⚠️  주의사항:")
    print("- OpenAI API 키가 필요합니다 (.env 파일 설정)")
    print("- max_iterations로 무한 루프 방지")
    print("- Tool 함수에는 명확한 docstring 작성 필수")


if __name__ == "__main__":
    main()

