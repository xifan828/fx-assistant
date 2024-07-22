from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Set up Chrome options
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
driver.save_screenshot("screenshot_1.png")

second_button_xpath = '(//div[@class="block-sjmalUvv"]//button)[2]'
second_button = driver.find_element("xpath", second_button_xpath)
second_button.click()

# Wait for any potential page changes to take effect
time.sleep(3)

# Optional: take another screenshot after clicking the button
driver.save_screenshot("screenshot_2.png")

third_button_xpath = '(//div[@class="block-sjmalUvv"]//button)[3]'
third_button = driver.find_element("xpath", third_button_xpath)
third_button.click()

time.sleep(3)

# Optional: take another screenshot after clicking the button
driver.save_screenshot("screenshot_3.png")


# Close the browser
driver.quit()
