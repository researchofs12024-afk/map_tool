import streamlit as st
import requests
import json

st.set_page_config(
    page_title="건축물대장 조회 서비스",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# [1] API 키 설정
try:
    KAKAO_JS_KEY     = st.secrets["KAKAO_JS_KEY"].strip()
    KAKAO_REST_KEY   = st.secrets["KAKAO_REST_KEY"].strip()
    BUILDING_API_KEY = st.secrets["BUILDING_API_KEY"].strip()
    VWORLD_KEY       = st.secrets["VWORLD_KEY"].strip()
except:
    # 기본값 (테스트용)
    KAKAO_JS_KEY     = "057a4a253017791fe6072d7b089a063a"
    KAKAO_REST_KEY   = "c5af33c0d1d6a654362d3fea152cc076"
    BUILDING_API_KEY = "9619e124e16b9e57bad6cfefdc82f6c87749176260b4caff32eda964aad5de1b"
    VWORLD_KEY       = "F12043F0-86DF-3395-9004-27A377FD5FB6"

MY_DOMAIN = "s1map-tool.streamlit.app"

# [2] 건축물대장 및 주소 조회 함수 (기존 로직 유지)
def get_region_code(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    try:
        resp = requests.get(url, headers=headers, params={"x": lng, "y": lat}, timeout=5)
        return next((d for d in resp.json().get("documents", []) if d.get("region_type") == "B"), None)
    except: return None

def get_jibun_address(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    try:
        resp = requests.get(url, headers=headers, params={"x": lng, "y": lat}, timeout=5)
        return resp.json().get("documents", [{}])[0]
    except: return {}

def get_building_title(sc, bc, bun, ji):
    url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitleInfo"
    params = {
        "serviceKey": BUILDING_API_KEY, "sigunguCd": sc, "bjdongCd": bc,
        "bun": str(bun).zfill(4), "ji": str(ji).zfill(4), "numOfRows": "10", "_type": "json"
    }
    try:
        res = requests.get(url, params=params, timeout=5).json()
        items = res.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        return [items] if isinstance(items, dict) else items
    except: return []

# [3] UI 디자인
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.app-header { background: linear-gradient(135deg, #0f2027 0%, #2c5364 100%); border-radius: 15px; padding: 25px; color: white; margin-bottom: 20px; }
.info-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #eee; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
.data-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed #eee; font-size: 14px; }
</style>
<div class="app-header"><h1>🏢 건축물대장 & 지적도 서비스</h1><p>지도를 클릭하면 필지 경계가 붉게 표시됩니다.</p></div>
""", unsafe_allow_html=True)

col_map, col_info = st.columns([6, 4])

if "addr_info" not in st.session_state: st.session_state.addr_info = None
if "building_title" not in st.session_state: st.session_state.building_title = None

# Hidden Input for JS communication
coord_input = st.text_input("coord", value="", key="coord_box", label_visibility="collapsed")

if coord_input:
    lat, lng = map(float, coord_input.split(","))
    st.session_state.addr_info = get_jibun_address(lat, lng)
    bjd = get_region_code(lat, lng)
    if bjd:
        code = bjd.get("code", "")
        jb = st.session_state.addr_info.get("address", {})
        st.session_state.building_title = get_building_title(code[:5], code[5:10], jb.get("main_address_no", "0"), jb.get("sub_address_no", "0"))

# [4] 지도 HTML 템플릿 (f-string을 쓰지 않아 안전함)
MAP_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        * { margin:0; padding:0; }
        #map { width:100%; height:520px; border-radius:12px; background: #f0f0f0; }
        #status { position:absolute; top:10px; left:50%; transform:translateX(-50%); background:white; padding:8px 15px; border-radius:20px; z-index:10; font-size:12px; box-shadow:0 2px 10px rgba(0,0,0,0.1); font-weight:bold; }
    </style>
</head>
<body>
    <div id="status">🖱️ 지도를 클릭해 보세요</div>
    <div id="map"></div>
    <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=__KAKAO_KEY__&autoload=false"></script>
    <script>
    var VWORLD_KEY = "__VWORLD_KEY__";
    var DOMAIN = "__DOMAIN__";

    kakao.maps.load(function() {
        var container = document.getElementById('map');
        var options = { center: new kakao.maps.LatLng(37.5665, 126.9780), level: 3 };
        var map = new kakao.maps.Map(container, options);
        var polygon = null;
        var marker = null;

        function drawPolygon(geom) {
            if (polygon) polygon.setMap(null);
            var rings = (geom.type === 'Polygon') ? geom.coordinates[0] : geom.coordinates[0][0];
            var path = rings.map(function(c) { return new kakao.maps.LatLng(c[1], c[0]); });
            
            polygon = new kakao.maps.Polygon({
                map: map, path: path, strokeWeight: 3, strokeColor: '#FF0000', strokeOpacity: 0.8, fillColor: '#FF0000', fillOpacity: 0.2
            });
            
            var bounds = new kakao.maps.LatLngBounds();
            path.forEach(function(p) { bounds.extend(p); });
            map.setBounds(bounds, 80);
            document.getElementById('status').innerHTML = '🔴 필지 하이라이트 완료';
        }

        function getVworldData(lat, lng) {
            var url = "https://api.vworld.kr/req/data?service=data&request=GetFeature&data=lp_pa_cbnd_bubun&key=" + VWORLD_KEY + 
                      "&geomFilter=POINT(" + lng + " " + lat + ")&geometry=true&crs=EPSG:4326&domain=" + DOMAIN;
            
            fetch(url)
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    if (data.response && data.response.status === "OK") {
                        drawPolygon(data.response.result.featureCollection.features[0].geometry);
                    } else {
                        document.getElementById('status').innerHTML = '⚠️ 지적도 정보 없음';
                    }
                }).catch(function(e) { console.error(e); });
        }

        kakao.maps.event.addListener(map, 'click', function(e) {
            var lat = e.latLng.getLat();
            var lng = e.latLng.getLng();
            
            if (marker) marker.setMap(null);
            marker = new kakao.maps.Marker({ position: e.latLng, map: map });
            
            document.getElementById('status').innerHTML = '⏳ 조회 중...';
            getVworldData(lat, lng);

            var inputs = window.parent.document.querySelectorAll('input[type="text"]');
            if (inputs.length > 0) {
                var inp = inputs[0];
                var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
                setter.call(inp, lat.toFixed(7) + ',' + lng.toFixed(7));
                inp.dispatchEvent(new Event('input', { bubbles: true }));
                inp.dispatchEvent(new KeyboardEvent('keydown', { key:'Enter', keyCode:13, bubbles:true }));
            }
        });
    });
    </script>
</body>
</html>
"""

# HTML 데이터 주입 (f-string 우회)
final_html = MAP_HTML_TEMPLATE.replace("__KAKAO_KEY__", KAKAO_JS_KEY)\
                             .replace("__VWORLD_KEY__", VWORLD_KEY)\
                             .replace("__DOMAIN__", MY_DOMAIN)

with col_map:
    st.components.v1.html(final_html, height=540)

with col_info:
    if st.session_state.addr_info:
        addr = st.session_state.addr_info
        st.markdown(f"""
        <div class="info-card">
            <h3>📍 선택된 위치</h3>
            <div class="data-row"><span>지번 주소</span><span>{addr.get('address',{}).get('address_name','-')}</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        titles = st.session_state.building_title
        if titles:
            for item in titles[:3]:
                st.markdown(f"""
                <div class="info-card">
                    <h3 style="color:#1565c0;">🏗️ {item.get('bldNm') or '건물'}</h3>
                    <div class="data-row"><span>주용도</span><b>{item.get('mainPurpsCdNm')}</b></div>
                    <div class="data-row"><span>연면적</span><span>{item.get('totArea')} ㎡</span></div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.write("지도를 클릭해 주세요.")
