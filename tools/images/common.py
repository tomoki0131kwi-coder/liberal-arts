"""図版の取得で共通に使う部品：Wikimedia Commons への問い合わせと、ライセンスの判定。

Wikimedia のロボット方針（https://wikitech.wikimedia.org/wiki/Robot_policy）に従い、
連絡先入りの User-Agent を付け、一度に一つずつ要求し、429 には retry-after だけ待つ。
"""
import gzip, html, json, os, re, sys, time, urllib.error, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://commons.wikimedia.org/w/api.php"
UA = "KyoyoHimekuriBot/1.0 (personal study page; tomoki0131kwi@gmail.com) python-urllib"


def get(url, tries=8):
    """URL を取得する。429・5xx は retry-after だけ待って再試行し、最後の試行では待たずに例外を投げる。"""
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                return gzip.decompress(body) if r.headers.get("Content-Encoding") == "gzip" else body
        except urllib.error.HTTPError as e:
            if (e.code == 429 or e.code >= 500) and i < tries - 1:
                wait = int(e.headers.get("retry-after") or 20) + 2
                print(f"  {e.code} wait {wait}s", file=sys.stderr, flush=True)
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            if i == tries - 1:
                raise
            print(f"  err {e} retry", file=sys.stderr, flush=True)
            time.sleep(10)
    raise RuntimeError("gave up: " + url)


def api(params):
    import urllib.parse
    return json.loads(get(API + "?" + urllib.parse.urlencode({"format": "json", **params})))


def norm(t):
    t = t.strip().replace("_", " ")
    if not t.lower().startswith("file:"):
        t = "File:" + t
    return "File:" + t[5:].strip()


def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def ok_license(m):
    """パブリックドメイン・CC0・CC BY・CC BY-SA（と同等の自由ライセンス）だけを通す。NC・ND・フェアユースは不可。"""
    lic = (m.get("LicenseShortName", {}).get("value", "") + " " + m.get("License", {}).get("value", "")).lower()
    if m.get("NonFree", {}).get("value") in ("true", True):
        return False
    if re.search(r"\bnc\b|non-?commercial|\bnd\b|no-?deriv|fair use|non-?free|copyrighted", lic):
        return False
    return bool(re.search(r"public domain|\bpd\b|^pd|pd-|cc0|cc[- ]by|attribution|gfdl|free art|ogl|kogl|etalab", lic))


def load_lessons():
    """src/data/*.js の回を node で読み出す（id → {field, title, lead, body}）。"""
    import subprocess
    js = r"""
const fs=require("fs"),path=require("path");const L=[];const dir=path.join(process.argv[1],"src/data");
for(const f of fs.readdirSync(dir).filter(f=>f.endsWith(".js")).sort()) new Function("LESSONS",fs.readFileSync(path.join(dir,f),"utf8"))(L);
const s=t=>String(t||"").replace(/<[^>]+>/g,"");const o={};for(const l of L)o[l.id]={field:l.field,title:s(l.title),lead:s(l.lead),body:l.body.map(s)};
process.stdout.write(JSON.stringify(o));"""
    return json.loads(subprocess.check_output(["node", "-e", js, ROOT]))
