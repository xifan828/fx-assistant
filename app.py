import streamlit as st
from ai.agent import FXAgent, KnowledgeBase
import json

kb = KnowledgeBase()
agent = FXAgent()
#st.title("EUR USD trading assistant")
st.markdown("# :euro: EUR / :dollar: USD trading assistant")
st.caption("An assistant developed by Xifan Wang")

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    auth_email_adress = st.text_input("Email account")

kb = KnowledgeBase()
agent = FXAgent()

if "economic_indicators" not in st.session_state:
    st.session_state["economic_indicators"] = json.dumps(kb.get_economic_indicators())
if "technical_analysis" not in st.session_state:
    st.session_state["technical_analysis"] = json.dumps(kb.get_technical_analysis())
if "technical_indicator" not in st.session_state:
    st.session_state["technical_indicator"] = kb.get_technical_indicators()
if "central_bank" not in st.session_state:
    st.session_state["central_bank"] = json.dumps(kb.get_central_bank())
    
with st.expander("Economic Indicators"):
    st.json(json.loads(st.session_state["economic_indicators"]))
with st.expander("Technical Analysis"):
    st.json(json.loads(st.session_state["technical_analysis"]))
with st.expander("Technical Indicators"):
    st.write(st.session_state["technical_indicator"])
with st.expander("Central Bank"):
    st.json(json.loads(st.session_state["central_bank"]))

if "prefix_messages" not in st.session_state:
    st.session_state["prefix_messages"] = agent.formulate_first_round_messages(
        st.session_state["economic_indicators"], 
        st.session_state["technical_analysis"],
        st.session_state["technical_indicator"],
        st.session_state["central_bank"]
    )
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hello, how may I help you?"},
    ]

for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = agent.chat_completions(st.session_state["prefix_messages"] + st.session_state["messages"])
    st.session_state["messages"].append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)


 

