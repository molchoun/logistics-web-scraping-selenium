import json
import sys
import time
import numpy as np
from bs4 import BeautifulSoup as soup
from selenium.webdriver.support.wait import WebDriverWait
from selenium_browser import Browser
from selenium_browser import get_credentials
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd

URL = "https://b2b-transportationinsight.okta.com/"

start_time = time.time()
def filter_params(file):
    with open(file) as f:
        data = f.read()
    return json.loads(data)


def open_beon_app(browser):
    #  navigate to beon carrier url and submit e-mail
    app_url = browser.find_web_element(by=By.XPATH,
                                       value="//*[@id='main-content']/section/section/section/section/div[2]/a").get_attribute('href')

    try:
        browser.open_page(app_url)
        browser.click_button(by=By.XPATH, value="//button[@class='p-button p-component ntgv_primary ']")
        # browser.send_input(by=By.XPATH, value="/html/body/app-root/div/div[2]/main/app-spa-host/div/div/div/div[1]/input",
        #                    text=get_credentials('credentials.ini')[0])
        # browser.click_button(by=By.XPATH, value="//*[@id='app']/div/div/div[2]/button")
        WebDriverWait(drvr, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        time.sleep(10)
    except TimeoutException as err:
        print("Page didn't load correctly, try running the script again.\n", err)
        sys.exit()


def pick_radius(browser, orig_radius, del_radius):
    # find slider element and move to according parameter
    radius1 = browser.find_web_element(by=By.XPATH, value="//*[@id='app']/div[2]/div[1]/div/div[1]/div/div[3]/div/span[2]")
    radius2 = browser.find_web_element(by=By.XPATH, value="//*[@id='app']/div[2]/div[1]/div/div[1]/div/div[5]/div/span[2]")
    move = ActionChains(drvr)
    # wrap in try/except as after page loads website occasionally reloads page
    try:
        move.click_and_hold(radius1).move_by_offset(int(orig_radius), 0).release().perform()
        move.click_and_hold(radius2).move_by_offset(int(del_radius), 0).release().perform()
    except MoveTargetOutOfBoundsException:
        time.sleep(3)
        radius1 = browser.find_web_element(by=By.XPATH,
                                           value="//*[@id='app']/div[2]/div[1]/div/div[1]/div/div[2]/div/span[2]")
        radius2 = browser.find_web_element(by=By.XPATH,
                                           value="//*[@id='app']/div[2]/div[1]/div/div[1]/div/div[4]/div/span[2]")
        move.click_and_hold(radius1).move_by_offset(250, 0).release().perform()
        move.click_and_hold(radius2).move_by_offset(250, 0).release().perform()


def pick_dates(browser, day_interval):
    # click datepicker calendar button
    browser.click_button(by=By.XPATH, value="//*[@id='app']/div[2]/div[1]/div/div[1]/div/div[6]/span[2]/button/span[1]")
    # click on today's date element
    browser.click_button(by=By.CSS_SELECTOR, value="body > div > div.p-datepicker-group-container > div > "
                                                   "div.p-datepicker-calendar-container > table > tbody > "
                                                   "tr:nth-child(4) > td.p-datepicker-today > span")
    to_date = (pd.to_datetime('today') + pd.Timedelta(days=day_interval)).strftime('%B-%-d')
    month, day = to_date.split('-')
    pickup_dates = browser.find_web_elements(by=By.TAG_NAME, value="td")
    pickup_month = browser.find_web_element(by=By.CLASS_NAME, value="p-datepicker-month")
    while True:
        if month == pickup_month.text:
            for date in pickup_dates:
                if day == date.text:
                    date.click()
                    # click confirm button in calendar
                    browser.click_button(by=By.XPATH, value="/html/body/div/div[2]/div/div[2]/button/span")
                    time.sleep(1)
                    break
            break
        datepicker_next = browser.find_web_element(by=By.XPATH, value="/html/body/div/div[1]/div/div[1]/button[2]/span")
        datepicker_next.click()
        pickup_month = browser.find_web_element(by=By.CLASS_NAME, value="p-datepicker-month")
        pickup_dates = browser.find_web_elements(by=By.TAG_NAME, value="td")


def retrying_get_attr(drvr, url):
    attempts = 0
    while attempts < 1:
        try:
            url = url.get_attribute('href')
            return url
        except StaleElementReferenceException:
            attempts += 1
    return None


def rows_per_page(browser):
    # if load area is loaded click on 'rows per page' dropdown field and click on max count, exit otherwise
    try:
        browser.click_button(by=By.XPATH, value="//*[@id='app']/div[2]/div[2]/div/div[13]/div/div/div/div[3]/span")
        browser.click_button(by=By.XPATH, value="/html/body/div/div/ul/li[4]")
    except TimeoutException as err:
        print("Error occurred during loading web page, please rerun the script.\n", err)
        sys.exit()


def scrape_loads(browser):
    n = 0
    load_id, origin_city, origin_state, date1, delivery_city, delivery_state, date2, distance, stops, weight, equip, view = [[] for i in range(12)]
    while True:
        urls = browser.find_web_elements(by=By.XPATH, value="//a[@class='yG0JhEyfj-9Yv-P+TXqWag==']")
        for url in urls:
            url = retrying_get_attr(drvr, url)
            if not url:
                continue
            view.append(url)
        loads_selen = browser.find_web_element(by=By.XPATH, value="//*[@id='app']/div[2]/div[2]/div")
        e_soup = soup(loads_selen.get_attribute("innerHTML"), 'html.parser')
        loads = e_soup.select(".KbTBMYEUoamXo1NoPjkmjg\=\=")
        for load in loads:
            load_id.append(load.select_one(".eWuxVQqn84eM6A5SV1z7VQ\=\=").text)
            origin_city.append(load.select_one(".fyoy3f9tItKU74O8yTwFvQ\=\= .qZK4iPHf-3A2tqtETvGbEw\=\=").text.split(',')[0].title())
            origin_state.append(load.select_one(".fyoy3f9tItKU74O8yTwFvQ\=\= .qZK4iPHf-3A2tqtETvGbEw\=\=").text.split(',')[1].strip())
            date1.append(load.select_one("._6\+RYFQYCZe1SqQNK9VUylw\=\=").text.split('-')[0])
            delivery_city.append(load.select_one(".Y5Q4FAX6PQJcKtxXtv08rQ\=\= .qZK4iPHf-3A2tqtETvGbEw\=\=").text.split(',')[0].title())
            delivery_state.append(load.select_one(".Y5Q4FAX6PQJcKtxXtv08rQ\=\= .qZK4iPHf-3A2tqtETvGbEw\=\=").text.split(',')[1].strip())
            date2.append(load.select_one("._6\+RYFQYCZe1SqQNK9VUylw\=\=").text.split('-')[1])
            distance.append(load.select_one(".text_gray").text.strip().split()[0].replace(",", ""))
            stops.append(load.select_one("span:nth-child(1) .qZK4iPHf-3A2tqtETvGbEw\=\=").text)
            weight.append(load.select_one("span+ span .qZK4iPHf-3A2tqtETvGbEw\=\=").text.replace(",", ""))
            equip.append(load.select_one(".iconInfo").text)
        n += len(urls)
        sys.stdout.write("\r%i loads extracted" % n)
        sys.stdout.flush()
        try:
            nxt = browser.find_web_element(by=By.XPATH, value="//*[@id='app']/div[2]/div[2]/div/div[123]/div/button[2]")
        except TimeoutException:
            break
        nxt.click()
    df = pd.DataFrame(np.column_stack([load_id, origin_city, origin_state, date1, delivery_city, delivery_state, date2,
                                       distance, stops, weight, equip, view]),
                      columns=['load_id', 'pick_up_city', 'pick_up_state', 'pick_up_date', 'deliver_city', 'delivery_state',
                               'deliver_date', 'distance', 'stops', 'weight', 'equipment', 'view'])
    return df


if __name__ == "__main__":
    print("Running...")
    browser = Browser("chromedriver")
    drvr = browser.driver
    browser.open_page(URL)
    browser.login_beon("input#okta-signin-username", "input#okta-signin-password", "okta-signin-submit")
    open_beon_app(browser)

    # unpack search filter parameters
    day_interval, origin_radius, delivery_radius = filter_params("filter_parameters.txt").values()
    pick_radius(browser, origin_radius, delivery_radius)
    pick_dates(browser, day_interval)

    # apply search filter parameters by clicking apply button
    browser.click_button(by=By.XPATH, value="//*[@id='app']/div[2]/div[1]/div/div[2]/div[2]/button")
    rows_per_page(browser)
    time.sleep(3)

    df = scrape_loads(browser)
    drvr.close()

    filename = "beoncarrier_" + pd.to_datetime('today').strftime('%d-%m-%Y') + "_links"
    df.to_excel(f'{filename}.xlsx', index=False)
    end_time = time.time()
    time_spent = str(int(end_time - start_time)) + " seconds"

    print(f"\nTime spent: {time_spent}" + "\n" +
          f"Scraped records: {len(df)}" + "\n" +
          f"Saved to file '{filename}.xlsx'")


