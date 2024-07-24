from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
from PIL import Image
import os


# Set up Chrome options
def scrape_pair_overview(is_local):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")  # Starts the browser maximized
    chrome_options.add_argument("--window-size=1920,1080")  # Sets a default window size

    # Set up the Chrome driver
    if is_local:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        chrome_path = '/usr/bin/chromium'
        chromedriver_path = '/usr/bin/chromedriver'
        chrome_options.binary_location = chrome_path
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

    # Navigate to the website
    url = "https://www.google.com/finance/quote/EUR-USD?sa=X&ved=2ahUKEwiYxI_g9L2HAxWaa0EAHb1zGVIQmY0JegQIGRAw"  # Replace with the website you want to scrape
    driver.get(url)

    time.sleep(2)
    try:
        consent_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all')]"))
        )
        consent_button.click()
        print("Cookie consent accepted")
        time.sleep(2)  # Wait for the page to reload after accepting cookies
    except TimeoutException:
        print("Cookie consent button not found or not needed")

    # Set window size to full page size
    driver.set_window_size(1920, 1080)
    driver.save_screenshot("data/eur_usd_chart_1_day.png")

    second_button_xpath = '//div[@class="VfPpkd-AznF2e-LUERP-vJ7A6b VfPpkd-AznF2e-LUERP-vJ7A6b-OWXEXe-XuHpsb"]//button[@id="5dayTab"]'
    second_button = driver.find_element("xpath", second_button_xpath)
    driver.execute_script("arguments[0].click();", second_button)
    time.sleep(1.5)
    driver.save_screenshot("data/eur_usd_chart_5_days.png")

    second_button_xpath = '//div[@class="VfPpkd-AznF2e-LUERP-vJ7A6b VfPpkd-AznF2e-LUERP-vJ7A6b-OWXEXe-XuHpsb"]//button[@id="1monthTab"]'
    second_button = driver.find_element("xpath", second_button_xpath)
    driver.execute_script("arguments[0].click();", second_button)
    time.sleep(1.5)
    driver.save_screenshot("data/eur_usd_chart_1_month.png")

    url = "https://www.tradingview.com/symbols/EURUSD/technicals/"
    driver.get(url)
    driver.execute_script("window.scrollBy(0, 550);")
    time.sleep(5)
    driver.set_window_size(1920, 1920)
    driver.save_screenshot("data/technicals_1_day_interval.png")

    second_button_xpath = '//div[@data-name="square-tabs-buttons"]//button[@id="4h"]'
    second_button = driver.find_element("xpath", second_button_xpath)
    driver.execute_script("arguments[0].scrollIntoView(true);", second_button)
    time.sleep(1)  # wait a bit for scrolling
    driver.execute_script("arguments[0].click();", second_button)
    # Wait for any potential page changes to take effect
    time.sleep(3)
    driver.execute_script("window.scrollBy(0, -100);")
    driver.save_screenshot("data/technicals_4_hours_interval.png")

    second_button_xpath = '//div[@data-name="square-tabs-buttons"]//button[@id="1h"]'
    second_button = driver.find_element("xpath", second_button_xpath)
    driver.execute_script("arguments[0].scrollIntoView(true);", second_button)
    time.sleep(1)  # wait a bit for scrolling
    driver.execute_script("arguments[0].click();", second_button)
    # Wait for any potential page changes to take effect
    time.sleep(3)
    driver.execute_script("window.scrollBy(0, -100);")
    driver.save_screenshot("data/technicals_1_hour_interval.png")

    driver.quit()

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

    for file_name in os.listdir("data/"):
        if file_name.endswith(".png"):
            with Image.open(f"data/{file_name}") as img:
                if "eur_usd" in file_name:
                    cropped_img = img.crop((pair_left_crop, pair_top_crop, width-pair_right_crop, height-pair_bottom_crop))
                    cropped_img.save(f"data/{file_name}")
                if "technicals" in file_name:
                    cropped_img = img.crop((0, technicals_top_crop, width, width-technicals_bottom_crop))
                    cropped_img.save(f"data/{file_name}")
                    pivot_img = img.crop((0, pivot_top_crop, width-pivot_right_crop, width-pivot_bottom_crop))
                    pivot_file_name = file_name.replace("technicals", "pivot")
                    pivot_img.save(f"data/{pivot_file_name}")




if __name__ == "__main__":
    scrape_pair_overview(is_local=True)
    #test()