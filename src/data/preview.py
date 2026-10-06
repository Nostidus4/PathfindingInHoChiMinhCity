"""Bản đồ preview POI bằng folium. Owner: P1."""

from __future__ import annotations

from pathlib import Path

from src.config import REPO_ROOT
from src.data.districts import DISTRICT_POLYGONS
from src.models import POI


def render_poi_preview(
    pois: list[POI],
    out_path: Path = REPO_ROOT / "outputs" / "pois_preview.html",
) -> Path:
    """Xuất bản đồ HTML preview các POI."""

    import folium

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Trung tâm TP.HCM
    m = folium.Map(
        location=[10.7757, 106.7004],
        zoom_start=13,
    )

    district_colors = {
        "Quan 1": "red",
        "Quan 3": "blue",
        "Quan 5": "green",
        "Binh Thanh": "purple",
        "Phu Nhuan": "orange",
    }

    # Vẽ ranh giới các quận
    for district, polygon in DISTRICT_POLYGONS.items():
        folium.Polygon(
            locations=polygon,
            color=district_colors.get(district, "gray"),
            fill=False,
            weight=2,
            tooltip=district,
        ).add_to(m)

    # Vẽ POI
    for poi in pois:
        color = district_colors.get(poi.district, "gray")

        folium.CircleMarker(
            location=[poi.lat, poi.lon],
            radius=5,
            color=color,
            fill=True,
            fill_opacity=0.8,
            tooltip=poi.name,
            popup=(
                f"<b>{poi.name}</b><br>"
                f"District: {poi.district}<br>"
                f"Kind: {poi.kind}<br>"
                f"Lat: {poi.lat:.6f}<br>"
                f"Lon: {poi.lon:.6f}"
            ),
        ).add_to(m)

    m.save(out_path)

    return out_path