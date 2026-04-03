import streamlit as st
import requests
import json
import os

st.set_page_config(
    page_title="건축물대장 + GeoJSON 하이라이트",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# API Key 설정
# -----------------------------
try:
    KAKAO_JS_KEY     = st.secrets["KAKAO_JS_KEY"]
    KAKAO_REST_KEY   = st.secrets["KAKAO_REST_KEY"]
    BUILDING_API_KEY = st.secrets["BUILDING_API_KEY"]
    VWORLD_KEY       = st.secrets["VWORLD_KEY"]
except Exception:
    KAKAO_JS_KEY     = "057a4a253017791fe6072d7b089a063a"
    KAKAO_REST_KEY   = "c5af33c0d1d6a654362d3fea152cc076"
    BUILDING_API_KEY = "9619e124e16b9e57bad6cfefdc82f6c87749176260b4caff32eda964aad5de1b"
    VWORLD_KEY       = "F12043F0-86DF-3395-9004-27A377FD5FB6"

# -----------------------------
# GeoJSON 파일 로드
# -----------------------------
GEOJSON_FILE = "서울중구.geojson"
geojson_data = None
if os.path.exists(GEOJSON_FILE):
    with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

# -----------------------------
# 기존 건축물대장 조회 함수들
# 그대로 유지
# -----------------------------
def get_region_code(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    try:
        resp = requests.get(url, headers=headers, params={"x": lng, "y": lat}, timeout=10)
        docs = resp.json().get("documents", [])
        return next((d for d in docs if d.get("region_type") == "B"), None)
    except Exception:
        return None

def get_jibun_address(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    try:
        resp = requests.get(url, headers=headers, params={"x": lng, "y": lat}, timeout=10)
        docs = resp.json().get("documents", [])
        return docs[0] if docs else {}
    except Exception:
        return {}

def get_parcel_polygon(lat, lng):
    v_key = VWORLD_KEY.strip()
    url = "https://api.vworld.kr/req/data"
    params = {
        "service": "data",
        "request": "GetFeature",
        "data": "lp_pa_cbnd_bubun",
        "key": v_key,
        "geomFilter": f"POINT({lng} {lat})",
        "geometry": "true",
        "crs": "EPSG:4326",
        "domain": "s1map-tool.streamlit.app"
    }
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://s1map-tool.streamlit.app"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        if data.get("response", {}).get("status") == "OK":
            feature = data["response"]["result"]["featureCollection"]["features"][0]
            return feature.get("geometry"), "OK"
        return None, f"데이터 없음: {data.get('response',{}).get('status')}"
    except Exception as e:
        return None, f"연결오류: {str(e)[:50]}"

def get_building_title(sigungu_cd, bjdong_cd, bun, ji):
    url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitleInfo"
    params = {
        "serviceKey": BUILDING_API_KEY,
        "sigunguCd": sigungu_cd, "bjdongCd": bjdong_cd,
        "bun": str(bun).zfill(4), "ji": str(ji).zfill(4),
        "numOfRows": "10", "pageNo": "1", "_type": "json",
    }
    try:
        body  = requests.get(url, params=params, timeout=10).json().get("response", {}).get("body", {})
        items = body.get("items", {})
        if not items: return []
        il = items.get("item", [])
        return [il] if isinstance(il, dict) else il
    except Exception:
        return []

def get_building_info(sigungu_cd, bjdong_cd, bun, ji):
    url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrBasisOulnInfo"
    params = {
        "serviceKey": BUILDING_API_KEY,
        "sigunguCd": sigungu_cd, "bjdongCd": bjdong_cd,
        "bun": str(bun).zfill(4), "ji": str(ji).zfill(4),
        "numOfRows": "10", "pageNo": "1", "_type": "json",
    }
    try:
        body  = requests.get(url, params=params, timeout=10).json().get("response", {}).get("body", {})
        items = body.get("items", {})
        if not items: return []
        il = items.get("item", [])
        return [il] if isinstance(il, dict) else il
    except Exception:
        return []

# -----------------------------
# Streamlit Map HTML (Kakao) + GeoJSON 하이라이트
# -----------------------------
parcel_json = json.dumps(st.session_state.get("parcel_geom")) if st.session_state.get("parcel_geom") else "null"
geojson_json = json.dumps(geojson_data) if geojson_data else "null"

MAP_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
#map {{ width:100%; height:520px; border-radius:12px; }}
#status {{ position:absolute; top:10px; left:50%; transform:translateX(-50%);
           background:rgba(255,255,255,.95); border-radius:24px; padding:8px 20px;
           font-size:13px; color:#37474f; box-shadow:0 2px 12px rgba(0,0,0,.15);
           z-index:10; backdrop-filter:blur(4px); white-space:nowrap; }}
</style>
</head>
<body>
<div class="wrapper">
  <div id="status">🖱️ 지도를 클릭하면 필지를 조회합니다</div>
  <div id="map"></div>
</div>
<script>
var PARCEL_GEOM = {parcel_json};
var GEOJSON     = {geojson_json};

(function() {{
  var script = document.createElement('script');
  script.src = 'https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false';
  script.onload = function() {{
    kakao.maps.load(function() {{
      var map = new kakao.maps.Map(document.getElementById('map'), {{
        center: new kakao.maps.LatLng(37.5665, 126.9780), level: 3
      }});
      map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
      map.addControl(new kakao.maps.MapTypeControl(), kakao.maps.ControlPosition.TOPRIGHT);

      // 기존 필지 Polygon
      var parcelPoly = null;
      function drawParcel(geom) {{
        if(parcelPoly) parcelPoly.setMap(null);
        if(!geom) return;
        var rings = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0];
        var path = rings.map(c => new kakao.maps.LatLng(c[1], c[0]));
        parcelPoly = new kakao.maps.Polygon({{
          map: map, path: path,
          strokeWeight: 3, strokeColor: '#E53E3E', strokeOpacity: 1,
          fillColor: '#FC8181', fillOpacity: 0.35,
        }});
      }}
      drawParcel(PARCEL_GEOM);

      // GeoJSON Polygon 하이라이트
      var geoPolys = [];
      if(GEOJSON && GEOJSON.features){{
        GEOJSON.features.forEach(f => {{
          var coords = f.geometry.coordinates;
          coords.forEach(polygonSet => {{
            polygonSet.forEach(ring => {{
              var path = ring.map(c => new kakao.maps.LatLng(c[1], c[0]));
              var poly = new kakao.maps.Polygon({{
                map: map, path: path,
                strokeWeight: 1, strokeColor: '#3182CE',
                fillColor: '#63B3ED', fillOpacity: 0.25,
              }});
              geoPolys.push(poly);
            }});
          }});
        }});
      }}

      // 클릭 이벤트 (기존 건축물대장 조회)
      kakao.maps.event.addListener(map, 'click', function(e){{
        var lat = e.latLng.getLat(), lng = e.latLng.getLng();
        var inputs = window.parent.document.querySelectorAll('input[type="text"]');
        if(inputs.length>0){{
          var inp = inputs[0], coord = lat.toFixed(7)+','+lng.toFixed(7);
          var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype,'value').set;
          setter.call(inp, coord);
          ['input','keydown','keypress','keyup'].forEach(t=>{{
            inp.dispatchEvent(t.startsWith('key') ? new inp.ownerDocument.defaultView.KeyboardEvent(t,{{key:'Enter',keyCode:13,bubbles:true}})
                                                 : new inp.ownerDocument.defaultView.Event(t,{{bubbles:true}}));
          }});
        }}
      }});
    }});
  }};
  document.head.appendChild(script);
}})();
</script>
</body>
</html>
"""

# -----------------------------
# Streamlit Columns
# -----------------------------
col_map, col_info = st.columns([6,4], gap="medium")
with col_map:
    st.components.v1.html(MAP_HTML, height=520, scrolling=False)
