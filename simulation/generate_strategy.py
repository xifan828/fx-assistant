from ai.agent import StrtegyAgent, KnowledgeBase
from datetime import datetime
import pandas as pd
import os 
import json
from openai import OpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser


def main(model_name, temperature):

    with open(r"D:\Projects\fx-assistant\simulation\test.txt", "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -> script ran. \n")

    # kb = KnowledgeBase()
    # economic_indicators = kb.get_economic_indicators()
    # print("Getting technical news")
    # technical_news = kb.get_technical_news()
    # #print(technical_news)
    # print("Getting technical analysis")
    # technical_analysis = kb.get_technical_analysis(is_local=True)
    # print("Getting central bank")
    # central_bank = kb.get_central_bank()

    # print("Agent starts answering.")
    # agent = StrtegyAgent(model_name=model_name, temperature=temperature)
    # model_name = agent.model_name
    # temperature = agent.temperature
    # response = agent.generate_strategy(economic_indicators=economic_indicators, technical_analysis=technical_analysis, technical_news=technical_news, central_bank=central_bank)
    # print(response)
    # try:
    #     response_dict = json.loads(response)
    # except json.JSONDecodeError as e:
    #     print(f"JSONDecodeError: {e}")
    #     response_clean = response.replace('\n', '\\n').replace('\r', '\\r')
    #     response_dict = json.loads(response_clean)
    # response_dict["time_generated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # response_dict["model"] = model_name
    # response_dict["temperature"] = temperature
    # df = pd.DataFrame([response_dict])

    # file_path = "simulation/trading_strategy.csv"
    # if os.path.exists(file_path):
    #     df.to_csv(file_path, mode='a', header=False, index=False)
    # else:
    #     df.to_csv(file_path, index=False)

if __name__ == "__main__":
    main("gpt-4o", 1.0)
