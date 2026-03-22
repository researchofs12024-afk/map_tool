import streamlit as st
import requests

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


def get_building_info(sigungu_cd, bjdong_cd, bun, ji):
    """건축물대장 기본개요 조회"""
    url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrBasisOulnInfo"
    params = {
        "serviceKey": BUILDING_API_KEY,
        "sigunguCd":  sigungu_cd,
        "bjdongCd":   bjdong_cd,
        "bun":        str(bun).zfill(4),
        "ji":         str(ji).zfill(4),
        "numOfRows":  "10",
        "pageNo":     "1",
        "_type":      "json",
    }
    try:
        resp  = requests.get(url, params=params, timeout=10)
        data  = resp.json()
        body  = data.get("response", {}).get("body", {})
        items = body.get("items", {})
        if not items:
            return []
        item_list = items.get("item", [])
        return [item_list] if isinstance(item_list, dict) else item_list
    except Exception as e:
        return {"error": str(e)}


def get_building_title(sigungu_cd, bjdong_cd, bun, ji):
    """건축물대장 표제부 조회 (상세 면적/구조/층수 포함)"""
    url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitleInfo"
    params = {
        "serviceKey": BUILDING_API_KEY,
        "sigunguCd":  sigungu_cd,
        "bjdongCd":   bjdong_cd,
        "bun":        str(bun).zfill(4),
        "ji":         str(ji).zfill(4),
        "numOfRows":  "10",
        "pageNo":     "1",
        "_type":      "json",
    }
    try:
        resp  = requests.get(url, params=params, timeout=10)
        data  = resp.json()
        body  = data.get("response", {}).get("body", {})
        items = body.get("items", {})
        if not items:
            return []
        item_list = items.get("item", [])
        return [item_list] if isinstance(item_list, dict) else item_list
    except Exception as e:
        return []


