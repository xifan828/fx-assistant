from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains

import time
from PIL import Image, ImageDraw, ImageFont
import os
from backend.utils.logger_config import get_logger
import threading, time

logger = get_logger(__name__)

class SeleniumScrapper:
    _local = threading.local()

    def __init__(self, driver_path=None, headless: bool = True):

        self.driver_path = "/usr/local/bin/chromedriver"

        # Path to Google Chrome binary
        self.chrome_binary_path = "/opt/google/chrome/chrome" # Or /usr/bin/google-chrome-stable
        logger.info(f"Thread {threading.get_ident()}: SeleniumScrapper __init__ called. Headless: {headless}")

        if getattr(self._local, "driver", None) is None:
            logger.info(f"Thread {threading.get_ident()}: No existing driver found for this thread. Initializing new WebDriver instance.")
            self._local.driver = self._init_driver(headless)
        else:
            logger.info(f"Thread {threading.get_ident()}: Reusing existing WebDriver instance for this thread.")
        self.driver = self._local.driver

    def _init_driver(self, headless: bool):
        logger.info(f"Thread {threading.get_ident()}: _init_driver called. Headless: {headless}")
        opts = Options()
        if headless:
            opts.add_argument("--headless=new")

        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-infobars")
        opts.add_argument("--remote-debugging-port=0")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.page_load_strategy = "eager"
        opts.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/136.0.7103.113 Safari/537.36" # Update this to your Chrome version
        )
        opts.add_experimental_option("prefs", {
            # Block notifications
            "profile.default_content_setting_values.notifications": 2,
            # Disable push and permission dialogs
            "profile.default_content_setting_values.popups": 2,
            "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,
        })
        # Also you can disable cookies entirely if you don’t need them:
        opts.add_argument("--disable-site-isolation-trials")

        # Explicitly set the binary location for Google Chrome
        opts.binary_location = self.chrome_binary_path

        service = Service(
            executable_path=self.driver_path,
            # service_args = ["--verbose"],
            # log_output="chromedriver.log" 
            )
        

        try:
            #logger.info(f"Thread {threading.get_ident()}: Attempting to start Chrome with driver: {self.driver_path} and browser: {self.chrome_binary_path}")
            driver = webdriver.Chrome(service=service, options=opts)
            driver.set_page_load_timeout(60)
            #logger.info(f"Thread {threading.get_ident()}: WebDriver initialized successfully for this thread.")
            return driver
        except Exception as e:
            logger.error(f"Thread {threading.get_ident()}: Failed to initialize WebDriver: {e}", exc_info=True)
            logger.error(f"Using chromedriver: {self.driver_path}, chrome binary: {self.chrome_binary_path}")
            raise

    def wait_for_popup(self, timeout: int = 5):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.any_of( # Use any_of if multiple conditions might indicate a popup
                    EC.presence_of_element_located((By.XPATH, "//*[text()='×']")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(@class,'close')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(@id,'close')]")),
                    EC.presence_of_element_located((By.XPATH, "//button[contains(translate(text(), 'CLOSE', 'close'), 'close')]")) # More robust close button check
                )
            )
            logger.info("Popup indicator appeared.")
            return True # Indicate popup was found
        except Exception:
            logger.info("No popup indicator appeared within %s s.", timeout)
            return False
        
    def close_cookie_banner(self, timeout=5):
        try:
            # Wait until a clear “Accept All” button appears
            btn = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(
                    (By.ID, "onetrust-accept-btn-handler")  # or another reliable locator
                )
            )
            # Scroll into view & click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            btn.click()
            logger.info("Cookie banner accepted.")
            return True
        except TimeoutException:
            logger.info("No cookie banner found after %ss", timeout)
            return False
        except Exception as e:
            logger.warning("Error clicking cookie banner: %s", e)
            return False

    def close_ads(self, max_attempts: int = 3):
        selectors = [
            "//div[contains(@class,'popup') or contains(@class,'modal') or contains(@class,'overlay')]//*[text()='×' or translate(text(), 'CLOSE', 'close')='close' or @aria-label='Close' or contains(@class,'close') or contains(@id,'close')]",
            "//button[contains(text(),'×') or translate(text(), 'CLOSE', 'close')='close' or @aria-label='Close' or contains(@class,'close') or contains(@id,'close')]",
            "//div[contains(@aria-label,'Close') or contains(@aria-label,'close')]",
            "//div[contains(@class,'close') or contains(@id,'close')]",
            "//div[@role='dialog']//button[contains(@class,'close') or @aria-label='Close']",
            "//iframe[contains(@id, 'sp_message_iframe') or contains(@title, 'Privacy Message') or contains(@title, 'Consent')]" # For CMP popups
        ]
        # Handle cookie banners specifically
        cookie_banners = [
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'got it')]",
            "//div[@id='onetrust-accept-btn-handler']", # Common OneTrust ID
            "//button[@id='acceptAllButton']"
        ]

        logger.info("Attempting to close ads/popups/cookie banners...")
        while True:
            clicked_any = False

            for sel in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, sel)
                    for el in elements:
                        if el.is_displayed() and el.is_enabled():
                            logger.info(f"Found popup via {sel}, clicking…")
                            self.driver.execute_script("arguments[0].click();", el)

                            # Wait for that exact element to go away before continuing
                            WebDriverWait(self.driver, 5).until(
                                EC.staleness_of(el)
                            )

                            clicked_any = True
                            # break out of inner loop to restart scanning selectors
                            break
                    if clicked_any:
                        # One closed—there *might* be another
                        break
                except Exception as e:
                    logger.debug(f"Selector {sel} gave error or no match: {e}")

            if not clicked_any:
                # We ran through every selector and clicked nothing
                logger.info("No more popups found.")
                break

        logger.info("Finished close_ads().")

    def quit_driver(self):
        if getattr(self._local, "driver", None):
            logger.info(f"Thread {threading.get_ident()}: Quitting WebDriver instance (Google Chrome). Session ID: {self._local.driver.session_id if hasattr(self._local.driver, 'session_id') else 'N/A'}")
            try:
                self._local.driver.quit()
            except Exception as e:
                logger.error(f"Thread {threading.get_ident()}: Error quitting WebDriver (Google Chrome): {e}", exc_info=True)
            finally:
                self._local.driver = None
                logger.info(f"Thread {threading.get_ident()}: WebDriver instance for this thread set to None.")


