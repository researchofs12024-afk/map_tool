import streamlit as st
import requests
import json

st.set_page_config(
    page_title="건축물대장 조회 서비스",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 키 설정 (공백 제거 적용)
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

MY_DOMAIN = "s1map-tool.streamlit.app"

# [기존 기능 유지] 주소 및 건축물 정보 조회 함수들
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
        "serviceKey": BUILDING_API_KEY,
        "sigunguCd": sigungu_cd, "bjdongCd": bjdong_cd,
        "bun": str(bun).zfill(4), "ji": str(ji).zfill(4),
        "numOfRows": "10", "pageNo": "1", "_type": "json",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        body = resp.json().get("response", {}).get("body", {})
        items = body.get("items", {})
        if not items: return []
        il = items.get("item", [])
        return [il] if isinstance(il, dict) else il
    except Exception: return []

# 스타일 정의
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.app-header {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    border-radius: 16px; padding: 28px 36px; margin-bottom: 20px;
    display: flex; align-items: center; gap: 18px; color: white;
}
.app-header h1 { color:#fff; margin:0; font-size:1.7rem; }
.info-card {
    background:#fff; border:1px solid #e8edf2; border-radius:14px;
    padding:22px 26px; margin-bottom:16px; box-shadow:0 2px 12px rgba(0,0,0,.06);
}
.data-row { display:flex; justify-content:space-between; padding:7px 0; border-bottom:1px dashed #f0f4f8; font-size:.88rem; }
.data-label { color:#6b7c8d; font-weight:500; }
.data-value { color:#1a2e3b; font-weight:600; }
.badge { padding:3px 10px; border-radius:20px; font-size:.78rem; font-weight:600; }
.badge-green { background:#e8f5e9; color:#2e7d32; }
.badge-orange { background:#fff3e0; color:#e65100; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div style="font-size:2.4rem">🏢</div>
    <div>
        <h1>건축물대장 조회 서비스</h1>
        <p style="margin:0; font-size:0.9rem; color:#8ecae6;">지도를 클릭하면 해당 필지 경계가 표시되고 정보가 조회됩니다</p>
    </div>
</div>
""", unsafe_allow_html=True)

col_map, col_info = st.columns([6, 4], gap="medium")

# 세션 상태 초기화
for k, v in [("addr_info",None),("building_title",None),("last_coord","")]:
    if k not in st.session_state: st.session_state[k] = v

# 히든 입력창 (JS에서 좌표를 전달받음)
coord_input = st.text_input("coord", value="", key="coord_box", label_visibility="collapsed")

if coord_input and coord_input != st.session_state.last_coord:
    st.session_state.last_coord = coord_input
    lat, lng = map(float, coord_input.split(","))
    
    # 1. 주소 정보 가져오기
    addr_doc = get_jibun_address(lat, lng)
    bjd_doc = get_region_code(lat, lng)
    st.session_state.addr_info = addr_doc

    # 2. 건축물대장 정보 가져오기
    if bjd_doc:
        b_code = bjd_doc.get("code", "")
        jibun = addr_doc.get("address", {}) if addr_doc else {}
        if len(b_code) >= 10:
            sc = b_code[:5]; bc = b_code[5:10]
            st.session_state.building_title = get_building_title(sc, bc, jibun.get("main_address_no", "0"), jibun.get("sub_address_no", "0"))

# 지도 HTML 구성 (브이월드 호출을 JS에서 처리)
MAP_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; }}
  #map {{ width:100%; height:520px; border-radius:12px; }}
  #status {{
    position:absolute; top:10px; left:50%; transform:translateX(-50%);
    background:white; padding:8px 15px; border-radius:20px; z-index:10;
    font-size:12px; box-shadow:0 2px 10px rgba(0,0,0,0.1);
  }}
</style>
</head>
<body>
<div id="status">🖱️ 지도를 클릭해 보세요</div>
<div id="map"></div>
<script>
var VWORLD_KEY = "{VWORLD_KEY}";
var MY_DOMAIN = "{MY_DOMAIN}";

(function() {{
  var script = document.createElement('script');
  script.src = 'https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false';
  script.onload = function() {{
    kakao.maps.load(function() {{
      var map = new kakao.maps.Map(document.getElementById('map'), {{
        center: new kakao.maps.LatLng(37.5665, 126.9780), level: 3
      }});
      map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);

      var polygon = null, marker = null;

      // 브이월드 API를 브라우저에서 직접 호출 (CORS/RemoteDisconnected 방지)
      function getParcel(lat, lng) {{
        var url = `https://api.vworld.kr/req/data?service=data&request=GetFeature&data=LP_PA_CBND_BUBUN&key=${{VWORLD_KEY}}&geomFilter=POINT(${{lng}}%20${{lat}})&geometry=true&crs=EPSG:4326&domain=${{MY_DOMAIN}}`;
        
        fetch(url).then(res => res.json()).then(data => {{
          if (data.response.status === "OK") {{
            var geom = data.response.result.featureCollection.features[0].geometry;
            drawPolygon(geom);
          }} else {{
             document.getElementById('status').innerHTML = '⚠️ 필지 경계 없음';
          }}
        }}).catch(e => console.error(e));
      }}

      function drawPolygon(geom) {{
        if (polygon) polygon.setMap(null);
        var rings = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0];
        var path = rings.map(c => new kakao.maps.LatLng(c[1], c[0]));
        polygon = new kakao.maps.Polygon({{
          map: map, path: path,
          strokeWeight: 3, strokeColor: '#FF0000', strokeOpacity: 0.8,
          fillColor: '#FF0000', fillOpacity: 0.2
        }});
        var bounds = new kakao.maps.LatLngBounds();
        path.forEach(p => bounds.extend(p));
        map.setBounds(bounds, 100);
        document.getElementById('status').innerHTML = '🔴 필지 하이라이트 완료';
      }}

      kakao.maps.event.addListener(map, 'click', function(e) {{
        var lat = e.latLng.getLat(), lng = e.latLng.getLng();
        if (marker) marker.setMap(null);
        marker = new kakao.maps.Marker({{ position: e.latLng, map: map }});
        
        document.getElementById('status').innerHTML = '⏳ 조회 중...';
        getParcel(lat, lng); // 브라우저에서 직접 하이라이트 실행

        // 파이썬 서버로 데이터 전달
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
    st.components.v1.html(MAP_HTML, height=540)

with col_info:
    if st.session_state.addr_info is None:
        st.markdown('<div style="text-align:center; padding:50px; color:#6b7c8d;">🗺️ 지도를 클릭하여 건물 정보를 확인하세요.</div>', unsafe_allow_html=True)
    else:
        addr = st.session_state.addr_info
        st.markdown(f"""
        <div class="info-card">
            <h3>📍 선택된 위치</h3>
            <div class="data-row"><span class="data-label">지번주소</span><span class="data-value">{addr.get("address",{}).get("address_name","정보 없음")}</span></div>
        </div>
        """, unsafe_allow_html=True)

        titles = st.session_state.building_title
        if titles:
            for item in titles[:3]:
                name = item.get("bldNm") or "이름 없는 건물"
                use = item.get("mainPurpsCdNm") or "-"
                area = f"{float(item.get('totArea',0)):,.2f}㎡"
                st.markdown(f"""
                <div class="info-card">
                    <h3 style="color:#1565c0;">🏗️ {name}</h3>
                    <div class="data-row"><span class="data-label">주용도</span><span class="badge badge-green">{use}</span></div>
                    <div class="data-row"><span class="data-label">연면적</span><span class="data-value">{area}</span></div>
                    <div class="data-row"><span class="data-label">층수</span><span class="data-value">지상 {item.get('grndFlrCnt')}층 / 지하 {item.get('ugrndFlrCnt')}층</span></div>
                    <div class="data-row"><span class="data-label">사용승인일</span><span class="data-value">{item.get('useAprDay') or '-'}</span></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("해당 지번에 등록된 건축물대장이 없습니다.")
