"""
Robust Calculator Agent (works without OpenAI integration)

This file provides an agent wrapper that uses LangChain/LangGraph where
available, but has a safe local fallback to evaluate arithmetic expressions
without requiring network calls. That makes the Streamlit demo work even
when OpenAI or langchain-openai isn't installed.

Usage:
- For full LLM experience install `langchain-openai` and set OPENAI_API_KEY.
- Otherwise, the agent will use a safe evaluator for arithmetic expressions.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional

from langchain.tools import tool

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

# Try to import Chat model helpers; if missing we'll use local fallback
try:
    from langchain.chat_models import init_chat_model  # type: ignore
    CHAT_INIT_AVAILABLE = True
except Exception:
    init_chat_model = None
    CHAT_INIT_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI  # type: ignore
    CHAT_OPENAI_AVAILABLE = True
except Exception:
    ChatOpenAI = None
    CHAT_OPENAI_AVAILABLE = False

# Try to import create_agent (LangChain >=1.2 factory)
try:
    from langchain.agents.factory import create_agent
    CREATE_AGENT_AVAILABLE = True
except Exception:
    create_agent = None
    CREATE_AGENT_AVAILABLE = False


# ---- Safe evaluator (used when no LLM available) ----
_ALLOWED_AST_NODES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.FloorDiv,
    ast.USub,
    ast.UAdd,
    ast.Load,
    ast.Constant,
    ast.Tuple,
    ast.List,
}


def _safe_eval_expr(expr: str) -> float:
    """Safely evaluate a simple arithmetic expression using ast.

    Supports + - * / ** // % and numeric constants. Raises ValueError on
    unsupported syntax.
    """
    try:
        node = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError("잘못된 수식 문법") from e

    # Walk nodes and ensure only allowed
    for n in ast.walk(node):
        if type(n) not in _ALLOWED_AST_NODES:
            raise ValueError("허용되지 않는 연산/노드가 포함되어 있습니다")

    # Evaluate in a restricted environment
    compiled = compile(node, filename="<ast>", mode="eval")
    return float(eval(compiled, {"__builtins__": {}}))


# ---- Tools ----
@tool
def add_tool(x: float, y: float) -> float:
    """두 수를 더합니다."""
    return x + y


@tool
def multiply_tool(x: float, y: float) -> float:
    """두 수를 곱합니다."""
    return x * y


@tool
def divide_tool(x: float, y: float) -> float:
    """두 수를 나눕니다. 0으로 나누는 경우 예외를 발생시킵니다."""
    if y == 0:
        raise ValueError("0으로 나눌 수 없습니다")
    return x / y


@dataclass
class LocalFallbackAgent:
    """A very small local 'agent' used when LLM integration is missing.

    It looks for a mathematical expression in the user input and evaluates
    it with a safe evaluator. If it can't find an expression, it returns a
    helpful message.
    """

    def run(self, query: str) -> str:
        # Try to find an expression like '((2 + 3) * 4) / 2'
        expr_match = re.search(r"[0-9\(\)\s\+\-\*\/\%\.\\]+", query)
        if expr_match:
            expr = expr_match.group(0).strip()
            try:
                val = _safe_eval_expr(expr)
                return str(val)
            except Exception as e:
                return f"수식 평가 오류: {e}"
        return "로컬 모드: 수식을 포함한 간단한 수학 질의만 처리할 수 있습니다. OPENAI_API_KEY를 설정하면 LLM 기반 에이전트를 사용합니다."


class CalculatorAgentWorking:
    """Robust agent wrapper: prefer LLM-based agent, but fall back to local evaluator."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        # Try to build an LLM model if integration is available
        self.graph_agent = None
        if self.api_key and (CHAT_INIT_AVAILABLE or CHAT_OPENAI_AVAILABLE) and CREATE_AGENT_AVAILABLE:
            try:
                model = None
                if CHAT_INIT_AVAILABLE:
                    model = init_chat_model("gpt-4o-mini", model_provider="openai")
                elif CHAT_OPENAI_AVAILABLE:
                    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

                if model is not None:
                    # Use create_agent from langchain to make a tool-invoking agent
                    self.graph_agent = create_agent(
                        model=model,
                        tools=[add_tool, multiply_tool, divide_tool],
                        system_prompt="You are a helpful calculator. Use tools to compute when necessary.",
                        debug=False,
                        name="calculator_agent",
                    )
            except Exception:
                # If anything fails, fall back to local agent
                self.graph_agent = None

        if self.graph_agent is None:
            self.fallback = LocalFallbackAgent()
        else:
            self.fallback = None

    def run(self, query: str) -> str:
        if self.graph_agent is not None:
            # create_agent graphs expect inputs like dict; try .run, .stream, or invoke
            inputs = {"messages": [{"role": "user", "content": query}]}
            try:
                if hasattr(self.graph_agent, "run"):
                    return self.graph_agent.run(inputs)
                elif hasattr(self.graph_agent, "stream"):
                    last = None
                    for chunk in self.graph_agent.stream(inputs, stream_mode="final"):
                        last = chunk
                    return str(last)
                else:
                    res = self.graph_agent(inputs)
                    return str(res)
            except Exception as e:
                return f"에이전트 실행 오류: {e}"
        else:
            return self.fallback.run(query)


# Convenience alias for importing from other modules
CalculatorAgent = CalculatorAgentWorking
__all__ = ["CalculatorAgent", "openai_api_key", "add_tool", "multiply_tool", "divide_tool"]