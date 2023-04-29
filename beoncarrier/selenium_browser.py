from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import configparser
import time



def get_credentials(filename):
    """
        Reads file and gets an option value for a given section.

        :return: tuple with username and password
    """
    config = configparser.ConfigParser()
    config.read(filename)
    username = config.get('credentials', 'username')
    password = config.get('credentials', 'password')
    return username, password


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
    # chrome_options.add_argument('--headless')  # allows execution of the browser while controlling it programmatically
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-notifications")  # disables in-browser notification
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    def __init__(self, driver):
        # super(Browser, self).__init__()
        self.service = Service(driver)
        self.driver = Chrome(options=self.chrome_options)
        # self.driver.maximize_window()
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

    def login_beon(self, val_uname, val_pword, val_submit):
        username, password = get_credentials('credentials.ini')
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, val_uname)))
        self.send_input(by=By.CSS_SELECTOR, value=val_uname, text=username)
        self.send_input(by=By.CSS_SELECTOR, value=val_pword, text=password)
        # self.click_button(by=By.NAME, value="button")
        self.click_button(by=By.ID, value=val_submit)
        time.sleep(10)

    def find_web_element(self, by: By, value):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((by, value)))
        web_element = self.driver.find_element(by=by, value=value)
        return web_element

