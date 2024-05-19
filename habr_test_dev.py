import json

import folium
import geopandas as gpd
import h3
import numpy as np
import pandas as pd
from shapely.geometry import Polygon


# https://habr.com/ru/articles/579838/

def visualize_hexagons(hexagons, color="red", folium_map=None):
    polylines = []
    lat = []
    lng = []
    for hex in hexagons:
        polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
        outlines = [loop for polygon in polygons for loop in polygon]
        polyline = [outline + [outline[0]] for outline in outlines][0]
        lat.extend(map(lambda v: v[0], polyline))
        lng.extend(map(lambda v: v[1], polyline))
        polylines.append(polyline)

    if folium_map is None:
        m = folium.Map(location=[sum(lat) / len(lat), sum(lng) / len(lng)], zoom_start=20, tiles='cartodbpositron')
    else:
        m = folium_map

    for polyline in polylines:
        my_PolyLine = folium.PolyLine(locations=polyline, weight=8, color=color)
        m.add_child(my_PolyLine)
    return m


def visualize_polygons(geometry):
    lats, lons = get_lat_lon(geometry)

    m = folium.Map(location=[sum(lats) / len(lats), sum(lons) / len(lons)], zoom_start=13, tiles='cartodbpositron')

    overlay = gpd.GeoSeries(geometry).to_json()
    folium.GeoJson(overlay, name='boundary').add_to(m)

    return m


# выводим центроиды полигонов
def get_lat_lon(geometry):
    lon = geometry.apply(lambda x: x.x if x.geom_type == 'Point' else x.centroid.x)
    lat = geometry.apply(lambda x: x.y if x.geom_type == 'Point' else x.centroid.y)
    return lat, lon


def create_hexagons(geoJson, mapa=None):
    polyline = geoJson['coordinates'][0]

    polyline.append(polyline[0])
    lat = [p[0] for p in polyline]
    lng = [p[1] for p in polyline]

    if mapa is None:
        # чем меньше zoom_start, тем больше площади земли захватывает экран
        m = folium.Map(location=[sum(lat) / len(lat), sum(lng) / len(lng)], zoom_start=5, tiles='cartodbpositron')
    else:
        m = mapa
    # my_PolyLine = folium.PolyLine(locations=polyline, weight=8, color="green")
    my_PolyLine = folium.PolyLine(locations=polyline, weight=8, color="white")
    m.add_child(my_PolyLine)

    hexagons = list(
        h3.polyfill(geoJson, 2))  # Второй параметр отвечает за размер гексагона. Чем меньше число, тем больше гексагон
    polylines = []
    lat = []
    lng = []
    for hex in hexagons:
        polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
        # flatten polygons into loops.
        outlines = [loop for polygon in polygons for loop in polygon]
        polyline = [outline + [outline[0]] for outline in outlines][0]
        lat.extend(map(lambda v: v[0], polyline))
        lng.extend(map(lambda v: v[1], polyline))
        polylines.append(polyline)
    for polyline in polylines:
        my_PolyLine = folium.PolyLine(locations=polyline, weight=3, color='red')
        m.add_child(my_PolyLine)

    polylines_x = []
    for j in range(len(polylines)):
        a = np.column_stack((np.array(polylines[j])[:, 1], np.array(polylines[j])[:, 0])).tolist()
        polylines_x.append([(a[i][0], a[i][1]) for i in range(len(a))])

    polygons_hex = pd.Series(polylines_x).apply(lambda x: Polygon(x))

    return m, polygons_hex, polylines

mapTemplate = folium.Map(tiles='cartodbpositron')
with open('russia.geojson', encoding='utf-8') as f:
    geojson_data = json.load(f)

gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])

# Преобразуйте GeoJSON в GeoDataFrame
geoJsonGeometry = json.loads(gpd.GeoSeries(gdf['geometry']).to_json())
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
    m.save("habr_devmap_polygons.html")
