from backend.service.SeleniumScrapper import SeleniumScrapper
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
from backend.utils.parameters import INVESTING_NEWS_ROOT_WEBSITE

class InvestingScrapper(SeleniumScrapper):

    def __init__(self, currency_pair: str, driver_path = None, is_headless = True):
        super().__init__(driver_path, is_headless)
        self.currency_pair = currency_pair
        self.news_root_url = INVESTING_NEWS_ROOT_WEBSITE[self.currency_pair]

    def get_news_websites(self):
        self.driver.get(self.news_root_url)
        self.driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(2)

        wait = WebDriverWait(self.driver, 10)
        # Wait until at least one article title link is present
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "a[data-test='article-title-link']"))
        )

        # Find all anchor elements with data-test="article-title-link"
        link_elements = self.driver.find_elements(
            By.CSS_SELECTOR, "a[data-test='article-title-link']"
        )
        links = [link.get_attribute("href") for link in link_elements]
        print(links[:10])
        return links


if __name__ == "__main__":
    scrapper = InvestingScrapper("EUR/USD")
    scrapper.get_news_websites()