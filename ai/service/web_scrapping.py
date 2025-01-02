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
from ai.parameters import ECONOMIC_INDICATORS_WEBSITES, INVESTING_NEWS_ROOT_WEBSITE
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

class TechnicalNewsScrapper:

    def __init__(self, root_page_url: str = None, ai_scrape_prefix: str = None, top_k: int = 5, currency_pair: str = "EUR/USD"):
        self.root_page_url = root_page_url if root_page_url else "https://www.tradingview.com/symbols/EURUSD/news/"
        self.ai_scrape_prefix = ai_scrape_prefix if ai_scrape_prefix else "https://r.jina.ai/"
        self.top_k = top_k
        self.context_length = self.top_k * 1000
        self.headers = {'Authorization': 'Bearer jina_b37b7eba34a644cfa1f8160db31778d7laDb6g0DMobEA5ZGTtn9L9Ev1mcy'}
        self.currency_pair = currency_pair

    def scrape_news(self) -> str:
        try:
            for i in range(10):
                root_page_content = self.scrape_root_page()
                sub_page_websites = self.parse_root_page(root_page_content)
                if sub_page_websites[0]["article"] is not None:
                    break
                else:
                    time.sleep(1)
                    continue
    
            print(sub_page_websites)
            if sub_page_websites[0]["article"] is not None:
                sub_page_contents = self.scrape_sub_pages(sub_page_websites)
            else:
                sub_page_contents = []
            investing_sub_page_contents = self.scrape_investing_news()
            sub_page_contents += investing_sub_page_contents
            print(sub_page_contents)

            sub_page_summaries = self.summarize_sub_pages(sub_page_contents)
            #print(sub_page_summaries)
            # for summary in sub_page_summaries:
            #     print(summary["article"])
            #     print(summary["summary"])
            #     print("\n")
            final_summary = self.create_final_summary(sub_page_summaries)
            return final_summary
        except:
            return ""
    
    def scrape_investing_news(self) -> List[Dict[str, str]]:
        investing_news_url = INVESTING_NEWS_ROOT_WEBSITE[self.currency_pair]
        response = requests.get(investing_news_url)
        print(response.status_code)
        if response.status_code == 200:

            soup = BeautifulSoup(response.text, "html.parser")

            link_tags = soup.find_all("a", attrs={"data-test": "article-title-link"})

            articles = []
            if link_tags:
                for link_tag in link_tags:
                    href = link_tag.get("href")            # Extract the URL
                    title = link_tag.get_text(strip=True)  # Extract the text inside the <a> tag, stripping whitespace
                    articles.append({"article": title, "link": href})
            else:
                print("Could not find the link tag.")
            
            for article in articles:
                response = requests.get(article["link"])
                soup = BeautifulSoup(response.text, "html.parser")
                article_divs = soup.find_all("div", id="article")

                paragraphs = article_divs[0].find_all("p")
                content = "\n".join(p.get_text(strip=True) for p in paragraphs)
                article["content"] = content
            return articles
        else:
            return [{"article": "None", "content": "None"}]

    def scrape_root_page(self) -> str:
        response = requests.get(self.ai_scrape_prefix + self.root_page_url)
        if response.status_code == 200:
            return response.text[:self.context_length]
        else:
            raise requests.HTTPError(f"Failed to retrieve {self.ai_scrape_prefix + self.root_page_url}: Status code {response.status_code}")
    
    def parse_root_page(self, scrapped_content: str) -> List[Dict[str, str]]:
        model = Config(model_name="gpt-4o").get_model()

        parser = PydanticOutputParser(pydantic_object=ArticlesExtraction)

        system_prompt = """You are provided with the content scrapped from a financial website with news regarding the {currency_pair} trading pair. Your task is to extract the **FIRST** {article_number} appearing news articles and their urls to the user.
You must wrap the output in `json` tags
{format_instructions}.
If you can not find specific news article, set the 'article' and 'url' value to null.
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Below is the content. \n{content}")
        ]).partial(format_instructions=parser.get_format_instructions())
        chain = prompt | model | StrOutputParser()
        response = chain.invoke({"content": scrapped_content, "article_number": self.top_k, "currency_pair": self.currency_pair}).strip("```json").strip("```").strip()
        websites = json.loads(response)
        if isinstance(websites, dict):
            websites = [websites]
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
        model = Config(model_name="gpt-4o-mini", temperature=0.2).get_model()
        system_message = """You are a {currency_pair} forex news analyst tasked with identifying the most important and relevant information from news articles that could impact the forex market. 
