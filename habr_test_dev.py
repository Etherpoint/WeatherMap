import datetime
import json
import os
import time

import folium
import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import requests
from geojson import Polygon, Feature, FeatureCollection, dump
from shapely import wkt
from shapely.geometry import Polygon
import jenkspy

# https://habr.com/ru/articles/579838/
api = os.getenv("API_KEY")
country_id = 0
hex_id = 0
features = []

# Начало подсчета времени выполнения программы
start = datetime.datetime.now()


def getTemperatureByLatLon(array):
    global country_id
    url = "https://api.openweathermap.org/data/2.5/weather?exclude=minutely,hourly,daily,alerts&units=metric&lat=" + str(
        array[0]) + "&lon=" + str(
        array[1]) + "&appid=" + api
    res = requests.get(url)
    waitTime = res.elapsed.microseconds / 1000000
    res = res.json()['main']['temp']
    with open('temperatures.csv', 'a') as f:
        f.write(str(country_id) + "," + str(res) + "\n")
        print(str(res) + " для гексагона №: " + str(hex_id))
        country_id += 1

    # искусственное замедление программы из-за лимитов сервиса openweather
    time.sleep(0 if (1 - waitTime) < 0 else 1 - waitTime)


def createChoropleth(hex_gjn, m):
    data = pd.read_csv("temperatures.csv")

    folium.Choropleth(
        geo_data=hex_gjn,
        name="temperatures",
        columns=["id", "temperature"],
        key_on="feature.id",
        data=data,
        line_opacity=0.1,
        fill_color="Spectral_r",
        nan_fill_color="black",
        use_jenks=True
    ).add_to(m)
    folium.LayerControl().add_to(m)
    return m


def addHexagonToFeature(hexagon):
    global hex_id
    global features
    polygon = Polygon((hexagon[0])[0])
    features.append(Feature(geometry=polygon, id=hex_id))
    hex_id += 1


def addFeatureToFile():
    global features
    feature_collection = FeatureCollection(features)
    with open('hexagons.geojson', 'a') as gj:
        dump(feature_collection, gj)


def create_hexagons(geoJson):
    polyline = geoJson['coordinates'][0]
    polyline.append(polyline[0])
    hexagons = list(
        h3.polyfill(geoJson, 4))  # Второй параметр отвечает за размер гексагона. Чем меньше число, тем больше гексагон
    polylines = []
    lat = []
    lng = []
    for hex in hexagons:
        polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
        addHexagonToFeature(h3.h3_set_to_multi_polygon([hex], geo_json=True))
        # Получаем и выводим координату центра гексагона
        hexCenter = h3.h3_to_geo(hex)
        # Получаем температуру по гексагону
        getTemperatureByLatLon(hexCenter)

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


def fileStartCreating():
    with open('hexagons.geojson', 'w'):
        print("Создается файл для хранения гексагонов")
    with open('temperatures.csv', 'w') as t:
        t.write("id,temperature" + "\n")
    with open('MSKandMO/MoscowAND_MO_test.geojson', encoding='utf-8') as f:
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
        print("Запустился процесс обработки массива №: " + str(i + 1))
        geoJsonFeatures = geoJsonGeometry['features'][i]['geometry']
        geoJson = {'type': 'Polygon',
                   'coordinates': [np.column_stack((np.array(geoJsonFeatures['coordinates'][0])[:, 1],
                                                    np.array(geoJsonFeatures['coordinates'][0])[:,
                                                    0])).tolist()]}
        templateMap, polygons, polylines = create_hexagons(geoJson)
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
