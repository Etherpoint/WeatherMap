import json
import requests
import os

api = os.getenv("API_KEY")
print(api)
lat = 55.7522
lon = 37.6156

url = "https://api.openweathermap.org/data/2.5/weather?units=metric&lat=" + str(lat) + "&lon=" + str(lon) + "&appid=" + api
print(url)
res = json.dumps(requests.get(url).json(), indent=4)
print(res)