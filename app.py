import streamlit as st
from ai.agent import FXAgent, KnowledgeBase

import os
from dotenv import load_dotenv



load_dotenv()
def check_email(email):
    allowed_emails = os.getenv("ALLOWED_EMAILS", "").split(',')
    return email.strip().lower() in [e.strip().lower() for e in allowed_emails]

def main():

    st.markdown("# :euro: EUR / :dollar: USD trading assistant")
    st.caption("An assistant developed by Xifan Wang")

    with st.sidebar:
        auth_email_address = st.text_input("Email address", key="auth_email")
        authenticate = st.button("Authenticate")

    if authenticate:
        if check_email(auth_email_address):
            st.session_state["authenticated"] = True
            st.success("Authentication successful!")
        else:
            st.error("Authentication failed. Please check your email address.")

    if "authenticated" in st.session_state and st.session_state["authenticated"]:
        # Main app logic goes here
        with st.sidebar:
            openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

        kb = KnowledgeBase()
        agent = FXAgent()

        if "economic_indicators" not in st.session_state:
            st.session_state["economic_indicators"] = kb.get_economic_indicators()
        if "technical_news" not in st.session_state:
            st.session_state["technical_news"] = kb.get_technical_news()
        if "technical_analysis" not in st.session_state:
            st.session_state["technical_analysis"] = kb.get_technical_analysis()
        if "central_bank" not in st.session_state:
            st.session_state["central_bank"] = kb.get_central_bank()
        
        with st.expander("Economic Indicators"):
            st.write(st.session_state["economic_indicators"])
        with st.expander("Technical Analysis"):
            st.write(st.session_state["technical_analysis"])
        with st.expander("Technical News"):
            st.write(st.session_state["technical_news"])
        with st.expander("Central Bank"):
            st.write(st.session_state["central_bank"])

        if "prefix_messages" not in st.session_state:
            st.session_state["prefix_messages"] = agent.formulate_first_round_messages(
                st.session_state["economic_indicators"], 
                st.session_state["technical_analysis"],
                st.session_state["technical_news"],
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
    else:
        st.warning("Please authenticate to access the application.")

if __name__ == "__main__":
    main()