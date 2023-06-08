import csv
import json

import requests
from datetime import datetime  # for date and time manipulation
from datetime import timedelta, time  # time, time time
from decouple import config  # secret configs
import pendulum

if __name__ != "__main__":
    from airflow.decorators import dag, task
else:
    mock_decorator = lambda f=None, **d: f if f else lambda x: x
    dag = mock_decorator
    task = mock_decorator

def setups():
    """Getting config variable from system.
    `.env` file og `setting.ini` (or maybe even environment vars?).
    Some of these are secret like api keys password etc.
    These shold NOT be in souce-code, where it could accidentially be shared to others.
    Therefore the file `.env` id NOT commited to git but added to `.gitignore`.
    There is an example `.env.example`, withou real sensible values."""
    global api_key_lightning, DMI_URL, api_key_climate
    api_key_lightning = config("DMI_API_lightning_KEY")
    DMI_URL = 'https://dmigw.govcloud.dk/v2/'
    api_key_climate = config("DMI_API_climate_KEY")


# global api_key, DMI_URL
#     api_key = config("DMI_API_KEY")
#     DMI_URL = 'https://dmigw.govcloud.dk/v2'

# https://dmigw.govcloud.dk/v2/lightningdata/collections/observation/items?datetime=1993-01-20T22%3A42%3A52Z&bbox-crs=https%3A%2F%2Fwww.opengis.net%2Fdef%2Fcrs%2FOGC%2F1.3%2FCRS84&api-key=7e699dd3-35ac-4ab7-85a8-1eaa9b5b4a08
def pull_data_request_lightning(service: str, data_dir: str, data_name: str,page_size: int, apikey: str, ts: datetime, starttime: datetime) -> list:

    nFeatures = 0
    page_index = 0

    fNames = []

    while True:
        params = {
            'api-key': apikey,
            'datetime': starttime.astimezone().isoformat(timespec='seconds') + '/' + ts.astimezone().isoformat(timespec='seconds'),  # (Default/dont write anything, from this date and forward: "2018-02-12T00:00:00Z/..", Inde for en periode: "2018-02-12T00:00:00Z/2018-03-18T12:31:12Z", på en specifik dag: "2018-02-12T23:20:52Z", fra denne dato og tidligere: "../2018-03-18T12:31:12Z" )
            # 'period'    :"default", # skal vælge mellem at bruge datime eller period (Default/dont write anything, latest, latest-day, latest-hour, latest-10-minutes, latest-week, latest-month)
            'limit': page_size,  # Maximum number of results to return
            'offset': page_index * page_size,  # number of results to skip before returning matching results
            # 'sortorder' :"default", # Det den eneste mulighed" observed,DESC"Order by which to return results. Default is not sorted
            # 'type'      :"default", # 0,1,2 - sky til land(negative), sky til land(positiv), sky til sky
            # 'bbox'      :"default", # Kan kun bruge 1 bbox ad gangen og crs'en kan ikke slås fra.
            'bbox-crs': "https://www.opengis.net/def/crs/OGC/1.3/CRS84",
        }
        print(params)
        r = requests.get(DMI_URL + service, params=params)

        if r.status_code != requests.codes.ok:
            print(r)
            print(r.text)
            print(params)
            print(
                "FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! FEJL! ")
            break
        else:
            rjson = r.json()
            print(
                "KAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARL")
            print(params['datetime'])
            print(f"Total number of features: {len(rjson['features'])}")
            nFeatures += len(rjson['features'])

        if rjson['numberReturned'] > 0:
            page_index += 1
            print("/////////////////////////////////////////////////////////////////////////////////////////////////")
            fName = f'{data_dir}/{data_name}_#{page_index}.json'.replace(':', '-')
            with open(fName, 'w+', encoding='Utf-8') as f:
                f.write(r.text)
            fNames.append(fName)
            #break
        else:
            print("No values")
            break
    return fNames


@task()
def extract_lyn(**kwargs):
    service = 'lightningdata/collections/observation/items'
    apikey = api_key_lightning

    ts = datetime.fromisoformat(kwargs['ts'])
    starttime = ts - timedelta(days=10)
    data_dir = kwargs['sti']
    data_name = "Data_lightning"

    page_size = 500

    return pull_data_request_lightning(service, data_dir, data_name, page_size, apikey, ts, starttime)

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


@task()
def raw_json_files_to_csv(filenames: list) -> list:
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
    return[raw_jsonfile_to_csvFile(filename) for filename in filenames]

def raw_jsonfile_to_csvFile(filename: str) -> str:
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
    flat_features = [flatten_json(feature, denorm=['parameterId', 'coordinates'], sep=".") for feature in j['features']]
    csv_filename = (filename + ".csv").replace(':', '-')
    print(flat_features[0].keys())
    with open(csv_filename, 'w+', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=flat_features[0].keys(), quotechar="'")

        csv_writer.writeheader()
        csv_writer.writerows(flat_features)
    return csv_filename


@dag(
    # schedule=None,
    schedule=timedelta(days=10),
    start_date=pendulum.datetime(2018, 3, 18, 12, 0, 0, tz="Europe/Copenhagen"),
    catchup=True,
    tags=['experimental', 'lyn', 'rest api'],
)
def dmi_light():
    setups()
    if __name__ != "__main__":
        print('DMI light')
        sti = 'dags/dmilightning/datalightning'
        lyn_files = extract_lyn(sti=sti)

        lyn_files_csv = raw_json_files_to_csv(lyn_files)
    else:
        sti = 'datalightning'
        ds = "2018-03-18T12:31:12Z"
        lyn_files = extract_lyn(ts=ds, ds=ds, sti=sti)

        lyn_files_csv = raw_json_files_to_csv(lyn_files)

dmi_light()