# ── CSS ──────────────────────────────────────────────────────────────────────
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
    padding:22px 26px; margin-bottom:16px;
    box-shadow:0 2px 12px rgba(0,0,0,.06);
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
    padding:30px 22px; text-align:center; color:#37474f;
    font-size:.9rem; line-height:1.9;
}
.hint-box .icon { font-size:2.4rem; margin-bottom:10px; }
.error-box {
    background:#fff3cd; border:1px solid #ffc107; border-radius:10px;
    padding:14px 18px; color:#856404; font-size:.88rem;
}
.raw-box {
    background:#f8f9fa; border:1px solid #dee2e6; border-radius:10px;
    padding:12px 16px; font-size:.75rem; font-family:monospace;
    color:#495057; word-break:break-all; line-height:1.7; margin-bottom:12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div style="font-size:2.4rem">🏢</div>
    <div>
        <h1>건축물대장 조회 서비스</h1>
        <p>카카오맵에서 건물을 클릭하면 건축물대장 정보를 즉시 조회합니다</p>
    </div>
</div>
""", unsafe_allow_html=True)

col_map, col_info = st.columns([6, 4], gap="medium")

if "addr_info"      not in st.session_state: st.session_state.addr_info      = None
if "building_basic" not in st.session_state: st.session_state.building_basic = None
if "building_title" not in st.session_state: st.session_state.building_title = None
if "last_coord"     not in st.session_state: st.session_state.last_coord     = ""

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
                sc = b_code[:5]
                bc = b_code[5:10]
                st.session_state.building_basic = get_building_info(sc, bc, main_no, sub_no)
                st.session_state.building_title = get_building_title(sc, bc, main_no, sub_no)
            else:
                st.session_state.building_basic = None
                st.session_state.building_title = None
        else:
            st.session_state.building_basic = None
            st.session_state.building_title = None
    except Exception as e:
        st.session_state.addr_info      = {"error": str(e)}
        st.session_state.building_basic = None
        st.session_state.building_title = None

MAP_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: sans-serif; background:#f8fafc; }
  #map { width:100%; height:500px; border-radius:12px; overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,.12); }
  #status {
    position:absolute; top:10px; left:50%; transform:translateX(-50%);
    background:rgba(255,255,255,.95); border-radius:24px;
    padding:8px 20px; font-size:13px; color:#37474f;
    box-shadow:0 2px 12px rgba(0,0,0,.15); z-index:10;
    backdrop-filter:blur(4px); white-space:nowrap;
  }
  .wrapper { position:relative; }
</style>
</head>
<body>
<div class="wrapper">
  <div id="status">🖱️ 지도를 클릭하면 건물 정보를 조회합니다</div>
  <div id="map"></div>
</div>
<script>
(function() {
  var script = document.createElement('script');
  script.type = 'text/javascript';
  script.src = 'https://dapi.kakao.com/v2/maps/sdk.js?appkey=KAKAO_JS_KEY_PLACEHOLDER&autoload=false';
  script.onload = function() {
    kakao.maps.load(function() {
      var container = document.getElementById('map');
      var options = { center: new kakao.maps.LatLng(37.5665, 126.9780), level: 4 };
      var map    = new kakao.maps.Map(container, options);
      var marker = null;
      map.addControl(new kakao.maps.ZoomControl(),    kakao.maps.ControlPosition.RIGHT);
      map.addControl(new kakao.maps.MapTypeControl(), kakao.maps.ControlPosition.TOPRIGHT);
      kakao.maps.event.addListener(map, 'click', function(mouseEvent) {
        var lat = mouseEvent.latLng.getLat();
        var lng = mouseEvent.latLng.getLng();
        if (marker) marker.setMap(null);
        marker = new kakao.maps.Marker({ position: mouseEvent.latLng, map: map });
        document.getElementById('status').innerHTML = '⏳ 조회 중...';
        var inputs = window.parent.document.querySelectorAll('input[type="text"]');
        for (var i = 0; i < inputs.length; i++) {
          var inp    = inputs[i];
          var coord  = lat.toFixed(7) + ',' + lng.toFixed(7);
          var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
          setter.call(inp, coord);
          inp.dispatchEvent(new inp.ownerDocument.defaultView.Event('input', { bubbles: true }));
          inp.dispatchEvent(new inp.ownerDocument.defaultView.KeyboardEvent('keydown',  { key:'Enter', keyCode:13, bubbles:true }));
          inp.dispatchEvent(new inp.ownerDocument.defaultView.KeyboardEvent('keypress', { key:'Enter', keyCode:13, bubbles:true }));
          inp.dispatchEvent(new inp.ownerDocument.defaultView.KeyboardEvent('keyup',    { key:'Enter', keyCode:13, bubbles:true }));
          break;
        }
        setTimeout(function() {
          document.getElementById('status').innerHTML = '📍 위도: ' + lat.toFixed(5) + ' / 경도: ' + lng.toFixed(5);
        }, 2000);
      });
    });
  };
  script.onerror = function() { document.getElementById('status').innerHTML = '❌ 카카오맵 로드 실패'; };
  document.head.appendChild(script);
})();
</script>
</body>
</html>
""".replace("KAKAO_JS_KEY_PLACEHOLDER", KAKAO_JS_KEY)

with col_map:
    st.components.v1.html(MAP_HTML, height=520, scrolling=False)

with col_info:
    if st.session_state.addr_info is None:
        st.markdown("""
        <div class="hint-box">
            <div class="icon">🗺️</div>
            <strong>지도를 클릭해 건물 정보를 조회하세요</strong><br>
            건물 위치를 클릭하면<br>건축물대장 정보가 이 곳에 표시됩니다
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

        # ── 표제부(상세) 우선 표시 ──
        title_data = st.session_state.building_title
        basic_data = st.session_state.building_basic

        def fmt_area(v):
            try: return f"{float(v):,.2f} ㎡" if float(v) > 0 else "-"
            except: return str(v) if v else "-"

        def fmt_date(v):
            s = str(v).strip()
            return f"{s[:4]}-{s[4:6]}-{s[6:]}" if len(s) == 8 and s.isdigit() else (s if s else "-")

        def val(v):
            return str(v).strip() if v and str(v).strip() not in ["", "0", "None"] else "-"

        if title_data and isinstance(title_data, list) and len(title_data) > 0:
            for i, item in enumerate(title_data[:3]):
                # 표제부 필드명
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
                bc_area  = fmt_area(item.get("archArea"))   # 건축면적
                height   = val(item.get("heit"))
                approve  = fmt_date(item.get("useAprDay"))
                fam_cnt  = val(item.get("hhldCnt"))
                ho_cnt   = val(item.get("hoCnt"))
                prkg     = val(item.get("indrAutoUtcnt"))   # 옥내자주식
                regstr   = val(item.get("regstrGbCdNm"))
                kind     = val(item.get("regstrKindCdNm"))

                badge_cls = "badge-green"  if "주거" in use_nm else \
                            "badge-orange" if any(k in use_nm for k in ["상업","근린","업무","판매"]) else \
                            "badge-blue"
                kind_badge = f'<span class="badge badge-purple" style="font-size:.72rem">{regstr} · {kind}</span>' \
                             if regstr != "-" else ""

                rows = []
                rows.append(f"<div class='data-row'><span class='data-label'>주용도</span><span class='data-value'><span class='badge {badge_cls}'>{use_nm}</span></span></div>")
                if struct != "-": rows.append(f"<div class='data-row'><span class='data-label'>구조</span><span class='data-value'>{struct}</span></div>")
                if roof   != "-": rows.append(f"<div class='data-row'><span class='data-label'>지붕</span><span class='data-value'>{roof}</span></div>")
                rows.append(f"<div class='data-row'><span class='data-label'>층수</span><span class='data-value'>지상 {floor_u}층 / 지하 {floor_d}층</span></div>")
                if area      != "-": rows.append(f"<div class='data-row'><span class='data-label'>연면적</span><span class='data-value'>{area}</span></div>")
                if bc_area   != "-": rows.append(f"<div class='data-row'><span class='data-label'>건축면적</span><span class='data-value'>{bc_area}</span></div>")
                if plat_area != "-": rows.append(f"<div class='data-row'><span class='data-label'>대지면적</span><span class='data-value'>{plat_area}</span></div>")
                if height    != "-": rows.append(f"<div class='data-row'><span class='data-label'>높이</span><span class='data-value'>{height} m</span></div>")
                if approve   != "-": rows.append(f"<div class='data-row'><span class='data-label'>사용승인일</span><span class='data-value'>{approve}</span></div>")
                if fam_cnt   != "-": rows.append(f"<div class='data-row'><span class='data-label'>세대수</span><span class='data-value'>{fam_cnt}세대</span></div>")
                if ho_cnt    != "-": rows.append(f"<div class='data-row'><span class='data-label'>호수</span><span class='data-value'>{ho_cnt}호</span></div>")
                if prkg      != "-": rows.append(f"<div class='data-row'><span class='data-label'>옥내주차</span><span class='data-value'>{prkg}대</span></div>")

                st.markdown(f"""
                <div class="info-card">
                    <h3>🏗️ {name} {kind_badge}</h3>
                    {"".join(rows)}
                </div>""", unsafe_allow_html=True)

        elif basic_data and isinstance(basic_data, list) and len(basic_data) > 0:
            # 표제부 없으면 기본개요 표시
            for i, item in enumerate(basic_data[:3]):
                name  = (item.get("bldNm") or "").strip() or (item.get("platPlc") or f"건물 {i+1}")
                regstr = val(item.get("regstrGbCdNm"))
                kind   = val(item.get("regstrKindCdNm"))
                kind_badge = f'<span class="badge badge-purple" style="font-size:.72rem">{regstr} · {kind}</span>' if regstr != "-" else ""
                st.markdown(f"""
                <div class="info-card">
                    <h3>🏗️ {name} {kind_badge}</h3>
                    <div class="raw-box">{str(item)[:600]}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-box">ℹ️ 해당 위치에 등록된 건축물대장 정보가 없습니다.</div>', unsafe_allow_html=True)

        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.addr_info      = None
            st.session_state.building_basic = None
            st.session_state.building_title = None
            st.session_state.last_coord     = ""
            st.rerun()
