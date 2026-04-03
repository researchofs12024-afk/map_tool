import streamlit as st
import streamlit.components.v1 as components
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
except Exception:
    KAKAO_JS_KEY     = "057a4a253017791fe6072d7b089a063a"
    KAKAO_REST_KEY   = "c5af33c0d1d6a654362d3fea152cc076"
    BUILDING_API_KEY = "9619e124e16b9e57bad6cfefdc82f6c87749176260b4caff32eda964aad5de1b"

# -------------------------------
# 1️⃣ 로컬 GeoJSON 불러오기
# -------------------------------
with open("서울중구.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)
geojson_str = json.dumps(geojson_data)


# -------------------------------
# 2️⃣ 카카오 REST / 건축물대장 API
# -------------------------------
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


# -------------------------------
# 3️⃣ CSS
# -------------------------------
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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div style="font-size:2.4rem">🏢</div>
    <div>
        <h1>건축물대장 조회 서비스</h1>
        <p>클릭한 필지가 하이라이트되고 건축물대장 정보를 즉시 조회합니다</p>
    </div>
</div>
""", unsafe_allow_html=True)


# -------------------------------
# 4️⃣ Session state 초기화
# -------------------------------
for k, v in [("addr_info", None), ("building_title", None), ("building_basic", None), ("last_coord", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

# 숨겨진 좌표 입력창 (지도 클릭 → Streamlit 통신용)
coord_input = st.text_input("coord", value="", key="coord_box", label_visibility="collapsed")

if coord_input and coord_input != st.session_state.last_coord:
    st.session_state.last_coord = coord_input
    try:
        lat, lng = map(float, coord_input.split(","))
        addr_doc = get_jibun_address(lat, lng)
        bjd_doc  = get_region_code(lat, lng)

        st.session_state.addr_info = addr_doc

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
        st.session_state.addr_info = {"error": str(e)}


# -------------------------------
# 5️⃣ 레이아웃
# -------------------------------
col_map, col_info = st.columns([6, 4], gap="medium")

# ── 지도 ──
html_code = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false"></script>
</head>
<body style="margin:0;padding:0;background:#f8fafc;">
<div id="map" style="width:100%;height:520px;border-radius:12px;overflow:hidden;
     box-shadow:0 4px 20px rgba(0,0,0,.12);"></div>
<script>
var geojson = {geojson_str};

kakao.maps.load(function() {{
    var map = new kakao.maps.Map(document.getElementById('map'), {{
        center: new kakao.maps.LatLng(37.5636, 126.9976),
        level: 4
    }});
    map.addControl(new kakao.maps.ZoomControl(),    kakao.maps.ControlPosition.RIGHT);
    map.addControl(new kakao.maps.MapTypeControl(), kakao.maps.ControlPosition.TOPRIGHT);

    var selectedPolygon = null;

    function pointInPolygon(point, vs) {{
        var x = point[0], y = point[1];
        var inside = false;
        for (var i = 0, j = vs.length - 1; i < vs.length; j = i++) {{
            var xi = vs[i][0], yi = vs[i][1];
            var xj = vs[j][0], yj = vs[j][1];
            var intersect = ((yi > y) != (yj > y))
                && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
            if (intersect) inside = !inside;
        }}
        return inside;
    }}

    function sendCoordToStreamlit(lat, lng) {{
        var inputs = window.parent.document.querySelectorAll('input[type="text"]');
        if (!inputs.length) return;
        var inp    = inputs[0];
        var coord  = lat.toFixed(7) + ',' + lng.toFixed(7);
        var setter = Object.getOwnPropertyDescriptor(
            window.parent.HTMLInputElement.prototype, 'value'
        ).set;
        setter.call(inp, coord);
        ['input','keydown','keypress','keyup'].forEach(function(t) {{
            inp.dispatchEvent(
                t.startsWith('key')
                    ? new inp.ownerDocument.defaultView.KeyboardEvent(t, {{key:'Enter', keyCode:13, bubbles:true}})
                    : new inp.ownerDocument.defaultView.Event(t, {{bubbles:true}})
            );
        }});
    }}

    kakao.maps.event.addListener(map, 'click', function(mouseEvent) {{
        var lat = mouseEvent.latLng.getLat();
        var lng = mouseEvent.latLng.getLng();

        if (selectedPolygon) {{
            selectedPolygon.setMap(null);
        }}

        for (var f of geojson.features) {{
            var coords = f.geometry.coordinates;
            for (var polygonSet of coords) {{
                for (var ring of polygonSet) {{
                    if (pointInPolygon([lng, lat], ring)) {{
                        var path = ring.map(coord =>
                            new kakao.maps.LatLng(coord[1], coord[0])
                        );
                        selectedPolygon = new kakao.maps.Polygon({{
                            path: path,
                            strokeWeight: 2,
                            strokeColor: '#FF0000',
                            fillColor: '#FF0000',
                            fillOpacity: 0.3
                        }});
                        selectedPolygon.setMap(map);
                        sendCoordToStreamlit(lat, lng);
                        return;
                    }}
                }}
            }}
        }}

        // GeoJSON 범위 밖이어도 건축물대장 조회는 실행
        sendCoordToStreamlit(lat, lng);
    }});
}});
</script>
</body>
</html>
"""

with col_map:
    components.html(html_code, height=540, scrolling=False)


# ── 정보 패널 ──
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
        </div>""", unsafe_allow_html=True)

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
                name      = (item.get("bldNm") or "").strip() or \
                            (item.get("splotNm") or "").strip() or \
                            (item.get("newPlatPlc") or item.get("platPlc") or f"건물 {i+1}")
                use_nm    = val(item.get("mainPurpsCdNm"))
                struct    = val(item.get("strctCdNm"))
                roof      = val(item.get("roofCdNm"))
                floor_u   = val(item.get("grndFlrCnt"))
                floor_d   = val(item.get("ugrndFlrCnt"))
                area      = fmt_area(item.get("totArea"))
                plat_area = fmt_area(item.get("platArea"))
                bc_area   = fmt_area(item.get("archArea"))
                height    = val(item.get("heit"))
                approve   = fmt_date(item.get("useAprDay"))
                fam_cnt   = val(item.get("hhldCnt"))
                ho_cnt    = val(item.get("hoCnt"))
                prkg      = val(item.get("indrAutoUtcnt"))
                regstr    = val(item.get("regstrGbCdNm"))
                kind      = val(item.get("regstrKindCdNm"))

                badge_cls  = "badge-green" if "주거" in use_nm else \
                             "badge-orange" if any(k in use_nm for k in ["상업","근린","업무","판매"]) else "badge-blue"
                kind_badge = f'<span class="badge badge-purple" style="font-size:.72rem">{regstr} · {kind}</span>' if regstr != "-" else ""

                rows = [f"<div class='data-row'><span class='data-label'>주용도</span><span class='data-value'><span class='badge {badge_cls}'>{use_nm}</span></span></div>"]
                for label, v in [("구조", struct), ("지붕", roof)]:
                    if v != "-": rows.append(f"<div class='data-row'><span class='data-label'>{label}</span><span class='data-value'>{v}</span></div>")
                rows.append(f"<div class='data-row'><span class='data-label'>층수</span><span class='data-value'>지상 {floor_u}층 / 지하 {floor_d}층</span></div>")
                for label, v in [("연면적", area), ("건축면적", bc_area), ("대지면적", plat_area)]:
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
            for k in ["addr_info", "building_title", "building_basic"]:
                st.session_state[k] = None
            st.session_state.last_coord = ""
            st.rerun()
