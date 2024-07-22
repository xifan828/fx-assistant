from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Set up Chrome options
def scrape_pair_overview():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")  # Starts the browser maximized
    chrome_options.add_argument("--window-size=1920,1080")  # Sets a default window size

    # Set up the Chrome driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Navigate to the website
    url = "https://www.tradingview.com/symbols/EURUSD/"  # Replace with the website you want to scrape
    driver.get(url)

    # Wait for the page to load (you might need to adjust the time)
    time.sleep(5)

    #driver.execute_script("window.scrollBy(0, 450);")

    # Set window size to full page size
    driver.set_window_size(1920, 1080)

    # Take a screenshot of the full page
    driver.save_screenshot("eur_usd_chart_1_day.png")

    second_button_xpath = '(//div[@class="block-sjmalUvv"]//button)[2]'
    second_button = driver.find_element("xpath", second_button_xpath)
    second_button.click()

    # # Wait for any potential page changes to take effect
    time.sleep(3)

    # # Optional: take another screenshot after clicking the button
    driver.save_screenshot("eur_usd_chart_5_days.png")

    third_button_xpath = '(//div[@class="block-sjmalUvv"]//button)[3]'
    third_button = driver.find_element("xpath", third_button_xpath)
    third_button.click()

    time.sleep(3)

    # # Optional: take another screenshot after clicking the button
    driver.save_screenshot("eur_usd_chart_1_month.png")
    # Close the browser

    url = "https://www.tradingview.com/symbols/EURUSD/technicals/"
    driver.get(url)
    driver.execute_script("window.scrollBy(0, 550);")
    time.sleep(5)
    driver.set_window_size(1920, 1920)
    driver.save_screenshot("technicals_1_day_interval.png")

    second_button_xpath = '//div[@data-name="square-tabs-buttons"]//button[@id="4h"]'
    second_button = driver.find_element("xpath", second_button_xpath)
    driver.execute_script("arguments[0].scrollIntoView(true);", second_button)
    time.sleep(1)  # wait a bit for scrolling
    driver.execute_script("arguments[0].click();", second_button)
    # Wait for any potential page changes to take effect
    time.sleep(3)
    driver.execute_script("window.scrollBy(0, -100);")
    driver.save_screenshot("technicals_4_hours_interval.png")

    second_button_xpath = '//div[@data-name="square-tabs-buttons"]//button[@id="1h"]'
    second_button = driver.find_element("xpath", second_button_xpath)
    driver.execute_script("arguments[0].scrollIntoView(true);", second_button)
    time.sleep(1)  # wait a bit for scrolling
    driver.execute_script("arguments[0].click();", second_button)
    # Wait for any potential page changes to take effect
    time.sleep(3)
    driver.execute_script("window.scrollBy(0, -100);")
    driver.save_screenshot("technicals_1_hour_interval.png")

    driver.quit()



if __name__ == "__main__":
    scrape_pair_overview()