# Set up Chrome options
def scrape_technical_indicators(indicator_url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")  # Especially on Windows
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
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

    driver.get(indicator_url)
    close_ads(driver)
    
    driver.execute_script("window.scrollBy(0, 550);")
    time.sleep(2)
    driver.set_window_size(1920, 1920)

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

    driver.quit()

def scrape_economic_calenders(calender_url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")  # Especially on Windows
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
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

def scrape_trading_view_news(news_url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless to avoid opening a browser window
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        chrome_driver_path = r"C:\Windows\chromedriver.exe"
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        chrome_path = '/usr/bin/chromium'
        chromedriver_path = '/usr/bin/chromedriver'
        chrome_options.binary_location = chrome_path
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(news_url)
    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(2)

    wait = WebDriverWait(driver, 10)
    container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-iTt_Zp4a")))

    container_html = container.get_attribute("innerHTML")
    #print("Container HTML:\n", container_html)
    link_elements = container.find_elements(By.TAG_NAME, "a")
    links = [link.get_attribute("href") for link in link_elements]
    #print(link_elements)
    print(links[:10])


    driver.quit()
    return links

def scrape_aastocks_chart(url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")  # Especially on Windows
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
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

    from backend.utils.parameters import TECHNICAL_INDICATORS_WEBSITES

    #currency_pair = "EUR/USD"

    # scrape_economic_calenders(
    #     calender_url=TECHNICAL_INDICATORS_WEBSITES[currency_pair]["calender"]
    # )
    # scrape_technical_indicators(
    #     indicator_url=TECHNICAL_INDICATORS_WEBSITES[currency_pair]["indicator"]
    # )

    # scrape_aastocks_chart(
    #     url=TECHNICAL_INDICATORS_WEBSITES[currency_pair]["chart"]
    # )

    scrape_trading_view_news("https://www.tradingview.com/symbols/EURUSD/news/")
