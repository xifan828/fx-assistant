import pandas as pd
from backend.service.data_collection import TechnicalIndicators
from backend.utils.parameters import CURRENCY_TICKERS

class BackTest:
    def __init__(self, currency_pair: str, strategy_file_path: str, test_result_file_path:str,  custom: bool = False, profit_pips = None, loss_pips = None, fill_period = 2):
        self.currency_pair = currency_pair
        self.currency_ticker = CURRENCY_TICKERS[currency_pair]
        self.strategy_file_path = strategy_file_path
        self.test_result_file_path = test_result_file_path
        self.validate_custom_input(custom, profit_pips, loss_pips)
        self.custom = custom
        self.profit_pips = profit_pips
        self.loss_pips = loss_pips
        self.fill_period = fill_period
        if self.currency_pair == "EUR/USD":
            self.pip = 0.0001
        if self.currency_pair == "USD/JPY":
            self.pip = 0.01

    def validate_custom_input(self, custom, profit_pips, loss_pips):
        if custom:
            if profit_pips is None or loss_pips is None:
                raise ValueError("If custom is True, profit_pips and loss_pips can not be None")    
    
    def get_price(self, output_size, end_date):
        ti = TechnicalIndicators(currency_pair=self.currency_pair, interval="1min", outputsize=output_size, end_date=end_date)
        price_data = ti.download_data_wo_ti()
        try:
            dt_index_berlin = price_data.index.tz_convert("Europe/Berlin")
        except:
            dt_index_berlin = price_data.index.tz_localize("Europe/Berlin")
        price_data.index = dt_index_berlin
        return price_data
    
    def get_strategy(self):
        strategy_data = pd.read_csv(self.strategy_file_path, parse_dates=["order_time"], index_col="order_time")
        
        if self.custom:
            strategy_data.loc[strategy_data["strategy"] == "buy", "stop_loss_custom"] = strategy_data["entry_point"] - self.pip * self.loss_pips
            strategy_data.loc[strategy_data["strategy"] == "buy", "take_profit_custom"] = strategy_data["entry_point"] + self.pip * self.profit_pips

            strategy_data.loc[strategy_data["strategy"] == "sell", "stop_loss_custom"] = strategy_data["entry_point"] + self.pip * self.loss_pips
            strategy_data.loc[strategy_data["strategy"] == "sell", "take_profit_custom"] = strategy_data["entry_point"] - self.pip * self.profit_pips

        return strategy_data
    
    def get_trade_status(self, row, timeseries):
        price_at_order = None
        current_status = "pending"
        entry_time = None
        entry_point = None
        close_time = None
        close_price = None
        profit = None
        if row["strategy"] == "wait":
            return {"price_at_order": price_at_order, "status": "no_order", "entry_time": entry_time, "entry_price": entry_point, "close_time": close_time, "close_price": close_price, "profit": profit}
        start_time = timeseries.index[0]
        end_time = start_time + pd.Timedelta(hours=self.fill_period)
        timeseries_window = timeseries.loc[timeseries.index <= end_time]

        price_at_order = timeseries_window.iloc[0]["Close"]
        entry_point = row['entry_point']

        if row['strategy'] == 'sell':
            if entry_point > price_at_order:
                fill_condition = timeseries_window['High'] >= entry_point
            else:
                fill_condition = timeseries_window['Low'] <= entry_point
        elif row['strategy'] == 'buy':
            if entry_point < price_at_order:
                fill_condition = timeseries_window['Low'] <= entry_point
            else:
                fill_condition = timeseries_window['High'] >= entry_point
        if fill_condition.any():
            entry_time = fill_condition.idxmax()
            current_status = "open"
            
        else:
            current_status = "cancel"
            return  {"price_at_order": price_at_order, "status": current_status, "entry_time": entry_time, "entry_price": entry_point, "close_time": close_time, "close_price": close_price, "profit": profit}

        end_of_day = entry_time.normalize() + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        timeseries_window = timeseries.loc[(timeseries.index >= entry_time) & (timeseries.index <= end_of_day)]

        if self.custom:
            sl_val = row["stop_loss_custom"]
            tp_val = row["take_profit_custom"]
        else:
            sl_val = row["stop_loss"]
            tp_val = row["take_profit"]

        tp_condition = timeseries_window["High"] >= tp_val if row["strategy"] == "buy" else timeseries_window["Low"] <= tp_val
        sl_condition = timeseries_window["High"] >= sl_val if row["strategy"] == "sell" else timeseries_window["Low"] <= sl_val

        tp_time = tp_condition.idxmax() if tp_condition.any() else None
        sl_time = sl_condition.idxmax() if sl_condition.any() else None

        if tp_time and sl_time:
            if tp_time < sl_time:
                close_time = tp_time
                close_price = tp_val
                current_status = "take_profit"
            else:
                close_time = sl_time
                close_price = sl_val
                current_status = "stop_loss"
        elif tp_time is not None:
            close_time = tp_time
            close_price = tp_val
            current_status = "take_profit"
        elif sl_time is not None:
            close_time = sl_time
            close_price = sl_val
            current_status = "stop_loss"
        else:
            close_time = timeseries_window.index[-1]
            close_price = timeseries_window["Close"].iloc[-1]
            current_status = "eod"

        profit = close_price - entry_point if row["strategy"] == "buy" else entry_point - close_price
        profit_pips = profit / self.pip
        return  {"price_at_order": price_at_order, "status": current_status, "entry_time": entry_time, "entry_price": entry_point, "close_time": close_time, "close_price": close_price, "profit": round(profit_pips, 1)}


    def evaluate_strategy(self):
        strategy_data = self.get_strategy()
        not_closed_strategy = strategy_data[strategy_data["status"].isin(["open", "pending"])]

        i = 0
        for time_index, row in not_closed_strategy.iterrows():
            fx_data = self.get_price(output_size=48*60, end_date=time_index + pd.Timedelta(hours=48))
            fx_data = fx_data[fx_data.index >= time_index]
            status_dict = self.get_trade_status(row, fx_data)
            for k, v in status_dict.items():
                strategy_data.at[time_index, k] = v
        strategy_data.reset_index(drop=False, inplace=True, names="order_time")

        return strategy_data
    
    def write_strategy(self, df):
        df.to_csv(self.test_result_file_path, index=False)
    
    def run(self):
        df = self.evaluate_strategy()
        self.write_strategy(df)

if __name__ == "__main__":
    back_test = BackTest(currency_pair="USD/JPY", 
                         strategy_file_path=r"simulation\back_test\2024_11\USD_JPY_agg.csv", 
                         test_result_file_path=r"simulation\2025_01_06\USD_JPY_test.csv",
                         custom=False, profit_pips=25, loss_pips=15)
    back_test.evaluate_strategy()
    # back_test = BackTest(currency_pair="USD/JPY", 
    #                      strategy_file_path=r"simulation\2025_01_06\USD_JPY.csv", 
    #                      test_result_file_path=r"simulation\2025_01_06\USD_JPY_test_custom.csv",
    #                      custom=True, profit_pips=30, loss_pips=15)
    # back_test.run()