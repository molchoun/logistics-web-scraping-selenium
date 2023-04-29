from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import json
import time



def filter_params(file):
    with open(file) as f:
        data = f.read()
    return json.loads(data)


class Browser(Chrome):
    """
        The Browser object contains custom methods for clicking the button,
        sending inputs, finding element etc. Once instantiated it returns selenium WebDriver object.
        It inherits `selenium.webdriver.Chrome` class.

        :param driver: selenium WebDriver object
    """
    driver, service = None, None

    chrome_options = Options()
    # chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument('--headless')  # allows execution of the browser while controlling it programmatically
    chrome_options.add_argument("--disable-notifications")  # disables in-browser notification
    chrome_options.add_argument('--no-sandbox')

    def __init__(self, driver):
        self.service = Service(driver)
        self.driver = Chrome(options=self.chrome_options)
        self.driver.set_window_size(1920, 1080)

    def open_page(self, url):
        self.driver.get(url)

    def close_driver(self):
        self.driver.close()

    def send_input(self, by: By, value, text):
        WebDriverWait(self.driver, 2)
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((by, value)))
        input = self.driver.find_element(by=by, value=value)
        input.send_keys(text)
        time.sleep(1)

    def click_button(self, by: By, value):
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((by, value)))
        button = self.driver.find_element(by=by, value=value)
        button.click()
        time.sleep(1)

    def find_web_elements(self, by, value):
        web_elements = self.driver.find_elements(by, value=value)
        return web_elements

    def login_dat(self, val_uname, val_pword, val_submit):
        username, password = filter_params('credentials.json')["username"], filter_params('credentials.json')["password"]
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, val_uname)))
        self.send_input(by=By.CSS_SELECTOR, value=val_uname, text=username)
        self.send_input(by=By.CSS_SELECTOR, value=val_pword, text=password)
        self.click_button(by=By.CSS_SELECTOR, value=val_submit)
        time.sleep(3)

    def find_web_element(self, by: By, value):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((by, value)))
        web_element = self.driver.find_element(by=by, value=value)
        return web_element

