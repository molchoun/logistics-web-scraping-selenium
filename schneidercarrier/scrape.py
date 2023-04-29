import json
import time
from random import randint
from selenium_browser import Browser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup as soup
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import numpy as np
import sys

start_time = time.time()
URL = "https://schneidercarrier.b2clogin.com/schneidercarrier.onmicrosoft.com/oauth2/v2.0/authorize?p" \
      "=b2c_1a_signup_signin&client_id=19bdee4a-2166-40a9-bfa9-f9aaf19f2950&redirect_uri=https%3A%2F%2Ffreightpower" \
      ".schneider.com%2Fcarrier%2Flogin&audience=https%3A%2F%2Fgraph.microsoft.com&nonce=MW6hdvGWel4R.UY-ShU4&state" \
      "=MW6hdvGWel4R.UY-ShU4&scope=openid+offline_access+https%3A%2F%2Fschneidercarrier.onmicrosoft.com%2Fapi" \
      "%2Freadscope+https%3A%2F%2Fschneidercarrier.onmicrosoft.com%2Fapi%2Fwritescope&response_type=id_token+token" \
      "&response_mode=fragment"


def scrape_soup(web_elements, df):
    """
       Parses html given from Selenium Web Element using BeautifulSoup .
       Populates dictionary and concatenate to existing pandas dataframe.

       :param web_elements: Selenium WebElement, each representing load row in a website
       :param df: pandas DataFrame
       :returns dataframe with scraped data from a page
    """
    data_dict = dict()
    for element in web_elements:
        e_html = element.get_attribute('innerHTML')
        e_soup = soup(e_html, 'html.parser')
        data_dict["load_id"] = e_soup.find("p", {"class": "card_p-elements"}).text
        data_dict["pick_up_city"] = e_soup.find_all("p", {"class": "origin_city"})[0].text.split(',')[0].title()
        data_dict["pick_up_state"] = e_soup.find_all("p", {"class": "origin_city"})[0].text.split(',')[1].strip()
        data_dict["pick_up_date"] = e_soup.select("p.origin_dateTime.load_header_elements.stop-appointment.margin_top")[0].text
        data_dict["deliver_city"] = e_soup.find_all("p", {"class": "origin_city"})[1].text.split(',')[0].title()
        data_dict["deliver_state"] = e_soup.find_all("p", {"class": "origin_city"})[1].text.split(',')[1].strip()
        data_dict["deliver_date"] = e_soup.select("p.origin_dateTime.load_header_elements.stop-appointment.margin_top")[1].text
        try:
            price = e_soup.find("p", {"class": "card-price"}).text
            data_dict["price"] = float(price.replace("$", "").replace(",", ""))
        except AttributeError:
            data_dict["price"] = np.nan
        data_dict["distance"] = e_soup.find("p", {"class": "card-distance"}).text
        data_dict["deadhead_distance"] = e_soup.select("p.origin_dateTime.load_header_elements.stop-appointment")[1].text.split(' ', 1)[1]
        data_dict["capacity_type"] = e_soup.find("p", {"class": "card-trailerType"}).text
        data_dict["weight"] = e_soup.find("p", {"class": "card-lbs"}).text
        data_dict["pick_up_stop_activity"] = e_soup.select("p.origin_milehead.load_header_elements.stop-activity")[0].text
        data_dict["deliver_stop_activity"] = e_soup.select("p.origin_milehead.load_header_elements.stop-activity")[1].text

        df = pd.concat([df, pd.DataFrame.from_records([data_dict])])

    return df

def main(browser, df, filename):
    """
        Scrape data from selenium web elements and
        load to dataframe. Exits when selenium fails to find element.

        :param browser: instantiated Selenium Chrome() browser
        :param df: pandas empty DataFrame
        :param filename: 'schneidercarrier_' + generated current datetime
        :return: final dataframe with scraped data
    """
    try:
        web_elements = browser.find_web_elements(By.CLASS_NAME, "card-content-load-web")
        df = scrape_soup(web_elements, df)
    except:
        df.to_excel(f'{filename}.xlsx', index=False)
    finally:
        browser.close_driver()

    return df


