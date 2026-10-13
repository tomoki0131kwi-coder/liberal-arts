#!/usr/bin/env python3
"""取り込んだ画像を一覧画像（コンタクトシート）にして、目視確認しやすくする。

使い方:
  python3 tools/images/sheet.py 出力.jpg id1 id2 …   # 指定した回（省略時はすべて。36枚ずつ 出力-1.jpg …）
"""
import json, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT

d = json.load(open(os.path.join(ROOT, "src", "images.json")))
out, ids = sys.argv[1], [i for i in (sys.argv[2:] or sorted(d)) if i in d]
cw, ch, cols = 260, 230, 6
for n in range(0, len(ids), 36):
    part = ids[n:n + 36]
    rows = (len(part) + cols - 1) // cols
    sh = Image.new("RGB", (cw * cols, ch * rows), "white")
    dr = ImageDraw.Draw(sh)
    for k, i in enumerate(part):
        im = Image.open(os.path.join(ROOT, d[i]["file"]))
        im.thumbnail((cw - 10, ch - 28))
        x, y = (k % cols) * cw, (k // cols) * ch
        sh.paste(im, (x + 5, y + 3))
        dr.text((x + 5, y + ch - 22), i[:38], fill="black")
    path = out if len(ids) <= 36 else out.replace(".jpg", f"-{n // 36 + 1}.jpg")
    sh.save(path, quality=80)
    print(path, len(part))
