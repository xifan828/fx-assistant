
from simulation.generate_strategy import generate_trading_strategy_new, generate_back_test_strategies
from simulation.back_test import BackTest
import time 
from ai.agent import KnowledgeBase
import asyncio
from ai.service.technical_indicators import TechnicalIndicators
import os
from dotenv import load_dotenv

#generate_trading_strategy()

def back_test(currency_pair, strategy_file_path):
    back_test = BackTest(
        currency_pair=currency_pair,
        strategy_file_path=strategy_file_path
    )
    updated_strategy = back_test.evaluate_strategy()
    back_test.write_strategy(updated_strategy)

def main():
    load_dotenv() 
    asyncio.run(generate_trading_strategy_new(file_path=r"simulation\forward_test\2025_01_20\EUR_USD.csv", 
                                          currency_pair="EUR/USD",
                                          gemini_model="gemini-2.0-flash-exp"))
    time.sleep(60)
    asyncio.run(generate_trading_strategy_new(file_path=r"simulation\forward_test\2025_01_20\USD_JPY.csv", 
                                          currency_pair="USD/JPY",
                                          gemini_model="gemini-2.0-flash-exp"))
    
if __name__ == "__main__":
    #back_test("EUR/USD", r"simulation\trading_strategy.csv")

    # asyncio.run(generate_trading_strategy_new(file_path=r"simulation\forward_test\2025_01_13\EUR_USD.csv", 
    #                                           currency_pair="EUR/USD",
    #                                           gemini_model="gemini-2.0-flash-exp"))
    # time.sleep(60)
    # asyncio.run(generate_trading_strategy_new(file_path=r"simulation\forward_test\2025_01_13\USD_JPY.csv", 
    #                                           currency_pair="USD/JPY",
    #                                           gemini_model="gemini-2.0-flash-exp"))

    # begin = time.time()
    # start_date = "2024-12-02"
    # end_date = "2024-12-20"
    # currency_pair = "EUR/USD"
    # currency_name = "EUR_USD"
    # #gemini_model = "gemini-exp-1206"
    # gemini_model = "gemini-2.0-flash-exp"
    # file_path = f"simulation/2024_12/{currency_name}.csv"
    # generate_back_test_strategies(start_date, end_date, currency_pair, file_path, gemini_model)
    # end = time.time()

    # print(f"Used {end - begin} seconds.")

    main()