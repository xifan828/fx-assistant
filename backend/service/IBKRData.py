from ib_client import get_data

class IBKRData:
    def __init__(self, currency_pair: str, interval: str):
        self.currency_pair = currency_pair
        self.interval = interval
    
    def get_data(self):
        data = get_data(self.currency_pair, self.interval)
        return data

if __name__ == "__main__":
    # Example usage
    ibkr = IBKRData(currency_pair="EUR/USD", interval="1h")
    data = ibkr.get_data()
    print("head")
    print(data.head())
    print("tail")
    print(data.tail())