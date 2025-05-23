import aiohttp
import asyncio
from bs4 import BeautifulSoup
import requests
from typing import List, Dict, Tuple
from backend.utils.parameters import FED_WATCH_WEBSITE
import pandas as pd
import io
from backend.service.SeleniumScrapper import SeleniumScrapper
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
from selenium.common.exceptions import TimeoutException
import os
from backend.utils.logger_config import get_logger
logger = get_logger(__name__)




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
                    # find historical description
                    content = soup.find('div', id='historical-desc').get_text(strip=True)
                    # find tables with <table class="table table-hover" id="calendar"> get all thead and tbody
                    tables = soup.find_all('table', class_='table table-hover', id='calendar')
                    if tables:
                        table = tables[0]
                        df = pd.read_html(io.StringIO(str(table)))[0]
                        df = df.astype(object)
                        df = df.where(pd.notnull(df), None)
                    else:
                        df = None
    
                    return name, content, df.to_dict(orient='records') if df is not None else None
                else:
                    return name, f'Failed to retrieve the page. Status code: {response.status}', None
        except Exception as e:
            return name, f'An error occurred: {e}', None

    async def scrape_websites(self, websites_dict: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        results = {}
        async with aiohttp.ClientSession() as session:
            tasks = []
            for name, url in websites_dict.items():
                tasks.append(self.fetch_content(session, name, url))
            results_list = await asyncio.gather(*tasks)
            for name, desc, table in results_list:
                results[name] = {"desc": desc, "table": table}
        return results

class FedWatchScrapper(SeleniumScrapper):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def run(self) -> Tuple[pd.DataFrame]:
        try:
            wait = WebDriverWait(self.driver, 20)

            logger.info(f"Navigating to {FED_WATCH_WEBSITE}")
            self.driver.get(FED_WATCH_WEBSITE)
            
            logger.info("Attempting to close any initial popups/banners on the main page.")
            self.close_cookie_banner()
            self.close_ads() # Call close_ads on the main page
            time.sleep(2) # G

            logger.info("Waiting for and switching to iframe.cmeIframe")
            iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.cmeIframe")))
            self.driver.switch_to.frame(iframe)

            df_rate_next, df_price_next = self.fetch_content()

            meeting_link = wait.until(
                EC.element_to_be_clickable(
                    (By.ID, "ctl00_MainContent_ucViewControl_IntegratedFedWatchTool_uccv_lvMeetings_ctrl4_lbMeeting")
                )
            )
            meeting_link.click()

            time.sleep(5)

            self.driver.switch_to.default_content()
            wait.until(EC.frame_to_be_available_and_switch_to_it(
                (By.CSS_SELECTOR, "iframe.cmeIframe")
            ))

            df_rate_end, df_price_end = self.fetch_content()


            return df_rate_next, df_price_next, df_rate_end, df_price_end
            
        except Exception as e:
            raise
        finally:
            self.quit_driver()

    def fetch_content(self) -> pd.DataFrame:
        try:
            wait = WebDriverWait(self.driver, 20)

            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "table.grid-thm.grid-thm-v2.w-lg")
            ))

            rate_table = self.driver.find_element(
                By.CSS_SELECTOR,
                "table[class='grid-thm grid-thm-v2 w-lg']"
            )

            rate_rows = rate_table.find_elements(
                By.CSS_SELECTOR,
                "tr[class='']"
            )

            price_table = self.driver.find_element(
                By.CSS_SELECTOR,
                "table[class='grid-thm grid-thm-v2 no-shadow w-lg']"
            )

            price_rows = price_table.find_elements(By.CSS_SELECTOR, "tbody tr")
            
            
            def get_data(rows):
                data = []
                for tr in rows:
                    tds = tr.find_elements(By.TAG_NAME, "td")
                    if len(tds) == 0:
                        continue
                    data.append([td.text for td in tds])
                return data

            rate_data = get_data(rate_rows)
            df_rate = pd.DataFrame(rate_data, columns=["Target Rate (bps)", "Probability Now", "Probability 1 Day Ago", "Probability 1 Week Ago", "Probability 1 Month Ago"]) 


            header_tr = price_rows[1]
            headers = [th.text for th in header_tr.find_elements(By.TAG_NAME, "th")]

            data_rows = price_rows[2:]
            price_data = []
            for row in data_rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                price_data.append([cell.text for cell in cells])

            df_price = pd.DataFrame(price_data, columns=headers)
            return df_rate, df_price
            
        except Exception as e:
            print(traceback.format_exc())  # This will show full stacktrace and error
            raise  

if __name__ == "__main__":
    scr = FedWatchScrapper()

    df_rate_next, df_price_next, df_rate_end, df_price_end = scr.run()
    print("Next Meeting Rate Table:")
    print(df_rate_next)
    print(df_rate_next.to_markdown(index=False))
    print("Next Meeting Price Table:")
    print(df_price_next)
    print("End of Meeting Rate Table:")
    print(df_rate_end)
    print("End of Meeting Price Table:")
    print(df_price_end)