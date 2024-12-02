import pandas as pd
from ai.service.technical_indicators import TechnicalIndicators
from ai.parameters import CURRENCY_TICKERS

class BackTest:
    def __init__(self, currency_pair, strategy_file_path, custom: bool = False, profit_pips = None, loss_pips = None):
        self.currency_pair = currency_pair
        self.currency_ticker = CURRENCY_TICKERS[currency_pair]
        self.strategy_file_path = strategy_file_path
        
        self.validate_custom_input(custom, profit_pips, loss_pips)
        self.custom = custom
        self.profit_pips = profit_pips
        self.loss_pips = loss_pips

    def validate_custom_input(self, custom, profit_pips, loss_pips):
        if custom:
            if profit_pips is None or loss_pips is None:
                raise ValueError("If custom is True, profit_pips and loss_pips can not be None")    
    
    def get_price(self):
        ti = TechnicalIndicators(ticker_symbol=self.currency_ticker)
        price_data = ti.download_data(interval="1m", period="5d")
        dt_index_berlin = price_data.index.tz_convert("Europe/Berlin")
        price_data.index = dt_index_berlin
        return price_data
    
    def get_strategy(self):
        strategy_data = pd.read_csv(self.strategy_file_path, parse_dates=["order_time"], index_col="order_time")
        
        if self.custom:
            strategy_data.loc[strategy_data["strategy"] == "buy", "stop_loss_custom"] = strategy_data["entry_point"] - 0.0001 * self.loss_pips
            strategy_data.loc[strategy_data["strategy"] == "buy", "take_profit_custom"] = strategy_data["entry_point"] + 0.0001 * self.profit_pips

            strategy_data.loc[strategy_data["strategy"] == "sell", "stop_loss_custom"] = strategy_data["entry_point"] + 0.0001 * self.loss_pips
            strategy_data.loc[strategy_data["strategy"] == "sell", "take_profit_custom"] = strategy_data["entry_point"] - 0.0001 * self.profit_pips

        return strategy_data

    def get_trade_status(self, status, strategy, entry_point, take_profit, stop_loss, timeseries):
        first_price = None
        current_status = status
        entry_time = None
        entry_price = None
        close_time = None
        close_price = None
        profit = None
        if timeseries.empty:
            return {"price_at_order": first_price, "status": current_status, "entry_time": entry_time, "entry_price": entry_price, "close_time": close_time, "close_price": close_price, "profit": profit}

        first_price = timeseries.iloc[0]["Close"]

        #if status == "pending":
            
        num_steps = 24 * 60
        timeseries_24h = timeseries.iloc[:num_steps] if len(timeseries) >= num_steps else timeseries

        if strategy == "buy":
            entry_condition = lambda price: price >= entry_point if entry_point >= first_price else price <= entry_point
        if strategy == "sell":
            entry_condition = lambda price: price <= entry_point if entry_point <= first_price else price >= entry_point
        
        entry_mask = timeseries_24h["Close"].apply(entry_condition)
        if entry_mask.any():
            current_status = "open"
            entry_time = entry_mask.idxmax()
            #print(entry_time)
            entry_price = timeseries.loc[entry_time, "Close"]
        else:
            if len(timeseries_24h) == num_steps:
                current_status = "cancel"
        
        if current_status in ["pending", "cancel"] :
            return {"price_at_order": round(first_price, 5), "status": current_status, "entry_time": entry_time, "entry_price": entry_price, "close_time": close_time, "close_price": close_price, "profit": profit}
        
        filtered_timeseries = timeseries.loc[timeseries.index >= entry_time]

        if strategy == "buy":
            close_condition = lambda price: (price >= take_profit) or (price <= stop_loss)
        if strategy == "sell":
            close_condition = lambda price: (price <= take_profit) or (price >= stop_loss)
        
        close_mask = filtered_timeseries["Close"].apply(close_condition)
        if close_mask.any():
            current_status = "close"
            close_time = close_mask.idxmax()
            close_price = filtered_timeseries.loc[close_time, "Close"]

        else:
            close_time = None
            close_price = filtered_timeseries.iloc[-1]["Close"]
        profit = close_price - entry_price if strategy == "buy" else entry_price - close_price

        if self.currency_pair == "EUR/USD":
            profit /= 0.0001

        return {"price_at_order": round(first_price, 5), "status": current_status, "entry_time": entry_time, "entry_price": round(entry_price, 5), "close_time": close_time, "close_price": round(close_price, 5), "profit": round(profit, 2)}
    
    def evaluate_strategy(self):
        price_data = self.get_price()
        strategy_data = self.get_strategy()
        not_closed_strategy = strategy_data[strategy_data["status"].isin(["open", "pending"])]

        for time_index, row in not_closed_strategy.iterrows():
            status = row["status"]
            print(time_index, status)
            strategy = row["strategy"]
            entry_point = row["entry_point"]

            if self.custom:
                take_profit = row["take_profit_custom"]
                stop_loss = row["stop_loss_custom"]
            else:
                take_profit = row["take_profit"]
                stop_loss = row["stop_loss"]
            
            filtered_price_data = price_data[price_data.index >= time_index]

            status_dict = self.get_trade_status(status, strategy, entry_point, take_profit, stop_loss, filtered_price_data)
            print(status_dict)
            print()

            for k, v in status_dict.items():
                strategy_data.at[time_index, k] = v
        strategy_data.reset_index(drop=False, inplace=True, names="order_time")
        return strategy_data
    
    def write_strategy(self, df):
        df.to_csv(self.strategy_file_path, index=False)
    
    def run(self):
        df = self.evaluate_strategy()
        self.write_strategy(df)

if __name__ == "__main__":
    back_test = BackTest(currency_pair="EUR/USD", strategy_file_path=r"simulation\12_02_12_06\trading_strategy.csv", custom=False)
    back_test.run()