from twelvedata import TDClient#
import pandas as pd
import os

class TwelveData:

    def __init__(self, currency_pair: str, interval: str, outputsize: int = 400, exchange: str = "OANDA", start_date: str = None, end_date: str = None):
        self.currency_pair = currency_pair
        self.interval = interval
        self.outputsize = outputsize
        self.exchange = exchange
        self.start_date = start_date
        self.end_date = end_date

    def _init_client(self):
        api_key = os.getenv("TD_API_KEY", None)
        if not api_key:
            raise ValueError("API key for TwelveData is not set in environment variables.")
        self.client = TDClient(apikey=api_key)
    
    def get_data(self) -> pd.DataFrame:
        self._init_client()
        try:
            if self.start_date and self.end_date:
                data = self.client.time_series(
                    symbol=self.currency_pair,
                    interval=self.interval,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    exchange=self.exchange
                ).as_pandas()
            else:
                data = self.client.time_series(
                    symbol=self.currency_pair,
                    interval=self.interval,
                    outputsize=self.outputsize,
                    exchange=self.exchange
                ).as_pandas()
            data.columns = ["Open", "High", "Low", "Close"]
            return data[::-1]
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

if __name__ == "__main__":
    # Example usage
    td = TwelveData(currency_pair="EUR/USD", interval="1h", outputsize=200, exchange="OANDA")
    data = td.get_data()
    print("head")
    print(data.head())
    print("tail")
    print(data.tail())