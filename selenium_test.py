import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Configure basic logging to see output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simple_selenium_test():
    logger.info("Starting simple Selenium test...")

    driver_path = "/usr/local/bin/chromedriver"
    chrome_binary_path = "/opt/google/chrome/chrome" # Or /usr/bin/google-chrome-stable

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--remote-debugging-port=0") # Try with a fixed port first for debugging
    # opts.add_argument("--remote-debugging-port=9222") # For debugging
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36" # Update to your actual Chrome version
    )
    opts.binary_location = chrome_binary_path

    service = Service(executable_path=driver_path)

    driver = None
    try:
        logger.info(f"Attempting to initialize WebDriver with driver: {driver_path} and browser: {chrome_binary_path}")
        driver = webdriver.Chrome(service=service, options=opts)
        logger.info("WebDriver initialized successfully.")

        logger.info("Attempting to get a simple page (google.com)...")
        driver.get("https://www.google.com")
        logger.info(f"Page title: {driver.title}")
        logger.info("Successfully fetched page.")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if driver:
            logger.info("Quitting driver.")
            driver.quit()
            logger.info("Driver quit.")
        logger.info("Simple Selenium test finished.")

if __name__ == "__main__":
    simple_selenium_test()