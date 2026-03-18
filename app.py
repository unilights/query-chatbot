"""
app.py — Streamlit entry point for the Unilights Data Intelligence Chatbot.
Run with: streamlit run app.py
"""
import streamlit as st

from src.loaders.order_loader import load_all_data
from src.config import DATA_DIR

st.set_page_config(
    page_title="Unilights Data Intelligence MVP",
    page_icon="🤖",
    layout="wide",
)

st.title("Unilights Query Chatbot 🤖")
st.markdown("Ask me questions about the factory's inventory and order data based on the extracted Excel sheets!")

# ── Session state initialisation ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am ready to answer questions about the Unilights data. What would you like to know?",
            "reasoning": "",
        }
    ]
if "agent" not in st.session_state:
    st.session_state.agent = None


# ── Data loading (cached) ─────────────────────────────────────────────────────
@st.cache_data
def load_data():
    return load_all_data(str(DATA_DIR))


with st.spinner("Loading Excel Data into Memory..."):
    df_dict = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📊 Loaded Data Sheets")
    for name, df in df_dict.items():
        st.markdown(f"- **{name}** ({len(df)} rows)")

# ── Chat history ──────────────────────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("reasoning"):
            with st.expander("🔍 Agent Reasoning (click to expand)"):
                st.code(message["reasoning"], language="text")

# ── User input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("E.g., How many HBRR150 units are currently in the Mech Store?"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt, "reasoning": ""})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        reasoning_log = ""

        try:
            if st.session_state.agent is None:
                with st.spinner("⚙️ Initializing Claude Data Agent for the first time..."):
                    from src.agent.client import create_agent
                    st.session_state.agent = create_agent()

            with st.spinner("🧠 Claude is analyzing the data..."):
                from src.agent.client import query_agent
                full_response, reasoning_log = query_agent(st.session_state.agent, prompt)

        except Exception as e:
            full_response = f"❌ Agent Error: {e}"

        message_placeholder.markdown(full_response)
        if reasoning_log:
            with st.expander("🔍 Agent Reasoning (click to expand)"):
                st.code(reasoning_log, language="text")

    st.session_state.messages.append({
        "role":      "assistant",
        "content":   full_response,
        "reasoning": reasoning_log,
    })
