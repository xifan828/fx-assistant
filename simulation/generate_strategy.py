from backend.agent import NaiveStrategyAgent, KnowledgeBase
from datetime import datetime
from dotenv import load_dotenv
import os
import pandas as pd
import pytz
import re
import json
from backend.service.technical_analysis import TechnicalAnalysis
from backend.service.data_collection import TechnicalIndicators
import asyncio
from datetime import datetime
import time 
import shutil

async def generate_trading_strategy_new(root_path: str, currency_pair: str, gemini_model: str):
    # prepare file and dir paths
    today_day = datetime.today().day
    today_hour = datetime.now().hour
    if currency_pair == "EUR/USD":
        decimal_points = 4
        strategy_file_path = os.path.join(root_path, "EUR_USD.csv")
        agg_strategy_file_path = os.path.join(root_path, "EUR_USD_agg.csv")
        analysis_dir_path = os.path.join(root_path, str(today_day), "EUR_USD")
    else:
        decimal_points = 2
        strategy_file_path = os.path.join(root_path, "USD_JPY.csv")
        agg_strategy_file_path = os.path.join(root_path, "USD_JPY_agg.csv")
        analysis_dir_path = os.path.join(root_path, str(today_day), "USD_JPY")
    os.makedirs(analysis_dir_path, exist_ok=True)
    analysis_file_path = os.path.join(analysis_dir_path, f"{today_hour}.json")

    # prepare charts, pivot points, current price
    kb = KnowledgeBase(currency_pair=currency_pair)
    latest_data_1h, latest_data_5min = kb.prepare_figures()

    current_price = latest_data_5min["Close"].round(decimal_points)
    print(current_price)

    save_chart(analysis_dir_path, today_hour)

    TA = TechnicalAnalysis(currency_pair=currency_pair, gemini_model=gemini_model, gemini_api_key=os.environ["GEMINI_API_KEY_KIEN"])
    results = await TA.extract_technical_indicators_with_gemini()
    technical_indicators, _  = results[0]
    
    # generate analysis
    coroutines = []
    for api_key in [os.environ["GEMINI_API_KEY_KIEN"], os.environ["GEMINI_API_KEY_CONG"], os.environ["GEMINI_API_KEY_XIFAN"]]:
   
        TA = TechnicalAnalysis(currency_pair=currency_pair, gemini_model=gemini_model, gemini_api_key=api_key)
        coroutines.append(TA.create_gemini_analysis(
            pivot_points=technical_indicators,
            current_price=current_price
        ))
    results = await asyncio.gather(*coroutines)
    print("Analysis generated")
    save_analysis_to_json(results, analysis_file_path)
    print("Analysis saved")

    # extract strategy
    berlin_tz = pytz.timezone("Europe/Berlin")
    timestamp = datetime.today().astimezone(berlin_tz).replace(microsecond=0)
    strategies = []
    for analysis in results:
        strategy = analysis["strategy"]
        match = re.search(r"```json(.*?)```", strategy, re.DOTALL)
        if match:
            json_string = match.group(1).strip()
            strategy = json.loads(json_string)
        else:
            strategy = {
                "strategy": "Match failed",
                "order_type": None,
                "entry_point": None,
                "stop_loss": None,
                "take_profit": None
            }
        strategies.append(strategy)
        save_strategy_to_file(strategy_file_path, timestamp, strategy)
    print("strategy saved")

    # aggregate strategy
    agg_strategy = aggregate_strategies(strategies, currency_pair)
    order_type = "LMT"
    if agg_strategy["strategy"] == "buy": 
        if agg_strategy["entry_point"] > current_price:
            order_type = "STP"
    elif agg_strategy["strategy"] == "sell": 
        if agg_strategy["entry_point"] < current_price:
            order_type = "STP"
    else:
        order_type = None
    agg_strategy["order_type"] = order_type
    save_strategy_to_file(agg_strategy_file_path, timestamp, agg_strategy)
    print("Aggregated strategy saved")
    return agg_strategy

