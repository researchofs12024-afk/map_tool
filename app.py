import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import math

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


# ─────────────────────────────────────────────
# 전국 지하철역 좌표 데이터
# ─────────────────────────────────────────────
STATIONS = [
    # 1호선
    ("소요산",37.6657,127.0607,"1호선"),("동두천",37.654,127.057,"1호선"),
    ("양주",37.5799,127.0454,"1호선"),("의정부",37.5381,127.0475,"1호선"),
    ("창동",37.653,127.0474,"1호선"),("월계",37.6358,127.0593,"1호선"),
    ("청량리",37.5805,127.0473,"1호선"),("제기동",37.5775,127.0381,"1호선"),
    ("신설동",37.5757,127.0289,"1호선"),("동묘앞",37.5718,127.0185,"1호선"),
    ("동대문",37.5718,127.0099,"1호선"),("종로5가",37.5703,126.9994,"1호선"),
    ("종로3가",37.5704,126.992,"1호선"),("종각",37.5701,126.9827,"1호선"),
    ("시청",37.5656,126.9774,"1호선"),("서울역",37.5546,126.9708,"1호선"),
    ("남영",37.5431,126.9714,"1호선"),("용산",37.5298,126.9649,"1호선"),
    ("노량진",37.5138,126.9426,"1호선"),("영등포",37.5158,126.907,"1호선"),
    ("신도림",37.5083,126.8912,"1호선"),("구로",37.5028,126.8815,"1호선"),
    ("개봉",37.4939,126.859,"1호선"),("온수",37.4928,126.8249,"1호선"),
    ("역곡",37.4872,126.8038,"1호선"),("부천",37.5032,126.7838,"1호선"),
    ("송내",37.5027,126.758,"1호선"),("부평",37.4897,126.7237,"1호선"),
    ("주안",37.473,126.7048,"1호선"),("인천",37.4736,126.6359,"1호선"),
    ("가산디지털단지",37.481,126.8829,"1·7호선"),
    ("독산",37.4739,126.894,"1호선"),("금천구청",37.4565,126.8954,"1호선"),
    ("시흥",37.3702,126.8029,"1호선"),("당정",37.3616,126.9273,"1호선"),
    ("의왕",37.3449,126.969,"1호선"),("수원",37.2665,127.0005,"1호선"),
    ("병점",37.2088,126.9797,"1호선"),("오산",37.1521,127.0701,"1호선"),
    ("평택",36.9928,127.089,"1호선"),("천안",36.8086,127.1481,"1호선"),
    # 2호선
    ("시청",37.5656,126.9774,"2호선"),("을지로입구",37.566,126.9824,"2호선"),
    ("을지로3가",37.5661,126.9909,"2호선"),("동대문역사문화공원",37.5651,127.0074,"2호선"),
    ("신당",37.5651,127.0193,"2호선"),("왕십리",37.5613,127.0368,"2호선"),
    ("뚝섬",37.5474,127.0476,"2호선"),("성수",37.5445,127.0564,"2호선"),
    ("건대입구",37.5403,127.07,"2호선"),("강변",37.5351,127.1002,"2호선"),
    ("잠실",37.5133,127.1001,"2호선"),("종합운동장",37.5104,127.0731,"2호선"),
    ("삼성",37.5087,127.063,"2호선"),("선릉",37.5042,127.049,"2호선"),
    ("역삼",37.5005,127.0367,"2호선"),("강남",37.4979,127.0276,"2호선"),
    ("교대",37.4935,127.0139,"2호선"),("사당",37.4764,126.9814,"2호선"),
    ("낙성대",37.4765,126.9637,"2호선"),("신림",37.4846,126.9297,"2호선"),
    ("구로디지털단지",37.4853,126.9012,"2호선"),("대림",37.4924,126.896,"2호선"),
    ("신도림",37.5083,126.8912,"2호선"),("문래",37.5176,126.8952,"2호선"),
    ("영등포구청",37.5262,126.8964,"2호선"),("당산",37.5338,126.9012,"2호선"),
    ("합정",37.5497,126.9143,"2호선"),("홍대입구",37.5573,126.9246,"2호선"),
    ("신촌",37.5553,126.9368,"2호선"),("이대",37.5567,126.9461,"2호선"),
    ("아현",37.5589,126.9568,"2호선"),("충정로",37.5598,126.9659,"2호선"),
    # 3호선
    ("대화",37.6733,126.7677,"3호선"),("원흥",37.634,126.8504,"3호선"),
    ("삼송",37.6497,126.8757,"3호선"),("구파발",37.6254,126.9201,"3호선"),
    ("연신내",37.619,126.9211,"3호선"),("불광",37.6106,126.9293,"3호선"),
    ("홍제",37.5924,126.9391,"3호선"),("경복궁",37.5758,126.9745,"3호선"),
    ("안국",37.578,126.985,"3호선"),("종로3가",37.5704,126.992,"3호선"),
    ("충무로",37.5616,126.9943,"3호선"),("약수",37.5547,127.0128,"3호선"),
    ("옥수",37.5437,127.0177,"3호선"),("압구정",37.5275,127.0274,"3호선"),
    ("신사",37.5197,127.0208,"3호선"),("고속터미널",37.5047,127.0049,"3호선"),
    ("교대",37.4935,127.0139,"3호선"),("양재",37.4843,127.0342,"3호선"),
    ("수서",37.488,127.1005,"3호선"),("가락시장",37.4924,127.1185,"3호선"),
    ("오금",37.5026,127.1302,"3호선"),
    # 4호선
    ("진접",37.7374,127.2063,"4호선"),("당고개",37.6661,127.1365,"4호선"),
    ("상계",37.6556,127.076,"4호선"),("노원",37.6548,127.0566,"4호선"),
    ("창동",37.653,127.0474,"4호선"),("수유",37.6376,127.0254,"4호선"),
    ("미아사거리",37.6203,127.0305,"4호선"),("길음",37.603,127.0254,"4호선"),
    ("성신여대입구",37.5929,127.0164,"4호선"),("한성대입구",37.5885,127.0065,"4호선"),
    ("혜화",37.5821,127.0017,"4호선"),("동대문",37.5718,127.0099,"4호선"),
    ("명동",37.5634,126.9831,"4호선"),("서울역",37.5546,126.9708,"4호선"),
    ("삼각지",37.5358,126.9734,"4호선"),("이촌",37.5229,126.9614,"4호선"),
    ("동작",37.5027,126.9793,"4호선"),("사당",37.4764,126.9814,"4호선"),
    ("인덕원",37.3968,126.9724,"4호선"),("평촌",37.3921,126.9524,"4호선"),
    ("범계",37.3867,126.9527,"4호선"),("금정",37.3744,126.9388,"4호선"),
    ("산본",37.3595,126.927,"4호선"),("상록수",37.3221,126.8627,"4호선"),
    ("한대앞",37.3193,126.8381,"4호선"),("중앙",37.3201,126.8268,"4호선"),
    ("고잔",37.3201,126.8126,"4호선"),("안산",37.3163,126.79,"4호선"),
    ("신길온천",37.3255,126.7768,"4호선"),("정왕",37.3384,126.733,"4호선"),
    ("오이도",37.3469,126.7133,"4호선"),
    # 5호선
    ("방화",37.5703,126.7971,"5호선"),("김포공항",37.5625,126.8008,"5호선"),
    ("마곡",37.5596,126.8279,"5호선"),("발산",37.5581,126.8385,"5호선"),
    ("화곡",37.5485,126.8546,"5호선"),("까치산",37.5459,126.8702,"5호선"),
    ("목동",37.5264,126.8745,"5호선"),("양평",37.528,126.9044,"5호선"),
    ("영등포구청",37.5262,126.8964,"5호선"),("신길",37.5084,126.9229,"5호선"),
    ("여의도",37.5215,126.9243,"5호선"),("공덕",37.544,126.9516,"5호선"),
    ("충정로",37.5598,126.9659,"5호선"),("광화문",37.5712,126.9769,"5호선"),
    ("종로3가",37.5704,126.992,"5호선"),("동대문역사문화공원",37.5651,127.0074,"5호선"),
    ("청구",37.5618,127.0178,"5호선"),("왕십리",37.5613,127.0368,"5호선"),
    ("군자",37.5613,127.0793,"5호선"),("천호",37.5388,127.1235,"5호선"),
    ("강동",37.53,127.1266,"5호선"),("고덕",37.5566,127.1733,"5호선"),
    ("상일동",37.5477,127.1847,"5호선"),("오금",37.5026,127.1302,"5호선"),
    ("마천",37.4946,127.1623,"5호선"),
    ("하남시청",37.5323,127.2093,"5호선"),("하남풍산",37.5425,127.2086,"5호선"),
    ("하남검단산",37.5258,127.2186,"5호선"),
    # 6호선
    ("응암",37.5993,126.9139,"6호선"),("연신내",37.619,126.9211,"6호선"),
    ("디지털미디어시티",37.5769,126.8901,"6호선"),("합정",37.5497,126.9143,"6호선"),
    ("공덕",37.544,126.9516,"6호선"),("효창공원앞",37.5378,126.9611,"6호선"),
    ("삼각지",37.5358,126.9734,"6호선"),("이태원",37.5345,126.9945,"6호선"),
    ("약수",37.5547,127.0128,"6호선"),("신당",37.5651,127.0193,"6호선"),
    ("동묘앞",37.5718,127.0185,"6호선"),("고려대",37.5887,127.0321,"6호선"),
    ("석계",37.6175,127.0697,"6호선"),("태릉입구",37.6253,127.0731,"6호선"),
    ("신내",37.6135,127.0955,"6호선"),
    # 7호선
    ("도봉산",37.6893,127.0455,"7호선"),("노원",37.6548,127.0566,"7호선"),
    ("태릉입구",37.6253,127.0731,"7호선"),("상봉",37.5971,127.085,"7호선"),
    ("군자",37.5613,127.0793,"7호선"),("건대입구",37.5403,127.07,"7호선"),
    ("청담",37.5225,127.0528,"7호선"),("강남구청",37.5175,127.0427,"7호선"),
    ("논현",37.5108,127.0237,"7호선"),("고속터미널",37.5047,127.0049,"7호선"),
    ("이수",37.4872,126.982,"7호선"),("대림",37.4924,126.896,"7호선"),
    ("남구로",37.4865,126.8852,"7호선"),("가산디지털단지",37.481,126.8829,"7호선"),
    ("철산",37.4739,126.8639,"7호선"),("온수",37.4928,126.8249,"7호선"),
    ("부천종합운동장",37.5088,126.8003,"7호선"),("신중동",37.5016,126.7752,"7호선"),
    ("부천시청",37.5033,126.7641,"7호선"),("부평구청",37.5075,126.7231,"7호선"),
    ("옥길",37.4746,126.8195,"7호선"),
    # 8호선
    ("암사",37.5531,127.1314,"8호선"),("천호",37.5388,127.1235,"8호선"),
    ("잠실",37.5133,127.1001,"8호선"),("문정",37.4874,127.1265,"8호선"),
    ("장지",37.4808,127.1256,"8호선"),("복정",37.4767,127.1492,"8호선"),
    ("모란",37.4373,127.1289,"8호선"),("단대오거리",37.4696,127.147,"8호선"),
    ("신흥",37.4538,127.147,"8호선"),("수진",37.4472,127.1453,"8호선"),
    ("별내별가람",37.676,127.1485,"8호선"),("다산",37.6143,127.1627,"8호선"),
    ("구리",37.5943,127.1397,"8호선"),
    # 9호선
    ("김포공항",37.5625,126.8008,"9호선"),("마곡나루",37.5608,126.8309,"9호선"),
    ("가양",37.5618,126.8544,"9호선"),("등촌",37.5567,126.8734,"9호선"),
    ("염창",37.5506,126.879,"9호선"),("당산",37.5338,126.9012,"9호선"),
    ("여의도",37.5215,126.9243,"9호선"),("노량진",37.5138,126.9426,"9호선"),
    ("동작",37.5027,126.9793,"9호선"),("고속터미널",37.5047,127.0049,"9호선"),
    ("신논현",37.5048,127.0253,"9호선"),("선정릉",37.51,127.0486,"9호선"),
    ("종합운동장",37.5104,127.0731,"9호선"),("석촌",37.505,127.1048,"9호선"),
    ("중앙보훈병원",37.517,127.1543,"9호선"),
    # 분당·수인선
    ("수원",37.2665,127.0005,"수인분당선"),("망포",37.2614,127.0448,"수인분당선"),
    ("기흥",37.2754,127.1158,"수인분당선"),("죽전",37.328,127.1148,"수인분당선"),
    ("오리",37.3515,127.1087,"수인분당선"),("미금",37.3602,127.1065,"수인분당선"),
    ("정자",37.3614,127.1095,"수인분당선"),("수내",37.374,127.1108,"수인분당선"),
    ("야탑",37.4108,127.1279,"수인분당선"),("모란",37.4373,127.1289,"수인분당선"),
    ("복정",37.4767,127.1492,"수인분당선"),("수원시청",37.2652,127.0265,"수인분당선"),
    ("신길온천",37.3255,126.7768,"수인분당선"),("정왕",37.3384,126.733,"수인분당선"),
    ("오이도",37.3469,126.7133,"수인분당선"),("인천",37.4736,126.6359,"수인분당선"),
    ("인천대입구",37.3466,126.7148,"수인분당선"),
    # 신분당선
    ("강남",37.4979,127.0276,"신분당선"),("양재",37.4843,127.0342,"신분당선"),
    ("판교",37.3946,127.1109,"신분당선"),("정자",37.3614,127.1095,"신분당선"),
    ("미금",37.3602,127.1065,"신분당선"),("동천",37.3414,127.0985,"신분당선"),
    ("수지구청",37.3217,127.0905,"신분당선"),("상현",37.2903,127.0521,"신분당선"),
    ("광교중앙",37.2799,127.0448,"신분당선"),("광교",37.2748,127.055,"신분당선"),
    # 경의중앙선
    ("행신",37.5905,126.8348,"경의중앙선"),("능곡",37.6244,126.8348,"경의중앙선"),
    ("디지털미디어시티",37.5769,126.8901,"경의중앙선"),
    ("홍대입구",37.5573,126.9246,"경의중앙선"),("용산",37.5298,126.9649,"경의중앙선"),
    ("왕십리",37.5613,127.0368,"경의중앙선"),("청량리",37.5805,127.0473,"경의중앙선"),
    ("구리",37.5943,127.1397,"경의중앙선"),("덕소",37.5889,127.233,"경의중앙선"),
    ("가좌",37.5717,126.9019,"경의중앙선"),
    # 경춘선
    ("갈매",37.6247,127.1476,"경춘선"),("별내",37.6476,127.1476,"경춘선"),
    ("퇴계원",37.6588,127.1697,"경춘선"),
    # 인천1호선
    ("계양",37.5503,126.7375,"인천1호선"),("갈산",37.4937,126.7212,"인천1호선"),
    ("부평구청",37.4975,126.7231,"인천1호선"),("부평",37.4897,126.7237,"인천1호선"),
    ("인천시청",37.4677,126.6789,"인천1호선"),("인천대입구",37.3466,126.7148,"인천1호선"),
    ("송도",37.3977,126.7794,"인천1호선"),
    # 김포골드라인
    ("김포공항",37.5625,126.8008,"김포골드라인"),("고촌",37.6054,126.7708,"김포골드라인"),
    ("사우",37.6154,126.7108,"김포골드라인"),("구래",37.6454,126.7308,"김포골드라인"),
    ("마산",37.6454,126.7508,"김포골드라인"),("장기",37.6654,126.7508,"김포골드라인"),
    ("운양",37.6754,126.7208,"김포골드라인"),
    # 의정부경전철
    ("의정부",37.5381,127.0475,"의정부경전철"),("민락",37.6081,127.0975,"의정부경전철"),
    # 대구
    ("반월당",35.8658,128.5957,"대구1·2호선"),("수성못",35.8499,128.636,"대구3호선"),
    ("용산",35.8568,128.566,"대구2호선"),("중앙로",35.8717,128.5957,"대구1호선"),
    # 대전
    ("대전역",36.3321,127.4347,"대전1호선"),("대전시청",36.3494,127.3847,"대전1호선"),
    # 광주
    ("상무",35.1551,126.8553,"광주1호선"),("광주송정",35.1399,126.7936,"광주1호선"),
    ("금남로4가",35.1464,126.9151,"광주1호선"),
    # 부산
    ("해운대",35.163,129.1637,"부산2호선"),("감전",35.157,128.9837,"부산2호선"),
    ("사상",35.1515,128.9924,"부산2호선"),("부산역",35.1146,129.0411,"부산1호선"),
    ("서면",35.1574,129.0592,"부산1·2호선"),
    ("재송",35.172,129.14,"부산2호선"),
    # SRT·GTX
    ("수서",37.488,127.1005,"3호선·SRT"),("동탄",37.2265,127.0797,"SRT·GTX-A"),
    ("평택지제",36.9952,127.0789,"SRT"),
    # 동해선
    ("태화강",35.5516,129.33,"동해선"),
]


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return R * 2 * math.asin(math.sqrt(a))


