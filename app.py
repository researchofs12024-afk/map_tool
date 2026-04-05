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

# [수정됨] 하이라이트를 위해 Vworld 호출 로직을 안정적인 방식으로 변경
def get_parcel_polygon(lat, lng):
    url = "https://api.vworld.kr/req/data"

    params = {
        "service": "data",
        "request": "GetFeature",
        "data": "lp_pa_cbnd_bubun",
        "key": VWORLD_KEY.strip(),
        "geomFilter": f"POINT({lng} {lat})",
        "geometry": "true",
        "attribute": "true",
        "crs": "EPSG:4326",
        "domain": "s1map-tool.streamlit.app"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://s1map-tool.streamlit.app"
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)

        if resp.status_code != 200:
            return None, f"서버 응답 에러: {resp.status_code}"

        data = resp.json()

        if data.get("response", {}).get("status") == "OK":
            features = data["response"]["result"]["featureCollection"]["features"]
            if features:
                return features[0].get("geometry"), "OK"
            else:
                return None, "필지 없음"

        return None, f"API 오류: {data}"

    except Exception as e:
        return None, f"연결 오류: {str(e)}"    
    # 3. 중요: 브이월드 방화벽을 통과하기 위한 헤더 (User-Agent와 Referer 필수)
    # [핵심] 차단(RemoteDisconnected)을 막기 위한 헤더
headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "User-Agent": "Mozilla/5.0",
"Referer": "https://s1map-tool.streamlit.app"
}
    
try:
        # 세션을 사용하여 연결 안정성 확보
        with requests.Session() as session:
            resp = session.get(url, params=params, headers=headers, timeout=7)
            
            if resp.status_code != 200:
                return None, f"서버 응답 에러: {resp.status_code}"
                
            data = resp.json()
            
            if data.get("response", {}).get("status") == "OK":
                result = data["response"]["result"]["featureCollection"]["features"]
                if result:
                    return result[0].get("geometry"), "OK"
                else:
                    return None, "해당 좌표에 필지 정보가 없음"
            else:
                err_text = data.get("response", {}).get("error", {}).get("text", "데이터 없음")
                return None, f"API 상태 오류: {err_text}"
                
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        if data.get("response", {}).get("status") == "OK":
            feature = data["response"]["result"]["featureCollection"]["features"][0]
            return feature.get("geometry"), "OK"
        return None, f"데이터 없음: {data.get('response',{}).get('status')}"
    except Exception as e:
        return None, f"연결오류: {str(e)[:50]}"


