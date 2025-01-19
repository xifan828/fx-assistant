from ai.agent import NaiveStrategyAgent, KnowledgeBase
from datetime import datetime
from dotenv import load_dotenv
import os
import pandas as pd
import pytz
import re
import json
from ai.service.technical_analysis import TechnicalAnalysis
from ai.service.technical_indicators import TechnicalIndicators
import asyncio
from datetime import datetime
import time 


# def generate_trading_strategy(file_path: str, currency_pair: str):
#     load_dotenv()
#     kb = KnowledgeBase(currency_pair=currency_pair)
#     Knowledge = kb.get_partial_data()

#     #providers = ["openai", "google"]
#     providers =["openai"]

#     for provider in providers:
#         if provider == "openai":
#             model_name = "gpt-4o"
#         else:
#             model_name = "gemini-2.0-flash-exp"
#         agent = NaiveStrategyAgent(knowledge=Knowledge, provider=provider, model_name=model_name, temperature=0.5, currency_pair=currency_pair )
#         response = agent.generate_strategy()
#         thinking_steps = response.steps
#         reasoning = "\n".join([step.analysis for step in thinking_steps])
#         response_dict = dict(response.final_strategy)
#         response_dict["rationale"] = reasoning + response_dict["rationale"] 

#         berlin_tz = pytz.timezone("Europe/Berlin")
#         timestamp = datetime.today().astimezone(berlin_tz).replace(microsecond=0)
#         #response_dict["timestamp"] = timestamp
#         response_dict["status"] = "pending"
#         response_dict["provider"] = provider
#         for filed in ["take_profit_custom", "stop_loss_custom", "price_at_order", "entry_time", "entry_price", "close_time", "close_price", "profit"]:
#             response_dict[filed] = None

#         new_strategy = pd.DataFrame([response_dict])
#         new_strategy["order_time"] = timestamp

#         file_exists = os.path.isfile(file_path)

#         if file_exists:
#             old_strategy = pd.read_csv(file_path, parse_dates=["order_time"])
#             try:
#                 old_strategy["order_time"] = pd.to_datetime(old_strategy["order_time"]).dt.tz_convert("Europe/Berlin")
#             except:
#                 old_strategy["order_time"] = pd.to_datetime(old_strategy["order_time"]).dt.tz_localize("Europe/Berlin")
#             new_strategy = pd.concat([old_strategy, new_strategy], axis=0)

#         new_strategy.to_csv(file_path, index=False)

async def generate_trading_strategy_new(file_path: str, currency_pair: str, gemini_model: str):
    kb = KnowledgeBase(currency_pair=currency_pair)
    kb.prepare_figures()
    TA = TechnicalAnalysis(currency_pair=currency_pair, gemini_model=gemini_model, gemini_api_key=os.environ["GEMINI_API_KEY_KIEN"])
    results = await TA.extract_technical_indicators_with_gemini()
    technical_indicators, _  = results[0]
    TI = TechnicalIndicators(currency_pair=currency_pair, interval="1min", outputsize=200)
    data = TI.download_data()
    current_price = data.iloc[-1]["Close"]

    coroutines = []
    for api_key in [os.environ["GEMINI_API_KEY_KIEN"], os.environ["GEMINI_API_KEY_CONG"], os.environ["GEMINI_API_KEY_XIFAN"]]:
        TA = TechnicalAnalysis(currency_pair=currency_pair, gemini_model=gemini_model, gemini_api_key=api_key)
        coroutines.append(TA.create_gemini_analysis(
            pivot_points=technical_indicators,
            current_price=current_price
        ))
    results = await asyncio.gather(*coroutines)
    print("strategy generated")

    berlin_tz = pytz.timezone("Europe/Berlin")
    timestamp = datetime.today().astimezone(berlin_tz).replace(microsecond=0)
    for analysis in results:
        strategy = analysis["strategy"]
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
        save_strategy_to_file(file_path, timestamp, strategy)
    print("strategy saved")
    return


def find_working_days(start, end):
    all_days = pd.date_range(start=start, end=end)
    working_days = all_days[~all_days.weekday.isin([5, 6])]  # Exclude weekends (Saturday, Sunday)
    working_days_str = [day.strftime("%Y-%m-%d") for day in working_days]

    return working_days_str

def generate_strategy_time(days):
    times = []
    for day in days:
        for hour_time in ["05:00:00", "09:00:00", "13:00:00", "17:00:00"]:
            times.append(day + " " + hour_time)
    return times

def save_strategy_to_file(file_path, hour, strategy):
    # Define the header and extract values
    header = ["time", "strategy", "entry_point", "stop_loss", "take_profit"]
    row = [
        hour,
        strategy.get("strategy", ""),
        strategy.get("entry_point", ""),
        strategy.get("stop_loss", ""),
        strategy.get("take_profit", "")
    ]
    
    # Check if the file exists
    file_exists = os.path.isfile(file_path)
    
    # Open the file in append mode
    with open(file_path, "a") as file:
        if not file_exists:
            # Write header if the file does not exist
            file.write(",".join(header) + "\n")
        # Write the data row
        file.write(",".join(map(str, row)) + "\n")

async def generate_back_test_strategies(start_date, end_date, currency_pair, file_path, gemini_model):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    working_days = find_working_days(start, end)
    hours = generate_strategy_time(working_days)
    total = len(hours)

    for i, hour in enumerate(hours, start=1):
        print(f"{i}: Start generating for {hour}")
        for interval in ["1h", "5min"]:
            TI = TechnicalIndicators(
                currency_pair=currency_pair,
                interval=interval,
                outputsize=200,
                end_date=hour
            )
            data = TI.download_data()
            data = data.iloc[:-1]
            data = TI.calculate_technical_indicators(data)
            TI.plot_chart(data)
            TI.crop_image()
            if interval == "5min":
                current_price = data.iloc[-1]["Close"]

        coroutines = []
        for api_key in [os.environ["GEMINI_API_KEY_KIEN"], os.environ["GEMINI_API_KEY_CONG"], os.environ["GEMINI_API_KEY_XIFAN"]]:
            TA = TechnicalAnalysis(currency_pair=currency_pair, gemini_model=gemini_model, gemini_api_key=api_key)
            coroutines.append(TA.create_gemini_analysis(
                pivot_points="Pivot points are not provided.",
                current_price=current_price
            ))

        results = await asyncio.gather(*coroutines)

        for analysis in results:
            strategy = analysis["strategy"]
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
            save_strategy_to_file(file_path, hour, strategy)
            
        time.sleep(60)
        print(f"{i}: Complete generating for {hour}. {total - i} timestamps left.")


if __name__ == "__main__":
    #generate_trading_strategy_new(r"simulation\2025_01_06\trading_strategy.csv", "EUR/USD")
    begin = time.time()
    start_date = "2024-11-29"
    end_date = "2024-11-29"
    currency_pair = "EUR/USD"
    currency_name = "EUR_USD"
    gemini_model = "gemini-2.0-flash-exp"
    #gemini_model = "gemini-exp-1206"
    file_path = f"simulation/back_test/2024_11/{currency_name}.csv"
    asyncio.run(generate_back_test_strategies(start_date, end_date, currency_pair, file_path, gemini_model))
    end = time.time()

    print(f"Used {end - begin} seconds.")
    #print([os.environ["GEMINI_API_KEY_KIEN"], os.environ["GEMINI_API_KEY_CONG"], os.environ["GEMINI_API_KEY_XIFAN"]])