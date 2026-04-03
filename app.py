import streamlit as st
import json
import os

st.set_page_config(page_title="GeoJSON 지도", layout="wide")

KAKAO_JS_KEY = st.secrets.get("KAKAO_JS_KEY", "057a4a253017791fe6072d7b089a063a")

# GeoJSON 로드
GEOJSON_FILE = "서울중구.geojson"
geojson_data = None
if os.path.exists(GEOJSON_FILE):
    with open(GEOJSON_FILE, encoding="utf-8") as f:
        geojson_data = json.load(f)

geojson_json = json.dumps(geojson_data) if geojson_data else "null"

# HTML + JS
MAP_HTML = f"""
<div id="map" style="width:100%;height:520px;border-radius:12px;"></div>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false"></script>
<script>
kakao.maps.load(function() {{
    var map = new kakao.maps.Map(document.getElementById('map'), {{
        center: new kakao.maps.LatLng(37.5665, 126.9780),
        level: 5
    }});

    // GeoJSON 표시
    var GEOJSON = {geojson_json};
    if(GEOJSON && GEOJSON.features){{
        GEOJSON.features.forEach(f => {{
            if(f.geometry.type === 'Polygon'){{
                f.geometry.coordinates.forEach(ring => {{
                    var path = ring.map(c => new kakao.maps.LatLng(c[1], c[0]));
                    new kakao.maps.Polygon({{
                        map: map,
                        path: path,
                        strokeWeight: 2,
                        strokeColor: '#3182CE',
                        fillColor: '#63B3ED',
                        fillOpacity: 0.25
                    }});
                }});
            }}
            else if(f.geometry.type === 'MultiPolygon'){{
                f.geometry.coordinates.forEach(poly => {{
                    poly.forEach(ring => {{
                        var path = ring.map(c => new kakao.maps.LatLng(c[1], c[0]));
                        new kakao.maps.Polygon({{
                            map: map,
                            path: path,
                            strokeWeight: 2,
                            strokeColor: '#3182CE',
                            fillColor: '#63B3ED',
                            fillOpacity: 0.25
                        }});
                    }});
                }});
            }}
        }});
    }}
}});
</script>
"""

st.components.v1.html(MAP_HTML, height=540)
