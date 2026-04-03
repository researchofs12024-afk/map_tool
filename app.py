import streamlit as st
import requests
import json

st.set_page_config(
    page_title="건축물대장 조회 서비스",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 키 불러오기
try:
    KAKAO_JS_KEY     = st.secrets["KAKAO_JS_KEY"]
    KAKAO_REST_KEY   = st.secrets["KAKAO_REST_KEY"]
    BUILDING_API_KEY = st.secrets["BUILDING_API_KEY"]
except Exception:
    KAKAO_JS_KEY     = "YOUR_KAKAO_JS_KEY"
    KAKAO_REST_KEY   = "YOUR_KAKAO_REST_KEY"
    BUILDING_API_KEY = "YOUR_BUILDING_API_KEY"

# --- 기존 건축물대장 조회 함수들 그대로 유지 ---
# get_region_code, get_jibun_address, get_building_title, get_building_info 등
# 생략 (기존 코드 그대로 사용)

# --- GeoJSON 로드 ---
# Streamlit에 파일 업로드 UI로 GeoJSON 로드
geojson_file = st.file_uploader("GeoJSON 파일 선택 (서울중구 등)", type=["geojson"])
geojson_data = None
if geojson_file:
    geojson_data = json.load(geojson_file)

parcel_json = json.dumps(geojson_data) if geojson_data else "null"

# --- 지도 및 하이라이트 + 클릭 이벤트 HTML ---
MAP_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ margin:0; padding:0; }}
  #map {{ width:100%; height:500px; border-radius:12px; }}
</style>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false"></script>
</head>
<body>
<div id="map"></div>
<script>
var GEOJSON = {parcel_json};
(function(){{
  kakao.maps.load(function() {{
    var map = new kakao.maps.Map(document.getElementById('map'), {{
      center: new kakao.maps.LatLng(37.5665, 126.9780),
      level: 4
    }});

    var polygon = null;
    function drawPolygon(geom) {{
      if (!geom) return;
      if (polygon) polygon.setMap(null);
      var rings = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0];
      var path = rings.map(c => new kakao.maps.LatLng(c[1], c[0]));
      polygon = new kakao.maps.Polygon({{
        map: map,
        path: path,
        strokeWeight: 2,
        strokeColor: '#FF0000',
        fillColor: '#FF0000',
        fillOpacity: 0.3
      }});
      var bounds = new kakao.maps.LatLngBounds();
      path.forEach(p => bounds.extend(p));
      map.setBounds(bounds, 80);
    }}

    if (GEOJSON) drawPolygon(GEOJSON);

    kakao.maps.event.addListener(map, 'click', function(e) {{
      var lat = e.latLng.getLat();
      var lng = e.latLng.getLng();
      // Streamlit 텍스트박스로 좌표 전달
      var inputs = window.parent.document.querySelectorAll('input[type="text"]');
      if(inputs.length>0){{
        var inp = inputs[0];
        var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype,'value').set;
        setter.call(inp, lat.toFixed(7)+','+lng.toFixed(7));
        ['input','keydown','keypress','keyup'].forEach(t => {{
          inp.dispatchEvent(t.startsWith('key') 
            ? new inp.ownerDocument.defaultView.KeyboardEvent(t, {{key:'Enter', keyCode:13, bubbles:true}}) 
            : new inp.ownerDocument.defaultView.Event(t, {{bubbles:true}}));
        }});
      }}
    }});
  }});
}})();
</script>
</body>
</html>
"""

# --- Streamlit 레이아웃 ---
col_map, col_info = st.columns([6, 4], gap="medium")

with col_map:
    st.components.v1.html(MAP_HTML, height=520, scrolling=False)

with col_info:
    st.markdown("<p>지도를 클릭하면 건축물대장 조회와 하이라이트가 동시 작동합니다.</p>", unsafe_allow_html=True)