def find_nearest_station(lat, lon):
    best_name, best_line, best_dist = None, None, float('inf')
    for name, slat, slon, line in STATIONS:
        d = haversine(lat, lon, slat, slon)
        if d < best_dist:
            best_dist = d
            best_name = name
            best_line = line
    return best_name, best_line, round(best_dist, 2)


# ─────────────────────────────────────────────
# API 함수
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
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
.badge-subway { background:#e8f5e9; color:#1b5e20; }
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
.subway-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:6px 0; font-size:.85rem;
}
.subway-label { color:#6b7c8d; font-weight:500; }
.subway-value { color:#1b5e20; font-weight:700; }
.queue-item {
    background:#fff; border:1px solid #e0e0e0; border-radius:10px;
    padding:10px 14px; margin-bottom:8px; display:flex;
    justify-content:space-between; align-items:center;
}
.queue-item .q-addr { font-size:.85rem; font-weight:600; color:#1a2e3b; }
.queue-item .q-sub  { font-size:.76rem; color:#78909c; margin-top:2px; }
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


# ─────────────────────────────────────────────
# Session state 초기화
# ─────────────────────────────────────────────
defaults = {
    "last_coord": "",
    "preview": None,
    "queue": [],
    "batch_results": [],
    "queried": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# 좌표 입력 처리
# ─────────────────────────────────────────────
coord_input = st.text_input("coord", value="", key="coord_box", label_visibility="collapsed")

if coord_input and coord_input != st.session_state.last_coord:
    st.session_state.last_coord = coord_input
    st.session_state.queried = False
    try:
        lat, lng = map(float, coord_input.split(","))
        addr_doc = get_jibun_address(lat, lng)
        bjd_doc  = get_region_code(lat, lng)
        road_addr  = addr_doc.get("road_address") if addr_doc else None
        jibun_addr = addr_doc.get("address", {}) if addr_doc else {}

        # 가장 가까운 역 계산
        stn_name, stn_line, stn_dist = find_nearest_station(lat, lng)

        st.session_state.preview = {
            "road":     road_addr.get("address_name", "없음") if road_addr else "없음",
            "jibun":    jibun_addr.get("address_name", "없음"),
            "addr_doc": addr_doc,
            "bjd_doc":  bjd_doc,
            "lat":      lat,
            "lng":      lng,
            "stn_name": stn_name,
            "stn_line": stn_line,
            "stn_dist": stn_dist,
        }
    except Exception as e:
        st.session_state.preview = None


# ─────────────────────────────────────────────
# 레이아웃
# ─────────────────────────────────────────────
col_map, col_info = st.columns([6, 4], gap="medium")

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

with col_info:
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
        already = any(q["jibun"] == p["jibun"] for q in st.session_state.queue)

        st.markdown(f"""
        <div class="preview-box">
            <div class="addr-main">🏠 {p['road']}</div>
            <div class="addr-sub">지번: {p['jibun']}</div>
            <div class="subway-row" style="margin-top:8px;border-top:1px solid #bbdefb;padding-top:8px;">
                <span class="subway-label">🚇 가장 가까운 역</span>
                <span class="subway-value">{p['stn_name']}역 ({p['stn_line']}) · {p['stn_dist']}km</span>
            </div>
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
                        "lat":      p["lat"],
                        "lng":      p["lng"],
                        "stn_name": p["stn_name"],
                        "stn_line": p["stn_line"],
                        "stn_dist": p["stn_dist"],
                    })
                    st.session_state.preview = None
                    st.rerun()
            with c2:
                if st.button("✖ 건너뛰기", use_container_width=True):
                    st.session_state.preview = None
                    st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

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
                        <div class="q-sub">{item['jibun']} · 🚇 {item.get('stn_name','?')}역 {item.get('stn_dist','?')}km</div>
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


# ─────────────────────────────────────────────
# 일괄 조회 결과
# ─────────────────────────────────────────────
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

        # 지하철 정보
        stn_name = meta.get("stn_name", "-")
        stn_line = meta.get("stn_line", "-")
        stn_dist = meta.get("stn_dist", "-")

        with st.expander(
            f"🏢 {meta['road']}  |  {meta['jibun']}  |  🚇 {stn_name}역 {stn_dist}km",
            expanded=True
        ):
            # 지하철 정보 배너
            st.markdown(f"""
            <div style="background:#e8f5e9;border-radius:8px;padding:10px 16px;
                        margin-bottom:12px;display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.3rem">🚇</span>
                <div>
                    <span style="font-weight:700;color:#1b5e20;font-size:.95rem">
                        가장 가까운 역: {stn_name}역
                    </span>
                    <span style="margin-left:8px;font-size:.83rem;color:#388e3c">
                        {stn_line} · 직선거리 {stn_dist}km
                    </span>
                </div>
            </div>""", unsafe_allow_html=True)

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

                    # 지하철 정보도 카드에 추가
                    rows.append(
                        f"<div class='data-row'><span class='data-label'>가까운 역</span>"
                        f"<span class='data-value'>"
                        f"<span class='badge badge-subway'>🚇 {stn_name}역</span>"
                        f"</span></div>"
                    )
                    rows.append(
                        f"<div class='data-row'><span class='data-label'>직선거리</span>"
                        f"<span class='data-value'>{stn_dist}km ({stn_line})</span></div>"
                    )

                    st.markdown(f"""
                    <div class="info-card">
                        <h3>🏗️ {name} {kind_badge}</h3>
                        {"".join(rows)}
                    </div>""", unsafe_allow_html=True)
