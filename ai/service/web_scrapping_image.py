from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains

from webdriver_manager.chrome import ChromeDriverManager


import time
from PIL import Image, ImageDraw, ImageFont
import os


# Set up Chrome options
def scrape_technical_indicators(indicator_url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")  # Starts the browser maximized
    chrome_options.add_argument("--window-size=1920,1080")  # Sets a default window size

    # Set up the Chrome driver
    try:
        chrome_driver_path = r"C:\Windows\chromedriver.exe"  # Replace with your actual path
        service = Service(chrome_driver_path)
        # Initialize Chrome driver with options
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
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
    time.sleep(2)
    driver.set_window_size(1920, 1920)
    # driver.save_screenshot("data/technical_indicators/technicals_1_day_interval.png")

    # second_button_xpath = '//div[@data-name="square-tabs-buttons"]//button[@id="1h"]'
    # second_button = driver.find_element("xpath", second_button_xpath)
    # driver.execute_script("arguments[0].scrollIntoView(true);", second_button)
    # time.sleep(1)  # wait a bit for scrolling
    # driver.execute_script("arguments[0].click();", second_button)
    # # Wait for any potential page changes to take effect
    # time.sleep(3)
    # driver.execute_script("window.scrollBy(0, -100);")
    # driver.save_screenshot("data/technical_indicators/technicals_1_hour_interval.png")

    second_button_xpath = '//div[@data-name="square-tabs-buttons"]//button[@id="15m"]'
    second_button = driver.find_element("xpath", second_button_xpath)
    driver.execute_script("arguments[0].scrollIntoView(true);", second_button)
    time.sleep(1)  # wait a bit for scrolling
    driver.execute_script("arguments[0].click();", second_button)
    # Wait for any potential page changes to take effect
    time.sleep(2)
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

def scrape_economic_calenders(calender_url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")  # Starts the browser maximized
    chrome_options.add_argument("--window-size=1920,1080")  # Sets a default window size

    # Set up the Chrome driver
    try:
        chrome_driver_path = r"C:\Windows\chromedriver.exe"  # Replace with your actual path
        service = Service(chrome_driver_path)
        # Initialize Chrome driver with options
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
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

def scrape_aastocks_chart(url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")  # Starts the browser maximized
    chrome_options.add_argument("--window-size=1920,1080")  # Sets a default window size

    # Set up the Chrome driver
    try:
        chrome_driver_path = r"C:\Windows\chromedriver.exe"  # Replace with your actual path
        service = Service(chrome_driver_path)
        # Initialize Chrome driver with options
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Local Driver: done")
    except:
        chrome_path = '/usr/bin/chromium'
        chromedriver_path = '/usr/bin/chromedriver'
        chrome_options.binary_location = chrome_path
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.get(url)
    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(2)

    button_ids = {"QuickChartPeriod_5m1d_min": "1_day", "QuickChartPeriod_10d_hour": "10_days"} #, "QuickChartPeriod_6m_day"]
    screenshot_directory = "data/chart/"
    screen_shot_width = 3840
    normal_height = 2160
    for button_id, name in button_ids.items():
        # Click the time frame button
        first_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, button_id))
        )
        first_button.click()
        print(f"Clicked button with ID: {button_id}")
        time.sleep(2)

        # Click the second button to open a new window
        second_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "cp5"))
        )
        second_button.click()
        print("Clicked second button")
        time.sleep(2)

        # Switch to the new window
        main_window = driver.current_window_handle
        all_windows = driver.window_handles
        for window in all_windows:
            if window != main_window:
                driver.switch_to.window(window)
                print("Switched to new window")
                break

        time.sleep(2)

        # Perform screenshot in the new window
        action = ActionChains(driver)
        action.click().perform()
        print("Clicked on the page")
        time.sleep(2)

        driver.set_window_size(screen_shot_width, normal_height)

        screenshot_path = f"{screenshot_directory}{name}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Saved screenshot: {screenshot_path}")

        # Close the new window and switch back to the main window
        driver.close()
        driver.switch_to.window(main_window)
        print("Switched back to the main window")
        time.sleep(2)
    
    reduce_width = 650
    reduce_top = 140
    reduce_bottom = 240
    text_boxes = {
    "SMA10(Red), SMA20(Yellow), SMA50(White), SMA100(Orange), SMA150(Pink)": 50,
    "RSI(14)": 835,
    "MACD(12, 16): Red, EMA(9): Green, Divergence: Yellow": 1155,
    "ROC(12)": 1455
    }

    with Image.open(f"{screenshot_directory}10_days.png") as img:
        cropped_img = img.crop((1400, reduce_top, screen_shot_width - reduce_width, normal_height - reduce_bottom))
        draw = ImageDraw.Draw(cropped_img)

        font_size = 20
        try:
            font = ImageFont.truetype("arial.ttf", font_size)  # Use a truetype font
        except IOError:
            font = ImageFont.load_default()  # Use default font if `arial.ttf` is not found

        # Loop through the dictionary to create text boxes
        for text, text_y in text_boxes.items():
            # Calculate text size using textbbox
            text_bbox = draw.textbbox((0, 0), text, font=font)  # Get bounding box of the text
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            # Specify text position (left side, experiment with vertical position)
            text_x = 50  # Distance from the left

            # Draw text box background
            background_box = (text_x - 10, text_y - 10, text_x + text_width + 10, text_y + text_height + 10)
            draw.rectangle(background_box, fill="blue")  # White background for text

            # Add the text
            draw.text((text_x, text_y), text, fill="white", font=font)

        # Save the final image
        cropped_img.save(f"{screenshot_directory}10_days_cropped.png")
    
    with Image.open(f"{screenshot_directory}1_day.png") as img:
        cropped_img = img.crop((reduce_width, reduce_top, screen_shot_width - reduce_width, normal_height - reduce_bottom))
        draw = ImageDraw.Draw(cropped_img)

        font_size = 20
        try:
            font = ImageFont.truetype("arial.ttf", font_size)  # Use a truetype font
        except IOError:
            font = ImageFont.load_default()  # Use default font if `arial.ttf` is not found

        for text, text_y in text_boxes.items():

            text_bbox = draw.textbbox((0, 0), text, font=font)  # Get bounding box of the text
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            text_x = 50  # Distance from the left

            background_box = (text_x - 10, text_y - 10, text_x + text_width + 10, text_y + text_height + 10)
            draw.rectangle(background_box, fill="blue")  # White background for text

            draw.text((text_x, text_y), text, fill="white", font=font)
        cropped_img.save(f"{screenshot_directory}1_day_cropped.png")

    driver.quit()
if __name__ == "__main__":

    from ai.parameters import TECHNICAL_INDICATORS_WEBSITES

    currency_pair = "USD/JPY"

    scrape_economic_calenders(
        calender_url=TECHNICAL_INDICATORS_WEBSITES[currency_pair]["calender"]
    )
    scrape_technical_indicators(
        indicator_url=TECHNICAL_INDICATORS_WEBSITES[currency_pair]["indicator"]
    )

    scrape_aastocks_chart(
        url=TECHNICAL_INDICATORS_WEBSITES[currency_pair]["chart"]
    )