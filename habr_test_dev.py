import json

import folium
import geopandas as gpd
import os
import h3
import requests
import numpy as np
import pandas as pd
from shapely.geometry import Polygon


# https://habr.com/ru/articles/579838/
api = os.getenv("API_KEY")
def getTemperatureByLatLon(array,id):
    url = "https://api.openweathermap.org/data/2.5/weather?units=metric&lat=" + str(array[0]) + "&lon=" + str(
        array[1]) + "&appid=" + api
    res = requests.get(url).json()
    res = res['main']['temp']
    with open('temperatures.csv', 'a') as f:
        f.write(str(id)+ "," + str(res) + "\n")
    print(res)

def calculate_center(coordinates):
    x_coords = [coord[0] for coord in coordinates[0]]
    y_coords = [coord[1] for coord in coordinates[0]]
    center_x = sum(x_coords) / len(x_coords)
    center_y = sum(y_coords) / len(y_coords)
    return [center_x, center_y]

def createChoropleth(geojson, m):
    data = pd.read_csv("temperatures.csv")
    folium.Choropleth(
        geo_data=geojson,
        name="choropleth",
        data=data,
        columns=["location", "temperature"],
        key_on="feature.id",
        fill_color="YlOrRd",
       # fill_opacity=0.7,
        line_opacity=0.2,
        line_weight=1,
        nan_fill_color='white'
    ).add_to(m)
    folium.LayerControl().add_to(m)
    return m

def create_hexagons(geoJson, mapa=None):
    polyline = geoJson['coordinates'][0]

    polyline.append(polyline[0])
    lat = [p[0] for p in polyline]
    lng = [p[1] for p in polyline]


    if mapa is None:
        # чем меньше zoom_start, тем больше площади земли захватывает экран
        m = folium.Map(location=[sum(lat) / len(lat), sum(lng) / len(lng)],
                       zoom_start=11,
                       tiles='cartodbpositron',
                       max_lon=200)
    else:
        m = mapa
    my_PolyLine = folium.PolyLine(locations=polyline, weight=1, color="green")
    m.add_child(my_PolyLine)

    hexagons = list(
        h3.polyfill(geoJson, 3))  # Второй параметр отвечает за размер гексагона. Чем меньше число, тем больше гексагон
    polylines = []
    lat = []
    lng = []
    for hex in hexagons:
        polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)

        #Получаем и выводим координату центра гексагона
        hexCenter = h3.h3_to_geo(hex)
        print(hexCenter)
        #Получаем температуру по гексагону
        #getTemperatureByLatLon(hexCenter)

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


with open('temperatures.csv', 'w') as f:
    f.write("location,temperature" + "\n")
mapTemplate = folium.Map(tiles='cartodbpositron')
m = mapTemplate
with open('MSKandMO/MoscowAND_MO_test.geojson', encoding='utf-8') as f:
    geojson_data = json.load(f)

# Добавление уникального идентификатора к каждой геометрии
#for idx, feature in enumerate(geojson_data['features'], start=1):
#    feature['id'] = idx

# Добавление координат центра к каждой геометрии
#for feature in geojson_data['features']:
 #   coordinates = feature['geometry']['coordinates']
  #  center = calculate_center(coordinates)
  #  feature['center'] = center

# Сохранение измененных данных обратно в файл
#with open('MSKandMO/MoscowAND_MO_test.geojson', 'w') as file:
 #   json.dump(geojson_data, file, indent=4)
gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])

# Преобразуйте GeoJSON в GeoDataFrame
geoJsonGeometry = json.loads(gpd.GeoSeries(gdf['geometry']).to_json())
geoJson = []
for i in range(0, len(gdf)):
    print("Запустился процесс обработки массива №: " + str(i + 1))
    geoJsonFeatures = geoJsonGeometry['features'][i]['geometry']
    geoJson = {'type': 'Polygon', 'coordinates': [np.column_stack((np.array(geoJsonFeatures['coordinates'][0])[:, 1],
                                                                   np.array(geoJsonFeatures['coordinates'][0])[:,
                                                                   0])).tolist()]}
    if str(i) == '0':
        m, polygons, polylines = create_hexagons(geoJson)
        mapTemplate = m
    else:
        m, polygons, polylines = create_hexagons(geoJson, mapTemplate)
    getTemperatureByLatLon(geojson_data['features'][i]['center'],i)
m = createChoropleth(geoJsonGeometry, m)
m.save("habr_devmap_polygons.html")