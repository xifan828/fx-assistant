import asyncio
from ai.service.technical_indicators import TechnicalIndicators
from ai.agents.ATRAgent import ATRAgent
from ai.agents.MACDAgent import MACDAgent
from ai.agents.MAAgent import MAAgent

async def main(currency_pair: str, interval: str, size: int = 40):
    symbol = currency_pair.split("/")[0]

    currency = currency_pair.split("/")[1]

    ti = TechnicalIndicators(currency_pair=currency_pair, interval=interval)

    data = {}

    for indicator in ["EMA", "MACD", "ATR"]:
        if indicator == "EMA":
            chart_name = f"{symbol}{currency}_{interval}_EMA"
            chart_path = f"data/chart/{chart_name}.png"
            data
            data[indicator] = ti.plot_chart(size=size, chart_name=f"{symbol}{currency}_{interval}_" ,EMA20=True, EMA50=True, EMA100=True)    

    