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
# API 함수
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
# CSS
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
    padding:18px 22px; margin-bottom:12px; box-shadow:0 2px 12px rgba(0,0,0,.06);
}
.info-card h3 {
    color:#1a2e3b; font-size:1rem; font-weight:700;
    margin:0 0 12px 0; padding-bottom:8px; border-bottom:2px solid #e3f2fd;
}
.data-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:6px 0; border-bottom:1px dashed #f0f4f8; font-size:.85rem;
}
.data-row:last-child { border-bottom:none; }
.data-label { color:#6b7c8d; font-weight:500; min-width:120px; }
.data-value { color:#1a2e3b; font-weight:600; text-align:right; font-size:.83rem; }
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:.75rem; font-weight:600; }
.badge-green  { background:#e8f5e9; color:#2e7d32; }
.badge-blue   { background:#e3f2fd; color:#1565c0; }
.badge-orange { background:#fff3e0; color:#e65100; }
.badge-purple { background:#ede7f6; color:#4527a0; }
.badge-red    { background:#ffebee; color:#c62828; }
.hint-box {
    background:linear-gradient(135deg,#e3f2fd,#f3e5f5); border-radius:12px;
    padding:24px 18px; text-align:center; color:#37474f; font-size:.9rem; line-height:1.9;
}
.hint-box .icon { font-size:2.2rem; margin-bottom:8px; }
.error-box { background:#fff3cd; border:1px solid #ffc107; border-radius:10px;
             padding:12px 16px; color:#856404; font-size:.85rem; }
.preview-box {
    background:#f0f7ff; border:2px solid #1976d2; border-radius:12px;
    padding:16px 20px; margin-bottom:12px;
}
.preview-box .addr-main { font-size:1rem; font-weight:700; color:#1a2e3b; margin-bottom:4px; }
.preview-box .addr-sub  { font-size:.83rem; color:#546e7a; }
.queue-item {
    background:#fff; border:1px solid #e0e0e0; border-radius:10px;
    padding:10px 14px; margin-bottom:8px; display:flex;
    justify-content:space-between; align-items:center;
}
.queue-item .q-addr { font-size:.85rem; font-weight:600; color:#1a2e3b; }
.queue-item .q-sub  { font-size:.76rem; color:#78909c; margin-top:2px; }
.result-header {
    background: linear-gradient(135deg, #1565c0, #0d47a1);
    color:#fff; border-radius:12px 12px 0 0;
    padding:14px 20px; font-weight:700; font-size:1rem;
    margin-bottom:0;
}
.divider { border:none; border-top:2px solid #e3f2fd; margin:16px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div style="font-size:2.4rem">🏢</div>
    <div>
        <h1>건축물대장 일괄 조회 서비스</h1>
        <p>지도를 클릭해 건물을 선택하고, 리스트를 확정한 후 일괄 조회하세요</p>
    </div>
</div>
""", unsafe_allow_html=True)


# -------------------------------
# Session state 초기화
# -------------------------------
defaults = {
    "last_coord": "",
    "preview": None,        # 현재 클릭한 위치 미리보기 {road, jibun, bjd_doc, addr_doc}
    "queue": [],            # 추가 확정된 건물 리스트
    "batch_results": [],    # 일괄 조회 결과
    "queried": False,       # 일괄 조회 완료 여부
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# -------------------------------
# 좌표 입력 처리
# -------------------------------
coord_input = st.text_input("coord", value="", key="coord_box", label_visibility="collapsed")

if coord_input and coord_input != st.session_state.last_coord:
    st.session_state.last_coord = coord_input
    st.session_state.queried = False
    try:
        lat, lng = map(float, coord_input.split(","))
        addr_doc = get_jibun_address(lat, lng)
        bjd_doc  = get_region_code(lat, lng)
        road_addr = addr_doc.get("road_address") if addr_doc else None
        jibun_addr = addr_doc.get("address", {}) if addr_doc else {}
        st.session_state.preview = {
            "road":     road_addr.get("address_name", "없음") if road_addr else "없음",
            "jibun":    jibun_addr.get("address_name", "없음"),
            "addr_doc": addr_doc,
            "bjd_doc":  bjd_doc,
        }
    except Exception as e:
        st.session_state.preview = None


# -------------------------------
# 레이아웃: 지도 | 사이드패널
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
<div id="map" style="width:100%;height:580px;border-radius:12px;overflow:hidden;
     box-shadow:0 4px 20px rgba(0,0,0,.12);"></div>
<script>
kakao.maps.load(function() {{
    var map = new kakao.maps.Map(document.getElementById('map'), {{
        center: new kakao.maps.LatLng(37.5636, 126.9976),
        level: 4
    }});
    map.addControl(new kakao.maps.ZoomControl(),    kakao.maps.ControlPosition.RIGHT);
    map.addControl(new kakao.maps.MapTypeControl(), kakao.maps.ControlPosition.TOPRIGHT);

    var currentMarker = null;

    function sendCoordToStreamlit(lat, lng) {{
        var inputs = window.parent.document.querySelectorAll('input[type="text"]');
        if (!inputs.length) return;
        var inp   = inputs[0];
        var coord = lat.toFixed(7) + ',' + lng.toFixed(7);
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

        // 이전 마커 제거 후 새 마커 표시
        if (currentMarker) currentMarker.setMap(null);
        currentMarker = new kakao.maps.Marker({{
            position: new kakao.maps.LatLng(lat, lng),
            map: map
        }});

        sendCoordToStreamlit(lat, lng);
    }});
}});
</script>
</body>
</html>
"""

with col_map:
    components.html(html_code, height=600, scrolling=False)


# ── 사이드 패널 ──
with col_info:

    # ── 섹션 1: 현재 선택 미리보기 ──
    st.markdown("#### 📍 현재 선택 위치")

    if st.session_state.preview is None:
        st.markdown("""
        <div class="hint-box">
            <div class="icon">🗺️</div>
            <strong>지도를 클릭해 건물을 선택하세요</strong><br>
            주소 확인 후 리스트에 추가할 수 있습니다
        </div>""", unsafe_allow_html=True)
    else:
        p = st.session_state.preview
        # 이미 큐에 있는지 확인
        already = any(q["jibun"] == p["jibun"] for q in st.session_state.queue)

        st.markdown(f"""
        <div class="preview-box">
            <div class="addr-main">🏠 {p['road']}</div>
            <div class="addr-sub">지번: {p['jibun']}</div>
        </div>""", unsafe_allow_html=True)

        if already:
            st.info("✅ 이미 조회 리스트에 추가된 건물입니다.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("➕ 리스트에 추가", use_container_width=True, type="primary"):
                    st.session_state.queue.append({
                        "road":     p["road"],
                        "jibun":    p["jibun"],
                        "addr_doc": p["addr_doc"],
                        "bjd_doc":  p["bjd_doc"],
                    })
                    st.session_state.preview = None
                    st.rerun()
            with c2:
                if st.button("✖ 건너뛰기", use_container_width=True):
                    st.session_state.preview = None
                    st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── 섹션 2: 조회 대기 리스트 ──
    st.markdown(f"#### 📋 조회 리스트 ({len(st.session_state.queue)}건)")

    if not st.session_state.queue:
        st.caption("아직 추가된 건물이 없습니다.")
    else:
        for i, item in enumerate(st.session_state.queue):
            c_addr, c_del = st.columns([8, 2])
            with c_addr:
                st.markdown(f"""
                <div class="queue-item">
                    <div>
                        <div class="q-addr">{i+1}. {item['road']}</div>
                        <div class="q-sub">{item['jibun']}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with c_del:
                if st.button("🗑", key=f"del_{i}", help="리스트에서 제거"):
                    st.session_state.queue.pop(i)
                    st.rerun()

        st.markdown("")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            if st.button("🔍 일괄 조회", use_container_width=True, type="primary",
                         disabled=len(st.session_state.queue) == 0):
                results = []
                with st.spinner("건축물대장 조회 중..."):
                    for item in st.session_state.queue:
                        bjd  = item["bjd_doc"]
                        addr = item["addr_doc"]
                        if not bjd:
                            results.append({"meta": item, "titles": [], "error": "지역코드 없음"})
                            continue
                        b_code  = bjd.get("code", "")
                        jibun   = addr.get("address", {}) if addr else {}
                        main_no = jibun.get("main_address_no", "0") or "0"
                        sub_no  = jibun.get("sub_address_no",  "0") or "0"
                        if len(b_code) >= 10:
                            sc = b_code[:5]; bc = b_code[5:10]
                            titles = get_building_title(sc, bc, main_no, sub_no)
                            basics = get_building_info(sc, bc, main_no, sub_no)
                        else:
                            titles, basics = [], []
                        results.append({"meta": item, "titles": titles, "basics": basics})
                st.session_state.batch_results = results
                st.session_state.queried = True
                st.rerun()
        with col_q2:
            if st.button("🗑 전체 초기화", use_container_width=True):
                st.session_state.queue = []
                st.session_state.batch_results = []
                st.session_state.queried = False
                st.session_state.preview = None
                st.session_state.last_coord = ""
                st.rerun()


# -------------------------------
# 일괄 조회 결과 (지도 아래 전체 폭)
# -------------------------------
if st.session_state.queried and st.session_state.batch_results:

    st.markdown("---")
    st.markdown("## 📊 일괄 조회 결과")

    def fmt_area(v):
        try: return f"{float(v):,.2f} ㎡" if float(v) > 0 else "-"
        except: return "-"
    def fmt_date(v):
        s = str(v).strip()
        return f"{s[:4]}-{s[4:6]}-{s[6:]}" if len(s)==8 and s.isdigit() else (s or "-")
    def val(v):
        s = str(v).strip() if v else ""
        return s if s not in ["","0","None"] else "-"

    for res in st.session_state.batch_results:
        meta   = res["meta"]
        titles = res.get("titles", [])

        with st.expander(f"🏢 {meta['road']}  |  {meta['jibun']}", expanded=True):
            if not titles:
                st.markdown('<div class="error-box">ℹ️ 건축물대장 정보가 없습니다.</div>',
                            unsafe_allow_html=True)
                continue

            cols = st.columns(min(len(titles[:3]), 3))
            for idx, item in enumerate(titles[:3]):
                with cols[idx]:
                    name      = (item.get("bldNm") or "").strip() or \
                                (item.get("splotNm") or "").strip() or \
                                (item.get("newPlatPlc") or item.get("platPlc") or f"건물 {idx+1}")
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

                    badge_cls  = "badge-green"  if "주거" in use_nm else \
                                 "badge-orange" if any(k in use_nm for k in ["상업","근린","업무","판매"]) \
                                 else "badge-blue"
                    kind_badge = f'<span class="badge badge-purple" style="font-size:.72rem">{regstr} · {kind}</span>' \
                                 if regstr != "-" else ""

                    rows = [f"<div class='data-row'><span class='data-label'>주용도</span>"
                            f"<span class='data-value'><span class='badge {badge_cls}'>{use_nm}</span></span></div>"]
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
