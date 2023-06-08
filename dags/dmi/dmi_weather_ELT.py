from typing import TypeVar

import os  # contact to Operative System

from decouple import config  # secret configs
import requests  # for making HTTP requests
from datetime import datetime  # for date and time manipulation
from datetime import timedelta, time  # time, time time

from operator import itemgetter  # for sorting dicts
# from geopy.distance import distance         # calculate distance between geopos

import csv  # writing csv files

import json
import pendulum

## inspired by https://stackoverflow.com/questions/48393065/run-apache-airflow-dag-without-apache-airflow
if __name__ != "__main__":
    from airflow.decorators import dag, task
else:
    mock_decorator = lambda f=None, **d: f if f else lambda x: x
    dag = mock_decorator
    task = mock_decorator


# @task()
def setups():
    """Getting config variable from system. 
    `.env` file og `setting.ini` (or maybe even environment vars?).
    Some of these are secret like api keys password etc. 
    These shold NOT be in souce-code, where it could accidentially be shared to others. 
    Therefore the file `.env` id NOT commited to git but added to `.gitignore`. 
    There is an example `.env.example`, withou real sensible values."""
    global api_key, DMI_URL
    api_key = config("DMI_API_KEY")
    DMI_URL = 'https://dmigw.govcloud.dk/v2'


def pull_data(service: str, data_dir: str, data_name: str, data_timedate: str, page_size: int, params: dict) -> list:
    """
        Hjælpefuntion til at lave api requests
    """

    nFeatures = 0
    page_index = 0

    fNames = []

    while True:
        params['limit'] = page_size
        params['offset'] = page_index * page_size

        r = requests.get(DMI_URL + service, params=params)
        print("_______________________________________________________________")
        print(r.json())
        print("_______________________________________________________________")
        if r.status_code != requests.codes.ok:  # response 200 etc
            print(r)
            # print(r.headers)
            print(r.text)
            print(params)
            break
        else:
            rjson = r.json()  # Extract JSON object
            print(f"Total number of features: {len(rjson['features'])}")
            nFeatures += len(rjson['features'])

        if rjson['numberReturned'] > 0:
            page_index += 1
            # fName = f'{data_dir}/{data_name}_{rjson["timeStamp"]}_#{page_index}.json'
            fName = f'{data_dir}/{data_name}_{data_timedate}_#{page_index}.json'.replace(':', '-')
            with open(fName, "w+", encoding='utf-8') as f:
                f.write(r.text)
            fNames.append(fName)
        else:
            break
    return fNames


@task()
def extract_weather_stations(**kwargs):
    """
    Extract (the E in ELT) metadat regarding dmi's weather stations
    See https://dmigw.govcloud.dk/v2/metObs/swagger-ui/index.html#/Met%20station/getStations
    """

    global api_key, DMI_URL
    service = '/metObs/collections/station/items'

    data_dir = "data"
    data_name = "dmi_staions"

    page_size = 100

    # today = datetime.now().date()
    today = datetime.fromisoformat(kwargs['ds'])
    today = datetime.combine(today, time(0, 0))
    today = today.astimezone().isoformat(timespec='seconds') + '/' + '..'

    params = {'api-key': api_key}
    params['datetime'] = today

    ts = datetime.fromisoformat(kwargs['ts']).astimezone().isoformat(timespec='seconds')

    return pull_data(service, data_dir, data_name, ts, page_size, params)


@task()
def extract_metobs(**kwargs):
    """
    Extract (the E in ELT) metheological data from dmi's weather stations
    See https://dmigw.govcloud.dk/v2/metObs/swagger-ui/index.html#/Met%20observation/getObservation
    Parameters
    ----------
    kwargs
        Through kwargs (KeyWord Arguments) we recieve 'ts' an ISO datatime string, of when the task is supposed to run,
        meaning that if Airflow needs to "catchup" it will run the task several times with corresponding 'ts'
    """
    global api_key, DMI_URL
    service = '/metObs/collections/observation/items'
    params = {'api-key': api_key}

    ts = datetime.fromisoformat(kwargs['ts'])
    starttime = ts - timedelta(hours=0, minutes=10)

    params['datetime'] = starttime.astimezone().isoformat(timespec='seconds') + '/' + ts.astimezone().isoformat(
        timespec='seconds')

    data_datetime = starttime.astimezone().isoformat(timespec='seconds')

    print(params)

    data_dir = "data"
    data_name = "dmi_metobs"

    page_size = 500

    return pull_data(service, data_dir, data_name, data_datetime, page_size, params)


@task
def single_json(json_file_list: list) -> str:
    """
    Copies only 'features' from list of JSON files extracted form dmi, to a single JSON file
    Parameters
    ----------
    json_file_list: list
        the list og filenames to merge to single JSON file
    """

    features = []

    for json_file_name in json_file_list:
        with open(json_file_name, encoding='utf-8') as inputfile:
            j = json.load(inputfile)
        features.extend(j['features'])

    outfilename: str = json_file_list[-1]
    outfilename = outfilename[:outfilename.rindex('_#')] + ".json"

    with open(outfilename, 'w+', encoding='utf-8') as outfile:
        outfile.write(json.dumps(features))

    print(len(features))

    return outfilename


