import streamlit as st

from backend.agent import FXAgent, KnowledgeBase
import io
#from st.chat_message import message
import os
import numpy as np
from dotenv import load_dotenv
import asyncio


st.set_page_config(layout = "wide")

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
        st.text_input("Password", type="password")
        authenticate = st.button("Authenticate")

    if authenticate:
        if check_email(auth_email_address):
            st.session_state["authenticated"] = True
            st.success("Authentication successful!")
        else:
            st.error("Authentication failed. Please check your email address.")

    if st.session_state["authenticated"]:
        # Choices of Currency Pairs
        currencyOptions = ["EUR/USD", "USD/JPY", "GBP/USD", "USD/CNH"]
        
        # Model Selection
        model_choice = st.sidebar.selectbox(
            "Select Model",
            options=["gpt-4o", "gpt-4o-mini"],
            index=0
        )

        # Currency Pair Selection
        currency_pair = st.sidebar.selectbox(
            "Select Currency Pair",
            options=currencyOptions,
            index=0
        )

        run_process = st.sidebar.button("Live Market Update")
        if run_process or st.session_state["process_initialized"]:
            if run_process:
                st.session_state["process_initialized"] = True
    
                if "last_currency_pair" in st.session_state and st.session_state["last_currency_pair"] != currency_pair:
                    clear_session_states(["knowledge", "news", "technical_analysis", "risk_sentiment", "prefix_messages", "messages", "charts_data", "fundamental_analysis", "fed_watch"])
                st.session_state["last_currency_pair"] = currency_pair

                if "last_model_choice" in st.session_state and st.session_state["last_model_choice"] != model_choice:
                    clear_session_states(["messages"])
                st.session_state["last_model_choice"] = model_choice

                if "knowledge" not in st.session_state:
                    knowledge_base = KnowledgeBase(currency_pair=st.session_state["last_currency_pair"])
                    knowledge = asyncio.run(knowledge_base.get_all_synthesis())
                    st.session_state["knowledge"] = knowledge

                if "news" not in st.session_state:
                    st.session_state["news"] = st.session_state["knowledge"]["News Analysis"]
                    #st.session_state["news"] = "None"
                if "technical_analysis" not in st.session_state:
                    st.session_state["technical_analysis"] = st.session_state["knowledge"]["Technical Analysis"]
                    #st.session_state["technical_analysis"] = "None"
                if "charts_data" not in st.session_state:
                    st.session_state["charts_data"] = st.session_state["knowledge"]["Charts data"]
                if "risk_sentiment" not in st.session_state:
                    st.session_state["risk_sentiment"] = st.session_state["knowledge"]["Risk Sentiment"]
                if "fundamental_analysis" not in st.session_state:
                    st.session_state["fundamental_analysis"] = st.session_state["knowledge"]["Fundamental Analysis"]
                if "fed_watch" not in st.session_state:
                    st.session_state["fed_watch"] = st.session_state["knowledge"]["Fed Watch"]
                    
            chart, chat = st.columns(2)
            with chart:
                with st.container(height=350, border=True):
                    st.image(io.BytesIO(st.session_state["charts_data"]["normal"]), caption=st.session_state["last_currency_pair"], use_column_width=True)
                    # tab1, tab2= st.tabs(["5 minutes", "1 Hour"])
                    # with tab1:
                    #     st.image("data/chart/5min.png")
                    # with tab2:
                    #     st.image("data/chart/1h.png")

            agent = FXAgent(model_name=st.session_state["last_model_choice"], currency_pair=st.session_state["last_currency_pair"])
            if "prefix_messages" not in st.session_state:
                st.session_state["prefix_messages"] = agent.formulate_first_round_messages(
                    st.session_state["news"], 
                    st.session_state["technical_analysis"],
                    st.session_state["risk_sentiment"]
                    #st.session_state["risk_sentiment"]
                )
            if "messages" not in st.session_state:
                st.session_state["messages"] = [
                    {"role": "assistant", "content": "Hello, how may I help you?"},
                ]
            if "strategy" not in st.session_state:
                    st.session_state["strategy"] = []

            with chat:
                with st.container(height=350):
                    st.html("<div style='text-align: center; font-size: 35px'><b> Ask a question </b></div>")
                    msgs = st.container(height=190, border=False)

                    if prompt := st.chat_input():
                        with msgs:
                            st.session_state["messages"].append({"role": "user", "content": prompt})
                            message = st.chat_message("user")
                            message.write(prompt)
                            #st.chat_message(prompt, is_user=True)
                            response = agent.chat_completions(st.session_state["prefix_messages"] + st.session_state["messages"])
                            st.session_state["messages"].append({"role": "assistant", "content": response})
                            message = st.chat_message("assistant")
                            message.write(response)
                            #st.chat_message(response)


            with st.container():
                tab1, tab2, tab3, tab4, tab5 = st.tabs(
                    [
                    "Risk sentiment",
                    "Technical Analysis",
                    "Latest News",
                    "Fundamental Analysis",
                    "Fed Watch"
                    ]
                )

                with tab1:
                    st.write(st.session_state["risk_sentiment"])
                with tab2:
                    st.write(st.session_state["technical_analysis"])
                with tab3:
                    st.write(st.session_state["news"])
                with tab4:
                    st.write(st.session_state["fundamental_analysis"])
                with tab5:
                    st.write(st.session_state["fed_watch"])

        else:
            st.warning("Please authenticate to access the application.")

if __name__ == "__main__":
    main()