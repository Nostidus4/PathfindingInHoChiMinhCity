"""WP1 - Dữ liệu POI (owner: P1, review: P2).

Output chính: data/processed/pois.csv (>= 100 POI, >= 20 POI mỗi quận, 5 quận cũ).
Chỉ osm_fetch.py (và poi_select.py) được import osmnx/geopandas, và chỉ import
bên trong hàm để người không cài group `data` vẫn import được package.
"""
