# 教養日めくり

十の分野（哲学・歴史・自然科学・社会科学・芸術・言語と文学・数学と統計・酒の歴史と雑学・英語の歴史と雑学・動物と植物）の教養を、1回15分で学ぶページです。

- `src/app.html` … ページ本体（書架・今日の一枚・閲覧画面）
- `src/data/<分野>-*.js` … 各回のデータ。1回ごとに本文・解釈と諸説・原典の引用・クイズ3問・考える問い・出典をもつ
- `src/ruby.js` … 難読語のふりがな辞書（「語 よみ」を1行に1語）。閲覧画面では、各ステップで初出の語にだけふりがなを付ける
- `src/pwa/` … アプリ版（PWA）の外枠・Service Worker・マニフェスト・アイコン（`icon-source.html` はアイコンの元絵）
- `build.js` … データを検査し、`kyoyo-himekuri.html`（Artifact 用）と `docs/`（アプリ版）を出力する

```
node build.js
```

回を追加するときは `src/data/` のファイルに `LESSONS.push({...})` の形で書き足し、`node build.js` を実行します。

難読語を見つけたら `src/ruby.js` に1行足して `node build.js` を実行します。本文に出てこない語は警告されます。

## アプリ版（PWA）

`node build.js` を実行すると `docs/` にアプリ版ができます。ホーム画面に追加でき、一度開いた後はオフラインでも読めます。

GitHub Pages で公開する手順：

1. リポジトリの Settings → Pages を開く
2. Build and deployment の Source を「Deploy from a branch」にする
3. Branch に公開したいブランチを選び、フォルダを `/docs` にして Save
4. 数分後に表示される URL（`https://<ユーザー名>.github.io/<リポジトリ名>/`）を開く

ホーム画面への追加：iPhone は Safari の共有ボタン →「ホーム画面に追加」、Android は Chrome のメニュー →「アプリをインストール」（または「ホーム画面に追加」）。

記録とメモは、開いた場所（Artifact とアプリ版など）ごとに別々に保存されます。「Claude と深める」欄は Artifact 上でだけ使え、アプリ版では表示されません。
