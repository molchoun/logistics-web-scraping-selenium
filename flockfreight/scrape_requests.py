import json
import time
import pandas as pd
import requests

start_time = time.time()


def filter_params(file):
    with open(file) as f:
        data = f.read()
    return json.loads(data)


def create_payload():
    params = filter_params("filter_parameters.json")
    day_interval = params["days"]["day_interval"]
    orig_radius = params["radius"]["orig_radius"]
    eq_type = params["equip_type"]["53' Dry Van"]
    city = params["location"]["city"]
    state = params["location"]["state"]

    today = pd.to_datetime('today')
    daterange = pd.date_range(start=today, periods=day_interval)
    pre_load_payload = []
    for day in daterange:
        search_params = {
            "originCity": city,
            "originStateProvinceCode": state,
            "originLocationWithinRadiusMi": orig_radius,
            "source": "FF_WEB_APP",
            "destinationLocationWithinRadiusMi": '',
            "trailerType": eq_type,
            "trailerEmpty": True,
            "instantMatchAlertEnabled": False
        }
        search_params["dateAvailable"] = day.strftime('%Y-%m-%d')
        pre_load_payload.append(search_params)
    return pre_load_payload


def get_loads():
    payload_login = filter_params('credentials.json')
    pre_load_payload = create_payload()
    load_payload = {
        "shouldOnlyIncludeCoverable": "false",
        "token": "undefined"
    }
    login_url = 'https://api.flockfreight.com/auth/v1/login'
    pre_load_url = 'https://api.flockfreight.com/carriers/12367ffa-f45d-4062-a3a4-e65254908ea8/carrier-capacity-search-group'
    load_url = 'https://api.flockfreight.com/carriers/12367ffa-f45d-4062-a3a4-e65254908ea8/carrier-capacity-matches-for-selector?'
    login_headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    }
    with requests.Session() as s:
        s.post(login_url, headers=login_headers, json=payload_login)
        pre_load_resp = s.post(pre_load_url, headers=login_headers, json=pre_load_payload)
        group_id = json.loads(pre_load_resp.content.decode('utf-8'))['carrierCapacityGroupGuid']
        load_json = {
            "carrierCapacityGroupGuids": [
                group_id
            ],
            "preferredLaneGuids": []
        }
        loads = s.post(load_url, headers=login_headers, json=load_json, params=load_payload)
        loads_json = json.loads(loads.content.decode('utf-8'))
    return loads_json


def parse(loads_json):
    params = filter_params("filter_parameters.json")
    eq_type = params["equip_type"]["53' Dry Van"]
    loads_list = []
    for load in loads_json:
        loads_dict = dict()
        loads_dict["pick_up_city"] = load['load']['firstStopPickupAddress']['city'].title()
        loads_dict["pick_up_state"] = load['load']['firstStopPickupAddress']['stateProvinceCode']
        loads_dict["pick_up_date"] = load['load']['firstStopStartDate']
        loads_dict["deliver_city"] = load['load']['lastStopDeliveryAddress']['city'].title()
        loads_dict["deliver_state"] = load['load']['lastStopDeliveryAddress']['stateProvinceCode']
        loads_dict["delivery_date"] = load['load']['firstStopEndDate']
        try:
            loads_dict["price"] = int(float(load['carrierLoadDetails']['bookNowRateUsd']))
        except KeyError:
            loads_dict["price"] = int(float(load['carrierLoadDetails']['startingBidUsd']))
        loads_dict["distance"] = load['load']['routeDistanceMi']
        loads_dict["weight"] = load['load']['totalWeightLbs']
        loads_dict["stops"] = load['load']['stopCount']
        loads_dict["DH-O"] = load['milesToPickup']
        loads_dict["equipment_type"] = eq_type
        loads_list.append(loads_dict)
    df = pd.DataFrame.from_dict(loads_list)
    return df


def sort_df(df):
    """
    Sort Dataframe in descending order by price column
    """
    df["price"] = df["price"].astype(float)
    df.sort_values(by='price', ascending=False, inplace=True)
    df["website"] = "flockfreight"
    return df


def main():
    loads_json = get_loads()
    df = parse(loads_json)
    df = sort_df(df)
    filename = "flockfreight_" + pd.to_datetime('today').strftime('%d-%m-%Y')
    df.to_excel(f'{filename}.xlsx', index=False)
    end_time = time.time()
    time_spent = str(int(end_time - start_time)) + " seconds"
    print(f"\nTime spent: {time_spent}" + "\n" +
          f"Scraped records: {len(df)}" + "\n" +
          f"Saved to file '{filename}.xlsx'")


if __name__ == '__main__':
    main()
