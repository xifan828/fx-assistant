from ai.agent import NaiveStrategyAgent, KnowledgeBase
from datetime import datetime
from dotenv import load_dotenv
import os
import pandas as pd
import pytz
import re
import json
from ai.service.technical_analysis import TechnicalAnalysis
import asyncio


def generate_trading_strategy(file_path: str, currency_pair: str):
    load_dotenv()
    kb = KnowledgeBase(currency_pair=currency_pair)
    Knowledge = kb.get_partial_data()

    #providers = ["openai", "google"]
    providers =["openai"]

    for provider in providers:
        if provider == "openai":
            model_name = "gpt-4o"
        else:
            model_name = "gemini-2.0-flash-exp"
        agent = NaiveStrategyAgent(knowledge=Knowledge, provider=provider, model_name=model_name, temperature=0.5, currency_pair=currency_pair )
        response = agent.generate_strategy()
        thinking_steps = response.steps
        reasoning = "\n".join([step.analysis for step in thinking_steps])
        response_dict = dict(response.final_strategy)
        response_dict["rationale"] = reasoning + response_dict["rationale"] 

        berlin_tz = pytz.timezone("Europe/Berlin")
        timestamp = datetime.today().astimezone(berlin_tz).replace(microsecond=0)
        #response_dict["timestamp"] = timestamp
        response_dict["status"] = "pending"
        response_dict["provider"] = provider
        for filed in ["take_profit_custom", "stop_loss_custom", "price_at_order", "entry_time", "entry_price", "close_time", "close_price", "profit"]:
            response_dict[filed] = None

        new_strategy = pd.DataFrame([response_dict])
        new_strategy["order_time"] = timestamp

        file_exists = os.path.isfile(file_path)

        if file_exists:
            old_strategy = pd.read_csv(file_path, parse_dates=["order_time"])
            try:
                old_strategy["order_time"] = pd.to_datetime(old_strategy["order_time"]).dt.tz_convert("Europe/Berlin")
            except:
                old_strategy["order_time"] = pd.to_datetime(old_strategy["order_time"]).dt.tz_localize("Europe/Berlin")
            new_strategy = pd.concat([old_strategy, new_strategy], axis=0)

        new_strategy.to_csv(file_path, index=False)

def generate_trading_strategy_new(file_path: str, currency_pair: str):
    load_dotenv()
    kb = KnowledgeBase(currency_pair=currency_pair)
    kb.prepare_figures()
    
    ta = TechnicalAnalysis(
        currency_pair=currency_pair,
        #currency_pair="USD/JPY",
    )

    ta_analysis = asyncio.run(ta.run())
    summary = ta_analysis["summary"]
    strategy = ta_analysis["strategy"]

    match = re.search(r"```json(.*?)```", strategy, re.DOTALL)
    if match:
        json_string = match.group(1).strip()
        strategy = json.loads(json_string)
    else:
        strategy = {
            "strategy": "Match failed",
            "entry_point": None,
            "stop_loss": None,
            "take_profit": None
        }
    
    strategy["rationale"] = summary
    strategy["provider"] = "google"
    berlin_tz = pytz.timezone("Europe/Berlin")
    timestamp = datetime.today().astimezone(berlin_tz).replace(microsecond=0)
    strategy["status"] = "pending"

    for filed in ["take_profit_custom", "stop_loss_custom", "price_at_order", "entry_time", "entry_price", "close_time", "close_price", "profit"]:
        strategy[filed] = None

    new_strategy = pd.DataFrame([strategy])
    new_strategy["order_time"] = timestamp

    file_exists = os.path.isfile(file_path)
    if file_exists:
        old_strategy = pd.read_csv(file_path, parse_dates=["order_time"])
        try:
            old_strategy["order_time"] = pd.to_datetime(old_strategy["order_time"]).dt.tz_convert("Europe/Berlin")
        except:
            old_strategy["order_time"] = pd.to_datetime(old_strategy["order_time"]).dt.tz_localize("Europe/Berlin")
        new_strategy = pd.concat([old_strategy, new_strategy], axis=0)

    new_strategy.to_csv(file_path, index=False)

    return


if __name__ == "__main__":
    generate_trading_strategy_new(r"simulation\2025_01_06\trading_strategy.csv", "EUR/USD")
