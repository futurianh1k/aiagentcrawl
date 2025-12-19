"""
Streamlit GUI for CalculatorAgent

Usage:
  pip install streamlit
  streamlit run streamlit_app.py
"""

import io
from contextlib import redirect_stdout
import streamlit as st

from common.config import get_config
from .agent import CalculatorAgent, OPENAI_INTEGRATION_AVAILABLE

st.set_page_config(page_title="Calculator Agent", page_icon="🧮")
st.title("🧮 LangChain Calculator Agent (Streamlit)")

st.markdown("간단한 수학 질의를 자연어로 입력하면 Agent가 계산합니다.")

# 설정 확인
config = get_config()
openai_api_key = config.get_openai_key()

if not openai_api_key:
    st.warning(
        "OPENAI_API_KEY가 설정되지 않았습니다. `.env` 또는 환경 변수에 키를 추가하세요."
    )
    st.stop()

if not OPENAI_INTEGRATION_AVAILABLE:
    st.error(
        "OpenAI 통합(langchain-openai)이 설치되어 있지 않습니다. "
        "`pip install -U langchain-openai` 를 실행하세요."
    )
    st.stop()

# Agent 초기화
if "agent" not in st.session_state:
    try:
        st.session_state.agent = CalculatorAgent(openai_api_key)
        st.session_state.history = []
    except Exception as e:
        st.error(f"Agent 초기화 실패: {e}")
        st.stop()

# 예제 질의
examples = [
    "3과 5를 더해줘",
    "10에 7을 곱한 결과는?",
    "100을 4로 나누면?",
    "((2 + 3) * 4) / 2 를 계산해줘",
]

# UI 구성
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input(
        "질의 입력",
        value=examples[0],
        placeholder="예: 3과 4를 더해줘"
    )
with col2:
    example_query = st.selectbox("예제 선택", examples, label_visibility="collapsed")

if st.button("실행") and query.strip():
    with st.spinner("Agent 실행 중..."):
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                response = st.session_state.agent.run(query)
            logs = buf.getvalue()
            st.session_state.history.append({
                "query": query,
                "response": response,
                "logs": logs
            })
        except Exception as e:
            logs = buf.getvalue()
            st.session_state.history.append({
                "query": query,
                "response": f"오류: {e}",
                "logs": logs
            })
            st.error(f"실행 중 오류: {e}")

# 대화 기록 표시
if st.session_state.get("history"):
    st.header("대화 기록")
    for item in reversed(st.session_state.history):
        st.markdown(f"**질의:** {item['query']}")
        st.markdown(f"**응답:** {item['response']}")
        if item.get("logs"):
            with st.expander("실행 로그"):
                st.code(item["logs"])
