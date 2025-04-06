
from simulation.generate_strategy import generate_trading_strategy_new, generate_back_test_strategies
from simulation.back_test import BackTest
import time 
from backend.agent import KnowledgeBase
import asyncio
from backend.service.data_collection import TechnicalIndicators
import os
from dotenv import load_dotenv
from ib_client import execute_order, IBClient
import pandas as pd
from datetime import timedelta


#generate_trading_strategy()

def back_test(currency_pair, strategy_file_path):
    back_test = BackTest(
        currency_pair=currency_pair,
        strategy_file_path=strategy_file_path
    )
    updated_strategy = back_test.evaluate_strategy()
    back_test.write_strategy(updated_strategy)

class StrategyExecutor:
    def __init__(self, currency_pair: str, root_path: str, sl_pips: float = 15, tp_pips: float = 30, trailing_pips: float = 15):
        self.currency_pair = currency_pair
        self.symbol = currency_pair.split("/")[0]
        self.currency = currency_pair.split("/")[1]

        self.root_path = root_path
        self.strategy_file_path = os.path.join(root_path, f"{self.symbol}_{self.currency}_agg.csv")

        self.pip_size = 0.0001 if self.currency_pair == "EUR/USD" else 0.01
        self.sl_pips = sl_pips
        self.tp_pips = tp_pips
        self.trailing_pips = trailing_pips
    
    def determine_market_condition(self):
        # ti = TechnicalIndicators(currency_pair=self.currency_pair, interval="15min")
        # return ti.determine_market_condition()
        return "Trending"

    def generate_strategy(self):
        strategy = asyncio.run(generate_trading_strategy_new(root_path=self.root_path, currency_pair=self.currency_pair, gemini_model="gemini-2.0-flash"))
        return strategy

    def check_last_two_strategies(self):
        df = pd.read_csv(self.strategy_file_path, parse_dates=["time"])
        
        # if len(df) < 2:
        #     return False
    
        last_row = df.iloc[-1]
        #prev_row = df.iloc[-2]

        #time_diff = last_row["time"] - prev_row["time"]

        if (
            last_row["strategy"] == "wait" 
            #last_row["strategy"] != prev_row["strategy"] or
            #time_diff > timedelta(minutes=20)
        ):
            return False

        return True

    def place_order(self, strategy: str, client: IBClient):
        action = strategy["strategy"].upper()
        entry_type = strategy["order_type"]
        limit_price = strategy["entry_point"]
        if action == "BUY":
            stop_price = limit_price - self.sl_pips * self.pip_size
            take_profit_price = limit_price + self.tp_pips * self.pip_size
        else:
            stop_price = limit_price + self.sl_pips * self.pip_size
            take_profit_price = limit_price - self.tp_pips * self.pip_size
        execute_order(
            client=client,
            currency_pair=self.currency_pair,
            action=action,
            entry_order_type=entry_type,
            entry_price=limit_price,
            stop_price=stop_price,
            take_profit_price=take_profit_price,
            trailing_pips=self.trailing_pips,
            pip_size=self.pip_size,
            quantity=100000
        )
    
    def execute(self):
        # check if market is trending
        market_condition = self.determine_market_condition()
        print(f"Market condition: {market_condition}")
        if market_condition != "Trending":
            return
        
        # generate strategy
        new_strategy = self.generate_strategy()
        print(f"New strategy: {new_strategy}")

        # check if last two strategies are the same, not wait, and within 20 minutes
        if self.check_last_two_strategies():
            print("conditions met, execute strategy")
            client = IBClient("127.0.0.1", 7497, 1)
            while client.next_order_id is None:
                time.sleep(0.2)
            
            # retrieve current symbol positions
            client.reqPositions()
            client.reqAllOpenOrders()
            client.positions_event.wait(timeout=10)
            client.open_orders_event.wait(timeout=10)
            positions = client.get_position_quantiy(self.symbol)
            print(f"Current positions: {positions}")

            # close all positions if new strategy against the current positions
            if positions > 0 and new_strategy["strategy"] == "sell":
                client.close_positions(symbol=self.symbol)
                client.close_open_orders(symbol=self.symbol)
                print("Close all positions, open orders")
            if positions < 0 and new_strategy["strategy"] == "buy":
                client.close_positions(symbol=self.symbol)
                client.close_open_orders(symbol=self.symbol)
                print("Close all positions, open orders")
            
            # place order if current positions < 300000
            if abs(positions) < 300000:
                self.place_order(new_strategy, client)
            
            time.sleep(2)

            client.disconnect()

        return
            






    





def main():
    load_dotenv() 
    root_path = r"simulation\forward_test\2025_03_31"
    for currency_pair in ["EUR/USD", "USD/JPY"]:   
        executor = StrategyExecutor(currency_pair=currency_pair, root_path=root_path, sl_pips=15, tp_pips=30, trailing_pips=None)
        executor.execute()
        time.sleep(60)
    
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