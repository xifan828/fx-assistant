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

        # technical_indicators_directory = "data/technical_indicators"
        # files = list_files_in_directory(technical_indicators_directory)
        # st.sidebar.markdown("### Technical Indicators Files")
        # if files:
        #     for file in files:
        #         st.sidebar.write(file)
        # else:
        #     st.sidebar.write("No files found in the directory.")

        agent = FXAgent()
        if "knowledge" not in st.session_state:
            knowledge_base = KnowledgeBase()
            knowledge = knowledge_base.get_all_data(is_local=False)
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

        # technical_indicators_directory = "data/technical_indicators"
        # files = list_files_in_directory(technical_indicators_directory)
        # for file_name in files:
        #     file_path = technical_indicators_directory + "/" + file_name
        #     if os.path.exists(file_path):
        #         image = Image.open(file_path)
        #         st.image(image, caption='Sample Image', use_column_width=True)
        #     else:
        #         st.sidebar.write("Image file not found.")
            
        with st.expander("Economic Indicators"):
            st.write(st.session_state["economic_indicators"])
        with st.expander("Technical Analysis"):
            st.write(st.session_state["technical_analysis"])
        with st.expander("Latest News"):
            st.write(st.session_state["latest_news"])
        with st.expander("Central Bank"):
            st.write(st.session_state["central_bank"])
        with st.expander("Economic Events"):
            st.write(st.session_state["economic_events"])

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