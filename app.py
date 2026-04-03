import streamlit as st
import requests
import json
import os

st.set_page_config(
    page_title="건축물대장 조회 + GeoJSON 하이라이트",
    layout="wide",
)

# 🔑 키 불러오기
try:
    KAKAO_JS_KEY     = st.secrets["KAKAO_JS_KEY"]
    KAKAO_REST_KEY   = st.secrets["KAKAO_REST_KEY"]
    BUILDING_API_KEY = st.secrets["BUILDING_API_KEY"]
except Exception:
    KAKAO_JS_KEY     = "YOUR_KAKAO_JS_KEY"
    KAKAO_REST_KEY   = "YOUR_KAKAO_REST_KEY"
    BUILDING_API_KEY = "YOUR_BUILDING_API_KEY"

# ------------------------
# GeoJSON 로드 (Python에서)
# ------------------------
geojson_path = "서울중구.geojson"
if os.path.exists(geojson_path):
    with open(geojson_path, encoding="utf-8") as f:
        geojson_data = json.load(f)
    geojson_js = json.dumps(geojson_data)
else:
    geojson_data = None
    geojson_js = "null"

# ------------------------
# 건축물대장 조회 함수
# ------------------------
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

# ------------------------
# Streamlit session 초기화
# ------------------------
for k, v in [("addr_info",None),("building_title",None),("building_basic",None),
             ("last_coord",""),("parcel_geom",None),("parcel_status","")]:
    if k not in st.session_state:
        st.session_state[k] = v

coord_input = st.text_input("coord", value="", key="coord_box", label_visibility="collapsed")

# ------------------------
# 좌표 입력 시 데이터 조회
# ------------------------
if coord_input and coord_input != st.session_state.last_coord:
    st.session_state.last_coord = coord_input
    try:
        lat, lng = map(float, coord_input.split(","))
        addr_doc = get_jibun_address(lat, lng)
        bjd_doc  = get_region_code(lat, lng)

        st.session_state.addr_info = addr_doc

        if bjd_doc:
            b_code = bjd_doc.get("code", "")
            jibun = addr_doc.get("address", {}) if addr_doc else {}
            main_no = jibun.get("main_address_no", "0") or "0"
            sub_no  = jibun.get("sub_address_no",  "0") or "0"
            if len(b_code) >= 10:
                sc = b_code[:5]; bc = b_code[5:10]
                # 여기서 건축물대장 API 호출 가능
                st.session_state.building_title = []  # 실제 API 호출 필요
                st.session_state.building_basic = []

    except Exception as e:
        st.session_state.addr_info = {"error": str(e)}

# ------------------------
# Map HTML (GeoJSON + Parcel 하이라이트)
# ------------------------
MAP_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  #map {{ width:100%; height:520px; border-radius:12px; }}
  #status {{ position:absolute; top:10px; left:50%; transform:translateX(-50%);
             background:rgba(255,255,255,.95); padding:6px 12px; border-radius:12px; z-index:10; }}
</style>
</head>
<body>
<div id="status">🖱️ 클릭하면 필지 조회</div>
<div id="map"></div>
<script>
var GEOJSON_DATA = {geojson_js};

(function(){{
  var script = document.createElement('script');
  script.src = 'https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false';
  script.onload = function(){{
    kakao.maps.load(function(){{
      var map = new kakao.maps.Map(document.getElementById('map'), {{
        center: new kakao.maps.LatLng(37.5665, 126.9780), level: 3
      }});
      map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
      map.addControl(new kakao.maps.MapTypeControl(), kakao.maps.ControlPosition.TOPRIGHT);

      var polygon = null, marker = null;

      // 🔴 GeoJSON 하이라이트
      if(GEOJSON_DATA){{
        for(var f of GEOJSON_DATA.features){{
          var coords = f.geometry.coordinates;
          var rings = f.geometry.type === "Polygon" ? coords[0] : coords[0][0];
          var path = rings.map(c=> new kakao.maps.LatLng(c[1],c[0]));
          var pg = new kakao.maps.Polygon({{
            path:path, strokeWeight:2, strokeColor:'#FF0000',
            fillColor:'#FF0000', fillOpacity:0.3
          }});
          pg.setMap(map);
        }}
      }}

      // 지도 클릭 이벤트
      kakao.maps.event.addListener(map,'click',function(e){{
        var lat = e.latLng.getLat(), lng = e.latLng.getLng();
        if(marker) marker.setMap(null);
        marker = new kakao.maps.Marker({{ position:e.latLng, map:map }});

        var inputs = window.parent.document.querySelectorAll('input[type="text"]');
        if(inputs.length>0){{
          var inp = inputs[0], coord = lat.toFixed(7)+','+lng.toFixed(7);
          var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype,'value').set;
          setter.call(inp, coord);
          ['input','keydown','keypress','keyup'].forEach(function(t){{
            inp.dispatchEvent(t.startsWith('key')? new inp.ownerDocument.defaultView.KeyboardEvent(t,{{key:'Enter',keyCode:13,bubbles:true}}) : new inp.ownerDocument.defaultView.Event(t,{{bubbles:true}}));
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

col_map, col_info = st.columns([6,4], gap="medium")
with col_map:
    st.components.v1.html(MAP_HTML, height=520, scrolling=False)

with col_info:
    st.write("좌표 입력 후 클릭하면 GeoJSON 필지 하이라이트 + 건축물대장 정보 표시")
