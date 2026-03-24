import streamlit as st
import requests
import json

st.set_page_config(
    page_title="건축물대장 조회 서비스",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

# 파이썬 서버 호출은 무시하도록 변경 (RemoteDisconnected 방지)
def get_parcel_polygon(lat, lng):
    return None, "JS_HANDLED"


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


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.app-header {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    border-radius: 16px; padding: 28px 36px; margin-bottom: 20px;
    display: flex; align-items: center; gap: 18px;
    box-shadow: 0 8px 32px rgba(0,0,0,.25);
}
.app-header h1 { color:#fff; margin:0; font-size:1.7rem; font-weight:700; }
.app-header p  { color:#8ecae6; margin:0; font-size:.9rem; }
.info-card {
    background:#fff; border:1px solid #e8edf2; border-radius:14px;
    padding:22px 26px; margin-bottom:16px; box-shadow:0 2px 12px rgba(0,0,0,.06);
}
.info-card h3 {
    color:#1a2e3b; font-size:1rem; font-weight:700;
    margin:0 0 14px 0; padding-bottom:10px; border-bottom:2px solid #e3f2fd;
}
.data-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:7px 0; border-bottom:1px dashed #f0f4f8; font-size:.88rem;
}
.badge-green  { background:#e8f5e9; color:#2e7d32; padding:3px 10px; border-radius:20px; font-size:.78rem; font-weight:600;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-header"><div style="font-size:2.4rem">🏢</div><div><h1>건축물대장 조회 서비스</h1><p>클릭한 필지가 붉게 하이라이트되고 건축물대장 정보를 즉시 조회합니다</p></div></div>', unsafe_allow_html=True)

col_map, col_info = st.columns([6, 4], gap="medium")

for k, v in [("addr_info",None),("building_title",None),("last_coord","")]:
    if k not in st.session_state:
        st.session_state[k] = v

coord_input = st.text_input("coord", value="", key="coord_box", label_visibility="collapsed")

if coord_input and coord_input != st.session_state.last_coord:
    st.session_state.last_coord = coord_input
    try:
        lat, lng          = map(float, coord_input.split(","))
        addr_doc          = get_jibun_address(lat, lng)
        bjd_doc           = get_region_code(lat, lng)
        st.session_state.addr_info = addr_doc

        if bjd_doc:
            b_code  = bjd_doc.get("code", "")
            jibun   = addr_doc.get("address", {}) if addr_doc else {}
            main_no = jibun.get("main_address_no", "0") or "0"
            sub_no  = jibun.get("sub_address_no",  "0") or "0"
            if len(b_code) >= 10:
                sc = b_code[:5]; bc = b_code[5:10]
                st.session_state.building_title = get_building_title(sc, bc, main_no, sub_no)
    except Exception as e:
        st.session_state.addr_info = {"error": str(e)}

# f-string 충돌 방지를 위해 .replace 방식으로 데이터 주입 (지도 안나오는 문제 원천 차단)
MAP_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  #map { width:100%; height:500px; border-radius:12px; overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,.12); }
  #status { position:absolute; top:10px; left:50%; transform:translateX(-50%); background:rgba(255,255,255,.95); border-radius:24px; padding:8px 20px; font-size:13px; z-index:10; box-shadow:0 2px 12px rgba(0,0,0,0.15); }
</style>
</head>
<body>
<div id="status">🖱️ 지도를 클릭하면 필지를 조회합니다</div>
<div id="map"></div>
<script>
(function() {
  var script = document.createElement('script');
  script.src = 'https://dapi.kakao.com/v2/maps/sdk.js?appkey=__KAKAO_KEY__&autoload=false';
  script.onload = function() {
    kakao.maps.load(function() {
      var map = new kakao.maps.Map(document.getElementById('map'), {
        center: new kakao.maps.LatLng(37.5665, 126.9780), level: 3
      });
      map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
      
      var polygon = null, marker = null;

      // 필지 경계 그리기 함수
      function drawPolygon(geom) {
        if (polygon) polygon.setMap(null);
        var rings = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0];
        var path = rings.map(function(c) { return new kakao.maps.LatLng(c[1], c[0]); });
        
        polygon = new kakao.maps.Polygon({
          map: map, path: path,
          strokeWeight: 3, strokeColor: '#E53E3E', strokeOpacity: 1,
          fillColor: '#FC8181', fillOpacity: 0.35,
        });
        
        var bounds = new kakao.maps.LatLngBounds();
        path.forEach(function(p) { bounds.extend(p); });
        map.setBounds(bounds, 80);
        document.getElementById('status').innerHTML = '🔴 필지 하이라이트 완료';
      }

      // 브이월드 데이터 가져오기 (브라우저에서 직접 실행)
      function fetchVworldParcel(lat, lng) {
        var url = "https://api.vworld.kr/req/data?service=data&request=GetFeature&data=lp_pa_cbnd_bubun&key=__VWORLD_KEY__&geomFilter=POINT(" + lng + " " + lat + ")&geometry=true&crs=EPSG:4326&domain=s1map-tool.streamlit.app";
        
        fetch(url)
          .then(res => res.json())
          .then(data => {
            if (data.response && data.response.status === "OK") {
              drawPolygon(data.response.result.featureCollection.features[0].geometry);
            } else {
              document.getElementById('status').innerHTML = '⚠️ 필지 경계 없음';
            }
          })
          .catch(e => console.error(e));
      }

      kakao.maps.event.addListener(map, 'click', function(e) {
        var lat = e.latLng.getLat(), lng = e.latLng.getLng();
        if (marker) marker.setMap(null);
        marker = new kakao.maps.Marker({ position: e.latLng, map: map });
        
        document.getElementById('status').innerHTML = '⏳ 조회 중...';
        
        // 1. 하이라이트 수행 (JS)
        fetchVworldParcel(lat, lng);

        // 2. 파이썬 서버로 좌표 전달
        var inputs = window.parent.document.querySelectorAll('input[type="text"]');
        if (inputs.length > 0) {
          var inp = inputs[0], coord = lat.toFixed(7) + ',' + lng.toFixed(7);
          var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
          setter.call(inp, coord);
          inp.dispatchEvent(new Event('input', { bubbles: true }));
          inp.dispatchEvent(new KeyboardEvent('keydown', { key:'Enter', keyCode:13, bubbles:true }));
        }
      });
    });
  };
  document.head.appendChild(script);
})();
</script>
</body>
</html>
"""

final_html = MAP_HTML_TEMPLATE.replace("__KAKAO_KEY__", KAKAO_JS_KEY)\
                             .replace("__VWORLD_KEY__", VWORLD_KEY.strip())

with col_map:
    st.components.v1.html(final_html, height=520, scrolling=False)

with col_info:
    if st.session_state.addr_info is None:
        st.markdown('<div class="hint-box">지도를 클릭해 필지를 선택하세요</div>', unsafe_allow_html=True)
    else:
        addr = st.session_state.addr_info
        jibun = addr.get("address", {})
        st.markdown(f"""
        <div class="info-card">
            <h3>📍 위치 정보</h3>
            <div class="data-row"><span class="data-label">지번 주소</span><span class="data-value">{jibun.get("address_name","정보 없음")}</span></div>
        </div>""", unsafe_allow_html=True)

        titles = st.session_state.building_title
        if titles:
            for item in titles[:3]:
                st.markdown(f"""
                <div class="info-card">
                    <h3>🏗️ {item.get("bldNm") or "건물"}</h3>
                    <div class="data-row"><span class="data-label">주용도</span><span class="badge-green">{item.get("mainPurpsCdNm")}</span></div>
                    <div class="data-row"><span class="data-label">연면적</span><span class="data-value">{item.get("totArea")} ㎡</span></div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("건축물대장 정보가 없습니다.")
