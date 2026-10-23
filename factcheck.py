import re
import sys
import time

from place import search_place

파일 = "1.txt"
최대_줄 = 30  # 쿼터·예절: 한 번에 30줄까지만


def 파일_읽기(경로):
    """utf-8-sig → cp949 순서로 시도해 읽고, 어떤 인코딩인지 출력한다."""
    for 인코딩 in ("utf-8-sig", "cp949"):
        try:
            with open(경로, encoding=인코딩) as f:
                글 = f.read()
            print(f"읽은 인코딩: {인코딩}")
            return 글
        except UnicodeDecodeError:
            continue
    sys.exit(f"⛔ {경로}를 읽지 못했어요 (인코딩 확인)")


def 줄_해석(줄):
    """한 줄 → (이름, 주소). 줄 앞 번호·불릿·표 기호를 떼고, '|' 가 있으면 '|' 로, 없으면 첫 ': ' 로 나눈다."""
    줄 = 줄.strip()
    줄 = re.sub(r"^[\s|•·\-*]+", "", 줄)          # 불릿·표 기호
    줄 = re.sub(r"^\d+\s*[.)]\s*", "", 줄)         # 1. 2) 같은 번호
    줄 = 줄.strip(" |")
    if not 줄 or re.fullmatch(r"[\s|:\-]+", 줄):    # | --- | 같은 구분선
        return None
    if "|" in 줄:
        이름, _, 주소 = 줄.partition("|")
    elif ":" in 줄:
        이름, _, 주소 = 줄.partition(":")
    else:
        return None
    이름, 주소 = 이름.strip(), 주소.strip(" |")
    if not 이름 or not 주소:
        return None
    return 이름, 주소


def 주소_조각(주소):
    """주소 → 첫 단어(서울특별시/서울)를 뺀 조각들. 예: ['강남구', '역삼로', '3']"""
    조각 = 주소.replace(",", " ").split()
    return 조각[1:] if 조각 else []


def 이름_정리(이름):
    return re.sub(r"[\s·\-_.,&()]", "", 이름).lower()


def 이름_같음(a, b):
    a, b = 이름_정리(a), 이름_정리(b)
    return bool(a and b) and (a == b or a in b or b in a)


def 주소_맞음(원래, 찾은):
    """구가 같고, 길(도로명)이 있으면 길도 같아야 한다. 찾은 주소가 지번(동)이면 구만 비교한다."""
    가, 나 = 주소_조각(원래), 주소_조각(찾은)
    if len(가) < 2 or len(나) < 2 or 가[0] != 나[0]:
        return False
    길 = lambda t: bool(re.search(r"(로|길)\d*(길)?$", t))
    if 길(가[1]) and 길(나[1]):
        return 가[1] == 나[1]
    return True


def 판정(이름, 주소):
    """(기호, 설명) 을 돌려준다. 키·연결 에러는 RuntimeError('⛔...')."""
    조각 = 주소_조각(주소)
    동네 = 조각[0] if 조각 else ""
    후보들 = search_place(f"{동네} {이름}".strip(), 15)
    이름_같은곳 = [p for p in 후보들 if 이름_같음(이름, p["이름"])]
    if not 이름_같은곳:
        return "❌", "못 찾음"
    for p in 이름_같은곳:
        if 주소_맞음(주소, p["주소"]):
            return "✅", f"{p['이름']} / {p['주소']}"
    p = 이름_같은곳[0]
    return "🟡", f"이름은 있음: {p['이름']} / 카카오 주소: {p['주소']}"


if __name__ == "__main__":
    줄들 = [해석 for 해석 in map(줄_해석, 파일_읽기(파일).splitlines()) if 해석]
    print(f"읽은 줄 수: {len(줄들)}")
    if not 줄들:
        sys.exit("읽을 줄이 없어요")
    if len(줄들) > 최대_줄:
        print(f"⚠️ {최대_줄}줄까지만 확인해요")
        줄들 = 줄들[:최대_줄]

    개수 = {"✅": 0, "🟡": 0, "❌": 0}
    print()
    for i, (이름, 주소) in enumerate(줄들, 1):
        try:
            기호, 설명 = 판정(이름, 주소)
        except RuntimeError as e:
            print(str(e))
            break
        개수[기호] += 1
        print(f"{i}. {기호} {이름} | {주소}")
        print(f"     {설명}")
        time.sleep(0.1)

    확인 = sum(개수.values())
    if 확인:
        틀림 = 개수["🟡"] + 개수["❌"]
        print(f"\n확인한 곳 {확인}개: ✅ {개수['✅']} · 🟡 {개수['🟡']} · ❌ {개수['❌']}")
        print(f"AI 실수율 = (🟡 {개수['🟡']} + ❌ {개수['❌']}) / {확인} = {틀림 / 확인:.0%}")
        print("검산: 카카오 키워드 검색 '구 + 이름' 15건 중 이름이 같고(공백·기호 무시, 포함 허용) 구·길이 같으면 ✅")
    print("\n출처: 카카오 로컬 API (키워드로 장소 검색)")
