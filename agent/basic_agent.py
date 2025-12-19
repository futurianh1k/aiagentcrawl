"""
AI 에이전트 기반 뉴스 감성 분석 시스템 - 실습 1
==================================================
주제: LangChain 기본 Agent - Calculator Tool 예제

목표:
- LangChain의 기본 Agent 구조 이해
- Tool 정의 및 Agent 초기화 방법 학습
- Agent 실행 및 디버깅 방법 습득

필수 라이브러리:
# core: langchain
pip install langchain python-dotenv
# OpenAI 모델 통합(필수, 모델 사용 시):
pip install -U langchain-openai openai
# Streamlit GUI(선택):
pip install streamlit
"""

import os
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.agents.factory import create_agent
# OpenAI chat model integration (langchain-openai)
try:
    from langchain.chat_models import ChatOpenAI as OpenAI
    OPENAI_INTEGRATION_AVAILABLE = True
except Exception:
    OpenAI = None
    OPENAI_INTEGRATION_AVAILABLE = False
# Conversation memory is optional depending on langchain install
try:
    from langchain.memory import ConversationBufferMemory
    MEMORY_AVAILABLE = True
except Exception:
    ConversationBufferMemory = None
    MEMORY_AVAILABLE = False

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정 (환경 변수에서 읽기)
# .env 파일에 OPENAI_API_KEY=your_api_key_here 형태로 저장
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("⚠️  경고: OPENAI_API_KEY가 설정되지 않았습니다. 일부 기능이 동작하지 않을 수 있습니다.")
    print("   .env 파일에 OPENAI_API_KEY=your_key 를 추가하세요.")
    # 실제 키가 없으면 None으로 남겨 두어 호출자가 적절히 처리하도록 함
    openai_api_key = None

class CalculatorAgent:
    """기본 Calculator Tool을 사용하는 LangChain Agent"""

    def __init__(self, api_key: str):
        """Agent 초기화"""
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY가 필요합니다. 환경변수 또는 인자로 제공하세요.")

        if OpenAI is None:
            raise RuntimeError("OpenAI 통합이 설치되어 있지 않습니다. 'pip install -U langchain-openai' 를 실행하세요.")

        self.llm = OpenAI(
            temperature=0,
            api_key=api_key,
            verbose=True
        )

        # 메모리 설정 (대화 기록 보관) — 모듈이 없을 수 있으므로 선택적으로 설정
        if ConversationBufferMemory is not None:
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        else:
            self.memory = None


        # Agent 초기화 (LangChain v1.2+): create_agent 사용
        # model에 LLM 인스턴스를 전달하면 에이전트 그래프를 생성합니다.
        self.agent = create_agent(
            model=self.llm,
            tools=[add_tool, multiply_tool, divide_tool],
            system_prompt="You are a helpful calculator. Use tools to compute when necessary.",
            debug=True,
            name="calculator_agent",
        )


# Tool 함수들을 모듈 최상단으로 이동하여 LangChain의 @tool과 함께 사용합니다.
@tool
def add_tool(x: float, y: float) -> float:
    """두 수를 더하는 도구

    Args:
        x (float): 첫 번째 수
        y (float): 두 번째 수

    Returns:
        float: 두 수의 합
    """
    result = x + y
    print(f"덧셈 계산: {x} + {y} = {result}")
    return result


@tool
def multiply_tool(x: float, y: float) -> float:
    """두 수를 곱하는 도구

    Args:
        x (float): 첫 번째 수
        y (float): 두 번째 수

    Returns:
        float: 두 수의 곱
    """
    result = x * y
    print(f"곱셈 계산: {x} * {y} = {result}")
    return result


@tool
def divide_tool(x: float, y: float) -> float:
    """두 수를 나누는 도구

    Args:
        x (float): 분자
        y (float): 분모

    Returns:
        float: 나눈 결과
    """
    if y == 0:
        raise ValueError("0으로 나눌 수 없습니다!")

    result = x / y
    print(f"나눗셈 계산: {x} / {y} = {result}")
    return result

    def run(self, query: str) -> str:
        """Agent 실행"""
        try:
            print(f"\n🤖 사용자 질의: {query}")
            print("=" * 50)

            # create_agent로 생성된 그래프는 다양한 호출 방식을 제공합니다.
            # 우선적으로 graph.run(inputs) 형태를 시도하고, 없으면 stream 또는 직접 호출을 시도합니다.
            inputs = {"messages": [{"role": "user", "content": query}]}
            response = None

            if hasattr(self.agent, "run"):
                # 일부 구현은 run을 지원합니다.
                response = self.agent.run(inputs)

            elif hasattr(self.agent, "stream"):
                # stream으로 결과를 수집하여 마지막 청크를 응답으로 사용합니다.
                last = None
                for chunk in self.agent.stream(inputs, stream_mode="final"):
                    last = chunk
                response = last

            else:
                # fallback: 객체 호출
                try:
                    out = self.agent(inputs)
                    response = out
                except Exception:
                    response = "(에이전트가 응답을 생성하지 못했습니다)"

            print("=" * 50)
            print(f"✅ Agent 응답: {response}")
            return response

        except Exception as e:
            error_msg = f"❌ Agent 실행 중 오류: {str(e)}"
            print(error_msg)
            return error_msg

def main():
    """메인 실행 함수"""
    print("🚀 LangChain 기본 Agent 실습 시작")
    print("=" * 60)

    # Agent 초기화
    try:
        calculator = CalculatorAgent(openai_api_key)
    except RuntimeError as e:
        print(f"❌ {e}")
        print("터미널에서 실행하려면 OPENAI_API_KEY를 설정하세요. 또는 Streamlit GUI를 사용하려면 `streamlit run streamlit_app.py`를 실행하세요.")
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
        calculator.run(query)
        print("\n" + "-" * 40)

    print("\n🎯 주요 학습 포인트:")
    print("1. @tool 데코레이터로 함수를 Tool로 변환")
    print("2. initialize_agent로 Agent와 Tools 연결")
    print("3. AgentType.CONVERSATIONAL_REACT_DESCRIPTION 사용")
    print("4. verbose=True로 Agent 사고 과정 관찰")
    print("5. ConversationBufferMemory로 대화 기록 관리")

    print("\n⚠️  주의사항:")
    print("- OpenAI API 키가 필요합니다 (.env 파일 설정)")
    print("- max_iterations로 무한 루프 방지")
    print("- Tool 함수에는 명확한 docstring 작성 필수")

if __name__ == "__main__":
    main()
