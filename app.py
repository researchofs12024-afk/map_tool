import streamlit as st
import requests
import json

st.set_page_config(
    page_title="건축물대장 조회 서비스",
    page_icon="🏢",
    layout="wide"
)

# ------------------ KEY ------------------
try:
    KAKAO_JS_KEY     = st.secrets["KAKAO_JS_KEY"]
    KAKAO_REST_KEY   = st.secrets["KAKAO_REST_KEY"]
    BUILDING_API_KEY = st.secrets["BUILDING_API_KEY"]
    VWORLD_KEY       = st.secrets["VWORLD_KEY"]
except Exception:
    KAKAO_JS_KEY     = "YOUR_KEY"
    KAKAO_REST_KEY   = "YOUR_KEY"
    BUILDING_API_KEY = "YOUR_KEY"
    VWORLD_KEY       = "YOUR_KEY"

# ------------------ API ------------------
def get_region_code(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    try:
        res = requests.get(url, headers=headers, params={"x": lng, "y": lat}, timeout=10)
        docs = res.json().get("documents", [])
        return next((d for d in docs if d.get("region_type") == "B"), None)
    except:
        return None


def get_jibun_address(lat, lng):
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    try:
        res = requests.get(url, headers=headers, params={"x": lng, "y": lat}, timeout=10)
        docs = res.json().get("documents", [])
        return docs[0] if docs else {}
    except:
        return {}


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
        res = requests.get(url, params=params, headers=headers, timeout=10)

        if res.status_code != 200:
            return None, f"HTTP {res.status_code}"

        data = res.json()

        if data.get("response", {}).get("status") == "OK":
            features = data["response"]["result"]["featureCollection"]["features"]
            if features:
                return features[0]["geometry"], "OK"

        return None, "데이터 없음"

    except Exception as e:
        return None, str(e)


def get_building_title(sigungu_cd, bjdong_cd, bun, ji):
    url = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitleInfo"
    params = {
        "serviceKey": BUILDING_API_KEY,
        "sigunguCd": sigungu_cd,
        "bjdongCd": bjdong_cd,
        "bun": str(bun).zfill(4),
        "ji": str(ji).zfill(4),
        "_type": "json"
    }
    try:
        res = requests.get(url, params=params, timeout=10).json()
        items = res["response"]["body"]["items"]
        return items.get("item", [])
    except:
        return []


# ------------------ STATE ------------------
if "coord" not in st.session_state:
    st.session_state.coord = ""

# ------------------ INPUT ------------------
coord = st.text_input("좌표 (lat,lng)", value="")

# ------------------ PROCESS ------------------
if coord:
    try:
        lat, lng = map(float, coord.split(","))

        addr = get_jibun_address(lat, lng)
        region = get_region_code(lat, lng)
        geom, status = get_parcel_polygon(lat, lng)

        st.write("📍 주소:", addr.get("address", {}).get("address_name"))

        if geom:
            st.success("필지 가져오기 성공")
        else:
            st.warning(status)

        if region:
            code = region["code"]
            bun = addr.get("address", {}).get("main_address_no", "0")
            ji  = addr.get("address", {}).get("sub_address_no", "0")

            buildings = get_building_title(code[:5], code[5:10], bun, ji)

            if buildings:
                for b in buildings:
                    st.write("🏢 건물명:", b.get("bldNm"))
                    st.write("용도:", b.get("mainPurpsCdNm"))
                    st.write("---")
            else:
                st.info("건축물 없음")

    except Exception as e:
        st.error(f"에러: {e}")

# ------------------ MAP ------------------
MAP_HTML = f"""
<div id="map" style="width:100%;height:500px;"></div>

<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false"></script>
<script>
kakao.maps.load(function() {{
    var map = new kakao.maps.Map(document.getElementById('map'), {{
        center: new kakao.maps.LatLng(37.5665, 126.9780),
        level: 3
    }});

    kakao.maps.event.addListener(map, 'click', function(e) {{
        var lat = e.latLng.getLat();
        var lng = e.latLng.getLng();

        var input = window.parent.document.querySelector('input');
        input.value = lat + "," + lng;
        input.dispatchEvent(new Event('input', {{bubbles:true}}));
    }});
}});
</script>
"""

st.components.v1.html(MAP_HTML, height=520)
