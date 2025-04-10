import datetime
from backend.service.central_banks import FED, ECB, BOJ

# Get the current date
CURRENT_DATE = datetime.datetime.now()

# Format the date to "Month Year"
FORMATED_DATE = CURRENT_DATE.strftime("%B %Y")

ECONOMIC_INDICATORS_WEBSITES = {
    "USD": {
        "GDP_US": "https://tradingeconomics.com/united-states/gdp-growth",
        "Interest_Rate_US": "https://tradingeconomics.com/united-states/interest-rate",
        "Inflation_Rate_US": "https://tradingeconomics.com/united-states/inflation-cpi",
        "Unemployment_Rate_US": "https://tradingeconomics.com/united-states/unemployment-rate",
        "Non_Farm_Payrolls_US": "https://tradingeconomics.com/united-states/non-farm-payrolls",
    },
    "EUR": {
        "GDP_EU": "https://tradingeconomics.com/euro-area/gdp-growth",
        "Interest_Rate_EU": "https://tradingeconomics.com/euro-area/interest-rate",
        "Inflation_Rate_EU": "https://tradingeconomics.com/euro-area/inflation-cpi",
        "Unemployment_Rate_EU": "https://tradingeconomics.com/euro-area/unemployment-rate",
    },
    "JPY": {
        "GDP_JP": "https://tradingeconomics.com/japan/gdp-growth",
        "Interest_Rate_JP": "https://tradingeconomics.com/japan/interest-rate",
        "Inflation_Rate_JP": "https://tradingeconomics.com/japan/inflation-cpi",
        "Unemployment_Rate_JP": "https://tradingeconomics.com/japan/unemployment-rate"
    }
}

NEWS_ROOT_WEBSITE = {
    "EUR/USD": "https://www.tradingview.com/symbols/EURUSD/news/?exchange=FX",
    "USD/JPY": "https://www.tradingview.com/symbols/USDJPY/news/?exchange=FX"
}

INVESTING_NEWS_ROOT_WEBSITE = {
    "EUR/USD": "https://cn.investing.com/currencies/eur-usd-news",
    "USD/JPY": "https://cn.investing.com/currencies/usd-jpy-news"
}

TECHNICAL_INDICATORS_WEBSITES = {
    "EUR/USD": {
        "indicator": "https://www.tradingview.com/symbols/EURUSD/technicals/?exchange=FX",
        "calender": "https://www.tradingview.com/symbols/EURUSD/economic-calendar/?exchange=FX",
        "chart": "http://www.aastocks.com/en/forex/quote/chart.aspx?symbol=EURUSD"
    },
    "USD/JPY": {
        "indicator": "https://www.tradingview.com/symbols/USDJPY/technicals/?exchange=FX",
        "calender": "https://www.tradingview.com/symbols/USDJPY/economic-calendar/?exchange=FX",
        "chart": "http://www.aastocks.com/en/forex/quote/chart.aspx?symbol=USDJPY"
    }
}

CURRENCY_TICKERS = {
    "EUR/USD": "EURUSD=X",
    "USD/JPY": "USDJPY=X"
}

CENTRAL_BANKS = {
    "EUR": ECB(), "USD": FED(), "JPY": BOJ()
}

AI_SEARCH_QUERIES = [
        f"Recent FED reserve decisions affecting EUR/USD exchange rate {FORMATED_DATE}", 
        f"Recent ECB decisions affecting EUR/USD exchange rate {FORMATED_DATE}",
    ]


INVESTING_ASSETS = {
    "general": {
        "S&P 500": "https://www.investing.com/indices/us-spx-500",
        "Nasdaq": "https://www.investing.com/indices/nq-100",
        "STOXX50": "https://www.investing.com/indices/eu-stoxx50",
        "MSCI EM": "https://www.investing.com/indices/msci-em",
        "DXY": "https://www.investing.com/currencies/us-dollar-index",
        "Gold": "https://www.investing.com/commodities/gold",
        "Brent Oil": "https://www.investing.com/commodities/brent-oil",
        "VIX": "https://www.investing.com/indices/volatility-s-p-500"
    },

    "EUR": {
        "EUR/USD": "https://www.investing.com/currencies/eur-usd",
        "Germany 2Y Yield": "https://www.investing.com/rates-bonds/germany-2-year-bond-yield",
        "Germany 10Y Yield": "https://www.investing.com/rates-bonds/germany-10-year-bond-yield",
    },

    "USD": {
        "US 2Y Yield": "https://www.investing.com/rates-bonds/u.s.-2-year-bond-yield",
        "US 10Y Yield": "https://www.investing.com/rates-bonds/u.s.-10-year-bond-yield",
    },

    "JPY": {
        "USD/JPY": "https://www.investing.com/currencies/usd-jpy",
        "Japan 2Y Yield": "https://www.investing.com/rates-bonds/japan-2-year-bond-yield",
        "Japan 10Y Yield": "https://www.investing.com/rates-bonds/japan-10-year-bond-yield",
    }
}