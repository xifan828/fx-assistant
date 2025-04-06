import ta
import pandas as pd

class TechnicalIndicators:
    def __init__(self):
        pass
    
    @staticmethod
    def calculate_technical_indicators(df, sma=False, ema=True, rsi=True, macd=True, roc=True, bbands=True, atr=True):
        df = df.copy()

        # Ensure the index is a DateTimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be a DateTimeIndex")

        # --- Simple Moving Average (SMA) ---
        if sma:
            df['SMA10'] = ta.trend.sma_indicator(df['Close'], window=10)
            df['SMA20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['SMA50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['SMA100'] = ta.trend.sma_indicator(df['Close'], window=100)

        # --- Exponential Moving Average (EMA) ---
        if ema:
            df['EMA10'] = ta.trend.ema_indicator(df['Close'], window=10)
            df['EMA20'] = ta.trend.ema_indicator(df['Close'], window=20)
            df['EMA50'] = ta.trend.ema_indicator(df['Close'], window=50)
            df['EMA100'] = ta.trend.ema_indicator(df['Close'], window=100)

        # --- Relative Strength Index (RSI) ---
        if rsi:
            df['RSI14'] = ta.momentum.rsi(df['Close'], window=14)

        # --- Moving Average Convergence Divergence (MACD) ---
        if macd:
            macd = ta.trend.MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9)
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Diff'] = macd.macd_diff()  # This is the MACD Histogram

        # --- Rate of Change (ROC) ---
        if roc:
            df['ROC12'] = ta.momentum.roc(df['Close'], window=12)

        # --- Bollinger Bands (Default: 20 SMA, ±2 std) ---
        if bbands:
            bollinger = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
            df['BB_Mid']   = bollinger.bollinger_mavg()   # Middle band (20 SMA by default)
            df['BB_Upper'] = bollinger.bollinger_hband()  # Upper band (+2 std)
            df['BB_Lower'] = bollinger.bollinger_lband() 

        # --- Average True Range (ATR) ---
        if atr:
            atr = ta.volatility.AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14)
            df['ATR'] = atr.average_true_range()
            
        df['Date'] = df.index
        
        return df