For each article you receive, extract the key information, insights, and opinions that a forex trader would find valuable.

Pay particular attention to:
- Information likely to influence {currency_pair} valuations.
- Expert opinions and analysis from finance industry professionals.
- Key data points and their potential implications.
- Shifts in market sentiment or risk appetite.

Be concise and focus on the most impactful information.
"""
        prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", """<title>
         {title}
        </title>
         <content>
         {content}
         </content>""")
        ])
        chain = prompt | model | StrOutputParser()
        results = chain.batch([{"title": content["article"], "content": content["content"], "currency_pair": self.currency_pair} for content in contents])
        summaries = []
        for content, result in zip(contents, results):
            summaries.append({"article": content["article"], "summary": result})
        return summaries
        
    def create_final_summary(self, summaries: List[Dict[str, str]]):
        model = Config(model_name="gpt-4o", temperature=0.2).get_model()
#         system_prompt = f"""You are an advanced Forex Market Analyst specializing in the {self.currency_pair} currency pair. Your expertise lies in synthesizing information from multiple sources and extracting actionable insights for forex traders.
# You will be provided with the latest articles related to the {self.currency_pair} forex market. Each article will include a title and a summary. 
# Your tasks are:
# 1. Extract key insights impacting {self.currency_pair}.
# 2. Identify trends and potential market drivers.
# 3. Identify and summarize the prevailing market sentiment toward EUR/USD, noting recurring themes, biases, and shifts in tone that may influence currency movements.
# 4. Highlight conflicting viewpoints.
# 5. Quantify potential impacts when possible.
# 6. Summarize analysis: key drivers, impacts, and risks.
# Your analysis will be used by forex traders of varying experience levels. Your analysis should be clear, concise, and actionable, allowing traders to quickly grasp the most important information and apply it to their trading decisions. **Avoid** general advice about monitoring future events or data.
# """     
        system_prompt = f"""You are a highly skilled {self.currency_pair} forex market analyst specializing in synthesizing information from multiple news articles to provide a comprehensive market overview. 
Your primary input is a collection of key information extractions from recent news articles, each analyzed by another agent. 
Your goal is to synthesize these individual extractions into a cohesive summary that identifies the key drivers and themes impacting the {self.currency_pair} market, **paying particular attention to the opinions and insights shared by finance industry professionals**. Focus on:

- Identifying recurring themes and narratives across the articles.
- Determining the overall market sentiment, **giving weight to the opinions expressed by finance professionals**.
- Identifying the major factors currently influencing currency movements, **especially as highlighted by industry experts**.
- Highlighting any conflicting information or differing perspectives presented in the articles, **including any disagreements among industry commentators**.
- Assessing the potential short-term and medium-term outlook for the forex market based on the news, **considering the forecasts and expectations shared by experts**.

Provide a concise and insightful synthesis that is valuable for forex traders."""
        prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{content}")
                ])
        chain = prompt | model | StrOutputParser()

        final_summary = chain.invoke({"content": summaries})
        return final_summary

    
        



if __name__ == "__main__":
    start_time = time.time()
    # scraper = TradingEconomicsScraper()
    # scraped_data = asyncio.run(scraper.scrape_websites(ECONOMIC_INDICATORS_WEBSITES))
    # print(scraped_data)
    scrapper = TechnicalNewsScrapper(top_k=5)
    print(scrapper.scrape_investing_news())
    # print(scrapper.scrape_root_page())
    # results = scrapper.scrape_news()
    # print(results)