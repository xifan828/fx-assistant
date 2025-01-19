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
from PIL import Image, ImageDraw, ImageFont
from twelvedata import TDClient

# creqte a class for downloading and processing data from yfinance, calculate technical indicators and plot charts

class TechnicalIndicators:
    def __init__(self, currency_pair: str, interval: str, outputsize: int = 400, exchange: str = "OANDA", start_date: str = None, end_date: str = None):
        self.currency_pair = currency_pair
        self.interval = interval
        self.outputsize = outputsize
        self.exchange = exchange
        self.chart_root_path = "data/chart"
        self.df = None
        self.end_date = end_date
        self.start_date = start_date
    
    def download_data(self):
        """Download data from yfinance"""
        # if self.interval == "4h":
        #     data = yf.download(self.ticker, period=self.period, interval="1h")
        #     data = data.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        #     data = data.dropna(subset=["Open", "Close"])
        # else:
        #     data = yf.download(self.ticker, period=self.period, interval=self.interval)
        td = TDClient(apikey=os.environ["TD_API_KEY"])
        data = td.time_series(
            symbol=self.currency_pair,
            exchange=self.exchange,
            interval=self.interval,
            outputsize=self.outputsize,
            timezone="Europe/Berlin",
            end_date = self.end_date,
            start_date = self.start_date
        ).as_pandas()
        data = data.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"})
        data = data.iloc[::-1]
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

        #df = df.loc[df["Date"] <= "2025-01-06 15:55:00"]
        if self.interval == "15min" or self.interval=="5min":
            df = df.tail(int(1.5*24*4))
        elif self.interval == "1h":
            df = df.tail(4*24)
        elif self.interval == "4h":
            df = df.tail(int(1*20*6))
        self.df = df
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
        lines = []
        labels = []
        candlestick_ohlc(axes[0], ohlc_data.values, width=0.6, colorup='green', colordown='red', alpha=0.8)
        if self.interval == "15min" or self.interval == "5min":
            line, = axes[0].plot(fx_data['Index'], fx_data['EMA10'], label='EMA 10', color='blue', linewidth=2)
            lines.append(line)
            labels.append("EMA 10: blue")
        if self.interval != "4h":
            line, = axes[0].plot(fx_data['Index'], fx_data['EMA20'], label='EMA 20', color='orange', linewidth=2)
            lines.append(line)
            labels.append("EMA 20: orange")
        line, = axes[0].plot(fx_data['Index'], fx_data['EMA50'], label='EMA 50', color='purple', linewidth=2)
        lines.append(line)
        labels.append("EMA 50: purple")
        if self.interval != "15min" or self.interval != "5min":
            line, = axes[0].plot(fx_data['Index'], fx_data['EMA100'], label='EMA 100', color='violet', linewidth=2)
            lines.append(line)
            labels.append("EMA 100: violet")
        axes[0].legend(lines, labels, loc='upper left', fontsize=12)
        axes[0].set_title(f"{self.currency_pair} Candlestick Chart with EMAs")
        axes[0].grid(True)

        # --- Plot 2: RSI ---
        axes[1].plot(fx_data['Index'], fx_data['RSI14'], label='RSI (14)', color='purple')
        axes[1].axhline(70, color='red', linestyle='--')
        axes[1].axhline(30, color='green', linestyle='--')
        axes[1].legend(loc='upper left')
        axes[1].grid(True)

        # --- Plot 3: MACD ---
        lines = []
        labels = []
        line, = axes[2].plot(fx_data['Index'], fx_data['MACD'], label='MACD', color='red')
        lines.append(line)
        labels.append("MACD: red")
        line, = axes[2].plot(fx_data['Index'], fx_data['MACD_Signal'], label='EMA (9)', color='green')
        lines.append(line)
        labels.append("Signal: green")

        # Calculate histogram data
        macd_diff = fx_data['MACD_Diff']
        pos_diff = macd_diff.copy()
        neg_diff = macd_diff.copy()
        pos_diff[pos_diff <= 0] = 0  # Set negative values to 0 for positive bars
        neg_diff[neg_diff >= 0] = 0  # Set positive values to 0 for negative bars

        line = axes[2].bar(fx_data['Index'], pos_diff, color='peru', label='Divergence', width=0.6)
        lines.append(line)
        labels.append("Divergence (negative: black, positive: peru)")
        axes[2].bar(fx_data['Index'], neg_diff, color='black', width=0.6)

        axes[2].legend(lines, labels, loc='upper left', fontsize=12)
        axes[2].grid(True)

        # --- Plot 4: ROC ---
        if self.interval != "4h":
            axes[3].plot(fx_data['Index'], fx_data['ROC12'], label='ROC (12)', color='green')
            axes[3].axhline(0, color='black', linestyle='--')
            axes[3].legend(loc='upper left')
            axes[3].grid(True)

        # --- Formatting ---
        if self.currency_pair == "EUR/USD":
            def price_formatter(x, p):
                return f"{x:.4f}"
        if self.currency_pair == "USD/JPY":
            def price_formatter(x, p):
                return f"{x:.1f}"

        # Calculate y-axis limits and ticks for the first subplot
        y_min, y_max = ax1.get_ylim()
        # Round to nearest 5 pips below and above
        pip_interval_dict = {"EUR/USD": {'5min': 5 / 10000, '15min': 5 / 10000, '1h': 10 / 10000, '4h': 50 / 10000},
                             "USD/JPY": {'5min': 10 / 100,'15min': 10 / 100, '1h': 50 / 100, '4h': 50 / 100}}
        pip_interval = pip_interval_dict[self.currency_pair][self.interval]

        y_min = round(y_min / pip_interval) * pip_interval
        y_max = round(y_max / pip_interval) * pip_interval
        # Create ticks at 5 pip intervals
        y_ticks = np.arange(y_min, y_max + pip_interval, pip_interval)

        def date_formatter(x, pos):
            index = int(round(x))
            if index < len(fx_data):
                return fx_data['Date'].iloc[index].strftime('%m-%d %H:%M')  # Format as 'Hour:Minute'
            return ''

        for i, ax in enumerate(axes):
            ax.xaxis.set_major_formatter(FuncFormatter(date_formatter))
            ax.xaxis.set_major_locator(MaxNLocator(integer=True, prune='both', nbins=20))
            ax.set_xlim(0, len(fx_data) + 5)

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

        #------------------- Shading Added Here ------------------------------------------
        # Calculate the starting index for shading. Based on time interval.
        time_intervals_dict = {"5min": 12, "15min": 6, "1h": 5, "4h": 5} # Number of bars to mark
        bars_to_mark = time_intervals_dict[self.interval]

        start_shade = max(0, len(fx_data) - bars_to_mark)
        end_shade = len(fx_data)

        # Add shaded area
        for ax in axes:
            ax.axvspan(start_shade, end_shade, facecolor='grey', alpha=0.2, zorder=-1)

        # Add Text Annotation
        # time_unit = "minutes"
        # if self.interval == "1h" or self.interval == "4h":
        #     time_unit = "hours"
        
        # text_annotation = f"Last {bars_to_mark * int(self.interval.replace('min', '').replace('h', ''))} {time_unit}"
        
        # text_x = (start_shade + end_shade) / 2
        # text_y = ax1.get_ylim()[1] - (ax1.get_ylim()[1] - ax1.get_ylim()[0]) / 10  # Place text near the top
        # ax1.text(text_x, text_y, text_annotation, ha='center', va='bottom', fontsize=12)

        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        fig.savefig(os.path.join(self.chart_root_path, f"{self.interval}.png"))
        plt.close(fig)
        return 
    
    def crop_image(self):
        img_path = os.path.join(self.chart_root_path, f"{self.interval}.png")   
        partition_height = 720
        partition_width = 1200
        with Image.open(img_path) as img:
            width, height = img.size
            left = 0
            top = 0
            right = width
            bottom = height - partition_height
            img = img.crop((left, top, right, bottom))
            img.save(os.path.join(self.chart_root_path, f"{self.interval}_candel.png"))
        
        current_rsi = self.df.iloc[-1]["RSI14"]
        current_roc = self.df.iloc[-1]["ROC12"]
        text_boxes = {
        # "RSI(14)": 10,
        # "MACD: Red\nSignal: Green\nDivergence: (negative: black, positive: peru)": 260,
        # "ROC(12)": 520
        f"RSI(14): {current_rsi:.1f}": 10,
        "MACD": 260,
        f"ROC(12): {current_roc:.3f}": 520
        }
        font_size = 15
        with Image.open(img_path) as img:
            width, height = img.size
            left = partition_width
            top = height - partition_height
            right = width
            bottom = height
            img = img.crop((left, top, right, bottom))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)  # Use a truetype font
            except IOError:
                font = ImageFont.load_default()
            for text, text_y in text_boxes.items():
                # Calculate text size using textbbox
                text_bbox = draw.textbbox((0, 0), text, font=font)  # Get bounding box of the text
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                # Specify text position (left side, experiment with vertical position)
                text_x = 5  # Distance from the left

                # Draw text box background
                background_box = (text_x - 10, text_y - 10, text_x + text_width + 10, text_y + text_height + 10)
                draw.rectangle(background_box, fill="grey")  # White background for text

                # Add the text
                draw.text((text_x, text_y), text, fill="black", font=font)

            img.save(os.path.join(self.chart_root_path, f"{self.interval}_ti.png"))
        return

    

    def run(self):
        data = self.download_data()
        data = self.calculate_technical_indicators(data)
        self.plot_chart(data)
        self.crop_image()
        return data


if __name__ == "__main__":
    #print(pd.Timestamp.now().date() - pd.Timedelta(days=2))
    #currency_pair = "EUR/USD"
    currency_pair = "USD/JPY"
    ti = TechnicalIndicators(currency_pair=currency_pair, interval="4h")
    data = ti.run()
    ti = TechnicalIndicators(currency_pair=currency_pair, interval="1h")
    data = ti.run()
    ti = TechnicalIndicators(currency_pair=currency_pair, interval="5min")
    data = ti.run()

