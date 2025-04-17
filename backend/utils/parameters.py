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
    },

    "GBP": {
        "GDP_UK": "https://tradingeconomics.com/united-kingdom/gdp-growth",
        "Interest_Rate_UK": "https://tradingeconomics.com/united-kingdom/interest-rate",
        "Inflation_Rate_UK": "https://tradingeconomics.com/united-kingdom/inflation-cpi",
        "Unemployment_Rate_UK": "https://tradingeconomics.com/united-kingdom/unemployment-rate",
    },

    "CNH": {
        "GDP_CN": "https://tradingeconomics.com/china/gdp-growth",
        "Interest_Rate_CN": "https://tradingeconomics.com/china/interest-rate",
        "Inflation_Rate_CN": "https://tradingeconomics.com/china/inflation-cpi",
        "Unemployment_Rate_CN": "https://tradingeconomics.com/china/unemployment-rate",
    }
}

NEWS_ROOT_WEBSITE = {
    "EUR/USD": "https://www.tradingview.com/symbols/EURUSD/news/?exchange=FX",
    "USD/JPY": "https://www.tradingview.com/symbols/USDJPY/news/?exchange=FX",
    "GBP/USD": "https://www.tradingview.com/symbols/GBPUSD/news/?exchange=FX",
    "USD/CNH": "https://www.tradingview.com/symbols/USDCNH/news/?exchange=FX",
}

INVESTING_NEWS_ROOT_WEBSITE = {
    "EUR/USD": "https://cn.investing.com/currencies/eur-usd-news",
    "USD/JPY": "https://cn.investing.com/currencies/usd-jpy-news",
    "GBP/USD": "https://cn.investing.com/currencies/gbp-usd-news",
    "USD/CNH": "https://cn.investing.com/currencies/usd-cnh-news",
}

TECHNICAL_INDICATORS_WEBSITES = {
    "EUR/USD": {
        "indicator": "https://www.tradingview.com/symbols/EURUSD/technicals/?exchange=FX",
        "calender": "https://www.tradingview.com/symbols/EURUSD/economic-calendar/?exchange=FX",
    },
    "USD/JPY": {
        "indicator": "https://www.tradingview.com/symbols/USDJPY/technicals/?exchange=FX",
        "calender": "https://www.tradingview.com/symbols/USDJPY/economic-calendar/?exchange=FX",
    },
    "GBP/USD": {
        "indicator": "https://www.tradingview.com/symbols/GBPUSD/technicals/?exchange=FX",
        "calender": "https://www.tradingview.com/symbols/GBPUSD/economic-calendar/?exchange=FX",
    },

    "USD/CNH": {
        "indicator": "https://www.tradingview.com/symbols/USDCNH/technicals/?exchange=FX",
        "calender": "https://www.tradingview.com/symbols/USDCNH/economic-calendar/?exchange=FX",
    }
}

CURRENCY_TICKERS = {
    "EUR/USD": "EURUSD=X",
    "USD/JPY": "USDJPY=X",
    "GBP/USD": "GBPUSD=X",
    "USD/CNH": "USDCNH=X",
}

CENTRAL_BANKS = {
    "EUR": ECB(), "USD": FED(), "JPY": BOJ()
}

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
    },

    "GBP": {
        "GBP/USD": "https://www.investing.com/currencies/gbp-usd",
        "UK 2Y Yield": "https://www.investing.com/rates-bonds/uk-2-year-bond-yield",
        "UK 10Y Yield": "https://www.investing.com/rates-bonds/uk-10-year-bond-yield",
    },

    "CNH": {
        "USD/CNH": "https://www.investing.com/currencies/usd-cnh",
        "China 2Y Yield": "https://www.investing.com/rates-bonds/china-2-year-bond-yield",
        "China 10Y Yield": "https://www.investing.com/rates-bonds/china-10-year-bond-yield",
    }
}

PIP_INTERVALS = {
            "EUR/USD": {'5min': 5 / 10000, '15min': 5 / 10000, '1h': 20 / 10000, '4h': 50 / 10000},
            "USD/JPY": {'5min': 10 / 100, '15min': 10 / 100, '1h': 50 / 100, '4h': 50 / 100},
            "GBP/USD": {'5min': 5 / 10000, '15min': 5 / 10000, '1h': 20 / 10000, '4h': 50 / 10000},
            "AUD/USD": {'5min': 5 / 10000, '15min': 5 / 10000, '1h': 20 / 10000, '4h': 50 / 10000},
            "USD/CNH": {'5min': 0.01, '15min': 0.01, '1h': 0.02, '4h': 0.04},
        }

DECIMAL_PLACES = {
            "EUR/USD": 4,
            "USD/JPY": 2,
            "GBP/USD": 4,
            "AUD/USD": 4,
            "USD/CNH": 2,
        }