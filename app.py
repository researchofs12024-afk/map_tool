import streamlit as st
import requests
import json

st.set_page_config(
    page_title="건축물대장 조회 서비스",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# [설정] 비밀키 로드 및 공백 제거
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

# [기능] 카카오 API 주소 조회
def get_region_code(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    try:
        resp = requests.get(url, headers=headers, params={"x": lng, "y": lat}, timeout=10)
        docs = resp.json().get("documents", [])
        return next((d for d in docs if d.get("region_type") == "B"), None)
    except: return None

def get_jibun_address(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    try:
        resp = requests.get(url, headers=headers, params={"x": lng, "y": lat}, timeout=10)
        docs = resp.json().get("documents", [])
        return docs[0] if docs else {}
    except: return {}

# [기능] 건축물대장 정보 조회
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
    except: return []

# [CSS 스타일]
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.app-header { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); border-radius: 16px; padding: 28px 36px; margin-bottom: 20px; display: flex; align-items: center; gap: 18px; box-shadow: 0 8px 32px rgba(0,0,0,.25); }
.app-header h1 { color:#fff; margin:0; font-size:1.7rem; font-weight:700; }
.info-card { background:#fff; border:1px solid #e8edf2; border-radius:14px; padding:22px 26px; margin-bottom:16px; box-shadow:0 2px 12px rgba(0,0,0,.06); }
.data-row { display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px dashed #f0f4f8; font-size:.88rem; }
.badge-green { background:#e8f5e9; color:#2e7d32; padding:3px 10px; border-radius:20px; font-size:.78rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-header"><div style="font-size:2.4rem">🏢</div><div><h1>건축물대장 조회 서비스</h1><p style="color:#8ecae6;margin:0;">지도를 클릭하면 필지가 붉게 하이라이트됩니다</p></div></div>', unsafe_allow_html=True)

col_map, col_info = st.columns([6, 4], gap="medium")

# 세션 상태 관리
if "addr_info" not in st.session_state: st.session_state.addr_info = None
if "building_title" not in st.session_state: st.session_state.building_title = None
if "last_coord" not in st.session_state: st.session_state.last_coord = ""

# 숨겨진 좌표 입력창
coord_input = st.text_input("coord", value="", key="coord_box", label_visibility="collapsed")

if coord_input and coord_input != st.session_state.last_coord:
    st.session_state.last_coord = coord_input
    lat, lng = map(float, coord_input.split(","))
    st.session_state.addr_info = get_jibun_address(lat, lng)
    bjd_doc = get_region_code(lat, lng)
    if bjd_doc:
        b_code = bjd_doc.get("code", "")
        jibun = st.session_state.addr_info.get("address", {})
        st.session_state.building_title = get_building_title(b_code[:5], b_code[5:10], jibun.get("main_address_no", "0"), jibun.get("sub_address_no", "0"))

# --- 지도 HTML (중괄호 이스케이프 완료 및 지도 로딩 검증) ---
MAP_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; }}
  #map {{ width:100%; height:520px; border-radius:12px; }}
  #status {{ position:absolute; top:10px; left:50%; transform:translateX(-50%); background:white; padding:8px 20px; border-radius:24px; font-size:13px; z-index:10; box-shadow:0 2px 12px rgba(0,0,0,0.15); }}
</style>
</head>
<body>
<div id="status">🖱️ 지도를 클릭하면 필지를 조회합니다</div>
<div id="map"></div>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false"></script>
<script>
var VWORLD_KEY = "{VWORLD_KEY}";

kakao.maps.load(function() {{
  var mapContainer = document.getElementById('map');
  var mapOption = {{ center: new kakao.maps.LatLng(37.5665, 126.9780), level: 3 }};
  var map = new kakao.maps.Map(mapContainer, mapOption);
  
  var polygon = null;
  var marker = null;

  function drawPolygon(geom) {{
    if (polygon) polygon.setMap(null);
    var rings = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0];
    var path = rings.map(function(c) {{ return new kakao.maps.LatLng(c[1], c[0]); }});
    
    polygon = new kakao.maps.Polygon({{
      map: map,
      path: path,
      strokeWeight: 3,
      strokeColor: '#FF0000',
      strokeOpacity: 0.8,
      fillColor: '#FF0000',
      fillOpacity: 0.2
    }});
    
    var bounds = new kakao.maps.LatLngBounds();
    path.forEach(function(p) {{ bounds.extend(p); }});
    map.setBounds(bounds, 80);
    document.getElementById('status').innerHTML = '🔴 필지 하이라이트 완료';
  }}

  function fetchParcel(lat, lng) {{
    var url = "https://api.vworld.kr/req/data?service=data&request=GetFeature&data=lp_pa_cbnd_bubun&key=" + VWORLD_KEY + 
              "&geomFilter=POINT(" + lng + " " + lat + ")&geometry=true&crs=EPSG:4326&domain=s1map-tool.streamlit.app";
    
    fetch(url)
      .then(function(res) {{ return res.json(); }})
      .then(function(data) {{
        if (data.response && data.response.status === "OK") {{
          var feature = data.response.result.featureCollection.features[0];
          drawPolygon(feature.geometry);
        }}
      }})
      .catch(function(err) {{ console.error(err); }});
  }}

  kakao.maps.event.addListener(map, 'click', function(e) {{
    var lat = e.latLng.getLat();
    var lng = e.latLng.getLng();
    
    if (marker) marker.setMap(null);
    marker = new kakao.maps.Marker({{ position: e.latLng, map: map }});
    
    document.getElementById('status').innerHTML = '⏳ 필지 조회 중...';
    fetchParcel(lat, lng);

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
</script>
</body>
</html>
"""

with col_map:
    st.components.v1.html(MAP_HTML, height=540)

with col_info:
    if st.session_state.addr_info is None:
        st.info("지도를 클릭하여 건물 정보를 확인하세요.")
    else:
        addr = st.session_state.addr_info
        st.markdown(f'<div class="info-card"><h3>📍 선택 위치</h3><div class="data-row"><span class="data-label">주소</span><span class="data-value">{addr.get("address",{}).get("address_name","")}</span></div></div>', unsafe_allow_html=True)
        
        titles = st.session_state.building_title
        if titles:
            for item in titles[:3]:
                st.markdown(f"""
                <div class="info-card">
                    <h3>🏗️ {item.get('bldNm') or '건물'}</h3>
                    <div class="data-row"><span class="data-label">주용도</span><span class="badge-green">{item.get('mainPurpsCdNm')}</span></div>
                    <div class="data-row"><span class="data-label">연면적</span><span class="data-value">{item.get('totArea')} ㎡</span></div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("건축물대장 정보가 없습니다.")
