import pandas as pd
import streamlit as st
from agent import ask_agent

st.set_page_config(page_title="Data Analyst Agent", page_icon="📊", layout="wide")

st.title("📊 Data Analyst Agent")
st.caption("Upload a CSV and ask questions in plain English. The agent writes the analysis for you.")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("1. Your data")
    uploaded = st.file_uploader("Upload a CSV file", type="csv")

    st.header("2. Try asking")
    examples = [
        "Summarize this dataset.",
        "What columns do I have and what do they mean?",
        "Which category has the highest total? Show a chart.",
    ]
    clicked = None
    for q in examples:
        if st.button(q, use_container_width=True):
            clicked = q

# ---------- LOAD DATA ----------
if uploaded:
    df = pd.read_csv(uploaded, encoding="latin-1")
    source = uploaded.name
else:
    df = pd.read_csv("data.csv", encoding="latin-1")
    source = "sample data (data.csv)"

# start a fresh chat when the file changes
if st.session_state.get("source") != source:
    st.session_state.source = source
    st.session_state.messages = []

st.success(f"Using: {source} — {df.shape[0]} rows, {df.shape[1]} columns")
with st.expander("Preview the data"):
    st.dataframe(df.head(50), use_container_width=True)


# ---------- CHAT ----------
def show_message(m):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        for chart in m.get("charts", []):
            st.caption(chart["title"])
            st.bar_chart(chart["data"])
        if m.get("steps"):
            with st.expander("How the agent got this answer"):
                for i, s in enumerate(m["steps"], 1):
                    st.code(f"Step {i}: {s}")


for m in st.session_state.messages:
    show_message(m)

prompt = st.chat_input("Ask a question about your data...") or clicked

if prompt:
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)
    show_message(user_msg)

    with st.spinner("Analyzing your data..."):
        try:
            result = ask_agent(df, prompt)
            reply = {
                "role": "assistant",
                "content": result["answer"],
                "charts": result["charts"],
                "steps": result["steps"],
            }
        except Exception as e:
            reply = {"role": "assistant", "content": f"Something went wrong: {e}"}

    st.session_state.messages.append(reply)
    show_message(reply)