import json
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import requests
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from ai.config import Config
import time

# economic indicators
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

# moving average
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


class ArticlesExtraction(BaseModel):
    """Articles extraction output format"""

    article: str = Field(description="The name of the article")
    url: str = Field(description="The url of the article")

class TechnicalAnalysisScrapper:

    def __init__(self, root_page_url: str = None, ai_scrape_prefix: str = None, top_k: int = 5):
        self.root_page_url = root_page_url if root_page_url else "https://www.tradingview.com/symbols/EURUSD/news/"
        self.ai_scrape_prefix = ai_scrape_prefix if ai_scrape_prefix else "https://r.jina.ai/"
        self.top_k = top_k
    
    def scrape_technical_analysis(self):
        try:
            for i in range(5):
                root_page_content = self.scrape_root_page()
                sub_page_websites = self.parse_root_page(root_page_content)
                if sub_page_websites[0]["article"] is not None:
                    break
                else:
                    time.sleep(5)
                    continue
            sub_page_contents = self.scrape_sub_pages(sub_page_websites)
            sub_page_contents = self.summarize_sub_pages(sub_page_contents)
            return sub_page_contents
        except:
            return {}
 

    def scrape_root_page(self) -> str:
        response = requests.get(self.ai_scrape_prefix + self.root_page_url)
        if response.status_code == 200:
            return response.text
        else:
            raise requests.HTTPError(f"Failed to retrieve {self.ai_scrape_prefix + self.root_page_url}: Status code {response.status_code}")
    
    def parse_root_page(self, scrapped_content: str) -> List[Dict[str, str]]:
        model = Config().get_model()

        parser = PydanticOutputParser(pydantic_object=ArticlesExtraction)

        system_prompt = """You are provided with the content scrapped from a website. Your task is to extract the first {article_number} appearing technical articles and their urls to the user.
If you can find specific technical reports, Wrap the output in `json` tags
{format_instructions}.
If you can not find specific technical reports, set the 'article' and 'url' value to null.
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Below is the content. \n{content}")
        ]).partial(format_instructions=parser.get_format_instructions())
        chain = prompt | model | StrOutputParser()
        response = chain.invoke({"content": scrapped_content, "article_number": self.top_k}).strip("```json").strip("```").strip()
        websites = json.loads(response)
        return websites
    
    def scrape_sub_pages(self, websites: List[Dict[str, str]]) -> List[Dict[str, str]]:
        contents = []
        for website in websites:
            response = requests.get(self.ai_scrape_prefix+website["url"])
            if response.status_code == 200:
                content = response.text
                contents.append({"article": website["article"], "content": content})
            else:
                contents.append({"article": website["article"], "content": "Failed to scrape this article."})
        return contents
    
    def summarize_sub_pages(self, contents: List[Dict[str, str]]) -> List[Dict[str, str]]:
        model = Config(model_name="gpt-3.5-turbo-0125", temperature=0).get_model()
        prompt = ChatPromptTemplate.from_messages([
        ("system", "You are provided with the content scrapped from a website. Your task is to summarize the key information. The audience is financial experts in the fx trading of EUR/USD."),
        ("user", "{content}")
        ])
        chain = prompt | model | StrOutputParser()
        results = chain.batch([{"content": content["content"]} for content in contents])
        summaries = []
        for content, result in zip(contents, results):
            summaries.append({"article": content["article"], "summary": result})
        return summaries

    
        



if __name__ == "__main__":
    start_time = time.time()
#     websites = {
#     "GDP_US": "https://tradingeconomics.com/united-states/gdp-growth",
#     "GDP_EU": "https://tradingeconomics.com/euro-area/gdp-growth",
#     "Interest_Rate_US": "https://tradingeconomics.com/united-states/interest-rate",
#     "Interest_Rate_EU": "https://tradingeconomics.com/euro-area/interest-rate",
#     "Inflation_Rate_US": "https://tradingeconomics.com/united-states/inflation-cpi",
#     "Inflation_Rate_EU": "https://tradingeconomics.com/euro-area/inflation-cpi",
#     "Unemployment_Rate_US": "https://tradingeconomics.com/united-states/unemployment-rate",
#     "Unemployment_Rate_EU": "https://tradingeconomics.com/euro-area/unemployment-rate"

# }
    # scraper = TradingEconomicsScraper()
    # scraped_data = asyncio.run(scraper.scrape_websites(websites))
    # print(scraped_data)
    scrapper = TechnicalAnalysisScrapper(root_page_url="https://www.dailyfx.com/eur-usd/news-and-analysis")
    results = scrapper.scrape_technical_analysis()
    for result in results:
        print(result["article"])
        print(result["summary"])
        print("\n")

    end_time = time.time()

    print(f"{end_time - start_time}")