import yfinance as yf
import pandas as pd
import numpy as np
import ta
import matplotlib
matplotlib.use('Agg')
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import MaxNLocator
from matplotlib import pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import os
# creqte a class for downloading and processing data from yfinance, calculate technical indicators and plot charts

class TechnicalIndicators:
    def __init__(self, ticker: str, interval: str, period: str = None):
        self.ticker = ticker
        self.interval = interval
        if self.interval == "15m":
            self.period = "5d" if period is None else period
        elif self.interval == "1h":
            self.period = "1mo" if period is None else period
        elif self.interval == "4h":
            self.period = "6mo" if period is None else period
        elif self.interval == "1m":
            self.period = "1d" if period is None else period
        self.chart_root_path = "data/chart"
    
    def download_data(self):
        """Download data from yfinance"""
        if self.interval == "4h":
            data = yf.download(self.ticker, period=self.period, interval="1h")
            data = data.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
            data = data.dropna(subset=["Open", "Close"])
        else:
            data = yf.download(self.ticker, period=self.period, interval=self.interval)
        return data
    
    def calculate_technical_indicators(self, df):
        """
        Calculates various technical indicators using the 'ta' library.

        Args:
            df: Pandas DataFrame with DateTimeIndex and 'Open', 'High', 'Low', 'Close' columns.

        Returns:
            Pandas DataFrame with the added technical indicator columns.
        """

        # Ensure the index is a DateTimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be a DateTimeIndex")

        # --- Simple Moving Average (SMA) ---
        df['SMA10'] = ta.trend.sma_indicator(df['Close'], window=10)
        df['SMA20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['SMA50'] = ta.trend.sma_indicator(df['Close'], window=50)
        df['SMA100'] = ta.trend.sma_indicator(df['Close'], window=100)

        # --- Exponential Moving Average (EMA) ---
        df['EMA10'] = ta.trend.ema_indicator(df['Close'], window=10)
        df['EMA20'] = ta.trend.ema_indicator(df['Close'], window=20)
        df['EMA50'] = ta.trend.ema_indicator(df['Close'], window=50)
        df['EMA100'] = ta.trend.ema_indicator(df['Close'], window=100)

        # --- Relative Strength Index (RSI) ---
        df['RSI14'] = ta.momentum.rsi(df['Close'], window=14)

        # --- Moving Average Convergence Divergence (MACD) ---
        macd = ta.trend.MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Diff'] = macd.macd_diff()  # This is the MACD Histogram

        # --- Rate of Change (ROC) ---
        df['ROC12'] = ta.momentum.roc(df['Close'], window=12)
        
        df['Date'] = df.index

        today = pd.Timestamp.now().date()
        if self.interval == "15m":
            df = df.tail(2*24*4)
        elif self.interval == "1h":
            df = df.tail(12*24)
        elif self.interval == "4h":
            df = df.tail(int(2.5*20*6))
        return df
    
    def plot_chart(self, fx_data: pd.DataFrame):
        fx_data = fx_data.copy()

        fx_data.loc[:, 'Index'] = range(len(fx_data))  # New range index without gaps

        # --- Update OHLC Data for Candlestick ---
        ohlc_data = fx_data[['Index', 'Open', 'High', 'Low', 'Close']].copy()

        # Create the figure and subplots
        fig = plt.figure(figsize=(20, 15))
        gs = fig.add_gridspec(12, 1)  # 10 rows for more granular control
        ax1 = fig.add_subplot(gs[:6, :])  # Price chart takes up 6/10 of the height
        ax2 = fig.add_subplot(gs[6:8, :])  # RSI takes up 1/10
        ax3 = fig.add_subplot(gs[8:10, :])  # MACD takes up 1/10
        ax4 = fig.add_subplot(gs[10:12, :])  # ROC takes up 1/10
        axes = [ax1, ax2, ax3, ax4]

        # --- Plot 1: Candlestick Chart with SMA ---
        candlestick_ohlc(axes[0], ohlc_data.values, width=0.6, colorup='green', colordown='red', alpha=0.8)
        if self.interval == "15m":
            axes[0].plot(fx_data['Index'], fx_data['EMA10'], label='EMA 10', color='blue', linewidth=2)
        if self.interval != "4h":
            axes[0].plot(fx_data['Index'], fx_data['EMA20'], label='EMA 20', color='orange', linewidth=2)
        axes[0].plot(fx_data['Index'], fx_data['EMA50'], label='EMA 50', color='purple', linewidth=2)
        axes[0].plot(fx_data['Index'], fx_data['EMA100'], label='EMA 100', color='violet', linewidth=2)
        axes[0].legend(loc='upper left')
        axes[0].set_title('EUR/USD Candlestick Chart with SMA')
        axes[0].grid(True)

        # --- Plot 2: RSI ---
        axes[1].plot(fx_data['Index'], fx_data['RSI14'], label='RSI (14)', color='purple')
        axes[1].axhline(70, color='red', linestyle='--')
        axes[1].axhline(30, color='green', linestyle='--')
        axes[1].legend(loc='upper left')
        axes[1].grid(True)

        # --- Plot 3: MACD ---
        axes[2].plot(fx_data['Index'], fx_data['MACD'], label='MACD', color='red')
        axes[2].plot(fx_data['Index'], fx_data['MACD_Signal'], label='EMA (9)', color='lightgreen')

        # Calculate histogram data
        macd_diff = fx_data['MACD_Diff']
        pos_diff = macd_diff.copy()
        neg_diff = macd_diff.copy()
        pos_diff[pos_diff <= 0] = 0  # Set negative values to 0 for positive bars
        neg_diff[neg_diff >= 0] = 0  # Set positive values to 0 for negative bars

        axes[2].bar(fx_data['Index'], pos_diff, color='peru', label='Divergence', width=0.6)
        axes[2].bar(fx_data['Index'], neg_diff, color='black', width=0.6)

        axes[2].legend(loc='upper left')
        axes[2].grid(True)

        # --- Plot 4: ROC ---
        if self.interval != "4h":
            axes[3].plot(fx_data['Index'], fx_data['ROC12'], label='ROC (12)', color='green')
            axes[3].axhline(0, color='black', linestyle='--')
            axes[3].legend(loc='upper left')
            axes[3].grid(True)

        # --- Formatting ---
        def price_formatter(x, p):
            return f"{x:.4f}"

        # Calculate y-axis limits and ticks for the first subplot
        y_min, y_max = ax1.get_ylim()
        # Round to nearest 5 pips below and above
        pip_interval_dict = {"EURUSD=X": {'15m': 5 / 10000, '1h': 10 / 10000, '4h': 50 / 10000},
                             "USDJPY=X": {'15m': 10 / 100, '1h': 50 / 100, '4h': 50 / 100}}
        pip_interval = pip_interval_dict[self.ticker][self.interval]

        y_min = round(y_min / pip_interval) * pip_interval
        y_max = round(y_max / pip_interval) * pip_interval
        # Create ticks at 5 pip intervals
        y_ticks = np.arange(y_min, y_max + pip_interval, pip_interval)

        def date_formatter(x, pos):
            index = int(round(x))
            if index < len(fx_data):
                return fx_data['Date'].iloc[index].strftime('%d %H:%M')  # Format as 'Hour:Minute'
            return ''

        for i, ax in enumerate(axes):
            ax.xaxis.set_major_formatter(FuncFormatter(date_formatter))
            ax.xaxis.set_major_locator(MaxNLocator(integer=True, prune='both', nbins=10))
            ax.set_xlim(0, len(fx_data) + 10)

            ax.yaxis.tick_right()
            ax.yaxis.set_label_position("right")
            

            # Special formatting for the first subplot (price chart)
            if i == 0:
                ax.yaxis.set_major_formatter(FuncFormatter(price_formatter))
                ax.set_yticks(y_ticks)
                ax.tick_params(axis='x', rotation=0)
            else:
                ax.set_xticklabels([])
                ax.tick_params(axis='x', length=0)
            
            ax.grid(True, alpha=0.4)

        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        # save the figure
        chart_path = f"{self.interval}.png"
        fig.savefig(os.path.join(self.chart_root_path, chart_path))
        return 
    
    def run(self):
        data = self.download_data()
        data = self.calculate_technical_indicators(data)
        self.plot_chart(data)
        return data


if __name__ == "__main__":
    #print(pd.Timestamp.now().date() - pd.Timedelta(days=2))
    ti = TechnicalIndicators(ticker="EURUSD=X", interval="4h")
    data = ti.run()
    ti = TechnicalIndicators(ticker="EURUSD=X", interval="1h")
    data = ti.run()
    ti = TechnicalIndicators(ticker="EURUSD=X", interval="15m")
    data = ti.run()
