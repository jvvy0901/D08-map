import os
import sys

import requests
from dotenv import load_dotenv

# 🔌 API 주소는 여기 한 곳에만
API = {
    "addr2coord": "https://dapi.kakao.com/v2/local/search/address.json",  # 🔌 주소로 좌표 변환
    "coord2addr": "https://dapi.kakao.com/v2/local/geo/coord2address.json",  # 🔌 좌표로 주소 변환
}

load_dotenv(override=True)


def _카카오_get(주소, params):
    """카카오 로컬 API 공통 호출. 실패하면 '⛔'로 시작하는 RuntimeError를 낸다."""
    키 = os.getenv("KAKAO_REST_API_KEY")
    if not 키:
        raise RuntimeError("⛔ .env에 KAKAO_REST_API_KEY가 없어요")

    try:
        res = requests.get(  # 🔌 API 호출
            주소,
            headers={"Authorization": f"KakaoAK {키}"},
            params=params,
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
    return res.json().get("documents", [])


def address_to_coord(주소):
    """주소 글자 → (위도, 경도). 찾지 못하면 None.
    카카오 x=경도, y=위도 (글자) → float()로 바꿔 (위도, 경도) 순서로 돌려준다."""
    문서들 = _카카오_get(API["addr2coord"], {"query": 주소})
    if not 문서들:
        return None
    try:
        위도, 경도 = float(문서들[0]["y"]), float(문서들[0]["x"])
    except (KeyError, ValueError):
        return None
    if not (33 <= 위도 <= 39 and 124 <= 경도 <= 132):
        return None
    return 위도, 경도


def coord_to_address(위도, 경도):
    """(위도, 경도) → 도로명 주소, 도로명이 없으면 지번 주소. 찾지 못하면 None."""
    if not (33 <= 위도 <= 39 and 124 <= 경도 <= 132):
        return None
    문서들 = _카카오_get(API["coord2addr"], {"x": 경도, "y": 위도})  # 요청은 x=경도, y=위도
    if not 문서들:
        return None
    도로명 = 문서들[0].get("road_address") or {}  # 도로명 칸은 null일 수 있음
    지번 = 문서들[0].get("address") or {}
    return 도로명.get("address_name") or 지번.get("address_name") or None


if __name__ == "__main__":
    입력주소 = input("주소를 입력하세요 (예: 서울 성동구 왕십리로 83-21): ").strip()
    if not 입력주소:
        sys.exit("주소를 입력해 주세요")
    try:
        좌표 = address_to_coord(입력주소)
        if 좌표 is None:
            sys.exit(f"'{입력주소}'을(를) 찾지 못했어요")
        위도, 경도 = 좌표
        print(f"1) 주소 → 좌표: ({위도}, {경도})")

        다시주소 = coord_to_address(위도, 경도)
    except RuntimeError as e:
        sys.exit(str(e))

    if 다시주소 is None:
        sys.exit("이 좌표의 주소를 찾지 못했어요")
    print(f"2) 좌표 → 주소: {다시주소}")
    print("\n출처: 카카오 로컬 API (주소로 좌표 변환 · 좌표로 주소 변환)")
