import streamlit as st
import requests
import json

st.set_page_config(
    page_title="건축물대장 조회 서비스",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# [수정] 키 값들 공백 제거 및 할당
try:
    KAKAO_JS_KEY     = st.secrets["KAKAO_JS_KEY"].strip()
    KAKAO_REST_KEY   = st.secrets["KAKAO_REST_KEY"].strip()
    BUILDING_API_KEY = st.secrets["BUILDING_API_KEY"].strip()
    VWORLD_KEY       = st.secrets["VWORLD_KEY"].strip()
except Exception:
    KAKAO_JS_KEY     = "057a4a253017791fe6072d7b089a063a"
    KAKAO_REST_KEY   = "c5af33c0d1d6a654362d3fea152cc076"
    BUILDING_API_KEY = "9619e124e16b9e57bad6cfefdc82f6c87749176260b4caff32eda964aad5de1b"
    VWORLD_KEY       = "F12043F0-86DF-3395-9004-27A377FD5FB6"

# [수정] 브이월드 API 호출 함수 최적화 (RemoteDisconnected 해결용)
def get_parcel_polygon(lat, lng):
    # WFS 대신 더 안정적인 Data API 사용
    url = "https://api.vworld.kr/req/data"
    params = {
        "service": "data",
        "request": "GetFeature",
        "data": "LP_PA_CBND_BUBUN", # 지적도 레이어
        "key": VWORLD_KEY,
        "geomFilter": f"POINT({lng} {lat})", # 경도 위도 순서
        "geometry": "true",
        "crs": "EPSG:4326",
        "domain": "s1map-tool.streamlit.app" # 사용자님의 실제 도메인
    }
    # 브라우저 요청인 것처럼 헤더 추가 (매우 중요)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://s1map-tool.streamlit.app"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code != 200: return None, f"HTTP {resp.status_code}"
        data = resp.json()
        if data.get("response", {}).get("status") == "OK":
            feature = data["response"]["result"]["featureCollection"]["features"][0]
            return feature.get("geometry"), "OK"
        return None, "결과 없음"
    except Exception as e:
        return None, str(e)

# --- 기존 유틸리티 함수 (수정 없음) ---
def get_region_code(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    try:
        resp = requests.get(url, headers=headers, params={"x": lng, "y": lat}, timeout=10)
        docs = resp.json().get("documents", [])
        return next((d for d in docs if d.get("region_type") == "B"), None)
    except Exception: return None

def get_jibun_address(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    try:
        resp = requests.get(url, headers=headers, params={"x": lng, "y": lat}, timeout=10)
        docs = resp.json().get("documents", [])
        return docs[0] if docs else {}
    except Exception: return {}

def get_building_title(sigungu_cd, bjdong_cd, bun, ji):
    url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitleInfo"
    params = {
        "serviceKey": BUILDING_API_KEY, "sigunguCd": sigungu_cd, "bjdongCd": bjdong_cd,
        "bun": str(bun).zfill(4), "ji": str(ji).zfill(4), "numOfRows": "10", "_type": "json",
    }
    try:
        res = requests.get(url, params=params, timeout=10).json()
        items = res.get("response", {}).get("body", {}).get("items", {})
        if not items: return []
        il = items.get("item", [])
        return [il] if isinstance(il, dict) else il
    except Exception: return []

# --- 스타일 및 헤더 (기존 코드 유지) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.app-header { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); border-radius: 16px; padding: 28px 36px; margin-bottom: 20px; display: flex; align-items: center; gap: 18px; box-shadow: 0 8px 32px rgba(0,0,0,.25); }
.app-header h1 { color:#fff; margin:0; font-size:1.7rem; font-weight:700; }
.info-card { background:#fff; border:1px solid #e8edf2; border-radius:14px; padding:22px 26px; margin-bottom:16px; box-shadow:0 2px 12px rgba(0,0,0,.06); }
.data-row { display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px dashed #f0f4f8; font-size:.88rem; }
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:.78rem; font-weight:600; }
.badge-green { background:#e8f5e9; color:#2e7d32; }
.debug-box { background:#f0fff4; border:1px solid #9ae6b4; border-radius:8px; padding:10px 14px; color:#276749; font-size:.75rem; margin-bottom:10px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-header"><div style="font-size:2.4rem">🏢</div><div><h1>건축물대장 조회 서비스</h1><p style="color:#8ecae6;margin:0;">지도를 클릭하면 필지가 하이라이트됩니다</p></div></div>', unsafe_allow_html=True)

col_map, col_info = st.columns([6, 4], gap="medium")

for k, v in [("addr_info",None),("building_title",None),("last_coord",""),("parcel_geom",None),("parcel_status","")]:
    if k not in st.session_state: st.session_state[k] = v

coord_input = st.text_input("coord", value="", key="coord_box", label_visibility="collapsed")

if coord_input and coord_input != st.session_state.last_coord:
    st.session_state.last_coord = coord_input
    try:
        lat, lng = map(float, coord_input.split(","))
        st.session_state.addr_info = get_jibun_address(lat, lng)
        bjd_doc = get_region_code(lat, lng)
        geom, status = get_parcel_polygon(lat, lng)
        st.session_state.parcel_geom = geom
        st.session_state.parcel_status = status

        if bjd_doc:
            b_code = bjd_doc.get("code", "")
            jibun = st.session_state.addr_info.get("address", {})
            st.session_state.building_title = get_building_title(b_code[:5], b_code[5:10], jibun.get("main_address_no", "0"), jibun.get("sub_address_no", "0"))
    except Exception as e:
        st.session_state.parcel_status = str(e)

parcel_json = json.dumps(st.session_state.parcel_geom) if st.session_state.parcel_geom else "null"

# [수정] 지도를 그리는 JS 로직 유지 및 지적도 처리 부분 강화
MAP_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; }}
  #map {{ width:100%; height:500px; border-radius:12px; }}
  #status {{ position:absolute; top:10px; left:50%; transform:translateX(-50%); background:white; padding:8px 20px; border-radius:24px; font-size:13px; z-index:10; box-shadow:0 2px 12px rgba(0,0,0,.15); }}
</style>
</head>
<body>
<div id="status">🖱️ 지도를 클릭하면 필지를 조회합니다</div>
<div id="map"></div>
<script>
var PARCEL_GEOM = {parcel_json};
(function() {{
  var script = document.createElement('script');
  script.src = 'https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false';
  script.onload = function() {{
    kakao.maps.load(function() {{
      var map = new kakao.maps.Map(document.getElementById('map'), {{
        center: new kakao.maps.LatLng(37.5665, 126.9780), level: 3
      }});
      var polygon = null, marker = null;

      function drawPolygon(geom) {{
        if (polygon) polygon.setMap(null);
        if (!geom) return;
        // MultiPolygon과 Polygon 모두 대응
        var rings = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0];
        var path = rings.map(function(c) {{ return new kakao.maps.LatLng(c[1], c[0]); }});
        polygon = new kakao.maps.Polygon({{
          map: map, path: path, strokeWeight: 3, strokeColor: '#FF0000', strokeOpacity: 1, fillColor: '#FF0000', fillOpacity: 0.3
        }});
        var bounds = new kakao.maps.LatLngBounds();
        path.forEach(function(p) {{ bounds.extend(p); }});
        map.setBounds(bounds, 80);
      }}

      if (PARCEL_GEOM) drawPolygon(PARCEL_GEOM);

      kakao.maps.event.addListener(map, 'click', function(e) {{
        var lat = e.latLng.getLat(), lng = e.latLng.getLng();
        if (marker) marker.setMap(null);
        marker = new kakao.maps.Marker({{ position: e.latLng, map: map }});
        document.getElementById('status').innerHTML = '⏳ 조회 중...';
        
        var inputs = window.parent.document.querySelectorAll('input[type="text"]');
        if (inputs.length > 0) {{
          var inp = inputs[0];
          var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
          setter.call(inp, lat.toFixed(7) + ',' + lng.toFixed(7));
          inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
          inp.dispatchEvent(new KeyboardEvent('keydown', {{ key:'Enter', keyCode:13, bubbles:true }}));
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

with col_map:
    st.components.v1.html(MAP_HTML, height=520)

with col_info:
    if st.session_state.addr_info is None:
        st.info("지도를 클릭해 주세요.")
    else:
        # 결과 표시 (기존 코드와 동일)
        addr = st.session_state.addr_info
        st.markdown(f'<div class="info-card"><h3>📍 위치 정보</h3><div class="data-row"><span class="data-label">지번 주소</span><span class="data-value">{addr.get("address",{}).get("address_name","")}</span></div></div>', unsafe_allow_html=True)
        
        if st.session_state.parcel_status != "OK":
            st.markdown(f'<div class="debug-box">상태: {st.session_state.parcel_status}</div>', unsafe_allow_html=True)

        titles = st.session_state.building_title
        if titles:
            for item in titles[:3]:
                st.markdown(f"""
                <div class="info-card">
                    <h3>🏗️ {item.get('bldNm') or '건물'}</h3>
                    <div class="data-row"><span class="data-label">주용도</span><span class="badge badge-green">{item.get('mainPurpsCdNm')}</span></div>
                    <div class="data-row"><span class="data-label">연면적</span><span class="data-value">{item.get('totArea')} ㎡</span></div>
                </div>
                """, unsafe_allow_html=True)
