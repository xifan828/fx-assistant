import datetime
from ai.service.central_banks import FED, ECB, BOJ

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
    "EUR/USD": "https://www.tradingview.com/symbols/EURUSD/news/?exchange=FX_IDC",
    "USD/JPY": "https://www.tradingview.com/symbols/USDJPY/news/?exchange=FX_IDC"
}

TECHNICAL_INDICATORS_WEBSITES = {
    "EUR/USD": {
        "indicator": "https://www.tradingview.com/symbols/EURUSD/technicals/?exchange=FX_IDC",
        "calender": "https://www.tradingview.com/symbols/EURUSD/economic-calendar/?exchange=FX_IDC"
    },
    "USD/JPY": {
        "indicator": "https://www.tradingview.com/symbols/USDJPY/technicals/?exchange=FX_IDC",
        "calender": "https://www.tradingview.com/symbols/USDJPY/economic-calendar/?exchange=FX_IDC"
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

