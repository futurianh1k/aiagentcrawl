"""
Streamlit GUI for CalculatorAgent (LangChain v1.x / LangGraph)

Usage:
  streamlit run streamlit_app.py

Requirements:
- OPENAI_API_KEY in environment or .env
- langchain==1.2.0, langgraph==1.0.5, openai==2.x
"""

import io
from contextlib import redirect_stdout

import streamlit as st

# NOTE: 원본 lab1_basic_agent.py는 v0.x API(initialize_agent) 기준이라 ImportError가 발생합니다.
# 이 GUI는 수정본(lab1_basic_agent_fixed.py)을 import 합니다.
from lab1_basic_agent_fixed import CalculatorAgent, openai_api_key

st.set_page_config(page_title="Calculator Agent", page_icon="🧮")
st.title("🧮 LangChain/LangGraph Calculator Agent (Streamlit)")
st.markdown("간단한 수학 질의를 자연어로 입력하면 Agent가 Tool을 호출해 계산합니다.")

if not openai_api_key:
    st.warning("OPENAI_API_KEY가 설정되지 않았습니다. `.env` 또는 환경 변수에 키를 추가하세요.")
    st.stop()

if "agent" not in st.session_state:
    try:
        st.session_state.agent = CalculatorAgent(openai_api_key)
        # Agent에 전달할 히스토리(메시지)
        st.session_state.msg_history = []  # [{"role":"user"/"assistant","content":"..."}]
        # UI 출력용(로그 포함)
        st.session_state.ui_history = []   # [{"query":..., "response":..., "logs":...}]
    except Exception as e:
        st.error(f"Agent 초기화 실패: {e}")
        st.stop()

examples = [
    "3과 5를 더해줘",
    "10에 7을 곱한 결과는?",
    "100을 4로 나누면?",
    "((2 + 3) * 4) / 2 를 계산해줘",
]

query = st.text_input("질의 입력", value=examples[0], placeholder="예: 3과 4를 더해줘")

col_a, col_b = st.columns([1, 1])
with col_a:
    selected = st.selectbox("예제 선택", examples)
with col_b:
    if st.button("예제 적용"):
        query = selected
        st.session_state["_query_override"] = query

# Streamlit은 rerun 시 text_input의 value가 고정되므로 session_state로 덮어씀
if "_query_override" in st.session_state:
    st.session_state["_query_override"] = None

if st.button("실행") and query.strip():
    with st.spinner("Agent 실행 중..."):
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                response = st.session_state.agent.run(query, history=st.session_state.msg_history)
            logs = buf.getvalue()

            # 히스토리 업데이트
            st.session_state.msg_history.append({"role": "user", "content": query})
            st.session_state.msg_history.append({"role": "assistant", "content": response})

            st.session_state.ui_history.append({"query": query, "response": response, "logs": logs})
        except Exception as e:
            logs = buf.getvalue()
            st.session_state.ui_history.append({"query": query, "response": f"오류: {e}", "logs": logs})
            st.error(f"실행 중 오류: {e}")

if st.session_state.get("ui_history"):
    st.header("대화 기록")
    for item in reversed(st.session_state.ui_history):
        st.markdown(f"**질의:** {item['query']}")
        st.markdown(f"**응답:** {item['response']}")
        if item.get("logs"):
            with st.expander("실행 로그"):
                st.code(item["logs"])

with st.sidebar:
    st.subheader("유틸리티")
    if st.button("대화 초기화"):
        st.session_state.msg_history = []
        st.session_state.ui_history = []
        st.success("초기화 완료")
