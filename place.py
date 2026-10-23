import os
import sys

import requests
from dotenv import load_dotenv

# 🔌 API 주소는 여기 한 곳에만
API = {
    "keyword": "https://dapi.kakao.com/v2/local/search/keyword.json",  # 🔌 키워드로 장소 검색
}

load_dotenv(override=True)


def search_place(검색어, 개수=5):
    """카카오 키워드 검색. [{"이름", "주소", "위도", "경도"}, ...] 를 돌려준다.
    실패하면 '⛔'로 시작하는 한국어 한 줄 메시지의 RuntimeError를 낸다."""
    키 = os.getenv("KAKAO_REST_API_KEY")
    if not 키:
        raise RuntimeError("⛔ .env에 KAKAO_REST_API_KEY가 없어요")

    try:
        res = requests.get(  # 🔌 API 호출
            API["keyword"],
            headers={"Authorization": f"KakaoAK {키}"},
            params={"query": 검색어, "size": 개수},
            timeout=10,
        )
    except requests.RequestException:
        raise RuntimeError("⛔ 카카오 서버에 연결하지 못했어요. 인터넷을 확인해 주세요") from None

    if res.status_code == 401:
        raise RuntimeError("⛔ 카카오 REST API 키가 틀렸어요")
    if res.status_code == 403:
        raise RuntimeError("⛔ 카카오맵 사용 설정을 켜 주세요")
    if res.status_code != 200:
        raise RuntimeError(f"⛔ 카카오 응답 오류 (상태 {res.status_code})")

    장소들 = []
    for d in res.json().get("documents", []):
        try:
            위도, 경도 = float(d["y"]), float(d["x"])
        except (KeyError, ValueError):
            continue
        if not (33 <= 위도 <= 39 and 124 <= 경도 <= 132):
            continue
        장소들.append({
            "이름": d["place_name"],
            "주소": d.get("road_address_name") or d.get("address_name", ""),
            "위도": 위도,
            "경도": 경도,
        })
    return 장소들


if __name__ == "__main__":
    검색어 = input("검색어를 입력하세요 (예: 성수동 카페): ").strip()
    if not 검색어:
        sys.exit("검색어를 입력해 주세요")
    try:
        결과 = search_place(검색어)
    except RuntimeError as e:
        sys.exit(str(e))

    if not 결과:
        sys.exit(f"'{검색어}'을(를) 찾지 못했어요")

    for i, p in enumerate(결과, 1):
        print(f"{i}. {p['이름']}")
        print(f"   주소: {p['주소']}")
        print(f"   좌표: ({p['위도']}, {p['경도']})")
    print("\n출처: 카카오 로컬 API (키워드로 장소 검색)")
