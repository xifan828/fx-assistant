from backend.service.SeleniumScrapper import SeleniumScrapper
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
from PIL import Image, ImageDraw
import os
from backend.utils.parameters import NEWS_ROOT_WEBSITE, TECHNICAL_INDICATORS_WEBSITES
from backend.service.JinaAIScrapper import JinaAIScrapper
import asyncio
from typing import List, Dict
from backend.utils.logger_config import get_logger
import shutil
from glob import glob


logger = get_logger(__name__)

class TradingViewScrapper(SeleniumScrapper):

    def __init__(self, currency_pair: str, driver_path = None, is_headless = True):
        super().__init__(driver_path, is_headless)
        self.currency_pair = currency_pair
        self.currency_pair_formatted = currency_pair.lower().replace("/", "_")
        self.indicator_url = TECHNICAL_INDICATORS_WEBSITES[self.currency_pair]["indicator"]
        self.calender_url = TECHNICAL_INDICATORS_WEBSITES[self.currency_pair]["calender"]
        self.news_root_url = NEWS_ROOT_WEBSITE[self.currency_pair]

    def get_technical_indicators(self):
        self.driver.get(self.indicator_url)
        self.close_ads()
        
        self.driver.execute_script("window.scrollBy(0, 550);")
        time.sleep(2)
        self.driver.set_window_size(1920, 1920)

        second_button_xpath = '//div[@data-name="square-tabs-buttons"]//button[@id="15m"]'
        second_button = self.driver.find_element("xpath", second_button_xpath)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", second_button)
        time.sleep(1)  # wait a bit for scrolling
        self.driver.execute_script("arguments[0].click();", second_button)
        # Wait for any potential page changes to take effect
        time.sleep(2)
        self.driver.execute_script("window.scrollBy(0, -100);")
        self.driver.save_screenshot("data/technical_indicators/technicals_15_min_interval.png")

        width, height = 1920, 1080
        pair_left_crop = 400
        pair_right_crop = 800
        pair_top_crop = 250
        pair_bottom_crop = 430
        technicals_top_crop = 50
        technicals_bottom_crop = 700
        pivot_top_crop = 1300
        pivot_bottom_crop = 300
        pivot_right_crop = 1350

        for file_name in os.listdir("data/technical_indicators/"):
            if file_name.endswith(".png"):
                with Image.open(f"data/technical_indicators/{file_name}") as img:
                    if "eur_usd" in file_name:
                        cropped_img = img.crop((pair_left_crop, pair_top_crop, width-pair_right_crop, height-pair_bottom_crop))
                        cropped_img.save(f"data/technical_indicators/{file_name}")
                    if "technicals" in file_name:
                        cropped_img = img.crop((0, technicals_top_crop, width, width-technicals_bottom_crop))
                        cropped_img.save(f"data/technical_indicators/{file_name}")
                        pivot_img = img.crop((0, pivot_top_crop, width-pivot_right_crop, width-pivot_bottom_crop))
                        pivot_file_name = file_name.replace("technicals", "pivot")
                        pivot_img.save(f"data/technical_indicators/{pivot_file_name}")

    def get_economic_calenders(self):
        retry_attempts = 3
        for attempt in range(1, retry_attempts + 1):
            try:
                self.driver.get(self.calender_url)
                self.driver.execute_script("window.scrollBy(0, 400);")
                time.sleep(2)
                
                self.close_ads()
                
                # Wait for the importance button to be clickable
                wait = WebDriverWait(self.driver, 10)
                importance_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-name='importance-button']"))
                )
                importance_button.click()
                time.sleep(2)
    
                screen_shot_width = 900
                normal_width = 1920
                normal_height = 1080
                line_positions = [500, 620, 750]
    
                dir_path = os.path.join("data", "calender", self.currency_pair_formatted)
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                os.makedirs(dir_path)
    
                self.driver.set_window_size(screen_shot_width, normal_height)
                self.driver.save_screenshot(os.path.join(dir_path, "upcoming.png"))
                self.driver.set_window_size(normal_width, normal_height)
    
                # Wait for the Today button to be clickable
                today_button = wait.until(EC.element_to_be_clickable((By.ID, "Today")))
                today_button.click()
                time.sleep(2)
                self.driver.set_window_size(screen_shot_width, normal_height)
    
                self.driver.save_screenshot(os.path.join(dir_path, "today.png"))

                for file_path in glob(os.path.join(dir_path, "*.png")):
                    try:
                        with Image.open(file_path) as img:
                            w, h = img.size
                            left, upper = max(0, left), max(0, upper)
                            right  = min(w, right)
                            lower  = min(h, lower)
                            cropped = img.crop((left, upper, right, lower))
                            cropped.save(file_path)
                    except Exception as e:
                        logger.warning(f"Skipping {file_path}: {e}")
    
                # If completed successfully, exit the retry loop
                logger.info("Successfully fetched economic calenders.")
                return
    
            except Exception as e:
                logger.error(f"Attempt {attempt}: Error occurred while getting economic calenders: {e}")
                if attempt < retry_attempts:
                    time.sleep(2 ** attempt)
                else:
                    logger.error("Failed to process economic calenders after multiple attempts.")
    
    def get_news_websites(self) -> List[str]:
        attempt = 0
        while attempt < 2:
            try:
                self.driver.get(self.news_root_url)

                self.driver.execute_script("window.scrollBy(0, 400);")

                time.sleep(2)

                wait = WebDriverWait(self.driver, 10)

                container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-iTt_Zp4a")))
                
                elems = container.find_elements(By.TAG_NAME, "a")
                links = []
                for e in elems:
                    href = e.get_attribute("href")
                    if href and href.startswith(("http://", "https://")):
                        links.append(href)

                return links
            
            except (TimeoutException, NoSuchElementException) as e:
                attempt += 1
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            
            except WebDriverException as e:
                logger.error(f"WebDriverException occurred: {e}")
                break

            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                break

        logger.error(f"Failed to fetch news links after {attempt} attempts, return empty list")
        return []

    
    def get_news(self, links: List[str], k: int) -> List[Dict[str, str]]:

        scrapper = JinaAIScrapper()
        news = asyncio.run(scrapper.aget_multiple(links[:k]))
        return news

    
    def get_all(self, k):
        self.get_technical_indicators()
        print("get technical indicators")
        self.get_economic_calenders()
        print("get economic calenders")
        links = self.get_news_websites()
        print("get news websites")
        self.quit_driver()
        news = self.get_news(links, k)
        print("get news content")
        return news


if __name__ == "__main__":
    scrapper = TradingViewScrapper("EUR/USD")
    links = scrapper.get_news_websites()
    print(links)
    print(len(links))