def flatten_json(nested_json: dict, exclude: list = [''], denorm: list = [''], sep: str = '_') -> list:
    """
    Flatten a list of nested dicts.
    from https://stackoverflow.com/questions/58442723/how-to-flatten-a-nested-json-recursively-with-flatten-json
    Flatterns JSON structure to one (mostly) level. Each sublevel gets a key with it superior key and sep (default='_') prepended.
    Substructures with keys in demorm are returned as lists of values.
    Parameters
    ----------
    nested_json: dict,
    exclude: list =[''],
    denorm: list =[''],
    sep: str='_'
    Returns
    dict :
       Dictionaries with key:value pairs of values from each element in json input
    """
    out = dict()

    def flatten(x: list or dict, name: str = '', exclude=exclude, demorm=denorm):
        """
        Is called recursively, traversing down into the JSON tree
        """
        if type(x) is dict:
            for a in x:
                if a not in exclude:
                    ## added to de-normalize fields as texts with lists
                    if a in denorm:
                        out[f'{name}{a}'] = json.dumps(x[a])
                    else:
                        flatten(x[a], f'{name}{a}{sep}')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, f'{name}{i}{sep}')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(nested_json)
    return out


@task
def raw_jsonfiles_to_csv(filenames: list, **kwargs) -> list:
    """
    Converts a number of JSON files, given by a list of filenames, to a number of cvs files
    parameters
    ----------
    filenames: list
        a list og filenames to transform to csv
    returns
    ---
    list
        list og filenames of the created csv-files
    """
    return [raw_jsonfile_to_csvfile(filename) for filename in filenames]


def raw_jsonfile_to_csvfile(filename: str) -> str:
    """
    Converts a JSON file to a similar CSV file
    Parameters
    ----------
    filename: str
        Name of the JSON file to convert to CSV file
    Returns
    -------
    str
        Name of created CSV file
    """
    with open(filename, encoding='utf-8') as json_file:
        j = json.load(json_file)
    flat_features = [flatten_json(feature, denorm=['parameterId', 'coordinates'], sep='.') for feature in j['features']]
    csv_filename = (filename + ".csv").replace(':', '-')
    print(flat_features[0].keys())
    with open(csv_filename, 'w+', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=flat_features[0].keys(),
                                    quotechar="'")  # assuming that all features has the same
        csv_writer.writeheader()
        csv_writer.writerows(flat_features)
    return csv_filename


## ... flere tasks

@dag(
    # schedule=None,
    schedule=timedelta(minutes=10),
    start_date=pendulum.datetime(2023, 1, 1, 0, 0, 0, tz="Europe/Copenhagen"),
    catchup=True,
    tags=['experimental', 'metObs', 'rest api'],
)
def dmi_metobs(**kwargs):
    print('DMI metObs')

    setups()
    if __name__ != "__main__":  # as in "normal" operation as DAG stated in Airflow
        #stations_files = extract_weather_stations()
        metobs_files = extract_metobs()

        #stations_csv_files = raw_jsonfiles_to_csv(stations_files)
        metobs_csv_files = raw_jsonfiles_to_csv(metobs_files)

        #stations_file = single_json(stations_files)
        metobs_file = single_json(metobs_files)
    else:  # as regular python script (from IDE), mainly testing

        # extract_metobs(ts=datetime.now().isoformat())
        # metobs_files =  [
        #                    "data/dmi_metobs_2022-12-18T10:40:00+00:00_#1.json",
        #                    "data/dmi_metobs_2022-12-18T10:40:00+00:00_#2.json",
        #                    "data/dmi_metobs_2022-12-18T10:40:00+00:00_#3.json",
        #                    "data/dmi_metobs_2022-12-18T10:40:00+00:00_#4.json",
        #                    "data/dmi_metobs_2022-12-18T10:40:00+00:00_#5.json"
        # ]
        # # metobs_csv_files = raw_jsonfiles_to_csv(metobs_files)

        # stations_files= [
        #                     "data/dmi_staions_2022-12-18T10:40:00+00:00_#1.json",
        #                     "data/dmi_staions_2022-12-18T10:40:00+00:00_#2.json",
        #                     "data/dmi_staions_2022-12-18T10:40:00+00:00_#3.json",
        # ]
        # stations_cvs_files = raw_jsonfiles_to_csv(stations_files)

        ds = datetime.now().isoformat()
        stations_files = extract_weather_stations(ts=ds, ds=ds)
        metobs_files = extract_metobs(ts=ds, ds=ds)

        stations_csv_files = raw_jsonfiles_to_csv(stations_files)
        metobs_csv_files = raw_jsonfiles_to_csv(metobs_files)

        stations_file = single_json(stations_files)
        metobs_file = single_json(metobs_files)

    # stations = get_nearest_stations(extract_waether_stations(), 25)
    # met_obs_data = get_obs_from_stations(stations)
    # store_listofdicts_to_csv('metobs_Ballerup', met_obs_data, timestamped=True)
    # return met_obs_data


dmi_metobs()