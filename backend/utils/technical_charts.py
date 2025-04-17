import matplotlib
matplotlib.use('Agg')
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import MaxNLocator
from matplotlib import pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import pandas as pd
import os
import numpy as np
from backend.utils.parameters import PIP_INTERVALS, DECIMAL_PLACES

class TechnicalCharts:
    def __init__(self, currency_pair: str, interval: str, df: pd.DataFrame, size: int, chart_name: str):
        self.currency_pair = currency_pair
        self.interval = interval
        self.df = df
        self.size = size
        self.chart_name = chart_name
        self.chart_root_path = "data/chart"
    
    def plot_chart(self,
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
        decimal_places = DECIMAL_PLACES[self.currency_pair]

        # --- Data Preparation ---
        fx_data = self.df.copy()
        fx_data = fx_data.tail(self.size)
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
        ax_price.set_title(f"{self.currency_pair}")
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
        def make_price_formatter(decimal_places):
            def price_formatter(x, pos):
                return f"{x:.{decimal_places}f}"
            return price_formatter
        formatter = make_price_formatter(decimal_places)
        # def price_formatter(x, pos):
        #     return f"x:.{decimal_places}f"
        # if self.currency_pair == "EUR/USD":
        #     def price_formatter(x, pos):
        #         return f"{x:.4f}"
        # elif self.currency_pair == "USD/JPY":
        #     def price_formatter(x, pos):
        #         return f"{x:.1f}"
        # else:
        #     def price_formatter(x, pos):
        #         return str(x)

        # Calculate y-axis ticks for the price chart.
        y_min, y_max = ax_price.get_ylim()

        pip_interval = PIP_INTERVALS[self.currency_pair][self.interval]
        y_min = round(y_min / pip_interval) * pip_interval
        y_max = round(y_max / pip_interval) * pip_interval
        y_ticks = np.arange(y_min, y_max + pip_interval, pip_interval)
        # num_ticks = int(round((y_max - y_min) / pip_interval)) + 1
        # y_ticks = np.linspace(y_min, y_max, num_ticks)

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
                ax.yaxis.set_major_formatter(FuncFormatter(formatter))
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
        fig.savefig(os.path.join(self.chart_root_path, f"{self.chart_name}.png"))
        plt.close(fig)
        return data