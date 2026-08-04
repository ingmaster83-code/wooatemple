# -*- coding: utf-8 -*-
"""_rawdata/list_raw.json + detail_raw.json -> _data/temples.json"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST_SRC = ROOT / "_rawdata" / "list_raw.json"
DETAIL_SRC = ROOT / "_rawdata" / "detail_raw.json"
LIST_SRC_FAMOUS = ROOT / "_rawdata" / "list_raw_famous.json"
DETAIL_SRC_FAMOUS = ROOT / "_rawdata" / "detail_raw_famous.json"
OUT = ROOT / "_data" / "temples.json"

REGION_ALIAS = {
    "경기도": "경기", "경기": "경기",
    "인천광역시": "인천", "인천": "인천",
    "강원특별자치도": "강원", "강원도": "강원", "강원": "강원",
    "충청북도": "충북", "충북": "충북",
    "충청남도": "충남", "충남": "충남",
    "전북특별자치도": "전북", "전라북도": "전북", "전북": "전북",
    "전라남도": "전남", "전남": "전남",
    "경상북도": "경북", "경북": "경북",
    "경상남도": "경남", "경남": "경남",
    "대구광역시": "대구", "대구": "대구",
    "울산광역시": "울산", "울산": "울산",
    "부산광역시": "부산", "부산": "부산",
    "광주광역시": "광주", "광주": "광주",
    "세종특별자치시": "세종", "세종시": "세종", "세종": "세종",
    "대전광역시": "대전", "대전": "대전",
    "제주특별자치도": "제주", "제주도": "제주", "제주": "제주",
    "서울특별시": "서울", "서울": "서울",
}

REGION_SLUG = {
    "경기": "gyeonggi", "인천": "incheon", "강원": "gangwon",
    "충북": "chungbuk", "충남": "chungnam",
    "전북": "jeonbuk", "전남": "jeonnam",
    "경북": "gyeongbuk", "경남": "gyeongnam",
    "대구": "daegu", "울산": "ulsan", "부산": "busan",
    "광주": "gwangju", "세종": "sejong", "대전": "daejeon",
    "제주": "jeju", "서울": "seoul",
}

REGION_FULL = {
    "경기": "경기도", "인천": "인천광역시", "강원": "강원특별자치도",
    "충북": "충청북도", "충남": "충청남도",
    "전북": "전북특별자치도", "전남": "전라남도",
    "경북": "경상북도", "경남": "경상남도",
    "대구": "대구광역시", "울산": "울산광역시", "부산": "부산광역시",
    "광주": "광주광역시", "세종": "세종특별자치시", "대전": "대전광역시",
    "제주": "제주특별자치도", "서울": "서울특별시",
}

GWANGJU_CITY_HINTS = ("동구", "서구", "남구", "북구", "광산구")


def normalize_region(addr):
    if not addr:
        return None
    first = addr.split()[0]
    if first == "전남광주통합특별시":
        tokens = addr.split()
        city_token = tokens[1] if len(tokens) > 1 else ""
        if any(h in city_token for h in GWANGJU_CITY_HINTS):
            return "광주"
        return "전남"
    return REGION_ALIAS.get(first)


def extract_city(addr):
    tokens = addr.split()
    return tokens[1] if len(tokens) >= 2 else ""


def clean_address(addr, region):
    tokens = addr.split()
    if tokens and tokens[0] == "전남광주통합특별시":
        tokens[0] = REGION_FULL.get(region, tokens[0])
        return " ".join(tokens)
    return addr


def strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").strip()
    return text


def main():
    list_items = json.loads(LIST_SRC.read_text(encoding="utf-8"))
    details = json.loads(DETAIL_SRC.read_text(encoding="utf-8"))

    if LIST_SRC_FAMOUS.exists() and DETAIL_SRC_FAMOUS.exists():
        existing_ids = {it["contentid"] for it in list_items}
        famous_list = json.loads(LIST_SRC_FAMOUS.read_text(encoding="utf-8"))
        famous_details = json.loads(DETAIL_SRC_FAMOUS.read_text(encoding="utf-8"))
        added = 0
        for it in famous_list:
            if it["contentid"] not in existing_ids:
                list_items.append(it)
                added += 1
        details.update(famous_details)
        print(f"유명 사찰 보강: {added}곳 추가")

    region_seq = {}
    out = []
    skipped = 0

    for it in list_items:
        cid = it["contentid"]
        detail = details.get(cid, {})

        name = (it.get("title") or "").strip()
        addr = (detail.get("addr1") or it.get("addr1") or "").strip()
        if not name or not addr:
            skipped += 1
            continue

        region = normalize_region(addr)
        if not region:
            skipped += 1
            continue
        region_slug = REGION_SLUG[region]
        city = extract_city(addr)
        addr = clean_address(addr, region)

        region_seq[region_slug] = region_seq.get(region_slug, 0) + 1
        slug = f"{region_slug}-{region_seq[region_slug]:03d}"

        overview = strip_html(detail.get("overview", ""))
        image = detail.get("firstimage") or it.get("firstimage") or ""
        lat = detail.get("mapy") or it.get("mapy") or ""
        lng = detail.get("mapx") or it.get("mapx") or ""

        usetime = strip_html(detail.get("usetime") or "")
        restdate = strip_html(detail.get("restdate") or "")
        parking = (detail.get("parking") or "").strip()
        infocenter = strip_html(detail.get("infocenter") or "") or (detail.get("tel") or "")
        expguide = strip_html(detail.get("expguide") or "")

        out.append({
            "templeName": name,
            "region": region,
            "regionSlug": region_slug,
            "city": city,
            "address": addr,
            "lat": lat,
            "lng": lng,
            "slug": slug,
            "image": image,
            "overview": overview,
            "usetime": usetime,
            "restdate": restdate,
            "parking": parking if parking not in ("", "-") else "",
            "phone": infocenter,
            "expguide": expguide,
        })

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"총 {len(list_items)}건 중 {len(out)}개 저장, {skipped}개 스킵 -> {OUT}")

    region_count = {}
    for s in out:
        region_count[s["region"]] = region_count.get(s["region"], 0) + 1
    print("지역별:", region_count)


if __name__ == "__main__":
    main()
