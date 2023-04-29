import json
import os
import time
import numpy as np
import pandas as pd
import requests
from requests.exceptions import ConnectionError, InvalidHeader, HTTPError, Timeout, MissingSchema

start_time = time.time()


def get_credentials(file):
    with open(file) as f:
        data = f.read()
    return json.loads(data)


def get_loads():
    payload = get_credentials('credentials.json')
    payload_loads = {
        "limit": 1000,
        "filter_by": "available",
        "page": 1
    }
    login_url = 'https://capacity-b-prod.edgelogistics.com/api/www/v1/auth/login'
    loads_url = 'https://capacity2-b.edgelogistics.com/api/v1/orders/capacity'

    with requests.Session() as s:
        try:
            login_response = s.post(login_url, data=payload)
        except (ConnectionError, InvalidHeader, HTTPError, Timeout, MissingSchema) as err:
            print(f"There was a problem retrieving response: \n {err}")
        try:
            time.sleep(5)
            response_json = json.loads(login_response.content.decode('utf-8'))
            token = response_json['data']['auth']['access_token']
            header = {'authorization': 'Bearer ' + token}
        except (ValueError, json.decoder.JSONDecodeError, Exception) as err:
            print(f"There was a problem with json: \n {err}")
        try:
            loads_response = s.post(loads_url, data=payload_loads, headers=header)
        except (ConnectionError, InvalidHeader, HTTPError, Timeout, MissingSchema, Exception) as err:
            print(f"There was a problem retrieving response: \n {err}")
        loads_json = json.loads(loads_response.content.decode('utf-8'))

    return loads_json


def parse(loads_json):
    loads_list = []
    for load in loads_json['data']:
        try:
            loads_dict = dict()
            loads_dict["load_id"] = load['order_number']
            loads_dict["pick_up_city"] = load['origin']['city'].title()
            loads_dict["pick_up_state"] = load['origin']['state_code']
            loads_dict["pick_up_date"] = load['origin']['arrive_early_date']
            loads_dict["deliver_city"] = load['destination']['city'].title()
            loads_dict["deliver_state"] = load['destination']['state_code']
            loads_dict["delivery_date"] = load['destination']['arrive_early_date']
            try:
                loads_dict["price"] = int(load['rate'])
            except TypeError:
                loads_dict["price"] = np.nan
            loads_dict["equipment_type"] = load['equipment_type']['description']
            loads_dict["distance"] = load['distance']
            loads_dict["weight"] = load['weight']
            loads_dict["stops"] = load['stops_count']
            loads_list.append(loads_dict)
        except (KeyError, Exception) as e:
            print(f"Key Not Found: {e}")
            continue
    df = pd.DataFrame.from_dict(loads_list)
    return df


def sort_df(df):
    """
    Sort Dataframe in descending order by price column
    """
    df["price"] = df["price"].astype(float)
    df.sort_values(by='price', ascending=False, inplace=True)
    df["website"] = "edgelogistics"
    return df


def main():
    loads_json = get_loads()
    df = parse(loads_json)
    df = sort_df(df)
    filename = "edgelogistics_" + pd.to_datetime('today').strftime('%d-%m-%Y')
    df.to_excel(f'{filename}.xlsx', index=False)
    end_time = time.time()
    time_spent = str(int(end_time - start_time)) + " seconds"
    print(f"\nTime spent: {time_spent}" + "\n" +
          f"Scraped records: {len(df)}" + "\n" +
          f"Saved to file '{filename}.xlsx'")


if __name__ == '__main__':
    main()
