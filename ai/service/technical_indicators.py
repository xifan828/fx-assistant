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
import time
from ib_client import get_data

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
        self.client = TDClient(apikey=os.environ["TD_API_KEY"])
        self.ts = self.client.time_series(
            symbol=self.currency_pair,
            exchange=self.exchange,
            interval=self.interval,
            outputsize=self.outputsize,
            timezone="Europe/Berlin",
            end_date = self.end_date,
            start_date = self.start_date)
        
        self.ohlc = self.download_data_from_ibkr()
        self.ohlc_with_ti = self.calculate_technical_indicators(self.ohlc)
        
    def download_data_from_ibkr(self):
        df = get_data(currency_pair=self.currency_pair, interval=self.interval)
        return df

    def download_data_wo_ti(self):
        df = self.ts.as_pandas()
        df.columns = ["Open", "High", "Low", "Close"]
        df = df[::-1]
        return df
    
    def download_data_with_ti(self):
        """Download data from yfinance"""
        # if self.interval == "4h":
        #     data = yf.download(self.ticker, period=self.period, interval="1h")
        #     data = data.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        #     data = data.dropna(subset=["Open", "Close"])
        # else:
        #     data = yf.download(self.ticker, period=self.period, interval=self.interval)
        df = (
                self.ts
                .with_ema(time_period=10)
                .with_ema(time_period=20)
                .with_ema(time_period=50)
                .with_ema(time_period=100)
                .with_bbands(ma_type="SMA", sd=2, series_type="close", time_period=20)
                .with_macd(fast_period=12, series_type="close", signal_period=9, slow_period=26)
                .with_rsi(time_period=14)
                .with_roc(time_period=12)
                .as_pandas()
            )
        df.columns = ["Open", "High", "Low", "Close", "EMA10", "EMA20", "EMA50", "EMA100", "upper_band", "middle_band", "lower_band", "MACD", "MACD_Signal", "MACD_Diff", "RSI14", "ROC12"]
        df = df[::-1]
        return df
    
    def get_current_price(self):
        prices = []
        def on_event(e):
            print(e)
            if e["event"] == "price":
                prices.append(e["price"])
        ws = self.client.websocket(symbols=self.currency_pair, on_event=on_event)
        ws.subscribe([self.currency_pair])
        ws.connect()
        count = 0
        while True:
            ws.heartbeat()
            time.sleep(7)
            count += 1
            if count > 0:
                break
        ws.disconnect()
        if prices:
            current_price = np.mean(prices)
            if self.currency_pair == "EUR/USD":
                current_price = round(current_price, 4)
            if self.currency_pair == "USD/JPY":
                current_price = round(current_price, 2)
        else:
            current_price = "Not availabel currently."
        return current_price

    
    def calculate_technical_indicators(self, df, sma=False, ema=True, rsi=True, macd=True, roc=True, bbands=True, atr=True):
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

        #df = df.loc[df["Date"] <= "2025-01-06 15:55:00"]
        # if self.interval == "15min" or self.interval=="5min":
        #     #df = df.tail(int(1.5*24*4))
        #     df = df.tail(int(1.5*24*2))
        # elif self.interval == "1h":
        #     #df = df.tail(4*24)
        #     df = df.tail(2*24)
        # elif self.interval == "4h":
        #     df = df.tail(int(1*20*6))
        # self.df = df
        return df
    
    def plot_chart(self, size: int = 20,
               EMA10: bool = False,
               EMA20: bool = False,
               EMA50: bool = False,
               EMA100: bool = False,
               RSI14: bool = False,
               MACD: bool = False,
               ROC12: bool = False,
               ATR14: bool = False,
               shading: bool = False):
        # collect current data
        data = {}
        decimal_places = 4 if self.currency_pair == "EUR/USD" else 2

        # --- Data Preparation ---
        fx_data = self.ohlc_with_ti.copy()
        fx_data = fx_data.tail(size)
        fx_data['Date'] = fx_data.index
        data["Close"] = fx_data.iloc[-1]["Close"].round(decimal_places)

        # Create a new sequential index column
        fx_data.loc[:, 'Index'] = range(len(fx_data))
        ohlc_data = fx_data[['Index', 'Open', 'High', 'Low', 'Close']].copy()

        # --- Define the Indicator Settings from Input Parameters ---
        indicators = {
            'EMA10': EMA10,
            'EMA20': EMA20,
            'EMA50': EMA50,
            'EMA100': EMA100,
            'RSI14': RSI14,
            'MACD': MACD,
            'ROC12': ROC12,
            "ATR14": ATR14
        }

        # Determine which additional subplots to create.
        additional_indicators = []
        if indicators.get('RSI14'):
            additional_indicators.append('RSI')
        if indicators.get('MACD'):
            additional_indicators.append('MACD')
        if indicators.get('ROC12'):
            additional_indicators.append('ROC')
        if indicators.get('ATR14'):
            additional_indicators.append('ATR')

        # --- Figure Setup: Dynamic Subplots ---
        # Fixed size for the candlestick chart and each additional indicator chart
        price_chart_height_inch = 10      # Fixed height for the price chart
        indicator_height_inch = 3         # Fixed height for each additional indicator
        total_height = price_chart_height_inch + indicator_height_inch * len(additional_indicators)
        n_subplots = 1 + len(additional_indicators)
        height_ratios = [price_chart_height_inch] + [indicator_height_inch] * len(additional_indicators)

        fig, axes = plt.subplots(nrows=n_subplots, figsize=(20, total_height),
                                gridspec_kw={'height_ratios': height_ratios}, sharex=False)
        if n_subplots == 1:
            axes = [axes]
        ax_price = axes[0]

        # Map additional indicators to their dedicated axes in order (top to bottom)
        indicator_axes = {}
        for i, indicator in enumerate(additional_indicators):
            indicator_axes[indicator] = axes[i + 1]

        # --- Plot 1: Price Chart (Candlestick with Optional EMA Lines) ---
        lines = []
        labels = []
        candlestick_ohlc(ax_price, ohlc_data.values, width=0.6, colorup='green', colordown='red', alpha=0.8)
        # adjust wick width
        for line in ax_price.get_lines():
            x_data = line.get_xdata()
            # Check if the line is vertical (both x values are the same)
            if len(x_data) == 2 and x_data[0] == x_data[1]:
                line.set_linewidth(2.5) 

        if indicators.get('EMA10'):
            line, = ax_price.plot(fx_data['Index'], fx_data['EMA10'], label='EMA 10', color='blue', linewidth=2)
            lines.append(line)
            labels.append("EMA 10: blue")
            data["EMA10"] = fx_data.iloc[-1]["EMA10"].round(decimal_places)
        if indicators.get('EMA20'):
            line, = ax_price.plot(fx_data['Index'], fx_data['EMA20'], label='EMA 20', color='orange', linewidth=2)
            lines.append(line)
            labels.append("EMA 20: orange")
            data["EMA20"] = fx_data.iloc[-1]["EMA20"].round(decimal_places)
        if indicators.get('EMA50'):
            line, = ax_price.plot(fx_data['Index'], fx_data['EMA50'], label='EMA 50', color='purple', linewidth=2)
            lines.append(line)
            labels.append("EMA 50: purple")
            data["EMA50"] = fx_data.iloc[-1]["EMA50"].round(decimal_places)
        if indicators.get('EMA100'):
            line, = ax_price.plot(fx_data['Index'], fx_data['EMA100'], label='EMA 100', color='violet', linewidth=2)
            lines.append(line)
            labels.append("EMA 100: violet")
            data["EMA100"] = fx_data.iloc[-1]["EMA100"].round(decimal_places)
        if lines:
            ax_price.legend(lines, labels, loc='upper left', fontsize=12)
        ax_price.set_title(f"{self.currency_pair}-{self.interval}")
        ax_price.grid(True)

        # --- Plot Additional Indicators ---
        # RSI Plot
        if 'RSI' in indicator_axes:
            ax_rsi = indicator_axes['RSI']
            ax_rsi.plot(fx_data['Index'], fx_data['RSI14'], label='RSI (14)', color='purple')
            ax_rsi.axhline(70, color='red', linestyle='--')
            ax_rsi.axhline(30, color='green', linestyle='--')
            ax_rsi.legend(loc='upper left')
            ax_rsi.grid(True)
            data["RSI14"] = fx_data.iloc[-1]["RSI14"].round(2)
        # MACD Plot
        if 'MACD' in indicator_axes:
            ax_macd = indicator_axes['MACD']
            lines = []
            labels = []
            line, = ax_macd.plot(fx_data['Index'], fx_data['MACD'], label='MACD', color='red')
            lines.append(line)
            labels.append("MACD: red")
            line, = ax_macd.plot(fx_data['Index'], fx_data['MACD_Signal'], label='Signal', color='green')
            lines.append(line)
            labels.append("Signal: green")
            macd_diff = fx_data['MACD_Diff']
            pos_diff = macd_diff.copy()
            neg_diff = macd_diff.copy()
            pos_diff[pos_diff <= 0] = 0  # Only positive values
            neg_diff[neg_diff >= 0] = 0  # Only negative values
            ax_macd.bar(fx_data['Index'], pos_diff, color='peru', label='Divergence', width=0.6)
            ax_macd.bar(fx_data['Index'], neg_diff, color='black', width=0.6)
            ax_macd.legend(lines, labels, loc='upper left', fontsize=12)
            ax_macd.grid(True)
            data["MACD"] = fx_data.iloc[-1]["MACD"].round(decimal_places)
            data["MACD_Signal"] = fx_data.iloc[-1]["MACD_Signal"].round(decimal_places)
            data["MACD_Diff"] = fx_data.iloc[-1]["MACD_Diff"].round(decimal_places)
        # ROC Plot
        if 'ROC' in indicator_axes:
            ax_roc = indicator_axes['ROC']
            ax_roc.plot(fx_data['Index'], fx_data['ROC12'], label='ROC (12)', color='green')
            ax_roc.axhline(0, color='black', linestyle='--')
            ax_roc.legend(loc='upper left')
            ax_roc.grid(True)
            data["ROC12"] = fx_data.iloc[-1]["ROC12"].round(2)
        # ATR Plot
        if 'ATR' in indicator_axes:
            ax_atr = indicator_axes['ATR']
            ax_atr.plot(fx_data['Index'], fx_data['ATR'], label='ATR (14)', color='blue')
            ax_atr.legend(loc='upper left')
            ax_atr.grid(True)
            data["ATR14"] = fx_data.iloc[-1]["ATR"].round(decimal_places)

        # --- Formatting: Axis Labels, Ticks, and Grids ---
        if self.currency_pair == "EUR/USD":
            def price_formatter(x, pos):
                return f"{x:.4f}"
        elif self.currency_pair == "USD/JPY":
            def price_formatter(x, pos):
                return f"{x:.1f}"
        else:
            def price_formatter(x, pos):
                return str(x)

        # Calculate y-axis ticks for the price chart.
        y_min, y_max = ax_price.get_ylim()
        pip_interval_dict = {
            "EUR/USD": {'5min': 5 / 10000, '15min': 5 / 10000, '1h': 10 / 10000, '4h': 50 / 10000},
            "USD/JPY": {'5min': 10 / 100, '15min': 10 / 100, '1h': 50 / 100, '4h': 50 / 100}
        }
        pip_interval = pip_interval_dict[self.currency_pair][self.interval]
        y_min = round(y_min / pip_interval) * pip_interval
        y_max = round(y_max / pip_interval) * pip_interval
        y_ticks = np.arange(y_min, y_max + pip_interval, pip_interval)

        def date_formatter(x, pos):
            index = int(round(x))
            if index < len(fx_data):
                return fx_data['Date'].iloc[index].strftime('%m-%d %H:%M')
            return ''

        # Combine all axes (price chart + additional) for common formatting.
        all_axes = [ax_price] + [indicator_axes[ind] for ind in additional_indicators]
        for i, ax in enumerate(all_axes):
            ax.xaxis.set_major_formatter(FuncFormatter(date_formatter))
            ax.xaxis.set_major_locator(MaxNLocator(integer=True, prune='both', nbins=20))
            ax.set_xlim(0, len(fx_data) + 1)
            ax.yaxis.tick_right()
            ax.yaxis.set_label_position("right")
            if i == 0:
                ax.yaxis.set_major_formatter(FuncFormatter(price_formatter))
                ax.set_yticks(y_ticks)
                ax.tick_params(axis='x', rotation=0)
            else:
                ax.set_xticklabels([])
                ax.tick_params(axis='x', length=0)
            ax.grid(True, alpha=0.4)

        # --- Shading ---
        if shading:
            time_intervals_dict = {"5min": 0, "15min": 0, "1h": 6, "4h": 5}
            bars_to_mark = time_intervals_dict[self.interval]
            start_shade = max(0, len(fx_data) - bars_to_mark)
            end_shade = len(fx_data)
            for ax in all_axes:
                ax.axvspan(start_shade, end_shade, facecolor='blue', alpha=0.2, zorder=-1)

        # Save and close the figure
        plt.tight_layout()
        fig.savefig(os.path.join(self.chart_root_path, f"{self.interval}.png"))
        plt.close(fig)
        return data
        
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

    def determine_market_condition(self, adx_threshold=20):
        """
        Determines whether the current market is trending or range-bound for intraday forex CFD trading
        using a combination of ADX and Bollinger Band width ratio.

        Args:
            df: Pandas DataFrame with 'High', 'Low', 'Close' columns on a 15-min interval.

        Returns:
            A string "Trending" or "Range-bound" based on the computed indicators.
        """
        # get df
        df = self.download_data_from_ibkr()

        # Calculate ADX using a 14-period window
        adx_series = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
        current_adx = adx_series.iloc[-1]

        # Calculate Bollinger Bands (20 SMA, ±2 std)
        # bollinger = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
        # bb_upper = bollinger.bollinger_hband().iloc[-1]
        # bb_lower = bollinger.bollinger_lband().iloc[-1]
        # sma20 = bollinger.bollinger_mavg().iloc[-1]
        
        # Calculate Bollinger Band Width Ratio as a percentage
        #bbwr = (bb_upper - bb_lower) / sma20 * 100

        if current_adx > adx_threshold:
            return "Trending"
        else:
            return "Range-bound"

    def run_ibkr_data(self):
        data = self.download_data_from_ibkr()
        data = self.calculate_technical_indicators(data)
        self.plot_chart(data)
        return data

    def run(self):
        data = self.download_data_with_ti()
        self.plot_chart(data)
        #self.crop_image()
        return data


if __name__ == "__main__":
    #print(pd.Timestamp.now().date() - pd.Timedelta(days=2))
    #currency_pair = "EUR/USD"
    currency_pair = "USD/JPY"
    ti = TechnicalIndicators(currency_pair=currency_pair, interval="15min")
    data = ti.plot_chart(size=24, EMA20=True, EMA50=True, EMA100=True, RSI14=True, MACD=True)
    print(data)

    # ti = TechnicalIndicators(currency_pair=currency_pair, interval="1h")
    # data = ti.plot_chart(size=100, EMA20=True, EMA50=True, MACD=True)
    # print(data)
    # data = ti.run()
    # ti = TechnicalIndicators(currency_pair=currency_pair, interval="1h")
    # data = ti.run()
    # ti = TechnicalIndicators(currency_pair=currency_pair, interval="15min")
    # ti.run_ibkr_data()

    #print(ti.get_current_price())

    # ti = TechnicalIndicators(currency_pair=currency_pair, interval="15min")
    # print(ti.determine_market_condition())