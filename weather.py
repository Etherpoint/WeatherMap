import json
import sys
import requests

api = sys.argv[1]
print(api)
lat = 55.7522
lon = 37.6156

res = json.dumps(requests.
                 get("https://api.openweathermap.org/data/2.5/weather?units=metric&lat=" + str(lat) + "&lon=" + str(lon) + "&appid=" + api).json(), indent=4)
print(res)