def _point_in_geom(px, py, geom):
    try:
        rings = [geom["coordinates"][0]] if geom["type"] == "Polygon" \
                else [g[0] for g in geom["coordinates"]]
        for ring in rings:
            inside = False
            n = len(ring); j = n - 1
            for i in range(n):
                xi, yi = ring[i][0], ring[i][1]
                xj, yj = ring[j][0], ring[j][1]
                if ((yi > py) != (yj > py)) and (px < (xj-xi)*(py-yi)/(yj-yi+1e-15)+xi):
                    inside = not inside
                j = i
            if inside:
                return True
    except Exception:
        pass
    return False


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
.data-row:last-child { border-bottom:none; }
.data-label { color:#6b7c8d; font-weight:500; min-width:130px; }
.data-value { color:#1a2e3b; font-weight:600; text-align:right; font-size:.85rem; }
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:.78rem; font-weight:600; }
.badge-green  { background:#e8f5e9; color:#2e7d32; }
.badge-blue   { background:#e3f2fd; color:#1565c0; }
.badge-orange { background:#fff3e0; color:#e65100; }
.badge-purple { background:#ede7f6; color:#4527a0; }
.hint-box {
    background:linear-gradient(135deg,#e3f2fd,#f3e5f5); border-radius:12px;
    padding:30px 22px; text-align:center; color:#37474f; font-size:.9rem; line-height:1.9;
}
.hint-box .icon { font-size:2.4rem; margin-bottom:10px; }
.error-box { background:#fff3cd; border:1px solid #ffc107; border-radius:10px;
             padding:14px 18px; color:#856404; font-size:.88rem; }
.debug-box { background:#f0fff4; border:1px solid #9ae6b4; border-radius:8px;
             padding:10px 14px; color:#276749; font-size:.75rem;
             font-family:monospace; word-break:break-all; margin-bottom:10px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div style="font-size:2.4rem">🏢</div>
    <div>
        <h1>건축물대장 조회 서비스</h1>
        <p>클릭한 필지가 붉게 하이라이트되고 건축물대장 정보를 즉시 조회합니다</p>
    </div>
</div>
""", unsafe_allow_html=True)

col_map, col_info = st.columns([6, 4], gap="medium")

for k, v in [("addr_info",None),("building_title",None),("building_basic",None),
             ("last_coord",""),("parcel_geom",None),("parcel_status","")]:
    if k not in st.session_state:
        st.session_state[k] = v

coord_input = st.text_input("coord", value="", key="coord_box", label_visibility="collapsed")

if coord_input and coord_input != st.session_state.last_coord:
    st.session_state.last_coord = coord_input
    try:
        lat, lng          = map(float, coord_input.split(","))
        addr_doc          = get_jibun_address(lat, lng)
        bjd_doc           = get_region_code(lat, lng)
        geom, p_status    = get_parcel_polygon(lat, lng)

        st.session_state.addr_info     = addr_doc
        st.session_state.parcel_geom   = geom
        st.session_state.parcel_status = p_status

        if bjd_doc:
            b_code  = bjd_doc.get("code", "")
            jibun   = addr_doc.get("address", {}) if addr_doc else {}
            main_no = jibun.get("main_address_no", "0") or "0"
            sub_no  = jibun.get("sub_address_no",  "0") or "0"
            if len(b_code) >= 10:
                sc = b_code[:5]; bc = b_code[5:10]
                st.session_state.building_title = get_building_title(sc, bc, main_no, sub_no)
                st.session_state.building_basic = get_building_info(sc, bc, main_no, sub_no)
except Exception as e:
        # 에러 메시지를 좀 더 명확하게 표시
        return None, f"연결 실패: 브이월드 서버 IP 차단 가능성 ({str(e)[:30]})"
        st.session_state.addr_info     = {"error": str(e)}
        st.session_state.parcel_status = f"예외: {e}"

parcel_json = json.dumps(st.session_state.parcel_geom) if st.session_state.parcel_geom else "null"

MAP_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#f8fafc; }}
  #map {{ width:100%; height:500px; border-radius:12px; overflow:hidden;
          box-shadow:0 4px 20px rgba(0,0,0,.12); }}
  #status {{
    position:absolute; top:10px; left:50%; transform:translateX(-50%);
    background:rgba(255,255,255,.95); border-radius:24px; padding:8px 20px;
    font-size:13px; color:#37474f; box-shadow:0 2px 12px rgba(0,0,0,.15);
    z-index:10; backdrop-filter:blur(4px); white-space:nowrap;
  }}
  .wrapper {{ position:relative; }}
</style>
</head>
<body>
<div class="wrapper">
  <div id="status">🖱️ 지도를 클릭하면 필지를 조회합니다</div>
  <div id="map"></div>
</div>
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
      map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
      map.addControl(new kakao.maps.MapTypeControl(), kakao.maps.ControlPosition.TOPRIGHT);

      var polygon = null, marker = null;

      function drawPolygon(geom) {{
        if (polygon) polygon.setMap(null);
        if (!geom) return;
        var rings = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0];
        var path  = rings.map(function(c) {{ return new kakao.maps.LatLng(c[1], c[0]); }});
        var bounds = new kakao.maps.LatLngBounds();
        path.forEach(function(p) {{ bounds.extend(p); }});
        polygon = new kakao.maps.Polygon({{
          map: map, path: path,
          strokeWeight: 3, strokeColor: '#E53E3E', strokeOpacity: 1,
          fillColor: '#FC8181', fillOpacity: 0.35,
        }});
        map.setBounds(bounds, 80);
        document.getElementById('status').innerHTML = '🔴 필지 하이라이트 완료';
      }}

      if (PARCEL_GEOM) drawPolygon(PARCEL_GEOM);

      kakao.maps.event.addListener(map, 'click', function(e) {{
        var lat = e.latLng.getLat(), lng = e.latLng.getLng();
        if (marker) marker.setMap(null);
        marker = new kakao.maps.Marker({{ position: e.latLng, map: map }});
        document.getElementById('status').innerHTML = '⏳ 조회 중...';
        var inputs = window.parent.document.querySelectorAll('input[type="text"]');
        if (inputs.length > 0) {{
          var inp = inputs[0], coord = lat.toFixed(7) + ',' + lng.toFixed(7);
          var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
          setter.call(inp, coord);
          ['input','keydown','keypress','keyup'].forEach(function(t) {{
            inp.dispatchEvent(t.startsWith('key')
              ? new inp.ownerDocument.defaultView.KeyboardEvent(t, {{key:'Enter',keyCode:13,bubbles:true}})
              : new inp.ownerDocument.defaultView.Event(t, {{bubbles:true}}));
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

with col_map:
    st.components.v1.html(MAP_HTML, height=520, scrolling=False)

with col_info:
    if st.session_state.addr_info is None:
        st.markdown("""
        <div class="hint-box">
            <div class="icon">🗺️</div>
            <strong>지도를 클릭해 필지를 선택하세요</strong><br>
            클릭한 필지가 <span style="color:#E53E3E;font-weight:700">붉은색</span>으로 하이라이트되고<br>
            건축물대장 정보가 표시됩니다
        </div>""", unsafe_allow_html=True)
    else:
        addr_doc = st.session_state.addr_info
        road  = addr_doc.get("road_address") if addr_doc else None
        jibun = addr_doc.get("address", {})  if addr_doc else {}

        st.markdown(f"""
        <div class="info-card">
            <h3>📍 위치 정보</h3>
            <div class="data-row">
                <span class="data-label">도로명 주소</span>
                <span class="data-value">{road.get("address_name","없음") if road else "없음"}</span>
            </div>
            <div class="data-row">
                <span class="data-label">지번 주소</span>
                <span class="data-value">{jibun.get("address_name","없음")}</span>
            </div>
            <div class="data-row">
                <span class="data-label">필지 경계</span>
                <span class="data-value">{"🔴 하이라이트됨" if st.session_state.parcel_geom else "⚠️ 경계 없음"}</span>
            </div>
        </div>""", unsafe_allow_html=True)

        if st.session_state.parcel_status and not st.session_state.parcel_geom:
            st.markdown(f'<div class="debug-box">필지 디버그: {st.session_state.parcel_status}</div>',
                        unsafe_allow_html=True)

        def fmt_area(v):
            try: return f"{float(v):,.2f} ㎡" if float(v) > 0 else "-"
            except: return "-"
        def fmt_date(v):
            s = str(v).strip()
            return f"{s[:4]}-{s[4:6]}-{s[6:]}" if len(s)==8 and s.isdigit() else (s or "-")
        def val(v):
            s = str(v).strip() if v else ""
            return s if s not in ["","0","None"] else "-"

        title_data = st.session_state.building_title
        if title_data and isinstance(title_data, list):
            for i, item in enumerate(title_data[:3]):
                name     = (item.get("bldNm") or "").strip() or \
                           (item.get("splotNm") or "").strip() or \
                           (item.get("newPlatPlc") or item.get("platPlc") or f"건물 {i+1}")
                use_nm   = val(item.get("mainPurpsCdNm"))
                struct   = val(item.get("strctCdNm"))
                roof     = val(item.get("roofCdNm"))
                floor_u  = val(item.get("grndFlrCnt"))
                floor_d  = val(item.get("ugrndFlrCnt"))
                area     = fmt_area(item.get("totArea"))
                plat_area= fmt_area(item.get("platArea"))
                bc_area  = fmt_area(item.get("archArea"))
                height   = val(item.get("heit"))
                approve  = fmt_date(item.get("useAprDay"))
                fam_cnt  = val(item.get("hhldCnt"))
                ho_cnt   = val(item.get("hoCnt"))
                prkg     = val(item.get("indrAutoUtcnt"))
                regstr   = val(item.get("regstrGbCdNm"))
                kind     = val(item.get("regstrKindCdNm"))

                badge_cls  = "badge-green" if "주거" in use_nm else \
                             "badge-orange" if any(k in use_nm for k in ["상업","근린","업무","판매"]) else "badge-blue"
                kind_badge = f'<span class="badge badge-purple" style="font-size:.72rem">{regstr} · {kind}</span>' if regstr != "-" else ""

                rows = [f"<div class='data-row'><span class='data-label'>주용도</span><span class='data-value'><span class='badge {badge_cls}'>{use_nm}</span></span></div>"]
                for label, v in [("구조",struct),("지붕",roof)]:
                    if v != "-": rows.append(f"<div class='data-row'><span class='data-label'>{label}</span><span class='data-value'>{v}</span></div>")
                rows.append(f"<div class='data-row'><span class='data-label'>층수</span><span class='data-value'>지상 {floor_u}층 / 지하 {floor_d}층</span></div>")
                for label, v in [("연면적",area),("건축면적",bc_area),("대지면적",plat_area)]:
                    if v != "-": rows.append(f"<div class='data-row'><span class='data-label'>{label}</span><span class='data-value'>{v}</span></div>")
                if height  != "-": rows.append(f"<div class='data-row'><span class='data-label'>높이</span><span class='data-value'>{height} m</span></div>")
                if approve != "-": rows.append(f"<div class='data-row'><span class='data-label'>사용승인일</span><span class='data-value'>{approve}</span></div>")
                if fam_cnt != "-": rows.append(f"<div class='data-row'><span class='data-label'>세대수</span><span class='data-value'>{fam_cnt}세대</span></div>")
                if ho_cnt  != "-": rows.append(f"<div class='data-row'><span class='data-label'>호수</span><span class='data-value'>{ho_cnt}호</span></div>")
                if prkg    != "-": rows.append(f"<div class='data-row'><span class='data-label'>옥내주차</span><span class='data-value'>{prkg}대</span></div>")

                st.markdown(f"""
                <div class="info-card">
                    <h3>🏗️ {name} {kind_badge}</h3>
                    {"".join(rows)}
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-box">ℹ️ 건축물대장 정보가 없습니다.</div>', unsafe_allow_html=True)

        if st.button("🔄 초기화", use_container_width=True):
            for k in ["addr_info","building_title","building_basic","parcel_geom","parcel_status"]:
                st.session_state[k] = None
            st.session_state.last_coord = ""
            st.rerun()
