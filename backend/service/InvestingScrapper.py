from backend.service.SeleniumScrapper import SeleniumScrapper
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
from backend.utils.parameters import INVESTING_NEWS_ROOT_WEBSITE, INVESTING_ASSETS
from typing import List, Dict
import pandas as pd

class InvestingScrapper(SeleniumScrapper):

    def __init__(self, currency_pair: str, driver_path = None, is_headless = True):
        super().__init__(driver_path, is_headless)
        self.currency_pair = currency_pair
        self.news_root_url = INVESTING_NEWS_ROOT_WEBSITE[self.currency_pair]
        self.assets_url = self._get_assets_url()
    
    def _get_assets_url(self) -> Dict:
        symbol = self.currency_pair.split("/")[0]
        currency = self.currency_pair.split("/")[1]
        general_urls = INVESTING_ASSETS["general"]
        symbol_urls = INVESTING_ASSETS[symbol]
        currency_urls = INVESTING_ASSETS[currency]
        combined_urls = {**general_urls, **symbol_urls, **currency_urls}
        return combined_urls

    def get_news_websites(self) -> List:
        self.driver.get(self.news_root_url)
        self.driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(2)

        #wait = WebDriverWait(self.driver, 10)
        # Wait until at least one article title link is present
        # wait.until(EC.presence_of_element_located(
        #     (By.CSS_SELECTOR, "a[data-test='article-title-link']"))
        # )

        # Find all anchor elements with data-test="article-title-link"
        link_elements = self.driver.find_elements(
            By.CSS_SELECTOR, "a[data-test='article-title-link']"
        )
        links = [link.get_attribute("href") for link in link_elements]
        print(links[:10])
        return links
    
    def get_asset(self, name, url) -> List[str]:
        self.driver.get(url)
        time.sleep(1)  # wait for JS to load

        try:
            price = self.driver.find_element(By.CSS_SELECTOR, 'span[data-test="instrument-price-last"]').text
            change = self.driver.find_element(By.CSS_SELECTOR, 'span[data-test="instrument-price-change"]').text
            change_pct = self.driver.find_element(By.CSS_SELECTOR, 'span[data-test="instrument-price-change-percent"]').text
            return [name, price, change, change_pct]
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            return [name, None, None, None]

    def get_all_assets(self) -> str:
        results = []
        for name, url in self.assets_url.items():
            result = self.get_asset(name, url)
            results.append(result)
            #print(f"Fetched data for {name}: {result}")
        self.quit_driver()

        results_df = pd.DataFrame(results, columns=["Asset", "Last Price", "Change", "Change (%)"])
        results_md = results_df.to_markdown(index=False)
        
        us_2y_yield = float(results_df[results_df['Asset'] == 'US 2Y Yield']['Last Price'].values[0])
        us_10y_yield = float(results_df[results_df['Asset'] == 'US 10Y Yield']['Last Price'].values[0])
        if self.currency_pair == "EUR/USD":
            germany_2y_yield = float(results_df[results_df['Asset'] == 'Germany 2Y Yield']['Last Price'].values[0])
            germany_10y_yield = float(results_df[results_df['Asset'] == 'Germany 10Y Yield']['Last Price'].values[0])
            us_germany_2y_spread = us_2y_yield - germany_2y_yield
            us_germany_10y_spread = us_10y_yield - germany_10y_yield
            spread_str = f"US 2Y - Germany 2Y spread: {us_germany_2y_spread:.2f} bps\nUS 10Y - Germany 10Y spread: {us_germany_10y_spread:.2f} bps"
        elif self.currency_pair == "USD/JPY":
            japan_2y_yield = float(results_df[results_df['Asset'] == 'Japan 2Y Yield']['Last Price'].values[0])
            japan_10y_yield = float(results_df[results_df['Asset'] == 'Japan 10Y Yield']['Last Price'].values[0])
            us_japan_2y_spread = us_2y_yield - japan_2y_yield
            us_japan_10y_spread = us_10y_yield - japan_10y_yield
            spread_str = f"US 2Y - Japan 2Y spread: {us_japan_2y_spread:.2f} bps\nUS 10Y - Japan 10Y spread: {us_japan_10y_spread:.2f} bps"
        
        assests_str = results_md + "\n\n" + spread_str
    
        return assests_str




if __name__ == "__main__":
    scrapper = InvestingScrapper("USD/JPY")
    #scrapper.get_news_websites()
    print(scrapper.get_all_assets())