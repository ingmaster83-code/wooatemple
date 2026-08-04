# -*- coding: utf-8 -*-
"""cat3=사찰 목록에서 누락된 유명 사찰 14곳을 contentId로 직접 보강 수집"""
import json
import os
import time
import urllib.request
import urllib.parse

API_KEY = "9490b1d34e92aa9e25b32a4cff1438fc7b9c71e5d332413916a391e867f61e86"
COMMON_URL = "https://apis.data.go.kr/B551011/KorService2/detailCommon2"
INTRO_URL = "https://apis.data.go.kr/B551011/KorService2/detailIntro2"
SCRIPT_DIR = os.path.dirname(__file__)
OUT_LIST = os.path.join(SCRIPT_DIR, "..", "_rawdata", "list_raw_famous.json")
OUT_DETAIL = os.path.join(SCRIPT_DIR, "..", "_rawdata", "detail_raw_famous.json")

FAMOUS = [
    ("126175", "해인사(합천)"),
    ("127923", "화엄사"),
    ("126148", "범어사(부산)"),
    ("126166", "경주 불국사 [유네스코 세계유산]"),
    ("126155", "직지사"),
    ("126170", "고운사(의성)"),
    ("126352", "내소사(부안)"),
    ("147548", "선운사(고창)"),
    ("126341", "백양사"),
    ("126507", "화계사(서울)"),
    ("126370", "미황사(해남)"),
    ("126361", "도갑사"),
    ("125759", "도피안사(철원)"),
    ("126153", "희방사(영주)"),
    ("126186", "통도사(양산)"),
    ("127669", "부석사 [유네스코 세계유산]"),
    ("126158", "봉정사 [유네스코 세계유산]"),
    ("125906", "보은 법주사 [유네스코 세계유산]"),
    ("126369", "선암사 [유네스코 세계유산]"),
    ("126371", "송광사(순천)"),
    ("126373", "대흥사(해남)"),
]

INTRO_FIELDS = [
    "infocenter", "opendate", "restdate", "expguide", "expagerange",
    "accomcount", "useseason", "usetime", "parking", "chkbabycarriage",
    "chkpet", "chkcreditcard",
]


def http_get_json(url, params, timeout=15):
    full = url + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(full, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_one(content_id):
    common = {}
    for attempt in range(3):
        try:
            data = http_get_json(COMMON_URL, {
                "serviceKey": API_KEY, "MobileOS": "ETC", "MobileApp": "wooahouse",
                "contentId": content_id, "_type": "json",
            })
            items = data["response"]["body"].get("items", "")
            if items:
                item = items["item"]
                if isinstance(item, list):
                    item = item[0] if item else {}
                common = {
                    "overview": item.get("overview", ""),
                    "tel": item.get("tel", ""),
                    "firstimage": item.get("firstimage", ""),
                    "addr1": item.get("addr1", ""),
                    "addr2": item.get("addr2", ""),
                    "mapx": item.get("mapx", ""),
                    "mapy": item.get("mapy", ""),
                }
            break
        except Exception as e:
            print(f"  common retry {content_id}: {e}")
            time.sleep(1.0)

    intro = {}
    for attempt in range(3):
        try:
            data = http_get_json(INTRO_URL, {
                "serviceKey": API_KEY, "MobileOS": "ETC", "MobileApp": "wooahouse",
                "contentId": content_id, "contentTypeId": "12", "_type": "json",
            })
            items = data["response"]["body"].get("items", "")
            if items:
                item = items["item"]
                if isinstance(item, list):
                    item = item[0] if item else {}
                intro = {k: item.get(k, "") for k in INTRO_FIELDS}
            break
        except Exception as e:
            print(f"  intro retry {content_id}: {e}")
            time.sleep(1.0)

    return content_id, {**common, **intro}


def main():
    list_items = []
    details = {}

    for cid, title in FAMOUS:
        _, info = fetch_one(cid)
        details[cid] = info
        list_items.append({
            "contentid": cid,
            "title": title,
            "addr1": info.get("addr1", ""),
            "firstimage": info.get("firstimage", ""),
            "mapx": info.get("mapx", ""),
            "mapy": info.get("mapy", ""),
        })
        print(f"{title} ({cid}) -> addr={info.get('addr1','')[:30]} overview_len={len(info.get('overview',''))}")
        time.sleep(0.3)

    with open(OUT_LIST, "w", encoding="utf-8") as f:
        json.dump(list_items, f, ensure_ascii=False, indent=2)
    with open(OUT_DETAIL, "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(list_items)} famous temples -> {OUT_LIST} / {OUT_DETAIL}")


if __name__ == "__main__":
    main()
