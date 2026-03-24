def get_parcel_polygon(lat, lng):
    # 1. API 키 공백 제거
    clean_key = VWORLD_KEY.strip()
    
    # 2. 가장 안정적인 Data API(GetFeature) 사용
    url = "https://api.vworld.kr/req/data"
    
    params = {
        "service": "data",
        "request": "GetFeature",
        "data": "lp_pa_cbnd_bubun", # 지적도 레이어
        "key": clean_key,
        "geomFilter": f"POINT({lng} {lat})",
        "geometry": "true",
        "attribute": "true",
        "crs": "EPSG:4326",
        "domain": "s1map-tool.streamlit.app" # 등록된 실제 도메인
    }
    
    # 3. 중요: 브이월드 방화벽을 통과하기 위한 헤더 (User-Agent와 Referer 필수)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
                
    except Exception as e:
        # 에러 메시지를 좀 더 명확하게 표시
        return None, f"연결 실패: 브이월드 서버 IP 차단 가능성 ({str(e)[:30]})"
