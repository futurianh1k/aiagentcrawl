# -*- coding: utf-8 -*-
"""
AI 에이전트 기반 뉴스 감성 분석 시스템 - 실습 1
==================================================
주제: LangChain v1.x + LangGraph 기본 Agent - Calculator Tool 예제

본 파일은 다음 환경을 전제로 수정되었습니다.
- Python 3.13
- langchain==1.2.0
- langchain-core==1.2.1
- langgraph==1.0.5 (langgraph-prebuilt 포함)
- openai==2.x

변경 요약
- langchain.agents.initialize_agent / AgentType 사용 제거 (v1.x에서 제거됨)
- LangGraph의 prebuilt ReAct agent(create_react_agent) 기반으로 재구성
- 기존 파일의 들여쓰기 오류(run 메서드가 divide_tool 내부로 들어가 있던 문제) 수정
"""

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# LangGraph 기반 ReAct 에이전트
from langgraph.prebuilt import create_react_agent

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정 (환경 변수에서 읽기)
# .env 파일에 OPENAI_API_KEY=your_api_key_here 형태로 저장
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("⚠️  경고: OPENAI_API_KEY가 설정되지 않았습니다. 일부 기능이 동작하지 않을 수 있습니다.")
    print("   .env 파일에 OPENAI_API_KEY=your_key 를 추가하세요.")
    openai_api_key = None


def _build_chat_model(api_key: str):
    """
    LangChain v1.x에서 모델 초기화는 환경/설치 상태에 따라 경로가 달라질 수 있습니다.

    우선순위:
      1) langchain.chat_models.init_chat_model (가능하면 이 경로가 가장 간단)
      2) langchain_openai.ChatOpenAI (langchain-openai 패키지가 설치된 경우)

    둘 다 불가하면, 사용자가 langchain-openai 설치가 필요합니다.
    """
    os.environ["OPENAI_API_KEY"] = api_key

    # 1) init_chat_model 우선 시도
    try:
        from langchain.chat_models import init_chat_model  # type: ignore

        # 모델명은 필요 시 변경 가능
        return init_chat_model("gpt-4o-mini", model_provider="openai")
    except Exception:
        pass

    # 2) langchain-openai 시도
    try:
        from langchain_openai import ChatOpenAI  # type: ignore

        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    except Exception as e:
        raise RuntimeError(
            "OpenAI Chat 모델 초기화에 실패했습니다. "
            "다음 중 하나를 확인하세요:\n"
            "1) OPENAI_API_KEY가 올바르게 설정되었는지\n"
            "2) `pip install -U langchain-openai` 설치 여부\n"
            f"(원인: {e})"
        ) from e


# ---- Tool 정의 ----
@tool
def add_tool(x: float, y: float) -> float:
    """두 수를 더합니다."""
    result = x + y
    print(f"🧮 덧셈 계산: {x} + {y} = {result}")
    return result


@tool
def multiply_tool(x: float, y: float) -> float:
    """두 수를 곱합니다."""
    result = x * y
    print(f"🧮 곱셈 계산: {x} × {y} = {result}")
    return result


@tool
def divide_tool(x: float, y: float) -> float:
    """두 수를 나눕니다. (0으로 나누기 방지)"""
    if y == 0:
        raise ValueError("0으로 나눌 수 없습니다!")
    result = x / y
    print(f"🧮 나눗셈 계산: {x} ÷ {y} = {result}")
    return result


class CalculatorAgent:
    """
    LangGraph prebuilt ReAct agent 기반 계산 에이전트.

    - Streamlit에서 대화 히스토리를 넘겨주면 맥락을 유지할 수 있습니다.
    - verbose 로그는 stdout으로 출력되며, streamlit_app.py에서 capture 합니다.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY가 필요합니다. 환경변수 또는 인자로 제공하세요.")

        self.model = _build_chat_model(api_key)
        self.tools = [add_tool, multiply_tool, divide_tool]
        self.agent = create_react_agent(self.model, self.tools)

    @staticmethod
    def _history_to_messages(history: Optional[List[Dict[str, str]]]) -> List[BaseMessage]:
        """
        Streamlit에서 저장하는 history 포맷을 LangChain 메시지로 변환.
        history item 예시: {"role": "user"|"assistant", "content": "..."}
        """
        if not history:
            return []

        msgs: List[BaseMessage] = []
        for item in history:
            role = (item.get("role") or "").lower()
            content = item.get("content") or ""
            if not content:
                continue
            if role in ("user", "human"):
                msgs.append(HumanMessage(content=content))
            else:
                msgs.append(AIMessage(content=content))
        return msgs

    def run(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        에이전트 실행.

        Args:
            query: 사용자 질의(자연어)
            history: 선택. [{"role":"user"/"assistant","content":"..."}] 리스트

        Returns:
            최종 응답 문자열
        """
        try:
            print(f"\n🤖 사용자 질의: {query}")
            print("=" * 50)

            messages = self._history_to_messages(history)
            messages.append(HumanMessage(content=query))

            result = self.agent.invoke({"messages": messages})

            # LangGraph agent는 messages를 누적해서 반환합니다.
            final_msg = result["messages"][-1]
            response = getattr(final_msg, "content", str(final_msg))

            print("=" * 50)
            print(f"✅ Agent 응답: {response}")
            return response

        except Exception as e:
            error_msg = f"❌ Agent 실행 중 오류: {str(e)}"
            print(error_msg)
            return error_msg


def main():
    """메인 실행 함수(터미널용)"""
    print("🚀 LangChain/LangGraph 기본 Agent 실습 시작")
    print("=" * 60)

    try:
        calculator = CalculatorAgent(openai_api_key)
    except RuntimeError as e:
        print(f"❌ {e}")
        print("OPENAI_API_KEY를 설정하세요. Streamlit GUI는 `streamlit run streamlit_app.py` 로 실행합니다.")
        return

    test_queries = [
        "3과 5를 더해줘",
        "10에 7을 곱한 결과는?",
        "100을 4로 나누면?",
        "((2 + 3) * 4) / 2 를 계산해줘",
    ]

    print("\n📝 테스트 질의 실행:")
    history: List[Dict[str, str]] = []
    for i, query in enumerate(test_queries, 1):
        print(f"\n[테스트 {i}]")
        response = calculator.run(query, history=history)
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": response})
        print("\n" + "-" * 40)


if __name__ == "__main__":
    main()
