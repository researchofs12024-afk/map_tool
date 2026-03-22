import streamlit as st
import requests
import json
from urllib.parse import quote

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="건축물대장 조회 서비스",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── API 키 (secrets 또는 하드코딩 폴백) ──────────────────────────────────────
try:
    KAKAO_JS_KEY     = st.secrets["KAKAO_JS_KEY"]
    KAKAO_REST_KEY   = st.secrets["KAKAO_REST_KEY"]
    BUILDING_API_KEY = st.secrets["BUILDING_API_KEY"]
except Exception:
    KAKAO_JS_KEY     = "057a4a253017791fe6072d7b089a063a"
    KAKAO_REST_KEY   = "c5af33c0d1d6a654362d3fea152cc076"
    BUILDING_API_KEY = "9619e124e16b9e57bad6cfefdc82f6c87749176260b4caff32eda964aad5de1b"

# ── 건축물대장 API 호출 ───────────────────────────────────────────────────────
def get_building_info(sigungu_cd: str, bjdong_cd: str, bun: str, ji: str):
    """
    건축물대장 기본개요 조회 (국토교통부 공공데이터 API)
    """
    url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrBasisOulnInfo"
    params = {
        "serviceKey": BUILDING_API_KEY,
        "sigunguCd":  sigungu_cd,
        "bjdongCd":   bjdong_cd,
        "bun":        bun.zfill(4),
        "ji":         ji.zfill(4),
        "numOfRows":  "10",
        "pageNo":     "1",
        "_type":      "json",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = (
            data.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
        )
        if isinstance(items, dict):
            items = [items]
        return items
    except Exception as e:
        return {"error": str(e)}


def get_address_from_coords(lat: float, lng: float):
    """카카오 좌표 → 주소 변환"""
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    params  = {"x": lng, "y": lat}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        docs = resp.json().get("documents", [])
        if docs:
            return docs[0]
        return None
    except Exception as e:
        return {"error": str(e)}


# ── 지번 파싱 헬퍼 ────────────────────────────────────────────────────────────
def parse_land_number(land_num: str):
    """'123-45' → bun='123', ji='45'"""
    if not land_num:
        return "0", "0"
    parts = land_num.replace(" ", "").split("-")
    bun = parts[0] if len(parts) > 0 else "0"
    ji  = parts[1] if len(parts) > 1 else "0"
    return bun, ji


# ── CSS / UI ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

/* 헤더 */
.app-header {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 18px;
    box-shadow: 0 8px 32px rgba(0,0,0,.25);
}
.app-header h1 { color:#fff; margin:0; font-size:1.7rem; font-weight:700; }
.app-header p  { color:#8ecae6; margin:0; font-size:.9rem; }

/* 카드 */
.info-card {
    background: #ffffff;
    border: 1px solid #e8edf2;
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,.06);
}
.info-card h3 {
    color: #1a2e3b;
    font-size: 1rem;
    font-weight: 700;
    margin: 0 0 14px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid #e3f2fd;
}

/* 데이터 행 */
.data-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px dashed #f0f4f8;
    font-size: .88rem;
}
.data-row:last-child { border-bottom: none; }
.data-label { color: #6b7c8d; font-weight: 500; min-width: 130px; }
.data-value { color: #1a2e3b; font-weight: 600; text-align: right; }

/* 배지 */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: .78rem;
    font-weight: 600;
}
.badge-green  { background:#e8f5e9; color:#2e7d32; }
.badge-blue   { background:#e3f2fd; color:#1565c0; }
.badge-orange { background:#fff3e0; color:#e65100; }
.badge-gray   { background:#f5f5f5; color:#616161; }

/* 안내 박스 */
.hint-box {
    background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
    border-radius: 12px;
    padding: 18px 22px;
    text-align: center;
    color: #37474f;
    font-size: .9rem;
    line-height: 1.7;
}
.hint-box .icon { font-size: 2rem; margin-bottom: 8px; }

/* 에러 */
.error-box {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 10px;
    padding: 14px 18px;
    color: #856404;
    font-size: .88rem;
}
</style>
""", unsafe_allow_html=True)

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div style="font-size:2.4rem">🏢</div>
    <div>
        <h1>건축물대장 조회 서비스</h1>
        <p>카카오맵에서 건물을 클릭하면 건축물대장 정보를 즉시 조회합니다</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 레이아웃 ──────────────────────────────────────────────────────────────────
col_map, col_info = st.columns([6, 4], gap="medium")

# ── 세션 상태 초기화 ──────────────────────────────────────────────────────────
if "clicked_lat"  not in st.session_state: st.session_state.clicked_lat  = None
if "clicked_lng"  not in st.session_state: st.session_state.clicked_lng  = None
if "addr_info"    not in st.session_state: st.session_state.addr_info    = None
if "building_data" not in st.session_state: st.session_state.building_data = None

# ── 카카오맵 HTML 컴포넌트 ────────────────────────────────────────────────────
MAP_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Noto Sans KR', sans-serif; background:#f8fafc; }}
  #map {{ width:100%; height:520px; border-radius:12px; overflow:hidden;
          box-shadow:0 4px 20px rgba(0,0,0,.12); }}
  #status {{
      position: absolute; top:10px; left:50%; transform:translateX(-50%);
      background:rgba(255,255,255,.95); border-radius:24px;
      padding:8px 20px; font-size:13px; color:#37474f;
      box-shadow:0 2px 12px rgba(0,0,0,.15); z-index:10;
      backdrop-filter:blur(4px);
  }}
  #crosshair {{
      position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
      width:20px; height:20px; pointer-events:none; z-index:5;
  }}
  #crosshair::before, #crosshair::after {{
      content:''; position:absolute; background:#e53935; border-radius:2px;
  }}
  #crosshair::before {{ width:2px; height:20px; left:9px; top:0; }}
  #crosshair::after  {{ width:20px; height:2px; left:0; top:9px; }}
  .wrapper {{ position:relative; }}
</style>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services&autoload=false"></script>
<script>
kakao.maps.load(function() {{
    var container = document.getElementById('map');
    var options   = {{ center: new kakao.maps.LatLng(37.5665, 126.9780), level: 4 }};
    var map       = new kakao.maps.Map(container, options);
    var geocoder  = new kakao.maps.services.Geocoder();
    var marker    = null;

    map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
    map.addControl(new kakao.maps.MapTypeControl(), kakao.maps.ControlPosition.TOPRIGHT);

    kakao.maps.event.addListener(map, 'click', function(mouseEvent) {{
        var lat = mouseEvent.latLng.getLat();
        var lng = mouseEvent.latLng.getLng();

        if (marker) marker.setMap(null);
        marker = new kakao.maps.Marker({{ position: mouseEvent.latLng, map: map }});

        document.getElementById('status').innerHTML = '⏳ 주소를 조회 중입니다...';

        window.parent.postMessage(
            {{ type: 'MAP_CLICK', lat: lat, lng: lng }},
            '*'
        );

        geocoder.coord2Address(lng, lat, function(result, status) {{
            if (status === kakao.maps.services.Status.OK) {{
                var addr = result[0].road_address
                    ? result[0].road_address.address_name
                    : result[0].address.address_name;
                document.getElementById('status').innerHTML = '📍 ' + addr;
            }} else {{
                document.getElementById('status').innerHTML = '⚠️ 주소를 찾을 수 없습니다';
            }}
        }});
    }});
}});
</script>
</head>
<body>
<div class="wrapper">
  <div id="status">🖱️ 지도를 클릭하면 건물 정보를 조회합니다</div>
  <div id="map"></div>
</div>
<script>
var container = document.getElementById('map');
var options   = {{ center: new kakao.maps.LatLng(37.5665, 126.9780), level: 4 }};
var map       = new kakao.maps.Map(container, options);
var geocoder  = new kakao.maps.services.Geocoder();
var marker    = null;

map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
map.addControl(new kakao.maps.MapTypeControl(), kakao.maps.ControlPosition.TOPRIGHT);

kakao.maps.event.addListener(map, 'click', function(mouseEvent) {{
    var lat = mouseEvent.latLng.getLat();
    var lng = mouseEvent.latLng.getLng();

    // 마커 표시
    if (marker) marker.setMap(null);
    marker = new kakao.maps.Marker({{ position: mouseEvent.latLng, map: map }});

    document.getElementById('status').innerHTML = '⏳ 주소를 조회 중입니다...';

    // 부모(Streamlit)에 좌표 전달
    window.parent.postMessage(
        {{ type: 'MAP_CLICK', lat: lat, lng: lng }},
        '*'
    );

    // 역지오코딩 (지도 위 표시용)
    geocoder.coord2Address(lng, lat, function(result, status) {{
        if (status === kakao.maps.services.Status.OK) {{
            var addr = result[0].road_address
                ? result[0].road_address.address_name
                : result[0].address.address_name;
            document.getElementById('status').innerHTML = '📍 ' + addr;
        }} else {{
            document.getElementById('status').innerHTML = '⚠️ 주소를 찾을 수 없습니다';
        }}
    }});
}});
</script>
</body>
</html>
"""

# ── 지도 렌더 ─────────────────────────────────────────────────────────────────
with col_map:
    # postMessage 수신 → URL 파라미터로 전달하는 브릿지
    BRIDGE_HTML = f"""
    <script>
    window.addEventListener('message', function(e) {{
        if (e.data && e.data.type === 'MAP_CLICK') {{
            var lat = e.data.lat;
            var lng = e.data.lng;
            // Streamlit query params로 전달
            var url = new URL(window.location.href);
            url.searchParams.set('lat', lat);
            url.searchParams.set('lng', lng);
            window.location.href = url.toString();
        }}
    }});
    </script>
    """

    st.components.v1.html(MAP_HTML, height=540, scrolling=False)

    # Query params로 클릭 좌표 수신
    query_params = st.query_params
    if "lat" in query_params and "lng" in query_params:
        try:
            new_lat = float(query_params["lat"])
            new_lng = float(query_params["lng"])
            if (new_lat != st.session_state.clicked_lat or
                    new_lng != st.session_state.clicked_lng):
                st.session_state.clicked_lat = new_lat
                st.session_state.clicked_lng = new_lng
                # 주소 조회
                addr_doc = get_address_from_coords(new_lat, new_lng)
                st.session_state.addr_info = addr_doc
                # 건축물대장 조회
                if addr_doc and "error" not in addr_doc:
                    road = addr_doc.get("road_address")
                    jibun = addr_doc.get("address")
                    if jibun:
                        region_1 = jibun.get("region_1depth_name", "")
                        region_2 = jibun.get("region_2depth_name", "")
                        h_code   = jibun.get("h_code", "")       # 행정동 코드
                        b_code   = jibun.get("b_code", "")       # 법정동 코드 (10자리)
                        main_no  = jibun.get("main_address_no", "0")
                        sub_no   = jibun.get("sub_address_no", "0")

                        sigungu_cd = b_code[:5]  if len(b_code) >= 5  else ""
                        bjdong_cd  = b_code[5:10] if len(b_code) >= 10 else ""

                        if sigungu_cd and bjdong_cd:
                            result = get_building_info(
                                sigungu_cd, bjdong_cd,
                                main_no or "0", sub_no or "0"
                            )
                            st.session_state.building_data = result
                        else:
                            st.session_state.building_data = None
        except Exception:
            pass

# ── 정보 패널 ─────────────────────────────────────────────────────────────────
with col_info:
    if st.session_state.addr_info is None:
        st.markdown("""
        <div class="hint-box">
            <div class="icon">🗺️</div>
            <strong>지도를 클릭해 건물 정보를 조회하세요</strong><br>
            건물 위치를 클릭하면<br>건축물대장 정보가 이 곳에 표시됩니다
        </div>
        """, unsafe_allow_html=True)
    else:
        addr_doc = st.session_state.addr_info

        # ── 주소 정보 카드 ──
        if "error" in addr_doc:
            st.markdown(f'<div class="error-box">⚠️ 주소 조회 오류: {addr_doc["error"]}</div>',
                        unsafe_allow_html=True)
        else:
            road   = addr_doc.get("road_address")
            jibun  = addr_doc.get("address", {})
            road_name  = road.get("address_name", "없음") if road else "없음"
            jibun_name = jibun.get("address_name", "없음")

            st.markdown(f"""
            <div class="info-card">
                <h3>📍 위치 정보</h3>
                <div class="data-row">
                    <span class="data-label">도로명 주소</span>
                    <span class="data-value">{road_name}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">지번 주소</span>
                    <span class="data-value">{jibun_name}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">위도/경도</span>
                    <span class="data-value" style="font-family:monospace;font-size:.82rem">
                        {st.session_state.clicked_lat:.6f}, {st.session_state.clicked_lng:.6f}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── 건축물대장 카드 ──
        bdata = st.session_state.building_data
        if bdata is None:
            st.markdown('<div class="error-box">⚠️ 법정동 코드를 확인할 수 없어 건축물대장 조회를 건너뜁니다.</div>',
                        unsafe_allow_html=True)
        elif isinstance(bdata, dict) and "error" in bdata:
            st.markdown(f'<div class="error-box">⚠️ 건축물대장 API 오류: {bdata["error"]}</div>',
                        unsafe_allow_html=True)
        elif not bdata:
            st.markdown('<div class="error-box">ℹ️ 해당 위치에 등록된 건축물대장 정보가 없습니다.</div>',
                        unsafe_allow_html=True)
        else:
            for i, item in enumerate(bdata[:3]):  # 최대 3개 표시
                name     = item.get("bldNm") or item.get("platPlcNm") or f"건물 {i+1}"
                use_nm   = item.get("mainPurpsCdNm", "-")
                struct   = item.get("strctCdNm", "-")
                roof     = item.get("roofCdNm", "-")
                floor_u  = item.get("grndFlrCnt", "-")
                floor_d  = item.get("ugrndFlrCnt", "0")
                area     = item.get("totArea", "-")
                plat_area = item.get("platArea", "-")
                height   = item.get("heit", "-")
                approve  = item.get("useAprDay", "-")
                fam_cnt  = item.get("hhldCnt", "-")
                dong_nm  = item.get("dongNm", "-")

                # 면적 포맷
                def fmt_area(v):
                    try: return f"{float(v):,.2f} ㎡"
                    except: return str(v)

                badge_use = "badge-blue"
                if "주거" in use_nm: badge_use = "badge-green"
                elif "상업" in use_nm or "근린" in use_nm: badge_use = "badge-orange"

                st.markdown(f"""
                <div class="info-card">
                    <h3>🏗️ {name}</h3>
                    <div class="data-row">
                        <span class="data-label">주용도</span>
                        <span class="data-value">
                            <span class="badge {badge_use}">{use_nm}</span>
                        </span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">구조</span>
                        <span class="data-value">{struct}</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">층수</span>
                        <span class="data-value">지상 {floor_u}층 / 지하 {floor_d}층</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">연면적</span>
                        <span class="data-value">{fmt_area(area)}</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">대지면적</span>
                        <span class="data-value">{fmt_area(plat_area)}</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">높이</span>
                        <span class="data-value">{height} m</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">사용승인일</span>
                        <span class="data-value">{approve[:4]+'-'+approve[4:6]+'-'+approve[6:] if len(str(approve))==8 else approve}</span>
                    </div>
                    {"<div class='data-row'><span class='data-label'>세대수</span><span class='data-value'>"+str(fam_cnt)+"세대</span></div>" if fam_cnt and fam_cnt != "-" else ""}
                </div>
                """, unsafe_allow_html=True)

        # ── 초기화 버튼 ──
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.clicked_lat   = None
            st.session_state.clicked_lng   = None
            st.session_state.addr_info     = None
            st.session_state.building_data = None
            st.query_params.clear()
            st.rerun()
