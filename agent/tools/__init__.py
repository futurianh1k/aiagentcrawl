"""
Agent Tools 패키지

뉴스 분석 Agent에서 사용하는 모든 Tool들을 제공합니다.
"""

# Calculator Tools (agent/tools.py에서 import)
# 상위 디렉토리의 tools.py를 import
import sys
import os

# agent/tools.py 경로
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # agent/tools.py를 import
    import importlib
    tools_module = importlib.import_module("tools")
    add_tool = getattr(tools_module, "add_tool", None)
    multiply_tool = getattr(tools_module, "multiply_tool", None)
    divide_tool = getattr(tools_module, "divide_tool", None)
except (ImportError, AttributeError):
    # tools.py가 없거나 함수가 없는 경우
    add_tool = None
    multiply_tool = None
    divide_tool = None

# News Scraper Tools
from .news_scraper import scrape_news, NewsScraperTool, NewsSource

# Data Analyzer Tools
from .data_analyzer import analyze_sentiment, analyze_news_trend, DataAnalyzerTool

__all__ = [
    # Calculator Tools
    "add_tool",
    "multiply_tool",
    "divide_tool",
    # News Scraper
    "scrape_news",
    "NewsScraperTool",
    "NewsSource",
    # Data Analyzer
    "analyze_sentiment",
    "analyze_news_trend",
    "DataAnalyzerTool",
]
