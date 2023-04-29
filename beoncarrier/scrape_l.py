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
        WebDriverWait(drvr, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        time.sleep(10)
    except TimeoutException as err:
        print("Page didn't load correctly, try running the script again.\n", err)
        exit()


def pick_radius(browser, orig_radius, del_radius):
    # find slider element and move to according parameter
    # xpath may change occasionally
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
    # xpath may change occasionally
    browser.click_button(by=By.XPATH, value="//*[@id='app']/div[2]/div[1]/div/div[1]/div/div[6]/span[2]/button/span[1]")
    # click on today's date element
    # xpath may change occasionally
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

def open_tab(drvr, url):
    drvr.execute_script("window.open('');")
    drvr.switch_to.window(drvr.window_handles[1])
    browser.open_page(url)


def close_tab(drvr):
    drvr.close()
    drvr.switch_to.window(drvr.window_handles[0])


def retrying_get_attr(drvr, url):
    attempts = 0
    while attempts < 3:
        try:
            url = url.get_attribute('href')
            return url
        except StaleElementReferenceException:
            attempts += 1
    return None


def soup_scrape(page_urls):
    page_num = 1
    data_dict = dict()
    df = pd.DataFrame()
    url_count = len(page_urls)
    try:
        for url in page_urls:
            try:
                open_tab(drvr, url)
            except:
                close_tab(drvr)
                continue
            try:
                web_element = browser.find_web_element(by=By.XPATH, value="//*[@id='app']/div/div[4]/div")
            except TimeoutException:
                close_tab(drvr)
                continue
            html = web_element.get_attribute('innerHTML')
            e_soup = soup(html, 'html.parser')
            try:
                data_dict["load_id"] = e_soup.select_one(".p-sm-6:nth-child(1) .infoLabelVal").text
            except AttributeError:
                continue
            data_dict["pick_up_city"] = e_soup.select_one(".p-sm-6:nth-child(3) .infoLabelVal").text.split(',')[0].title()
            data_dict["pick_up_state"] = e_soup.select_one(".p-sm-6:nth-child(3) .infoLabelVal").text.split(',')[1].strip()
            data_dict["pick_up_date"] = e_soup.select_one(".ntgv_panel_content:nth-child(1) .p-sm-4:nth-child(3) .NV0DXDiEpz7c6zBMe-tP-A\=\= , .ntgv_panel_content:nth-child(1) .p-sm-12+ .p-sm-4 .NV0DXDiEpz7c6zBMe-tP-A\=\=").text
            data_dict["deliver_city"] = e_soup.select_one(".p-sm-6:nth-child(4) .infoLabelVal").text.split(',')[0].title()
            data_dict["deliver_state"] = e_soup.select_one(".p-sm-6:nth-child(4) .infoLabelVal").text.split(',')[1].strip()
            data_dict["deliver_date"] = e_soup.select_one(".ntgv_panel_content+ .ntgv_panel_content .p-sm-4 .NV0DXDiEpz7c6zBMe-tP-A\=\=").text
            try:
                price = e_soup.find('div', class_="-vkYYNwHkNe4nznyFr-nUA==").text
                data_dict["price"] = int(float(price.replace('$', '').replace(',', '')))
            except AttributeError:
                data_dict["price"] = np.nan
            data_dict["distance"] = e_soup.select_one(".p-sm-6:nth-child(5) .infoLabelVal").text
            try:
                data_dict["stops"] = e_soup.select_one(".p-sm-6+ .p-sm-6 .infoLabelVal").text
            except AttributeError:
                data_dict["stops"] = ""
            try:
                data_dict["weight"] = e_soup.select_one(".p-sm-6:nth-child(6) .infoLabelVal").text.replace(",", "")
            except AttributeError:
                data_dict["weight"] = ""
            try:
                data_dict["set_temperature"] = e_soup.select_one(".p-sm-12~ .p-sm-12+ .p-sm-12 .infoLabelVal").text
            except AttributeError:
                data_dict["set_temperature"] = ""
            data_dict["equipment"] = e_soup.select_one(".p-sm-6+ .p-sm-12 .infoLabelVal").text
            data_dict["product_category"] = e_soup.select_one(".p-sm-12:nth-child(8) .infoLabelVal").text
            try:
                data_dict["cargo_info"] = e_soup.select_one(".infoLabelVal div").text
            except AttributeError:
                data_dict["cargo_info"] = ""
            try:
                data_dict["load_reqs"] = e_soup.select_one(".p-tag-value").text
            except AttributeError:
                data_dict["load_reqs"] = ""
            close_tab(drvr)
            df = pd.concat([df, pd.DataFrame.from_records([data_dict])])
            sys.stdout.write(f"\rPage {page_num} from {url_count} done.")
            sys.stdout.flush()
            page_num += 1
            time.sleep(1)
    except:
        df.to_excel(f'{filename}.xlsx', index=False)
        end_time = time.time()
        time_spent = str(int(end_time - start_time)) + " seconds"

        print("Error occured during fetching the data - not all data fetched.")
        print(f"\nTime spent: {time_spent}" + "\n" +
              f"Scraped records: {len(df)}" + "\n" +
              f"Saved to file '{filename}.xlsx'")
        drvr.quit()
        exit()
    drvr.quit()

    return df


def rows_per_page(browser):
    # if load area is loaded click on 'rows per page' dropdown field and click on max count, exit otherwise
    try:
        browser.click_button(by=By.XPATH, value="//*[@id='app']/div[2]/div[2]/div/div[13]/div/div/div/div[3]/span")
        browser.click_button(by=By.XPATH, value="/html/body/div/div/ul/li[4]")
    except TimeoutException as err:
        print("Error occurred during loading web page, please rerun the script.\n", err)
        exit()


def get_page_urls(browser):
    page_urls = []
    while True:
        urls = browser.find_web_elements(by=By.XPATH, value="//a[@class='yG0JhEyfj-9Yv-P+TXqWag==']")
        # page_urls += urls
        for url in urls:
            url = retrying_get_attr(drvr, url)
            if not url:
                continue
            page_urls.append(url)
        try:
            nxt = browser.find_web_element(by=By.XPATH, value="//*[@id='app']/div[2]/div[2]/div/div[123]/div/button[2]")
        except TimeoutException:
            break
        nxt.click()
    return page_urls


def sort_df(df):
    """
    Sort Dataframe in descending order by price column
    """
    df["price"] = df["price"].astype(float)
    df.sort_values(by='price', ascending=False, inplace=True)
    return df

if __name__ == "__main__":
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

    page_urls = get_page_urls(browser)
    filename = "beoncarrier_" + pd.to_datetime('today').strftime('%d-%m-%Y')
    df = soup_scrape(page_urls)
    df = sort_df(df)

    df.to_excel(f'{filename}.xlsx', index=False)
    end_time = time.time()
    time_spent = str(int(end_time - start_time)) + " seconds"

    print(f"\nTime spent: {time_spent}" + "\n" +
          f"Scraped records: {len(df)}" + "\n" +
          f"Saved to file '{filename}.xlsx'")


