"""
Agent 패키지

뉴스 감성 분석을 위한 AI Agent들을 제공합니다.
"""

# CalculatorAgent는 선택적 import (tools가 없을 수 있음)
try:
    from .agent import CalculatorAgent
    CALCULATOR_AVAILABLE = True
except ImportError:
    CalculatorAgent = None
    CALCULATOR_AVAILABLE = False

# NewsAnalysisAgent는 필수
from .news_agent import NewsAnalysisAgent

__all__ = [
    "NewsAnalysisAgent",
]

if CALCULATOR_AVAILABLE:
    __all__.append("CalculatorAgent")
