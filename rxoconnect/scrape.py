import time
from random import randint
import numpy as np
from selenium_browser import Browser
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as soup
import pandas as pd
import sys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

start_time = time.time()
URL = "https://xpoconnect.xpo.com/carrier/dashboard/overview"


def scrape_soup(web_elements, df):
    """
       Parses html given from Selenium Web Element using BeautifulSoup .
       Populates dictionary and concatenate to existing pandas dataframe.

       :param web_elements: Selenium WebElement, each representing load row in a website
       :param df: pandas DataFrame
       :returns dataframe with scraped data from a page
    """

    data_dict = dict()
    n = 0
    for element in web_elements:
        e_html = element.get_attribute('outerHTML')
        e_soup = soup(e_html, 'html.parser')
        # assign `.text` value to respective dictionary key if soup finds data, assign empty string otherwise
        try:
            data_dict['load_id'] = e_soup.select_one("div[id*='available-loads-grid-load-number' i]").text.strip()
        except (ValueError, AttributeError):
            data_dict['load_type'] = ""
        loc1 = e_soup.select_one("div[id*='available-loads-grid-origin' i]").text
        loc2 = e_soup.select_one("div[id*='available-loads-grid-dest' i]").text
        data_dict['pick_up_city'], data_dict['pick_up_state'] = loc1.strip().split(',')
        data_dict['pick_up_date'] = e_soup.select_one("div[id*='available-loads-grid-originNA-early-arriv' i]").text.replace('-', '').strip()
        data_dict['deliver_city'], data_dict['deliver_state'] = loc2.strip().split(',')
        data_dict['deliver_date'] = e_soup.select_one("div[id*='available-loads-grid-destNA-early-arriv' i]").text.replace('-', '').strip()
        try:
            price = e_soup.select_one("div[id*='available-loads-grid-load-price-value' i]").text
            data_dict['price'] = float(price.replace("$", "").replace(",", ""))
        except AttributeError:
            data_dict['price'] = np.nan
        try:
            distance = e_soup.select_one("div[id*='available-loads-grid-dist-value' i]").text.split()[0]
            data_dict['distance'] = float(distance)
        except (ValueError, AttributeError):
            data_dict['distance'] = np.nan
        try:
            data_dict['weight'] = e_soup.select_one("div[id*='available-loads-grid-weightNA-value' i]").text.split()[0]
        except (ValueError, AttributeError):
            data_dict['weight'] = np.nan
        try:
            stops = e_soup.select_one("div[id*='available-loads-grid-stops' i]").text
            data_dict['stops'] = stops
        except AttributeError:
            data_dict['stops'] = np.nan
        try:
            data_dict['equipment'] = e_soup.select_one("div[id*='available-loads-grid-equipmtNA-value' i]").text
        except AttributeError:
            data_dict['equipment'] = ""

        hot_deal = e_soup.find("span", {"class": "hot-deals"})
        if hot_deal:
            data_dict['hot deal'] = "yes"
        else:
            data_dict['hot deal'] = "no"

        df = pd.concat([df, pd.DataFrame.from_records([data_dict])])
        n += 1

    return df


def sort_df(df):
    """
    Sort Dataframe in descending order by price column
    """
    df['price'] = df['price'].replace({"bid only": "1", "quick bid": "2", ",": ""}, regex=True).astype(float)
    df.sort_values(by='price', ascending=False, inplace=True)
    df['price'] = df['price'].replace({1: "bid only", 2: "quick bid"})
    return df


def main(browser, df, filename):
    """
        Clicks on 'next' arrow button in pagination, scrape data and
        load to dataframe. Exits when selenium failes to find element.

        :param browser: instantiated Selenium Chrome() browser
        :param df: pandas empty DataFrame
        :param filename: 'data_' + generated current datetime
        :return: final dataframe with scraped data
    """
    try:
        page_num = 1
        while True:
            web_elements = browser.find_web_elements(By.CSS_SELECTOR, "div[id*='available-loads-grid-loadsNA' i]")
            df = scrape_soup(web_elements, df)
            try:
                browser.click_button(by=By.CLASS_NAME, value="mat-paginator-navigation-next")
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as err:
                break

            sys.stdout.write("\rPage %i done" % page_num)
            sys.stdout.flush()
            page_num += 1
            time.sleep(randint(1, 5))
    except:
        df.to_excel(f'{filename}.xlsx', index=False)
    finally:
        browser.close_driver()

    return df


if __name__ == "__main__":
    browser = Browser("chromedriver")
    browser.open_page(URL)
    browser.login_rxo("Username", "pwdlogin", "rxo-focus-indicator.rxo-flat-button.rxo-primary")

    # open loads webpage
    browser.open_page("https://rxoconnect.rxo.com/carrier/loads/available-loads")
    time.sleep(3)
    # click on "Search loads" button
    browser.click_button(by=By.ID, value="available-load-grid-search-allloads-btn")

    df = pd.DataFrame()
    filename = "rxoconnect_" + pd.to_datetime('today').strftime('%d-%m-%Y')
    df = main(browser, df, filename)
    df = sort_df(df)

    df.to_excel(f'{filename}.xlsx', index=False)
    end_time = time.time()
    time_spent = str(int(end_time - start_time)) + " seconds"

    print(f"\nTime spent: {time_spent}" + "\n" +
          f"Scraped records: {len(df)}" + "\n" +
          f"Saved to file '{filename}.xlsx'")
