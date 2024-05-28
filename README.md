# Weather map of Moscow and Moscow Region

---
**Task**: visualization of the heat map of Moscow and Moscow Region in real time.

**Example of work:**
![image (3)](https://github.com/Etherpoint/WeatherMap/assets/115358372/7ee52cae-54aa-4cc7-96ad-01c8daf08765)

Libraries used|Version|Description|
---|---|---|
folium|0.16.0|Сreating a map
geopandas|0.14.4|Parsing geojson
h3|3.7.7|Drawing hexagons
requests|2.31.0|Getting temperature via rest api

**Updates**: added multithreading in habr_test_dev_v2.py

Comparison of operating time in sequential and multi-threaded mode:
![Рисунок1](https://github.com/Etherpoint/WeatherMap/assets/115358372/c5e069db-ff20-4d9c-bf0b-5552010abdfa)

![Рисунок2](https://github.com/Etherpoint/WeatherMap/assets/115358372/7ca3a601-c772-44c3-aaea-1218934a57bd)


