import yfinance as yf
import pandas as pd
import numpy as np
import ta
import json

class TechnicalIndicators:
    def __init__(self, ticker_symbol: str = "EURUSD=X", interval: str = "1h", period: str = "5d"):
        self.ticker_symbol = ticker_symbol
        self.interval = interval
        self.period = period
        self.data = None
        self.indicators = {}
        self.oscillators = {}

    def download_data(self, interval, period):
        try:
            self.data = yf.download(self.ticker_symbol, period=period, interval=interval)
            return self.data
        except Exception as e:
            print(f"Error while downloading. {e}")
            return None
    

    def calculate_indicators(self):
        if self.data is not None:
            self.indicators['EMA_10'] = self.data['Close'].ewm(span=10, adjust=False).mean()
            self.indicators['SMA_10'] = self.data['Close'].rolling(window=10).mean()

            self.indicators['EMA_20'] = self.data['Close'].ewm(span=20, adjust=False).mean()
            self.indicators['SMA_20'] = self.data['Close'].rolling(window=20).mean()

            self.indicators['EMA_30'] = self.data['Close'].ewm(span=30, adjust=False).mean()
            self.indicators['SMA_30'] = self.data['Close'].rolling(window=30).mean()

            self.indicators['EMA_50'] = self.data['Close'].ewm(span=50, adjust=False).mean()
            self.indicators['SMA_50'] = self.data['Close'].rolling(window=50).mean()

            self.indicators['EMA_100'] = self.data['Close'].ewm(span=100, adjust=False).mean()
            self.indicators['SMA_100'] = self.data['Close'].rolling(window=100).mean()

            self.indicators['EMA_200'] = self.data['Close'].ewm(span=200, adjust=False).mean()
            self.indicators['SMA_200'] = self.data['Close'].rolling(window=200).mean()

            high_9 = self.data['High'].rolling(window=9).max()
            low_9 = self.data['Low'].rolling(window=9).min()
            self.indicators['Ichimoku_Base_Line'] = (high_9 + low_9) / 2

            self.indicators['HMA_9'] = self.hma(self.data['Close'], 9)

    def calculate_oscillators(self):
        if self.data is not None:
            self.oscillators['RSI_14'] = ta.momentum.RSIIndicator(self.data['Close'], window=14).rsi()
            self.oscillators['Stochastic_%K'] = ta.momentum.StochasticOscillator(self.data['High'], self.data['Low'], self.data['Close'], window=14, smooth_window=3).stoch()
            self.oscillators['CCI_20'] = ta.trend.CCIIndicator(self.data['High'], self.data['Low'], self.data['Close'], window=20).cci()
            try:
                self.oscillators['ADX_14'] = ta.trend.ADXIndicator(self.data['High'], self.data['Low'], self.data['Close'], window=14).adx()
            except ValueError:
                self.oscillators['ADX_14'] = pd.Series([np.nan] * len(self.data))
            self.oscillators['Awesome_Oscillator'] = ta.momentum.AwesomeOscillatorIndicator(self.data['High'], self.data['Low']).awesome_oscillator()
            self.oscillators['Momentum_10'] = ta.momentum.ROCIndicator(self.data['Close'], window=10).roc()
            self.oscillators['MACD_Level'] = ta.trend.MACD(self.data['Close'], window_slow=26, window_fast=12, window_sign=9).macd()
            self.oscillators['Stochastic_RSI_Fast'] = ta.momentum.StochRSIIndicator(self.data['Close'], window=14, smooth1=3, smooth2=3).stochrsi_k()
            self.oscillators['Williams_%R'] = ta.momentum.WilliamsRIndicator(self.data['High'], self.data['Low'], self.data['Close'], lbp=14).williams_r()
            self.oscillators['Bull_Bear_Power'] = self.data['Close'] - self.data['Close'].ewm(span=13, adjust=False).mean()
            self.oscillators['Ultimate_Oscillator'] = ta.momentum.UltimateOscillator(self.data['High'], self.data['Low'], self.data['Close']).ultimate_oscillator()

    def wma(self, data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda prices: np.dot(prices, weights) / weights.sum(), raw=True)

    def hma(self, data, period):
        half_length = int(period / 2)
        sqrt_length = int(np.sqrt(period))
        return self.wma(2 * self.wma(data, half_length) - self.wma(data, period), sqrt_length)

    def get_latest_signals(self):
        latest_values = []
        actions = []
        if self.data is not None:
            latest_close_price = self.data['Close'].iloc[-1]
            for name, indicator in self.indicators.items():
                latest_value = indicator.iloc[-1]
                latest_values.append(latest_value)
                if latest_close_price > latest_value:
                    actions.append("Buy")
                elif latest_close_price < latest_value:
                    actions.append("Sell")
                else:
                    actions.append("Hold")

        return {
            "Name": [
                "Exponential Moving Average (10)",
                "Simple Moving Average (10)",
                "Exponential Moving Average (20)",
                "Simple Moving Average (20)",
                "Exponential Moving Average (30)",
                "Simple Moving Average (30)",
                "Exponential Moving Average (50)",
                "Simple Moving Average (50)",
                "Exponential Moving Average (100)",
                "Simple Moving Average (100)",
                "Exponential Moving Average (200)",
                "Simple Moving Average (200)",
                "Ichimoku Base Line (9, 26, 52, 26)",
                "Hull Moving Average (9)"
            ],
            "Value": latest_values,
            "Action": actions
        }

    def get_latest_oscillators(self):
        latest_values = []
        actions = []
        if self.data is not None:
            for name, oscillator in self.oscillators.items():
                latest_value = oscillator.iloc[-1]
                latest_values.append(latest_value)
                if name == 'RSI_14':
                    if latest_value > 70:
                        actions.append("Sell")
                    elif latest_value < 30:
                        actions.append("Buy")
                    else:
                        actions.append("Neutral")
                elif name == 'Stochastic_%K' or name == 'Stochastic_RSI_Fast':
                    if latest_value > 80:
                        actions.append("Sell")
                    elif latest_value < 20:
                        actions.append("Buy")
                    else:
                        actions.append("Neutral")
                elif name == 'CCI_20':
                    if latest_value > 100:
                        actions.append("Buy")
                    elif latest_value < -100:
                        actions.append("Sell")
                    else:
                        actions.append("Neutral")
                elif name == 'Williams_%R':
                    if latest_value > -20:
                        actions.append("Sell")
                    elif latest_value < -80:
                        actions.append("Buy")
                    else:
                        actions.append("Neutral")
                else:
                    actions.append("Neutral")

        return {
            "Name": [
                "Relative Strength Index (14)",
                "Stochastic %K (14, 3, 3)",
                "Commodity Channel Index (20)",
                "Average Directional Index (14)",
                "Awesome Oscillator",
                "Momentum (10)",
                "MACD Level (12, 26)",
                "Stochastic RSI Fast (3, 3, 14, 14)",
                "Williams Percent Range (14)",
                "Bull Bear Power",
                "Ultimate Oscillator (7, 14, 28)"
            ],
            "Value": latest_values,
            "Action": actions
        }

    def output_to_json(self) -> str:
        latest_signals = self.get_latest_signals()
        latest_oscillators = self.get_latest_oscillators()
        latest_signals_json = pd.DataFrame(latest_signals).to_json(orient="records")
        latest_oscillators_json = pd.DataFrame(latest_oscillators).to_json(orient="records")
        output_str = f"Moving average signal: {latest_signals_json} \nOscillators signal: {latest_oscillators_json}"
        return output_str
        
