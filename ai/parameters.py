import datetime

# Get the current date
CURRENT_DATE = datetime.datetime.now()

# Format the date to "Month Year"
FORMATED_DATE = CURRENT_DATE.strftime("%B %Y")

ECONOMIC_INDICATORS_WEBSITES = {
    "GDP_US": "https://tradingeconomics.com/united-states/gdp-growth",
    "GDP_EU": "https://tradingeconomics.com/euro-area/gdp-growth",
    "Interest_Rate_US": "https://tradingeconomics.com/united-states/interest-rate",
    "Interest_Rate_EU": "https://tradingeconomics.com/euro-area/interest-rate",
    "Inflation_Rate_US": "https://tradingeconomics.com/united-states/inflation-cpi",
    "Inflation_Rate_EU": "https://tradingeconomics.com/euro-area/inflation-cpi",
    "Unemployment_Rate_US": "https://tradingeconomics.com/united-states/unemployment-rate",
    "Unemployment_Rate_EU": "https://tradingeconomics.com/euro-area/unemployment-rate",
    "Non_Farm_Payrolls_US": "https://tradingeconomics.com/united-states/non-farm-payrolls"
}

TECHNICAL_ANALYSIS_ROOT_WEBSITE = "https://www.tradingview.com/symbols/EURUSD/news/"

AI_SEARCH_QUERIES = [
        f"Recent FED reserve decisions affecting EUR/USD exchange rate {FORMATED_DATE}", 
        f"Recent ECB decisions affecting EUR/USD exchange rate {FORMATED_DATE}",
    ]