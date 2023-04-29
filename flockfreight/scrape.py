import json
import sys
import time
import numpy as np
import os
from bs4 import BeautifulSoup as soup
from selenium_browser import Browser
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotInteractableException
import pandas as pd

URL = "https://app.flockfreight.com/search-loads"

start_time = time.time()
def filter_params(file):
    with open(file) as f:
        data = f.read()
    return json.loads(data)


def login_to_website():
    try:
        browser.open_page(URL)
        browser.login_dat("input#mui-1", "input#mui-2", "button#mui-3")
    except TimeoutException as err:
        print("Error occurred during loading web page, please rerun the script.\n", err)
        drvr.quit()
        sys.exit()
    print("Successfully logged in to website.\n")

def soup_scrape(loads):

    cnt = 1
    data_dict = dict()
    df = pd.DataFrame()
    html = loads.get_attribute('innerHTML')
    e_soup = soup(html, 'html.parser')
    loads_soup = e_soup.select("div.css-1ek12j9")
    load_count = len(loads_soup)
    print("Starting to scrape loads data.")
    for load in loads_soup:
        data_dict["pick_up_city"] = load.select_one(".css-137cxoo:nth-child(1) .css-1p3b6x9").text.split(',')[0].title()
        data_dict["pick_up_state"] = load.select_one(".css-137cxoo:nth-child(1) .css-1p3b6x9").text.split(',')[1].strip()
        data_dict["pick_up_date"] = load.select_one(".css-137cxoo:nth-child(1) .css-luip82").text
        data_dict["deliver_city"] = load.select_one(".css-19ocola+ .css-137cxoo .css-1p3b6x9").text.split(',')[0].title()
        data_dict["deliver_state"] = load.select_one(".css-19ocola+ .css-137cxoo .css-1p3b6x9").text.split(',')[1].strip()
        data_dict["delivery_date"] = load.select_one(".css-19ocola+ .css-137cxoo .css-luip82").text
        price = load.select_one(".css-2eyou9 span").text
        if price.startswith('$'):
            data_dict["price"] = int(float(price.replace('$', '').replace(',', '')))
        else:
            data_dict["price"] = np.nan
        data_dict["distance"] = load.select_one("#carrier-reference-link div:nth-child(2) .css-eukk67").text.split()[0].replace(",", "")
        data_dict["weight"] = load.select_one("#carrier-reference-link div~ div+ div .css-eukk67 span").text.replace(",", "")
        data_dict["stops"] = load.select_one(".css-ql7nd0+ .css-ql7nd0").text.split()[0]
        data_dict["DH-O"] = load.select_one(".css-eukk67+ .css-ql7nd0").text.split()[0]

        df = pd.concat([df, pd.DataFrame.from_records([data_dict])])
        sys.stdout.write(f"\r{cnt} from {load_count} scraped.")
        sys.stdout.flush()
        cnt += 1
    print("\nDone")

    return df


def sort_df(df):
    """
    Sort Dataframe in descending order by price column
    """
    df["price"] = df["price"].astype(float)
    df.sort_values(by='price', ascending=False, inplace=True)
    params = filter_params("filter_parameters.json")
    eq_type = params["equip_type"]["53' Dry Van"]
    df["equipment_type"] = eq_type
    df["website"] = os.path.basename(os.path.dirname(__file__))
    return df


def select_city(city):
    browser.send_input(by=By.CSS_SELECTOR, value="input#rows-0-originCityState-desktop", text=city)
    time.sleep(1)


def pick_radius(distance1):
    orig_selector = "input#rows-0-originLocationRadius-desktop"
    browser.find_web_element(by=By.CSS_SELECTOR, value=orig_selector).send_keys(Keys.CONTROL + "a")
    browser.find_web_element(by=By.CSS_SELECTOR, value=orig_selector).send_keys(distance1)



def select_equipment(eq_type):
    selector = f"//select[@id='rows-0-trailerType-desktop']/option[@value='{eq_type}']"
    browser.click_button(by=By.ID, value="rows-0-trailerType-desktop")
    drvr.find_element(by=By.XPATH, value=selector).click()



def pick_dates(day_interval):
    # click on datepicker button to open calendar window
    browser.click_button(by=By.CSS_SELECTOR, value="input#rows-0-availableDates-desktop + input")
    # click on today's date
    drvr.find_element(by=By.CSS_SELECTOR, value="div.arrowTop div > span.flatpickr-day.today").click()
    # find all available dates of current month
    month1 = browser.find_web_elements(by=By.CSS_SELECTOR, value=".open span.flatpickr-day.today ~ span")
    len1 = len(month1)
    for i in range(len1):
        # find next element of selected element
        element = drvr.find_element(by=By.CSS_SELECTOR, value=".open span.flatpickr-day.selected ~ :not(.selected)")
        element.click()
        time.sleep(0.5)
    if day_interval > len(month1):
        browser.click_button(by=By.CSS_SELECTOR, value=".open .flatpickr-next-month")
        for i in range(day_interval - len1):
            element = drvr.find_element(by=By.CSS_SELECTOR, value=".open span.flatpickr-day.selected ~ :not(.selected)")
            element.click()
            time.sleep(0.5)
            try:
                browser.find_web_element(by=By.CSS_SELECTOR, value=".open .flatpickr-next-month").click()
            except (TimeoutException, ElementNotInteractableException):
                pass


def filter_search():
    print("Applying search filtering parameters:")
    params = filter_params("filter_parameters.json")
    day_interval = params["days"]["day_interval"]
    orig_radius = params["radius"]["orig_radius"]
    eq_type = params["equip_type"]["53' Dry Van"]
    city = params["location"]["city"] + ', ' + params["location"]["state"]
    print(f"Location: {city}, \n"
          f"Equipment type: {eq_type}, \n"
          f"Origin radius: {orig_radius}, \n"
          f"Day interval: {day_interval}\n")
    # navigate to 'search loads' page
    browser.find_web_element(by=By.XPATH, value="//a[@data-track='carrier__nav__search_loads']").click()
    time.sleep(2)

    pick_dates(day_interval)
    select_city(city)
    pick_radius(orig_radius)
    select_equipment(eq_type)
    browser.click_button(by=By.CSS_SELECTOR, value="button#save-button")
    time.sleep(5)


def get_loads():
    loads_sln = browser.find_web_element(by=By.CSS_SELECTOR, value="div.MuiBox-root.css-2flcaf + div")
    return loads_sln


def logout():
    browser.click_button(by=By.XPATH, value="//button[@aria-label='User Menu']")
    browser.click_button(by=By.CSS_SELECTOR, value="li.MuiMenuItem-root")
    drvr.quit()


def main():
    login_to_website()
    filter_search()
    loads_selen = get_loads()
    df = soup_scrape(loads_selen)
    df = sort_df(df)
    try:
        logout()
    except TimeoutException:
        pass

    return df


if __name__ == "__main__":
    print("Running...")
    browser = Browser("chromedriver")
    drvr = browser.driver

    df = main()
    filename = "flockfreight_" + pd.to_datetime('today').strftime('%d-%m-%Y')
    df.to_excel(f'{filename}.xlsx', index=False)

    end_time = time.time()
    time_spent = str(int(end_time - start_time)) + " seconds"

    print(f"\nTime spent: {time_spent}" + "\n" +
          f"Scraped records: {len(df)}" + "\n" +
          f"Saved to file '{filename}.xlsx'")


