#!/usr/bin/env python3
"""回ごとの検索語で Wikimedia Commons を検索し、自由ライセンスの画像候補を書き出す。

使い方:
  python3 tools/images/search.py 検索語.json 候補.json

検索語.json は {"回id": ["英語の検索語", ...], ...}。
候補.json には回ごとに {title, w, h, license, desc} の一覧が入る。これを見て選び、picks/ に選定結果を書く。
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import api, ok_license, strip_html


def main(qpath, out):
    queries = json.load(open(qpath))
    res = json.load(open(out)) if os.path.exists(out) else {}
    for n, (lid, qs) in enumerate(queries.items(), 1):
        if lid in res:
            continue
        cands, seen = [], set()
        for q in qs[:3]:
            d = api({"action": "query", "generator": "search", "gsrnamespace": 6, "gsrlimit": 10,
                     "gsrsearch": q + " filetype:bitmap", "prop": "imageinfo", "iiprop": "size|mime|extmetadata",
                     "iiextmetadatafilter": "LicenseShortName|License|NonFree|ImageDescription"})
            for p in sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
                info = (p.get("imageinfo") or [None])[0]
                if not info or p["title"] in seen:
                    continue
                seen.add(p["title"])
                m = info.get("extmetadata", {})
                if not ok_license(m) or info["mime"] not in ("image/jpeg", "image/png", "image/tiff") or info["width"] < 400:
                    continue
                cands.append({"title": p["title"], "q": q, "w": info["width"], "h": info["height"],
                              "license": strip_html(m.get("LicenseShortName", {}).get("value", "")),
                              "desc": strip_html(m.get("ImageDescription", {}).get("value", ""))[:160]})
            time.sleep(2)
        res[lid] = cands[:10]
        json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
        print(f"  {n}/{len(queries)} {lid}: {len(cands)}", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:3])