class FullRangeTechnicalIndicators:
    def __init__(self):
        pass

    def get_1_hour_indicators(self):
        ti = TechnicalIndicators(ticker_symbol='EURUSD=X', interval='1h', period='1mo')
        ti.download_data()
        ti.calculate_indicators()
        ti.calculate_oscillators()
        return ti.output_to_json()

    def get_4_hour_indicators(self):
        ti = TechnicalIndicators(ticker_symbol='EURUSD=X', interval='1h', period='3mo')
        ti.download_data()
        df = ti.data.drop(columns=["Adj Close"]).copy()
        df_resampled = df.resample("4h").ohlc()
        df_resampled.columns = ['_'.join(col) for col in df_resampled.columns]
        df_resampled.columns = ['Open' if 'Open_open' in col else
                                'High' if 'High_high' in col else
                                'Low' if 'Low_low' in col else
                                'Close' if 'Close_close' in col else col
                                for col in df_resampled.columns]
        ti.data = df_resampled
        ti.calculate_indicators()
        ti.calculate_oscillators()
        return ti.output_to_json()
    
    def get_1_day_indicators(self):
        ti = TechnicalIndicators(ticker_symbol='EURUSD=X', interval='1d', period='6mo')
        ti.download_data()
        ti.calculate_indicators()
        ti.calculate_oscillators()
        return ti.output_to_json()
    
    def get_full_indicators(self):
        return (
            "Technical indicators in **1 hour** interval. \n"
            f"{self.get_1_hour_indicators()} \n"
            "Technical indicators in **4 hour** interval. \n"
            f"{self.get_4_hour_indicators()} \n"
            "Technical indicators in **1 day** interval. \n"
            f"{self.get_1_day_indicators()} \n"
        )


# Example usage
if __name__ == "__main__":
    ti = FullRangeTechnicalIndicators()
    print(ti.get_full_indicators())