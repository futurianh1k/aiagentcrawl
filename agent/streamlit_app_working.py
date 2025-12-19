"""
Streamlit UI for the working Calculator Agent.

This app is resilient: if no OpenAI integration is available it still works
using a safe local evaluator for arithmetic expressions.
"""

import io
from contextlib import redirect_stdout
import streamlit as st

from lab1_basic_agent_working import CalculatorAgent, openai_api_key

st.set_page_config(page_title="Calculator Agent (working)", page_icon="🧮")
st.title("🧮 Calculator Agent (robust)")

st.markdown("간단한 수학 질의를 자연어로 입력하면 Agent가 계산합니다. (로컬 fallback 포함)")

if "agent" not in st.session_state:
    st.session_state.agent = CalculatorAgent(openai_api_key)
    st.session_state.history = []

examples = [
    "3과 5를 더해줘",
    "10에 7을 곱한 결과는?",
    "100을 4로 나누면?",
    "((2 + 3) * 4) / 2 를 계산해줘",
]

query = st.text_input("질의 입력", value=examples[0], placeholder="예: 3과 4를 더해줘")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("실행") and query.strip():
        with st.spinner("Agent 실행 중..."):
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    response = st.session_state.agent.run(query)
                logs = buf.getvalue()
                st.session_state.history.append({"query": query, "response": response, "logs": logs})
            except Exception as e:
                logs = buf.getvalue()
                st.session_state.history.append({"query": query, "response": f"오류: {e}", "logs": logs})
                st.error(f"실행 중 오류: {e}")
with col2:
    if st.button("예제 실행"):
        q = st.selectbox("예제", examples)
        if q:
            with st.spinner("Agent 실행 중..."):
                st.session_state.history.append({"query": q, "response": st.session_state.agent.run(q), "logs": ""})

if st.session_state.history:
    st.header("대화 기록")
    for item in reversed(st.session_state.history):
        st.markdown(f"**질의:** {item['query']}")
        st.markdown(f"**응답:** {item['response']}")
        if item.get("logs"):
            with st.expander("실행 로그"):
                st.code(item["logs"])