def wait_loading():
    """
    Finds page loading gif item wraper and deletes it from DOM.
    Exits if it becomes invisible
    :return: None
    """
    try:
        load_element = browser.find_web_element(by=By.ID, value="ion-overlay-1")
    except TimeoutException:
        return
    try:
        WebDriverWait(browser.driver, 10).until(EC.invisibility_of_element_located(load_element))
    except TimeoutException:
        browser.driver.execute_script("""
                                var element = document.getElementById('ion-overlay-1');
                                element.parentNode.removeChild(element);
                               """)
    finally:
        pass

def search_filter():
    # load search parameters from file
    with open("filter_parameters.txt") as f:
        data = f.read()
    params = json.loads(data)
    pickup_origin = params["pickup_origin"]
    date_interval = params["date"]

    # click on pickup input field
    browser.click_button(by=By.XPATH, value="//*[@id='top_recomm_load_clicked']/div[1]/form[1]/ion-grid[1]/ion-row["
                                            "2]/ion-col[1]/ion-grid[1]/ion-row[1]/ion-col[2]/div[1]/div[1]/div["
                                            "1]/div[1]/ion-item[1]/ion-input[1]/input[1]")
    # send key to pickup input field
    browser.send_input(by=By.XPATH, value="//*[@id='top_recomm_load_clicked']/div[1]/form[1]/ion-grid[1]/ion-row["
                                          "2]/ion-col[1]/ion-grid[1]/ion-row[1]/ion-col[2]/div[1]/div[1]/div[1]/div["
                                          "1]/ion-item[1]/ion-input[1]/input[1]", text=pickup_origin)
    # click on autocomplete suggestion line
    browser.click_button(by=By.CLASS_NAME, value="suggestions_list")
    time.sleep(1)
    # find and click on maximum radius button
    radius_btn = browser.find_web_element(by=By.XPATH, value="//*[@id='top_recomm_load_clicked']/div[1]/form["
                                                             "1]/ion-grid[1]/ion-row[2]/ion-col[1]/ion-grid["
                                                             "1]/ion-row[1]/ion-col[2]/div[2]/div[1]/div[1]/div["
                                                             "2]/div[5]/span[6]")
    radius_btn.click()
    # clear date input field
    browser.find_web_element(by=By.XPATH, value="//*[@id='top_recomm_load_clicked']/div[1]/form[1]/ion-grid["
                                                "1]/ion-row[2]/ion-col[1]/ion-grid[1]/ion-row[1]/ion-col[2]/div["
                                                "1]/div[1]/ion-grid[1]/ion-row[1]/ion-col[2]/div[1]/div[1]/div["
                                                "1]/input[1]").clear()
    # right interval for calendar datepick
    end_date = (pd.to_datetime('today') + pd.Timedelta(days=date_interval)).strftime('%b %d, %Y')
    # send `end_date` to calendar field
    browser.send_input(by=By.XPATH, value="//*[@id='top_recomm_load_clicked']/div[1]/form[1]/ion-grid[1]/ion-row["
                                          "2]/ion-col[1]/ion-grid[1]/ion-row[1]/ion-col[2]/div[1]/div[1]/ion-grid["
                                          "1]/ion-row[1]/ion-col[2]/div[1]/div[1]/div[1]/input[1]",
                       text=end_date)
    # click search button
    browser.click_button(by=By.XPATH, value="//*[@id='top_recomm_load_clicked']/div[1]/form[1]/ion-grid[1]/ion-row["
                                            "4]/ion-col[1]/ion-button[1]")
    # wait until search result is shown
    WebDriverWait(browser.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "total-load-count")))


def sort_df(df):
    """
    Sort Dataframe in descending order by price column
    """
    df["price"] = df["price"].astype(float)
    df.sort_values(by='price', ascending=False, inplace=True)
    return df

if __name__ == "__main__":
    browser = Browser("chromedriver")
    browser.open_page(URL)
    browser.login_rxo("signInName", "password", "next")

    browser.click_button(by=By.ID, value="tab-button-search")
    time.sleep(3)
    wait_loading()
    search_filter()

    df = pd.DataFrame()
    filename = "schneidercarrier_" + pd.to_datetime('today').strftime('%d-%m-%Y')
    df = main(browser, df, filename)
    df = sort_df(df)

    df.to_excel(f'{filename}.xlsx', index=False)
    end_time = time.time()
    time_spent = str(int(end_time - start_time)) + " seconds"

    print(f"\nTime spent: {time_spent}" + "\n" +
          f"Scraped records: {len(df)}" + "\n" +
          f"Saved to file '{filename}.xlsx'")
