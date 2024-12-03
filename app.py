import streamlit as st
from ai.agent import FXAgent, KnowledgeBase
from PIL import Image
import os
from dotenv import load_dotenv



load_dotenv()
def check_email(email):
    allowed_emails = os.getenv("ALLOWED_EMAILS", "").split(',')
    return email.strip().lower() in [e.strip().lower() for e in allowed_emails]

def list_files_in_directory(directory):
    try:
        return os.listdir(directory)
    except FileNotFoundError:
        return []

def clear_session_states(keys):
    for key in keys:
        st.session_state.pop(key, None)

def main():

    st.markdown("# Foreign exchange trading assistant")
    st.caption("An assistant developed by Xifan Wang Email: xifan828@gmail.com")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        
    if "process_initialized" not in st.session_state:
        st.session_state["process_initialized"] = False

    with st.sidebar:
        auth_email_address = st.text_input("Email address", key="auth_email")
        authenticate = st.button("Authenticate")

    if authenticate:
        if check_email(auth_email_address):
            st.session_state["authenticated"] = True
            st.success("Authentication successful!")
        else:
            st.error("Authentication failed. Please check your email address.")

    if st.session_state["authenticated"]:
        
        # Model Selection
        model_choice = st.sidebar.selectbox(
            "Select Model",
            options=["gpt-4o", "gpt-4o-mini"],
            index=0
        )

        # Currency Pair Selection
        currency_pair = st.sidebar.selectbox(
            "Select Currency Pair",
            options=["EUR/USD", "USD/JPY"],
            index=0
        )

        run_process = st.sidebar.button("Run")
        if run_process or st.session_state["process_initialized"]:
            if run_process:
                st.session_state["process_initialized"] = True
    
                if "last_currency_pair" in st.session_state and st.session_state["last_currency_pair"] != currency_pair:
                    clear_session_states(["knowledge", "economic_indicators", "technical_news", "technical_analysis", "central_bank", "economic_events", "prefix_messages", "messages"])
                st.session_state["last_currency_pair"] = currency_pair

                if "last_model_choice" in st.session_state and st.session_state["last_model_choice"] != model_choice:
                    clear_session_states(["messages"])
                st.session_state["last_model_choice"] = model_choice

                if "knowledge" not in st.session_state:
                    knowledge_base = KnowledgeBase(currency_pair=st.session_state["last_currency_pair"])
                    knowledge = knowledge_base.get_all_data()
                    st.session_state["knowledge"] = knowledge

                if "economic_indicators" not in st.session_state:
                    st.session_state["economic_indicators"] = st.session_state["knowledge"]["Economic Indicators"]
                if "technical_news" not in st.session_state:
                    st.session_state["latest_news"] = st.session_state["knowledge"]["Technical News"]
                if "technical_analysis" not in st.session_state:
                    st.session_state["technical_analysis"] = st.session_state["knowledge"]["Technical Analysis"]
                if "central_bank" not in st.session_state:
                    st.session_state["central_bank"] = st.session_state["knowledge"]["Central Bank"]
                if "economic_events" not in st.session_state:
                    st.session_state["economic_events"] = st.session_state["knowledge"]["Economic Events"]
                    
            with st.expander("Economic Indicators"):
                st.write(st.session_state["economic_indicators"])
            with st.expander("Technical Analysis"):
                st.write(st.session_state["technical_analysis"])
            with st.expander("Latest News"):
                st.write(st.session_state["latest_news"])
            with st.expander("Central Bank"):
                st.write(st.session_state["central_bank"])
            with st.expander("Economic Calenders"):
                st.write(st.session_state["economic_events"])


            agent = FXAgent(model_name=st.session_state["last_model_choice"], currency_pair=st.session_state["last_currency_pair"])
            if "prefix_messages" not in st.session_state:
                st.session_state["prefix_messages"] = agent.formulate_first_round_messages(
                    st.session_state["economic_indicators"], 
                    st.session_state["technical_analysis"],
                    st.session_state["latest_news"],
                    st.session_state["central_bank"],
                    st.session_state["economic_events"]
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