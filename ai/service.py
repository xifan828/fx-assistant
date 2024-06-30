import aiohttp
import asyncio
from bs4 import BeautifulSoup

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
    for name, content in scraped_data.items():
        print(f'{name}: {content}...\n')  # Print the first 100 characters of each content for brevity
