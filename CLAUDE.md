# 教養日めくり

## 構成

- `src/data/<分野>-*.js`：各回の本文
- `src/ruby.js`：ふりがな辞書
- `src/images.json`：各回の図版
- `src/app.html`：ページ本体
- `node build.js` を実行すると、これらを埋め込んだ `kyoyo-himekuri.html` ができる。

## 回を追加するとき

- **図版も必ず付ける。** 本文と一緒に、その回に合う画像を Wikimedia Commons の自由ライセンス画像から選んで取り込む。手順と基準は `tools/images/README.md` にある。
  - 合う画像がない回は、`src/images-none.json` に理由を書く。
  - `node build.js` の「図版がなく…」という警告が出ないことを確かめる。
- **公開するとき**は、増えた・変わった `img/*.webp` も Artifact の `files` に含める。
- **ふりがな**：`node build.js` の警告（本文に出てこない語）を確かめて、ふりがな辞書を整える。
