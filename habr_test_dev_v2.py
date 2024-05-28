import datetime
import json
import os
import threading
import time
from queue import Queue
from threading import Thread as th

import folium
import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import requests
from geojson import Polygon, Feature, FeatureCollection, dump
from shapely.geometry import Polygon

# https://habr.com/ru/articles/579838/

# api key from https://home.openweathermap.org/
#api = os.getenv("API_KEY")

# api key from https://www.weatherapi.com/
api_2 = os.getenv("API_KEY_2")
queueNumber = 0
country_id = Queue()
features = []
geojsonFileName = "MSKandMO/MoscowAND_MO_test.geojson"
lock = threading.Lock()
threads = []

# Начало подсчета времени выполнения программы
start = datetime.datetime.now()


def getTemperatureByLatLon(c_id, array):
    # url = "https://api.openweathermap.org/data/2.5/weather?units=metric&lat=" + str(array[0]) + "&lon=" + str(array[1]) + "&appid=" + api
    url = ("http://api.weatherapi.com/v1/current.json?q=" + str(array[0]) + "," + str(array[1]) + "&lang=ru&" + "key=" + api_2)
    res = requests.get(url)
    if res.status_code != 200:
        print("Ошибка при выполнении запроса: " + str(res.status_code) + "\n" + res.text)
    res = res.json()['current']['temp_c']
    with lock:
        with open('temperatures.csv', 'a') as f:
            f.write(str(c_id) + "," + str(res) + "\n")
            print(str(res) + " для гексагона №: " + str(c_id))

    # искусственное замедление программы из-за лимитов сервиса openweather
    # time.sleep(0 if (1.5 - waitTime) < 0 else 1.5 - waitTime)


def createChoropleth(hex_gjn, m):
    # data = sorted(pd.read_csv("temperatures.csv"), key=lambda row: row[0], reverse=False)
    data = pd.read_csv("temperatures.csv").sort_values(by='id')
    print(data)

    folium.Choropleth(
        geo_data=hex_gjn,
        name="temperatures",
        columns=["id", "temperature"],
        key_on="feature.id",
        data=data,
        line_opacity=1,
        line_color="Spectral_r",
        fill_color="Spectral_r",
        fill_opacity=0.8,
        nan_fill_color="black",
        use_jenks=True,
        bins=15
    ).add_to(m)
    folium.LayerControl().add_to(m)
    return m


def addHexagonToFeature(c_id, hexagon):
    global features
    polygon = Polygon((hexagon[0])[0])
    features.append(Feature(geometry=polygon, id=c_id))


def addFeatureToFile():
    global features
    features.sort(key=lambda x: x.get("id"), reverse=False)
    feature_collection = FeatureCollection(features)
    with open('hexagons.geojson', 'a') as gj:
        dump(feature_collection, gj)


def create_hexagons(geoJson, k=6):
    global country_id
    global queueNumber
    polyline = geoJson['coordinates'][0]
    polyline.append(polyline[0])
    hexagons = list(
        h3.polyfill(geoJson, k))  # Второй параметр отвечает за размер гексагона. Чем меньше число, тем больше гексагон
    polylines = []
    lat = []
    lng = []
    for hex in hexagons:
        polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
        polygonsForChoropleth = h3.h3_set_to_multi_polygon([hex], geo_json=True)
        # addHexagonToFeature(polygonsForChoropleth)
        # Получаем и выводим координату центра гексагона
        hexCenter = h3.h3_to_geo(hex)
        # Получаем температуру по гексагону
        while threading.active_count() >= 500:
            time.sleep(0.5)
        country_id.put(queueNumber, block=True)
        queueNumber += 1
        working_Thread = th(target=test, args=(hexCenter, polygonsForChoropleth))
        threads.append(working_Thread)
        working_Thread.start()
        # getTemperatureByLatLon(hexCenter)

        # flatten polygons into loops.
        outlines = [loop for polygon in polygons for loop in polygon]
        polyline = [outline + [outline[0]] for outline in outlines][0]
        lat.extend(map(lambda v: v[0], polyline))
        lng.extend(map(lambda v: v[1], polyline))
        polylines.append(polyline)
    for polyline in polylines:
        my_PolyLine = folium.PolyLine(locations=polyline, weight=0, color='red')
        m.add_child(my_PolyLine)

    polylines_x = []
    for j in range(len(polylines)):
        a = np.column_stack((np.array(polylines[j])[:, 1], np.array(polylines[j])[:, 0])).tolist()
        polylines_x.append([(a[i][0], a[i][1]) for i in range(len(a))])

    polygons_hex = pd.Series(polylines_x).apply(lambda x: Polygon(x))

    return m, polygons_hex, polylines


def test(hex_center, hex_polygons):
    global country_id
    thId = country_id.get(block=True)
    addHexagonToFeature(thId, hex_polygons)
    getTemperatureByLatLon(thId, hex_center)


def fileStartCreating():
    with open('hexagons.geojson', 'w'):
        print("Создается файл для хранения гексагонов")
    with open('temperatures.csv', 'w') as t:
        t.write("id,temperature" + "\n")
    with open(geojsonFileName, encoding='utf-8') as f:
        geojson_data = json.load(f)
    return geojson_data


def createMap():
    return folium.Map(location=[55.7522, 37.6156], tiles='cartodbpositron', zoom_start=6)


def prepareMap(templateMap):
    gdf = gpd.GeoDataFrame.from_features(fileStartCreating()['features'])

    # Преобразуйте GeoJSON в GeoDataFrame
    geoJsonGeometry = json.loads(gpd.GeoSeries(gdf['geometry']).to_json())
    geoJson = []
    for i in range(0, len(gdf)):
        # print("Запустился процесс обработки массива №: " + str(i + 1))
        geoJsonFeatures = geoJsonGeometry['features'][i]['geometry']
        geoJson = {'type': 'Polygon',
                   'coordinates': [np.column_stack((np.array(geoJsonFeatures['coordinates'][0])[:, 1],
                                                    np.array(geoJsonFeatures['coordinates'][0])[:,
                                                    0])).tolist()]}
        templateMap, polygons, polylines = create_hexagons(geoJson)

    for t in threads:
        t.join()

    addFeatureToFile()
    with open('hexagons.geojson', encoding='utf-8') as f:
        hex_data = json.load(f)
    hexdf = gpd.GeoDataFrame.from_features(hex_data['features'])
    geoJsonGeometryHex = json.loads(gpd.GeoSeries(hexdf['geometry']).to_json())
    createChoropleth(geoJsonGeometryHex, templateMap)


m = createMap()
prepareMap(m)

m.save("habr_devmap_polygons.html")

finish = datetime.datetime.now()
# вычитаем время старта из времени окончания
print('Время работы: ' + str(finish - start))
