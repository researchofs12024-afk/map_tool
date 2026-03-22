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
.error-box { background:#fff3cd; border:1px solid #ffc107; border-radius:10px; padding:14px 18px; color:#856404; font-size:.88rem; }
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

col_map, col_info = st.columns([6, 4], gap="medium")

for k, v in [("addr_info",None),("building_title",None),("building_basic",None),("last_coord","")]:
    if k not in st.session_state:
        st.session_state[k] = v

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

# VWorld 키를 JS에 전달 (브라우저에서 직접 호출 + corsproxy.io 우회)
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
var VWORLD_KEY = '{VWORLD_KEY}';

function point_in_polygon(px, py, coords) {{
  var inside = false;
  var n = coords.length, j = n - 1;
  for (var i = 0; i < n; i++) {{
    var xi = coords[i][0], yi = coords[i][1];
    var xj = coords[j][0], yj = coords[j][1];
    if (((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi))
      inside = !inside;
    j = i;
  }}
  return inside;
}}

(function() {{
  var script = document.createElement('script');
  script.src = 'https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false';
  script.onload = function() {{
    kakao.maps.load(function() {{
      var map = new kakao.maps.Map(document.getElementById('map'), {{
        center: new kakao.maps.LatLng(37.5665, 126.9780), level: 4
      }});
      map.addControl(new kakao.maps.ZoomControl(),    kakao.maps.ControlPosition.RIGHT);
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
          strokeWeight: 3, strokeColor: '#FF6B35', strokeOpacity: 1,
          fillColor: '#FF6B35', fillOpacity: 0.28
        }});
        map.setBounds(bounds, 60);
        document.getElementById('status').innerHTML = '🟧 필지 하이라이트 완료';
      }}

      function fetchParcel(lat, lng) {{
        var d   = 0.0005;
        // corsproxy.io 를 통해 CORS 우회
        var target = 'https://api.vworld.kr/req/wfs'
          + '?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature'
          + '&TYPENAME=lt_c_lhpllnd&SRSNAME=EPSG:4326'
          + '&BBOX=' + (lng-d) + ',' + (lat-d) + ',' + (lng+d) + ',' + (lat+d) + ',EPSG:4326'
          + '&OUTPUT=application/json'
          + '&KEY=' + VWORLD_KEY;

        var proxyUrl = 'https://corsproxy.io/?' + encodeURIComponent(target);

        fetch(proxyUrl)
          .then(function(r) {{ return r.json(); }})
          .then(function(data) {{
            var features = data.features || [];
            if (!features.length) {{
              document.getElementById('status').innerHTML = '⚠️ 필지 경계 없음';
              return;
            }}
            // 클릭 좌표 포함 필지 선택
            var best = null;
            for (var i = 0; i < features.length; i++) {{
              var geom = features[i].geometry;
              if (!geom) continue;
              var rings = geom.type === 'Polygon' ? [geom.coordinates[0]] : geom.coordinates.map(function(g){{return g[0];}});
              for (var r = 0; r < rings.length; r++) {{
                if (point_in_polygon(lng, lat, rings[r])) {{
                  best = geom; break;
                }}
              }}
              if (best) break;
            }}
            drawPolygon(best || features[0].geometry);
          }})
          .catch(function(e) {{
            document.getElementById('status').innerHTML = '⚠️ 필지 조회 실패: ' + e.message;
          }});
      }}

      kakao.maps.event.addListener(map, 'click', function(e) {{
        var lat = e.latLng.getLat(), lng = e.latLng.getLng();
        if (marker) marker.setMap(null);
        marker = new kakao.maps.Marker({{ position: e.latLng, map: map }});
        document.getElementById('status').innerHTML = '⏳ 필지 조회 중...';

        // 필지 하이라이트 (브라우저 JS → corsproxy → VWorld)
        fetchParcel(lat, lng);

        // 건축물대장 (Streamlit Python)
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
            클릭한 필지가 <span style="color:#FF6B35;font-weight:700">주황색</span>으로 하이라이트되고<br>
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
            for k in ["addr_info","building_title","building_basic"]:
                st.session_state[k] = None
            st.session_state.last_coord = ""
            st.rerun()
