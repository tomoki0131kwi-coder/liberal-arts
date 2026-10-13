#!/usr/bin/env python3
"""tools/images/picks/*.json の選定結果から画像を取得し、img/<回id>.webp と src/images.json を更新する。

使い方:
  python3 tools/images/fetch.py            # 選定結果のうち、まだ取り込んでいない回だけ
  python3 tools/images/fetch.py id1 id2    # 指定した回だけ

picks/*.json は [{"id", "files": [{"title": "File:…", "caption": "日本語の説明"}], "alt": "代替テキスト"}]。
ファイル名の順に読み、同じ回が複数あれば後のファイルが優先する（差し替えは新しいファイルに書く）。
files が空なら、その回の画像を外す（理由は src/images-none.json に書く）。
files は上から順に試し、ライセンスが自由（common.ok_license）で取得できた最初の一枚を使う。

Wikimedia は、キャッシュにない縮小画像の生成を強く制限する（429）。そのため
1280・960・500・330px の縮小画像と原寸を順に試し、すべて 429 なら retry-after だけ待つ。
"""
import glob, io, json, os, sys, time, urllib.error
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, HERE, api, get, norm, ok_license, strip_html

Image.MAX_IMAGE_PIXELS = None
MAXW = 800
CACHE = os.path.join(HERE, ".cache", "meta.json")
OUT = os.path.join(ROOT, "src", "images.json")


def load_picks():
    picks = {}
    for f in sorted(glob.glob(os.path.join(HERE, "picks", "*.json"))):
        for c in json.load(open(f)):
            picks[c["id"]] = c
    return picks


def query_meta(titles, meta):
    todo = [t for t in titles if t not in meta]
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        d = api({"action": "query", "prop": "imageinfo", "redirects": 1, "titles": "|".join(batch),
                 "iiprop": "url|size|mime|extmetadata",
                 "iiextmetadatafilter": "LicenseShortName|License|LicenseUrl|Artist|Credit|NonFree"})
        q = d.get("query", {})
        alias = {n["to"]: n["from"] for n in q.get("normalized", [])}
        for n in q.get("redirects", []):
            alias[n["to"]] = alias.get(n["from"], n["from"])
        for p in q.get("pages", {}).values():
            orig = alias.get(p["title"], p["title"])
            orig = alias.get(orig, orig)
            info = (p.get("imageinfo") or [None])[0]
            meta[norm(orig)] = {"missing": True} if not info else {
                "title": p["title"], "url": info["url"].split("?", 1)[0], "page": info["descriptionurl"],
                "w": info["width"], "h": info["height"], "mime": info["mime"], "m": info.get("extmetadata", {})}
        for t in batch:
            meta.setdefault(t, {"missing": True})
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        json.dump(meta, open(CACHE, "w"), ensure_ascii=False)
        time.sleep(3)


def download(m):
    url = m["url"]
    name = url.rsplit("/", 1)[1]
    base = url.replace("/wikipedia/commons/", "/wikipedia/commons/thumb/", 1)

    def thumb(px):
        if m["mime"] == "image/svg+xml":
            return f"{base}/{px}px-{name}.png"
        if m["mime"] == "image/tiff":
            return f"{base}/lossy-page1-{px}px-{name}.jpg"
        return f"{base}/{px}px-{name}" if m["w"] > px else url

    srcs = []
    for px in (1280, 960, 500, 330):
        if thumb(px) not in srcs:
            srcs.append(thumb(px))
    if m["mime"] in ("image/jpeg", "image/png", "image/gif", "image/webp") and m["w"] * m["h"] <= 25e6 and url not in srcs:
        srcs.append(url)
    for rnd in range(6):
        waits = []
        for src in srcs:
            try:
                return get(src, tries=1)
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    waits.append(int(e.headers.get("retry-after") or 60))
            except Exception as e:
                print(f"    {e}", flush=True)
            time.sleep(1)
        if not waits:
            break
        w = min(waits) + 60
        print(f"    すべて 429。{w} 秒待つ（{rnd + 1} 回目）", flush=True)
        time.sleep(w)
    raise RuntimeError("取得できない")


def main(only):
    picks = load_picks()
    out = json.load(open(OUT)) if os.path.exists(OUT) else {}
    meta = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    ids = [i for i in picks if not only or i in only]
    query_meta(sorted({norm(x["title"]) for i in ids for x in picks[i]["files"]}), meta)
    report = []
    for lid in ids:
        c, cur = picks[lid], out.get(lid)
        if not c["files"]:
            if cur:
                if os.path.exists(os.path.join(ROOT, cur["file"])):
                    os.remove(os.path.join(ROOT, cur["file"]))
                del out[lid]
                print(f"  外した {lid}", flush=True)
            continue
        if cur and os.path.exists(os.path.join(ROOT, cur["file"])):
            same = [x for x in c["files"] if norm(x["title"]) == cur["title"]]
            if same:  # 取り込み済み。説明文だけ変わっていれば書き換える
                cur["caption"], cur["alt"] = same[0]["caption"], c.get("alt", "")
                continue
        chosen = None
        for x in c["files"]:
            m = meta.get(norm(x["title"]))
            if not m or m.get("missing"):
                report.append(f"{lid}: Commons にない {x['title']}")
            elif not ok_license(m["m"]):
                report.append(f"{lid}: ライセンス不可 {m['m'].get('LicenseShortName', {}).get('value')} {x['title']}")
            else:
                chosen = (x, m)
                break
        if not chosen:
            report.append(f"{lid}: 使える画像なし")
            continue
        x, m = chosen
        try:
            im = Image.open(io.BytesIO(download(m)))
            im.draft("RGB", (1600, 1600))
            im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
            if im.mode == "RGBA":
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[3])
                im = bg
            if im.width > MAXW:
                im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
            fn = f"img/{lid}.webp"
            im.save(os.path.join(ROOT, fn), "WEBP", quality=70, method=6)
        except Exception as e:
            report.append(f"{lid}: 取得に失敗 {e}")
            continue
        mm = m["m"]
        artist = strip_html(mm.get("Artist", {}).get("value", "")) or strip_html(mm.get("Credit", {}).get("value", ""))
        if len(artist) > 90:
            artist = artist[:88] + "…"
        out[lid] = {"file": fn, "w": im.width, "h": im.height, "alt": c.get("alt", ""), "caption": x["caption"],
                    "artist": artist, "license": strip_html(mm.get("LicenseShortName", {}).get("value", "")),
                    "licenseUrl": mm.get("LicenseUrl", {}).get("value", ""), "page": m["page"], "title": m["title"]}
        json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
        print(f"  保存 {lid}（幅 {im.width}px）", flush=True)
        time.sleep(4)
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("\n".join(report) or "問題なし")
    print(f"図版 {len(out)} 枚")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
