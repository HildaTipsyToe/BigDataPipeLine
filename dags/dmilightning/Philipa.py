import requests

# global api_key, DMI_URL
#     api_key = config("DMI_API_KEY")
#     DMI_URL = 'https://dmigw.govcloud.dk/v2'

DMI_API_KEY="7e699dd3-35ac-4ab7-85a8-1eaa9b5b4a08"
Lightning_api_url = 'https://dmigw.govcloud.dk/v2/lightningdata/collections/observation/items?'
# https://dmigw.govcloud.dk/v2/lightningdata/collections/observation/items?datetime=1993-01-20T22%3A42%3A52Z&bbox-crs=https%3A%2F%2Fwww.opengis.net%2Fdef%2Fcrs%2FOGC%2F1.3%2FCRS84&api-key=7e699dd3-35ac-4ab7-85a8-1eaa9b5b4a08

params = {
    'datetime'  :"../2018-03-18T12:31:12Z", # (Default/dont write anything, from this date and forward: "2018-02-12T00:00:00Z/..", Inde for en periode: "2018-02-12T00:00:00Z/2018-03-18T12:31:12Z", på en specifik dag: "2018-02-12T23:20:52Z", fra denne dato og tidligere: "../2018-03-18T12:31:12Z" )
    'api-key' : DMI_API_KEY,
    # 'period'    :"default", # skal vælge mellem at bruge datime eller period (Default/dont write anything, latest, latest-day, latest-hour, latest-10-minutes, latest-week, latest-month)
    # 'limit'     :"default", # Maximum number of results to return
    # 'offset'    :"default", # number of results to skip before returning matching results
    # 'sortorder' :"default", # Det den eneste mulighed" observed,DESC"Order by which to return results. Default is not sorted
    # 'type'      :"default", # 0,1,2 - sky til land(negative), sky til land(positiv), sky til sky
    # 'bbox'      :"default", # Kan kun bruge 1 bbox ad gangen og crs'en kan ikke slås fra.
    'bbox-crs'  :"https://www.opengis.net/def/crs/OGC/1.3/CRS84", # jeg skal prøve at finde en converter
}



respons = requests.get(Lightning_api_url, params)
print(Lightning_api_url, params)

print(respons)
print(respons.json())