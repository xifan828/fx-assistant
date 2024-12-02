from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager


import time
from PIL import Image, ImageDraw
import os


# Set up Chrome options
def scrape_technical_indicators(is_local: bool, indicator_url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")  # Starts the browser maximized
    chrome_options.add_argument("--window-size=1920,1080")  # Sets a default window size

    # Set up the Chrome driver
    if is_local:
        chrome_driver_path = r"C:\Windows\chromedriver.exe"  # Replace with your actual path
        service = Service(chrome_driver_path)
        # Initialize Chrome driver with options
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        chrome_path = '/usr/bin/chromium'
        chromedriver_path = '/usr/bin/chromedriver'
        chrome_options.binary_location = chrome_path
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

    # Navigate to the website
    # url = "https://www.google.com/finance/quote/EUR-USD?sa=X&ved=2ahUKEwiYxI_g9L2HAxWaa0EAHb1zGVIQmY0JegQIGRAw"  # Replace with the website you want to scrape
    # driver.get(url)

    # time.sleep(2)
    # try:
    #     consent_button = WebDriverWait(driver, 10).until(
    #         EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all')]"))
    #     )
    #     consent_button.click()
    #     print("Cookie consent accepted")
    #     time.sleep(2)  # Wait for the page to reload after accepting cookies
    # except TimeoutException:
    #     print("Cookie consent button not found or not needed")

    # # Set window size to full page size
    # driver.set_window_size(1920, 1080)
    # driver.save_screenshot("data/eur_usd_chart_1_day.png")

    # second_button_xpath = '//div[@class="VfPpkd-AznF2e-LUERP-vJ7A6b VfPpkd-AznF2e-LUERP-vJ7A6b-OWXEXe-XuHpsb"]//button[@id="5dayTab"]'
    # second_button = driver.find_element("xpath", second_button_xpath)
    # driver.execute_script("arguments[0].click();", second_button)
    # time.sleep(1.5)
    # driver.save_screenshot("data/eur_usd_chart_5_days.png")

    # second_button_xpath = '//div[@class="VfPpkd-AznF2e-LUERP-vJ7A6b VfPpkd-AznF2e-LUERP-vJ7A6b-OWXEXe-XuHpsb"]//button[@id="1monthTab"]'
    # second_button = driver.find_element("xpath", second_button_xpath)
    # driver.execute_script("arguments[0].click();", second_button)
    # time.sleep(1.5)
    # driver.save_screenshot("data/eur_usd_chart_1_month.png")

    driver.get(indicator_url)
    close_ads(driver)
    
    driver.execute_script("window.scrollBy(0, 550);")
    time.sleep(3)
    driver.set_window_size(1920, 1920)
    driver.save_screenshot("data/technical_indicators/technicals_1_day_interval.png")

    second_button_xpath = '//div[@data-name="square-tabs-buttons"]//button[@id="1h"]'
    second_button = driver.find_element("xpath", second_button_xpath)
    driver.execute_script("arguments[0].scrollIntoView(true);", second_button)
    time.sleep(1)  # wait a bit for scrolling
    driver.execute_script("arguments[0].click();", second_button)
    # Wait for any potential page changes to take effect
    time.sleep(3)
    driver.execute_script("window.scrollBy(0, -100);")
    driver.save_screenshot("data/technical_indicators/technicals_1_hour_interval.png")

    second_button_xpath = '//div[@data-name="square-tabs-buttons"]//button[@id="15m"]'
    second_button = driver.find_element("xpath", second_button_xpath)
    driver.execute_script("arguments[0].scrollIntoView(true);", second_button)
    time.sleep(1)  # wait a bit for scrolling
    driver.execute_script("arguments[0].click();", second_button)
    # Wait for any potential page changes to take effect
    time.sleep(3)
    driver.execute_script("window.scrollBy(0, -100);")
    driver.save_screenshot("data/technical_indicators/technicals_15_min_interval.png")

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


    # with Image.open("data/calender/today.png") as img:
    #     cropped_img = img.crop((0, 0, width, height - 200))
    #     cropped_img.save(f"data/calender/today.png")
    # with Image.open("data/calender/upcoming.png") as img:
    #     cropped_img = img.crop((0, 0, width, height - 200))
    #     cropped_img.save(f"data/calender/upcoming.png")


    # investing_url = "https://www.investing.com/currencies/eur-usd-technical"
    # driver.get(investing_url)
    # try:
    #     accept_button = WebDriverWait(driver, 2).until(
    #         EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'I Accept')]"))
    #     )
    #     accept_button.click()
    #     print("Accepted cookie policy")
    # except Exception as e:
    #     print("No cookie consent popup found or issue with finding the button:", e)

    # driver.execute_script("window.scrollBy(0, 400);")
    # time.sleep(2)
    # driver.set_window_size(1920, 1920)
    # driver.save_screenshot("data/technical_indicators/technicals_1_hour_interval_investing.png")

    driver.quit()

def scrape_economic_calenders(is_local: bool, calender_url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")  # Starts the browser maximized
    chrome_options.add_argument("--window-size=1920,1080")  # Sets a default window size

    # Set up the Chrome driver
    if is_local:
        chrome_driver_path = r"C:\Windows\chromedriver.exe"  # Replace with your actual path
        service = Service(chrome_driver_path)
        # Initialize Chrome driver with options
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        chrome_path = '/usr/bin/chromium'
        chromedriver_path = '/usr/bin/chromedriver'
        chrome_options.binary_location = chrome_path
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.get(calender_url)
    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(2)
    
    close_ads(driver)

    screen_shot_width = 900
    normal_width = 1920
    normal_height = 1080
    line_positions = [500, 620, 750]

    importance_button = driver.find_element(By.CSS_SELECTOR, "button[data-name='importance-button']")
    importance_button.click()
    time.sleep(2)
    driver.set_window_size(screen_shot_width, normal_height)
    driver.save_screenshot("data/calender/upcoming.png")
    driver.set_window_size(normal_width, normal_height)

    today_button = driver.find_element(By.ID, "Today")
    today_button.click()
    time.sleep(2)
    driver.set_window_size(screen_shot_width, normal_height)
    driver.save_screenshot("data/calender/today.png")

    for file_name in os.listdir("data/calender/"):
        with Image.open(f"data/calender/{file_name}") as img:
            cropped_img = img.crop((0, 200, screen_shot_width, normal_height - 400))
            draw = ImageDraw.Draw(cropped_img)
            for line_position in line_positions:
                draw.line((line_position, 0, line_position, cropped_img.height), fill="black", width=3)
            

            cropped_img.save(f"data/calender/{file_name}")
    driver.quit()

def close_ads(driver):
    """
    Automatically finds and closes ads or modal pop-ups if they appear.
    """
    try:
        # Look for common ad elements
        potential_ads = driver.find_elements(By.XPATH, "//*[contains(@style, 'z-index')]")
        
        for ad in potential_ads:
            try:
                # Attempt to find a close button within the potential ad element
                close_button = ad.find_element(By.XPATH, ".//*[contains(text(), '×') or contains(@class, 'close') or contains(@id, 'close')]")
                close_button.click()
                print("Ad closed.")
                return  # Exit after closing one ad (if multiple, can loop through others)
            except NoSuchElementException:
                continue  # Skip if no close button found in this element

    except Exception as e:
        print(f"Error while attempting to close ads: {e}")

if __name__ == "__main__":
    # scrape_economic_calenders(
    #     is_local=True,
    #     calender_url="https://www.tradingview.com/symbols/EURUSD/economic-calendar"
    # )
    #test()

    scrape_technical_indicators(
        is_local=True,
        indicator_url="https://www.tradingview.com/symbols/EURUSD/technicals"
    )
