import streamlit as st

from backend.agent import FXAgent, KnowledgeBase
from PIL import Image
#from st.chat_message import message
import os
import numpy as np
from dotenv import load_dotenv
import datetime

st.set_page_config(layout="centered")

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
                    clear_session_states(["knowledge", "news", "technical_analysis", "risk_sentiment", "prefix_messages", "messages"])
                st.session_state["last_currency_pair"] = currency_pair

                if "last_model_choice" in st.session_state and st.session_state["last_model_choice"] != model_choice:
                    clear_session_states(["messages"])
                st.session_state["last_model_choice"] = model_choice

                if "knowledge" not in st.session_state:
                    knowledge_base = KnowledgeBase(currency_pair=st.session_state["last_currency_pair"])
                    knowledge = knowledge_base.create_all_analysis_parallel()
                    st.session_state["knowledge"] = knowledge

                if "news" not in st.session_state:
                    st.session_state["news"] = st.session_state["knowledge"]["News Analysis"]
                    #st.session_state["news"] = "None"
                if "technical_analysis" not in st.session_state:
                    st.session_state["technical_analysis"] = st.session_state["knowledge"]["Technical Analysis"]
                    #st.session_state["technical_analysis"] = "None"
                if "risk_sentiment" not in st.session_state:
                    st.session_state["risk_sentiment"] = st.session_state["knowledge"]["Risk Sentiment"]

            with st.container():
                st.title(currency_pair)
                st.image("data/chart/1h_ema.png")
                # tab1, tab2= st.tabs(["5 minutes", "1 Hour"])
                # with tab1:
                #     st.image("data/chart/5min.png")
                # with tab2:
                #     st.image("data/chart/1h.png")
                st.write("Last updated: ", datetime.datetime.now())
            st.divider()

            agent = FXAgent(model_name=st.session_state["last_model_choice"], currency_pair=st.session_state["last_currency_pair"])
            if "prefix_messages" not in st.session_state:
                st.session_state["prefix_messages"] = agent.formulate_first_round_messages(
                    st.session_state["news"], 
                    st.session_state["technical_analysis"],
                    st.session_state["risk_sentiment"]
                )
            if "messages" not in st.session_state:
                st.session_state["messages"] = [
                    {"role": "assistant", "content": "Hello, how may I help you?"},
                ]
            if "strategy" not in st.session_state:
                    st.session_state["strategy"] = []
            
            @st.dialog("Customise Strategy")
            def customise():
                
                totalWeight = 0

                interest = st.checkbox("Interest Rate")
                if interest:
                    interestSl = st.slider("Interest Rate", min_value=0, max_value=100, label_visibility="collapsed")
                    totalWeight += interestSl
                technical = st.checkbox("Technical Analysis")
                if technical:
                    technicalSl = st.slider("Technical Analysis", min_value=0, max_value=100, label_visibility="collapsed")
                    totalWeight += technicalSl
                dxy = st.checkbox("DXY Chart")
                if dxy:
                    dxySl = st.slider("DXY Chart", min_value=0, max_value=100, label_visibility="collapsed")
                    totalWeight += dxySl
                seasonality = st.checkbox("Seasonality")
                if seasonality:
                    seasonalitySl = st.slider("Seasonality", min_value=0, max_value=100, label_visibility="collapsed")
                    totalWeight += seasonalitySl
                fundamentals = st.checkbox("Fundamentals")
                if fundamentals:
                    fundamentalsSl = st.slider("Fundamentals", min_value=0, max_value=100, label_visibility="collapsed")
                    totalWeight += fundamentalsSl
                
                st.write("Total weight: ", totalWeight)
                if totalWeight <= 100 and totalWeight > 0:
                    st.button("Generate Strategy", use_container_width=True)

            @st.dialog("Full Analysis")
            def analysis():
                st.write(st.session_state["risk_sentiment"])


            with st.container():
                st.title("Market at a Glance")
                st.write(st.session_state["news"])
            st.divider()
            with st.container():
                st.title("Strategy Highlight")
                st.write(st.session_state["technical_analysis"])
                if "customise" not in st.session_state:
                    if st.button("Customise Strategy", use_container_width=True):
                        customise()
            st.divider()
            with st.container():
                st.write(st.session_state["risk_sentiment"])
                if "analysis" not in st.session_state:
                    if st.button("View Full Analysis", use_container_width=True):
                        analysis()

        else:
            st.warning("Please authenticate to access the application.")

if __name__ == "__main__":
    main()