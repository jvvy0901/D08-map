import json
import os
import sys

from dotenv import load_dotenv

from place import search_place

load_dotenv(override=True)

# 🔌 지도 SDK 주소 (JS 키는 config.js로만 전달. REST 키는 어디에도 넣지 않는다)
SDK = "https://dapi.kakao.com/v2/maps/sdk.js"  # 🔌 카카오 지도 JavaScript SDK

최대_마커 = 200

# map.html은 키도 데이터도 없는 고정 파일(깃에 올려도 안전). 키·데이터는 config.js, places.js 에서 읽는다.
HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>카카오 지도</title>
<style>
  body { font-family: sans-serif; margin: 16px; }
  #map { width: 100%; height: 520px; }
  .tip { color: #555; font-size: 14px; margin-top: 8px; }
  .info { padding: 6px 10px; font-size: 13px; min-width: 180px; }
  .info b { display: block; margin-bottom: 4px; }
</style>
</head>
<body>
<div id="map"></div>
<p class="tip">지도가 회색이면: ① 카카오맵 사용 설정 ② 지금 주소(포트까지) 등록 ③ 서버 주소로 열기</p>
<script src="config.js"></script>
<script src="places.js"></script>
<script>
function 지도그리기() {
  const 장소들 = window.PLACES || [];
  const map = new kakao.maps.Map(document.getElementById("map"), {
    center: new kakao.maps.LatLng(37.5665, 126.9780),
    level: 5,
  });
  const bounds = new kakao.maps.LatLngBounds();
  const info = new kakao.maps.InfoWindow({ removable: true });

  장소들.forEach(function (p) {
    const pos = new kakao.maps.LatLng(p.위도, p.경도);  // (위도, 경도) 순서
    const marker = new kakao.maps.Marker({ position: pos, map: map });
    bounds.extend(pos);
    kakao.maps.event.addListener(marker, "click", function () {
      const box = document.createElement("div");
      box.className = "info";
      const name = document.createElement("b");
      name.textContent = p.이름;
      const addr = document.createElement("span");
      addr.textContent = p.주소;
      box.appendChild(name);
      box.appendChild(addr);
      info.setContent(box);
      info.open(map, marker);
    });
  });

  if (장소들.length > 0) map.setBounds(bounds);  // 마커가 전부 보이게
}

if (!window.KAKAO_JS_KEY) {
  document.getElementById("map").textContent =
    "config.js가 없어요. python make_map.py 를 먼저 실행해 주세요.";
} else {
  const sdk = document.createElement("script");
  sdk.src = "__SDK__?appkey=" + encodeURIComponent(window.KAKAO_JS_KEY) + "&autoload=false";
  sdk.onload = function () { kakao.maps.load(지도그리기); };
  document.head.appendChild(sdk);
}
</script>
</body>
</html>
"""


def kakao_map(장소들, 파일="map.html"):
    """장소 목록 [{"이름", "주소", "위도", "경도"}, ...] 으로 마커 지도를 만든다.
    map.html(고정, 키 없음) + config.js(JS 키) + places.js(데이터)를 저장하고 map.html 이름을 돌려준다.
    JS 키가 없으면 '⛔'로 시작하는 RuntimeError."""
    js키 = os.getenv("KAKAO_JS_KEY")
    if not js키:
        raise RuntimeError("⛔ .env에 KAKAO_JS_KEY가 없어요")

    장소들 = 장소들[:최대_마커]
    폴더 = os.path.dirname(os.path.abspath(파일))
    with open(파일, "w", encoding="utf-8") as f:
        f.write(HTML.replace("__SDK__", SDK))
    with open(os.path.join(폴더, "config.js"), "w", encoding="utf-8") as f:
        f.write(f"window.KAKAO_JS_KEY = {json.dumps(js키)};\n")
    with open(os.path.join(폴더, "places.js"), "w", encoding="utf-8") as f:
        f.write(f"window.PLACES = {json.dumps(장소들, ensure_ascii=False)};\n")
    return 파일


if __name__ == "__main__":
    검색어 = input("검색어를 입력하세요 (예: 성수동 카페): ").strip()
    if not 검색어:
        sys.exit("검색어를 입력해 주세요")
    try:
        장소들 = search_place(검색어, 10)
        if not 장소들:
            sys.exit(f"'{검색어}'을(를) 찾지 못했어요")
        파일 = kakao_map(장소들)
    except RuntimeError as e:
        sys.exit(str(e))

    print(f"✅ {파일}, config.js, places.js 만들었어요 (마커 {len(장소들)}개)")
    print("\n열기: 이 폴더에서 아래 명령을 실행한 뒤 브라우저로 여세요.")
    print("  python -m http.server 8000 --bind 127.0.0.1")
    print("  http://localhost:8000/map.html")
    print("(카카오 콘솔 JavaScript SDK 도메인에 http://localhost:8000 이 등록돼 있어야 해요)")
    print("\n출처: 카카오 로컬 API (키워드로 장소 검색), 카카오 지도 JavaScript SDK")
