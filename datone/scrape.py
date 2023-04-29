import json
import sys
import time
import numpy as np
from bs4 import BeautifulSoup as soup
from selenium_browser import Browser
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotInteractableException
import pandas as pd

URL = "https://power.dat.com"

start_time = time.time()
def filter_params(file):
    with open(file) as f:
        data = f.read()
    return json.loads(data)


def login_to_website():
    try:
        browser.open_page(URL)
        browser.login_dat("input#mat-input-1", "input#mat-input-0", "button#submit-button")
    except TimeoutException as err:
        print("Error occurred during loading web page, please rerun the script.\n", err)
        drvr.quit()
        sys.exit()
    try:
        drvr.find_element(by=By.CSS_SELECTOR, value="button.confirm").click()
    except (TimeoutException, ElementNotInteractableException) as err:
        pass
    print("Successfully logged in to website.")

def soup_scrape(loads):

    cnt = 1
    data_dict = dict()
    df = pd.DataFrame()
    html = loads.get_attribute('innerHTML')
    e_soup = soup(html, 'html.parser')
    loads_soup = e_soup.select("tr.resultSummary")
    load_count = len(loads_soup)
    print("Starting to scrape loads data.")
    for load in loads_soup:
        data_dict["pick_up_city"] = load.select_one(".origin").text.split(',')[0].title()
        data_dict["pick_up_state"] = load.select_one(".origin").text.split(',')[1].strip()
        data_dict["pick_up_date"] = load.select_one(".avail").text + "/2023"
        data_dict["deliver_city"] = load.select_one(".dest").text.split(',')[0].title()
        data_dict["deliver_state"] = load.select_one(".dest").text.split(',')[1].strip()
        price = load.select_one(".rate").text
        if price.startswith('$'):
            data_dict["price"] = int(float(price.replace('$', '').replace(',', '')))
        else:
            data_dict["price"] = np.nan
        data_dict["distance"] = load.select_one(".do").text
        data_dict["length"] = load.select_one(".length").text.split()[0]
        data_dict["weight"] = load.select_one(".weight").text.replace(",", "").split()[0]
        data_dict["truck"] = load.select_one(".truck").text
        data_dict["fp"] = load.select_one(".fp").text
        data_dict["trip"] = load.select_one(".trip").text.replace(",", "")
        data_dict["company"] = load.select_one(".company").text.replace("\n", "").strip()
        data_dict["contact"] = load.select_one(".contact").text
        data_dict["cs"] = load.select_one(".cs").text
        data_dict["dtp"] = load.select_one(".dtp").text

        df = pd.concat([df, pd.DataFrame.from_records([data_dict])])
        sys.stdout.write(f"\r{cnt} from {load_count} done.")
        sys.stdout.flush()
        cnt += 1

    return df


def sort_df(df):
    """
    Sort Dataframe in descending order by price column
    """
    df["length"] = df["length"].replace("—", np.nan)
    df["weight"] = df["weight"].replace("—", np.nan)
    df["trip"] = df["trip"].replace("—", np.nan)
    df["cs"] = df["cs"].replace("—", np.nan)
    df["dtp"] = df["dtp"].replace("—", np.nan)
    df["price"] = df["price"].astype(float)
    df.sort_values(by='price', ascending=False, inplace=True)
    return df


def select_city(city):
    browser.send_input(by=By.CSS_SELECTOR, value="input.ui-autocomplete-input", text=city)
    time.sleep(1)


def pick_radius(distance):
    rad_selector = "td.dho input"
    browser.find_web_element(by=By.CSS_SELECTOR, value=rad_selector).send_keys(Keys.CONTROL + "a")
    browser.send_input(by=By.CSS_SELECTOR, value=rad_selector, text=distance)


def select_equipment(eq_type):
    browser.click_button(by=By.ID, value="s2id_autogen2")
    time.sleep(3)
    web_elem = browser.find_web_elements(by=By.CSS_SELECTOR, value="div.select2-formatresult-code")
    for elem in web_elem:
        if eq_type == elem.text:
            elem.click()
            break


def pick_dates(day_interval):
    from_date = pd.to_datetime('today').strftime("%m/%d")
    to_date = (pd.to_datetime('today') + pd.Timedelta(days=day_interval)).strftime('%m/%d')
    interval = from_date + "-" + to_date
    cal_selector = "tbody.isNew td.avail  input"
    browser.find_web_element(by=By.CSS_SELECTOR, value=cal_selector).clear()
    browser.send_input(by=By.CSS_SELECTOR, value=cal_selector, text=interval)


def filter_search():
    print("Applying search filtering parameters:")
    params = filter_params("filter_parameters.json")
    day_interval = params["days"]["day_interval"]
    distance = params["radius"]["distance"]
    eq_type = params["equip_type"]["Vans (Standard)"]
    city = params["city"]["name"]
    print(f"Location: {city}, \n"
          f"Equipment type: {eq_type}, \n"
          f"Distance: {distance}, \n"
          f"Day interval: {day_interval}")
    # navigate to 'search loads' page
    browser.open_page("https://power.dat.com/search/loads")
    # click on 'new load search' button
    browser.click_button(by=By.CSS_SELECTOR, value="#searchList > button")
    time.sleep(2)

    select_equipment(eq_type)
    select_city(city)
    pick_dates(day_interval)
    pick_radius(distance)
    browser.click_button(by=By.CSS_SELECTOR, value="button.search.qa-search-button")
    time.sleep(3)


def scroll_to_bottom():
    print("Fetching loads data: it may take a minute.")
    scroll_pause_time = 2
    last_height = drvr.execute_script("return document.querySelector('.searchResultsTable').scrollHeight")
    while True:
        drvr.execute_script(f"document.querySelector('#searchResults > div.fixed-table-container-inner').scrollBy(0, {last_height})")
        time.sleep(scroll_pause_time)
        # Calculate new scroll height and compare with last scroll height
        new_height = drvr.execute_script("return document.querySelector('#searchResults > div.fixed-table-container-inner').scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def get_loads():
    loads_sln = browser.find_web_element(by=By.CSS_SELECTOR, value="table.searchResultsTable")
    return loads_sln


def logout():
    browser.click_button(by=By.ID, value="user-salutation")
    browser.click_button(by=By.ID, value="logout")
    drvr.quit()


def main():
    login_to_website()
    filter_search()
    scroll_to_bottom()
    loads_selen = get_loads()
    df = soup_scrape(loads_selen)
    df = sort_df(df)
    logout()

    return df

if __name__ == "__main__":
    print("Running...")
    browser = Browser("chromedriver")
    drvr = browser.driver

    df = main()
    filename = "datone_" + pd.to_datetime('today').strftime('%d-%m-%Y')
    df.to_excel(f'{filename}.xlsx', index=False)

    end_time = time.time()
    time_spent = str(int(end_time - start_time)) + " seconds"

    print(f"\nTime spent: {time_spent}" + "\n" +
          f"Scraped records: {len(df)}" + "\n" +
          f"Saved to file '{filename}.xlsx'")


