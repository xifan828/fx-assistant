from backend.service.SeleniumScrapper import SeleniumScrapper
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
from backend.utils.parameters import INVESTING_NEWS_ROOT_WEBSITE, INVESTING_ASSETS
from typing import List, Dict
import pandas as pd
from backend.utils.logger_config import get_logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os


SCREENSHOT_DIR = "selenium_screenshots"
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

logger = get_logger(__name__)

class InvestingScrapper(SeleniumScrapper):

    def __init__(self, currency_pair: str, driver_path = None, is_headless = True):
        super().__init__(driver_path, is_headless)
        self.currency_pair = currency_pair
        self.driver_path = driver_path
        self.is_headless = is_headless  
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
        logger.info(f"Thread {threading.get_ident()}: Fetching data for {name} from {url}")
        max_retries = 3
        retry_delay = 5  # seconds, increased delay

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Thread {threading.get_ident()}: Attempt {attempt}: Navigating to {url}")
                self.driver.get(url)
                logger.info(f"Thread {threading.get_ident()}: Attempt {attempt}: Navigation to {url} possibly complete. Page title: '{self.driver.title}'")

                # Try to close any immediate pop-ups/ads/cookie banners
                logger.info(f"Thread {threading.get_ident()}: Attempt {attempt}: Trying to close ads/popups...")
                self.close_ads() # Call this first
                time.sleep(1) # Give it a moment for popups to close and DOM to settle

                # Increased timeout, useful for slower server connections or complex pages
                wait = WebDriverWait(self.driver, 30)

                # Wait for a very generic element first to see if page is responsive
                logger.info(f"Thread {threading.get_ident()}: Attempt {attempt}: Waiting for body tag...")
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info(f"Thread {threading.get_ident()}: Attempt {attempt}: Body tag found.")

                # Specific element waits
                logger.info(f"Thread {threading.get_ident()}: Attempt {attempt}: Waiting for price element 'span[data-test=\"instrument-price-last\"]'")
                price_el = wait.until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'span[data-test="instrument-price-last"]')
                ))
                logger.info(f"Thread {threading.get_ident()}: Attempt {attempt}: Waiting for change element 'span[data-test=\"instrument-price-change\"]'")
                change_el = wait.until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'span[data-test="instrument-price-change"]')
                ))
                logger.info(f"Thread {threading.get_ident()}: Attempt {attempt}: Waiting for change percent element 'span[data-test=\"instrument-price-change-percent\"]'")
                change_pct_el = wait.until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'span[data-test="instrument-price-change-percent"]')
                ))

                price = price_el.text
                change = change_el.text
                change_pct = change_pct_el.text

                logger.info(f"Thread {threading.get_ident()}: Fetched data for {name} on attempt {attempt}: {price}, {change}, {change_pct}")
                return [name, price, change, change_pct]

            except TimeoutException:
                logger.error(f"Thread {threading.get_ident()}: Attempt {attempt}: Timed out waiting for data for {name} at {url}.", exc_info=True)
                screenshot_filename = os.path.join(SCREENSHOT_DIR, f"timeout_{name.replace(' ', '_').replace('/', '_')}_attempt_{attempt}_{threading.get_ident()}.png")
                page_source_filename = os.path.join(SCREENSHOT_DIR, f"timeout_{name.replace(' ', '_').replace('/', '_')}_attempt_{attempt}_{threading.get_ident()}.html")
                try:
                    self.driver.save_screenshot(screenshot_filename)
                    logger.info(f"Saved screenshot to {screenshot_filename}")
                    with open(page_source_filename, "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    logger.info(f"Saved page source to {page_source_filename}")
                except Exception as ss_e:
                    logger.error(f"Failed to save screenshot/page source: {ss_e}")

            except (NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException) as e_interact:
                logger.error(f"Thread {threading.get_ident()}: Attempt {attempt}: Element interaction error for {name} at {url}: {e_interact}", exc_info=True)
                screenshot_filename = os.path.join(SCREENSHOT_DIR, f"interaction_error_{name.replace(' ', '_').replace('/', '_')}_attempt_{attempt}_{threading.get_ident()}.png")
                try:
                    self.driver.save_screenshot(screenshot_filename)
                    logger.info(f"Saved screenshot to {screenshot_filename}")
                except Exception as ss_e:
                    logger.error(f"Failed to save screenshot: {ss_e}")

            except Exception as e: # Catch all other exceptions
                logger.error(f"Thread {threading.get_ident()}: Attempt {attempt}: Generic error fetching data for {name} at {url}: {e}", exc_info=True)
                screenshot_filename = os.path.join(SCREENSHOT_DIR, f"generic_error_{name.replace(' ', '_').replace('/', '_')}_attempt_{attempt}_{threading.get_ident()}.png")
                try:
                    if hasattr(self, 'driver') and self.driver:
                        self.driver.save_screenshot(screenshot_filename)
                        logger.info(f"Saved screenshot to {screenshot_filename}")
                except Exception as ss_e:
                    logger.error(f"Failed to save screenshot on generic error: {ss_e}")

            logger.info(f"Thread {threading.get_ident()}: Attempt {attempt} for {name} failed. Sleeping for {retry_delay}s before retry.")
            time.sleep(retry_delay)

        logger.error(f"Thread {threading.get_ident()}: Failed to fetch data for {name} after {max_retries} attempts.")
        return [name, "N/A", "N/A", "N/A"] # Return placeholder for consistency

    def get_all_assets(self) -> str:
        results = []
        logger.info(f"Fetching data for all assets related to {self.currency_pair}")
        for name, url in self.assets_url.items():
            result = self.get_asset(name, url)
            results.append(result)
            #print(f"Fetched data for {name}: {result}")
        self.quit_driver()
        logger.info("All assets data fetched and driver closed.")

        results_df = pd.DataFrame(results, columns=["Asset", "Last Price", "Change", "Change (%)"])
        results_md = results_df.to_markdown(index=False)

        assests_str = results_md + "\n\n" + self.compute_spreads(results_df)
        return assests_str
        
    def compute_spreads(self, results_df: pd.DataFrame) -> str:
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
        elif self.currency_pair == "GBP/USD":
            uk_2y_yield = float(results_df[results_df['Asset'] == 'UK 2Y Yield']['Last Price'].values[0])
            uk_10y_yield = float(results_df[results_df['Asset'] == 'UK 10Y Yield']['Last Price'].values[0])
            us_uk_2y_spread = us_2y_yield - uk_2y_yield
            us_uk_10y_spread = us_10y_yield - uk_10y_yield
            spread_str = f"US 2Y - UK 2Y spread: {us_uk_2y_spread:.2f} bps\nUS 10Y - UK 10Y spread: {us_uk_10y_spread:.2f} bps"
        elif self.currency_pair == "USD/CNH":
            china_2y_yield = float(results_df[results_df['Asset'] == 'China 2Y Yield']['Last Price'].values[0])
            china_10y_yield = float(results_df[results_df['Asset'] == 'China 10Y Yield']['Last Price'].values[0])
            us_china_2y_spread = us_2y_yield - china_2y_yield
            us_china_10y_spread = us_10y_yield - china_10y_yield
            spread_str = f"US 2Y - China 2Y spread: {us_china_2y_spread:.2f} bps\nUS 10Y - China 10Y spread: {us_china_10y_spread:.2f} bps"
        return spread_str
    
    @staticmethod
    def _fetch_and_quit(name, url, currency_pair, driver_path, is_headless):
        tmp = InvestingScrapper(currency_pair, driver_path=driver_path, is_headless=is_headless)
        try:
            return tmp.get_asset(name, url)
        finally:
            tmp.quit_driver()

    def get_all_assets_parallel(self, max_workers=4) -> str:
        # build the jobs list
        jobs = [
            (name, url, self.currency_pair, self.driver_path, self.is_headless)
            for name, url in self.assets_url.items()
        ]

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    InvestingScrapper._fetch_and_quit,
                    name, url, cp, dp, hd
                )
                for name, url, cp, dp, hd in jobs
            ]
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Asset job error: {e}")
                    continue

        results_df = pd.DataFrame(results, columns=["Asset", "Last Price", "Change", "Change (%)"])
        results_md = results_df.to_markdown(index=False)
        return results_md + "\n\n" + self.compute_spreads(results_df)


if __name__ == "__main__":

    scrapper = InvestingScrapper("EUR/USD")
    
    asset_data = scrapper.get_asset("S&P 500", "https://www.investing.com/indices/us-spx-500")

    print(asset_data)