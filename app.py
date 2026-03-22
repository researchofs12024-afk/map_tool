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


def get_building_info(sigungu_cd, bjdong_cd, bun, ji):
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
        resp = requests.get(url, params=params, timeout=10)
        raw = resp.text
        try:
            data = resp.json()
        except Exception:
            return {"error": f"JSON 파싱 실패: {raw[:300]}"}
        body  = data.get("response", {}).get("body", {})
        total = body.get("totalCount", 0)
        items = body.get("items", {})
        if total == 0 or not items:
            return {"empty": True, "params": params, "raw": raw[:500]}
        item_list = items.get("item", [])
        if isinstance(item_list, dict):
            item_list = [item_list]
        return item_list
    except Exception as e:
        return {"error": str(e)}


def get_address_from_coords(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    params  = {"x": lng, "y": lat}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        docs = resp.json().get("documents", [])
        return docs[0] if docs else None
    except Exception as e:
        return {"error": str(e)}


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
.data-value { color:#1a2e3b; font-weight:600; text-align:right; }
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:.78rem; font-weight:600; }
.badge-green  { background:#e8f5e9; color:#2e7d32; }
.badge-blue   { background:#e3f2fd; color:#1565c0; }
.badge-orange { background:#fff3e0; color:#e65100; }
.hint-box {
    background:linear-gradient(135deg,#e3f2fd,#f3e5f5); border-radius:12px;
    padding:18px 22px; text-align:center; color:#37474f;
    font-size:.9rem; line-height:1.7;
}
.error-box {
    background:#fff3cd; border:1px solid #ffc107; border-radius:10px;
    padding:14px 18px; color:#856404; font-size:.88rem;
}
.debug-box {
    background:#f0f4ff; border:1px solid #90caf9; border-radius:10px;
    padding:14px 18px; color:#1a237e; font-size:.75rem;
    font-family: monospace; word-break: break-all; line-height:1.8;
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

if "addr_info"     not in st.session_state: st.session_state.addr_info     = None
if "building_data" not in st.session_state: st.session_state.building_data = None
if "last_coord"    not in st.session_state: st.session_state.last_coord    = ""
if "debug_info"    not in st.session_state: st.session_state.debug_info    = {}

coord_input = st.text_input("coord", value="", key="coord_box", label_visibility="collapsed")

if coord_input and coord_input != st.session_state.last_coord:
    st.session_state.last_coord = coord_input
    try:
        lat_str, lng_str = coord_input.split(",")
        lat = float(lat_str.strip())
        lng = float(lng_str.strip())

        addr_doc = get_address_from_coords(lat, lng)
        st.session_state.addr_info = addr_doc

        debug = {"lat": lat, "lng": lng}

        if addr_doc and "error" not in addr_doc:
            # ── 전체 address 객체 덤프해서 실제 필드 확인 ──
            jibun = addr_doc.get("address", {})
            debug["address_전체"] = str(jibun)  # 전체 필드 출력

            # 카카오 API 실제 필드명: b_code → 없을 수 있음, 대신 다른 필드 시도
            b_code  = (jibun.get("b_code") or
                       jibun.get("bcode") or
                       jibun.get("code") or "")
            main_no = (jibun.get("main_address_no") or
                       jibun.get("mainAddressNo") or
                       jibun.get("mountain_yn") or "0")  # 실제값 확인용
            sub_no  = (jibun.get("sub_address_no") or
                       jibun.get("subAddressNo") or "0")

            # address_name에서 직접 파싱 시도 (예: "서울 중구 소공동 1")
            addr_name = jibun.get("address_name", "")
            debug["address_name"] = addr_name
            debug["b_code_raw"]   = b_code
            debug["main_no_raw"]  = main_no
            debug["sub_no_raw"]   = sub_no

            # b_code가 있으면 코드 분리
            if b_code and len(b_code) >= 10:
                sigungu_cd = b_code[:5]
                bjdong_cd  = b_code[5:10]
                debug["sigungu_cd"] = sigungu_cd
                debug["bjdong_cd"]  = bjdong_cd

                result = get_building_info(sigungu_cd, bjdong_cd, main_no, sub_no)
                st.session_state.building_data = result
                debug["api_result"] = str(result)[:400]
            else:
                st.session_state.building_data = None
                debug["error"] = f"b_code 없음 또는 짧음: '{b_code}'"
        else:
            st.session_state.building_data = None
            debug["addr_error"] = str(addr_doc)

        st.session_state.debug_info = debug

    except Exception as e:
        st.session_state.addr_info     = {"error": str(e)}
        st.session_state.building_data = None
        st.session_state.debug_info    = {"exception": str(e)}

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
        document.getElementById('status').innerHTML = '📍 위도: ' + lat.toFixed(5) + ' / 경도: ' + lng.toFixed(5);
        var inputs = window.parent.document.querySelectorAll('input[type="text"]');
        for (var i = 0; i < inputs.length; i++) {
          var inp = inputs[i];
          var coord = lat.toFixed(7) + ',' + lng.toFixed(7);
          var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
          setter.call(inp, coord);
          inp.dispatchEvent(new inp.ownerDocument.defaultView.Event('input', { bubbles: true }));
          inp.dispatchEvent(new inp.ownerDocument.defaultView.KeyboardEvent('keydown',  { key:'Enter', keyCode:13, bubbles:true }));
          inp.dispatchEvent(new inp.ownerDocument.defaultView.KeyboardEvent('keypress', { key:'Enter', keyCode:13, bubbles:true }));
          inp.dispatchEvent(new inp.ownerDocument.defaultView.KeyboardEvent('keyup',    { key:'Enter', keyCode:13, bubbles:true }));
          break;
        }
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
        st.markdown("""<div class="hint-box"><div style="font-size:2rem">🗺️</div>
        <strong>지도를 클릭해 건물 정보를 조회하세요</strong></div>""", unsafe_allow_html=True)
    else:
        addr_doc = st.session_state.addr_info
        if "error" not in addr_doc:
            road  = addr_doc.get("road_address")
            jibun = addr_doc.get("address", {})
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

        # 디버그 박스
        if st.session_state.debug_info:
            d = st.session_state.debug_info
            lines = "<br>".join(f"<b>{k}</b>: {v}" for k, v in d.items())
            st.markdown(f'<div class="debug-box">🔍 디버그<br>{lines}</div>', unsafe_allow_html=True)

        bdata = st.session_state.building_data
        if bdata is None:
            st.markdown('<div class="error-box">⚠️ b_code를 가져오지 못했습니다. 디버그 정보를 확인하세요.</div>', unsafe_allow_html=True)
        elif isinstance(bdata, dict) and "error" in bdata:
            st.markdown(f'<div class="error-box">⚠️ API 오류: {bdata.get("error","")}</div>', unsafe_allow_html=True)
        elif isinstance(bdata, dict) and bdata.get("empty"):
            st.markdown(f'<div class="error-box">ℹ️ 건축물대장 없음<br>{bdata.get("raw","")[:200]}</div>', unsafe_allow_html=True)
        elif not bdata:
            st.markdown('<div class="error-box">ℹ️ 건축물대장 정보가 없습니다.</div>', unsafe_allow_html=True)
        else:
            for i, item in enumerate(bdata[:3]):
                name      = item.get("bldNm") or item.get("platPlcNm") or f"건물 {i+1}"
                use_nm    = item.get("mainPurpsCdNm", "-")
                struct    = item.get("strctCdNm", "-")
                floor_u   = item.get("grndFlrCnt", "-")
                floor_d   = item.get("ugrndFlrCnt", "0")
                area      = item.get("totArea", "-")
                plat_area = item.get("platArea", "-")
                height    = item.get("heit", "-")
                approve   = item.get("useAprDay", "-")
                fam_cnt   = item.get("hhldCnt", "-")
                def fmt_area(v):
                    try: return f"{float(v):,.2f} ㎡"
                    except: return str(v)
                def fmt_date(v):
                    s = str(v)
                    return f"{s[:4]}-{s[4:6]}-{s[6:]}" if len(s)==8 else s
                badge_cls = "badge-green" if "주거" in use_nm else \
                            "badge-orange" if any(k in use_nm for k in ["상업","근린"]) else "badge-blue"
                fam_row = (f"<div class='data-row'><span class='data-label'>세대수</span>"
                           f"<span class='data-value'>{fam_cnt}세대</span></div>"
                           if fam_cnt and fam_cnt != "-" else "")
                st.markdown(f"""
                <div class="info-card">
                    <h3>🏗️ {name}</h3>
                    <div class="data-row"><span class="data-label">주용도</span>
                        <span class="data-value"><span class="badge {badge_cls}">{use_nm}</span></span></div>
                    <div class="data-row"><span class="data-label">구조</span><span class="data-value">{struct}</span></div>
                    <div class="data-row"><span class="data-label">층수</span><span class="data-value">지상 {floor_u}층 / 지하 {floor_d}층</span></div>
                    <div class="data-row"><span class="data-label">연면적</span><span class="data-value">{fmt_area(area)}</span></div>
                    <div class="data-row"><span class="data-label">대지면적</span><span class="data-value">{fmt_area(plat_area)}</span></div>
                    <div class="data-row"><span class="data-label">높이</span><span class="data-value">{height} m</span></div>
                    <div class="data-row"><span class="data-label">사용승인일</span><span class="data-value">{fmt_date(approve)}</span></div>
                    {fam_row}
                </div>""", unsafe_allow_html=True)

        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.addr_info     = None
            st.session_state.building_data = None
            st.session_state.last_coord    = ""
            st.session_state.debug_info    = {}
            st.rerun()
