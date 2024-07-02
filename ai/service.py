import aiohttp
import asyncio
from bs4 import BeautifulSoup
import requests

class TradingEconomicsScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }

    async def fetch_content(self, session, name, url):
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    content = soup.find('div', id='historical-desc')
                    return name, content.get_text(strip=True) if content else 'Content not found'
                else:
                    return name, f'Failed to retrieve the page. Status code: {response.status}'
        except Exception as e:
            return name, f'An error occurred: {e}'

    async def scrape_websites(self, websites_dict):
        results = {}
        async with aiohttp.ClientSession() as session:
            tasks = []
            for name, url in websites_dict.items():
                tasks.append(self.fetch_content(session, name, url))
            results_list = await asyncio.gather(*tasks)
            for name, content in results_list:
                results[name] = content
        return results

class InvestingScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
        
    def fetch_hourly_moving_average(self):
        url = 'https://www.investing.com/technical/moving-averages'

        response = requests.get(url, headers=self.headers)

        # Dictionary to hold the MA values
        ma_values_dict = {}

        # Check if the request was successful
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the row for EUR/USD
            rows = soup.find('tbody').find_all('tr')
            for row in rows:
                name = row.find('td', class_='first left arial_14 noWrap').text.strip()
                if name == 'EUR/USD':
                    # Extracting each MA value and adding it to the dictionary
                    ma_columns = row.find_all('td')[1:]  # Skip the first column with the name
                    ma_labels = ['MA5', 'MA10', 'MA20', 'MA50', 'MA100', 'MA200']
                    ma_values = [td.get_text(strip=True).split('\n')[0] for td in ma_columns]  # Split to remove 'Buy/Sell'
                    
                    # Creating dictionary from labels and values
                    ma_values_dict = dict(zip(ma_labels, ma_values))
                    break
            return f"EUR/USD Moving Averages: {ma_values_dict}"
        else:
            return f"Failed to retrieve the page. Status code: {response.status_code}"

# Example usage
if __name__ == "__main__":
    websites = {
    "GDP_US": "https://tradingeconomics.com/united-states/gdp-growth",
    "GDP_EU": "https://tradingeconomics.com/euro-area/gdp-growth",
    "Interest_Rate_US": "https://tradingeconomics.com/united-states/interest-rate",
    "Interest_Rate_EU": "https://tradingeconomics.com/euro-area/interest-rate",
    "Inflation_Rate_US": "https://tradingeconomics.com/united-states/inflation-cpi",
    "Inflation_Rate_EU": "https://tradingeconomics.com/euro-area/inflation-cpi",
    "Unemployment_Rate_US": "https://tradingeconomics.com/united-states/unemployment-rate",
    "Unemployment_Rate_EU": "https://tradingeconomics.com/euro-area/unemployment-rate"

}
    scraper = TradingEconomicsScraper()
    scraped_data = asyncio.run(scraper.scrape_websites(websites))
    print(scraped_data)

    scraper = InvestingScraper()
    print(scraper.fetch_hourly_moving_average())