def aggregate_strategies(strategies, currency_pair):
    round_decimal = 4 if currency_pair == "EUR/USD" else 2
    group = pd.DataFrame(strategies)
    threshold = (len(group) // 2) + 1
    #threshold = len(group)
    if sum(group["strategy"] == "buy") >= threshold:
        strategy = "buy"
    # elif sum(group["strategy"] == "buy") == threshold and sum(group["strategy"] == "wait") >= 1:
    #     strategy = "buy"
    elif sum(group["strategy"] == "sell") >= threshold:
        strategy = "sell"
    # elif sum(group["strategy"] == "sell") == threshold and sum(group["strategy"] == "wait") >= 1:
    #     strategy = "sell"
    else:
        strategy = "wait"
    if strategy != "wait":
        entry_point = round(group.loc[group["strategy"] == strategy, "entry_point"].mean(), round_decimal)
        stop_loss = round(group.loc[group["strategy"] == strategy, "stop_loss"].mean(), round_decimal)
        take_profit = round(group.loc[group["strategy"] == strategy, "take_profit"].mean(), round_decimal)
    else:
        entry_point, stop_loss, take_profit = None, None, None
    return {"strategy": strategy, "entry_point": entry_point, "stop_loss": stop_loss, "take_profit": take_profit}



def find_working_days(start, end):
    all_days = pd.date_range(start=start, end=end)
    working_days = all_days[~all_days.weekday.isin([5, 6])]  # Exclude weekends (Saturday, Sunday)
    working_days_str = [day.strftime("%Y-%m-%d") for day in working_days]

    return working_days_str

def generate_strategy_time(days):
    times = []
    for day in days:
        for hour_time in ["02:00:00", "03:00:00", "04:00:00", "05:00:00", "06:00:00", "07:00:00", "08:00:00", "09:00:00", "10:00:00", "11:00:00", "12:00:00", "13:00:00", "14:00:00", "15:00:00", "16:00:00", "17:00:00", "18:00:00"]:
            times.append(day + " " + hour_time)
    return times

def save_strategy_to_file(file_path, hour, strategy):
    # Define the header and extract values
    header = ["time", "strategy", "order_type", "entry_point", "stop_loss", "take_profit"]
    row = [
        hour,
        strategy.get("strategy", ""),
        strategy.get("order_type", ""),
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

def save_analysis_to_json(analysis: list, file_path: str):
    file_root = file_path.split("\\")
    with open(file_path, "w") as f:
        json.dump(analysis, f, indent=4)

def save_chart(dst_dir: str, hour: str, src_dir: str = r"data\chart"):
    for file in os.listdir(src_dir):
        if file.endswith(".png"):
            src_file = os.path.join(src_dir, file)
            dst_file = os.path.join(dst_dir, f"{hour}_" + file)
            shutil.copy(src_file, dst_file)

async def generate_back_test_strategies(start_date, end_date, currency_pair, file_path, gemini_model):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    working_days = find_working_days(start, end)
    hours = generate_strategy_time(working_days)
    total = len(hours)
    try:
        generated_strategy = pd.read_csv(file_path)
        existed_hours = generated_strategy["time"].drop_duplicates().to_list()
    except:
        existed_hours = []

    for i, hour in enumerate(hours, start=1):
        if hour in existed_hours:
            continue
        print(f"{i}: Start generating for {hour}")
        for interval in ["1h", "5min", "1day"]:
            TI = TechnicalIndicators(
                currency_pair=currency_pair,
                interval=interval,
                outputsize=200,
                end_date=hour
            )
            data = TI.download_data_with_ti()
            data = data.iloc[:-1]
            if interval == "1day":
                open, high, low, close = data.iloc[-1][["Open", "High", "Low", "Close"]]
                pivot_point = (high + low + close) / 3
                r1 = (2 * pivot_point) - low
                r2 = pivot_point + (high - low)
                r3 = high + 2 * (pivot_point - low)
                s1 = (2 * pivot_point) - high
                s2 = pivot_point - (high - low)
                s3 = low - 2 * (high - pivot_point)
                if currency_pair == "EUR/USD":
                    decimal = 4
                else:
                    decimal = 2
                pivot_points = f"R3:{r3:.{decimal}f}\nR2:{r2:.{decimal}f}\nR1:{r1:.{decimal}f}\nPivot:{pivot_point:.{decimal}f}\ns1:{s1:.{decimal}f}\ns2:{s2:.{decimal}f}\ns3:{s3:.{decimal}f}"
            else:
                TI.plot_chart(data)
                if interval == "5min":
                    current_price = data.iloc[-1]["Close"]
            
        max_retries = 3   
        for attempt in range(max_retries):
            try:
                coroutines = []
                for api_key in [os.environ["GEMINI_API_KEY_KIEN"], os.environ["GEMINI_API_KEY_CONG"], os.environ["GEMINI_API_KEY_XIFAN"]]:
                    TA = TechnicalAnalysis(currency_pair=currency_pair, gemini_model=gemini_model, gemini_api_key=api_key)
                    coroutines.append(TA.create_gemini_analysis(
                        pivot_points=pivot_points,
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
                break 
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("Retrying in 120 seconds...")
                    await asyncio.sleep(120)  # Wait for 120 seconds before retrying
                else:
                    print(f"Max retries reached. Skipping {hour} for interval {interval}.")
                    break # break the retry loop after max_retries are reached. The outer loops keep running.

        print(f"{i}: Complete generating for {hour}. {total - i} timestamps left.")


if __name__ == "__main__":
    #generate_trading_strategy_new(r"simulation\2025_01_06\trading_strategy.csv", "EUR/USD")
    begin = time.time()
    start_date = "2025-02-10"
    end_date = "2025-02-10"
    currency_pair = "EUR/USD"
    currency_name = "EUR_USD"
    gemini_model = "gemini-2.0-flash"
    #gemini_model = "gemini-exp-1206"
    file_path = f"simulation/back_test/2025_02/{currency_name}.csv"
    asyncio.run(generate_back_test_strategies(start_date, end_date, currency_pair, file_path, gemini_model))
    end = time.time()

    print(f"Used {end - begin} seconds.")
    #print([os.environ["GEMINI_API_KEY_KIEN"], os.environ["GEMINI_API_KEY_CONG"], os.environ["GEMINI_API_KEY_XIFAN"]])