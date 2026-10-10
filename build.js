// 教養日めくり：src/app.html に src/data/*.js を埋め込んで kyoyo-himekuri.html（Artifact 用）と docs/（アプリ版）を生成し、データを検査する
const fs = require("fs");
const path = require("path");
const ROOT = __dirname;
const ORDER = ["phil", "hist", "sci", "soc", "art", "lit", "math", "drink", "eng", "bio"];
const dataDir = path.join(ROOT, "src/data");
const files = fs.readdirSync(dataDir).filter(f => f.endsWith(".js"))
  .sort((a, b) => ORDER.indexOf(a.split("-")[0]) - ORDER.indexOf(b.split("-")[0]) || a.localeCompare(b));

// 検査
const LESSONS = [];
for (const f of files) new Function("LESSONS", fs.readFileSync(path.join(dataDir, f), "utf8"))(LESSONS);
const ids = new Set(), errors = [];
for (const L of LESSONS) {
  const where = L.id || "(idなし)";
  if (ids.has(L.id)) errors.push(`${where}: id が重複`);
  ids.add(L.id);
  if (!ORDER.includes(L.field)) errors.push(`${where}: 不明な分野 ${L.field}`);
  for (const k of ["title", "lead", "think"]) if (typeof L[k] !== "string" || !L[k]) errors.push(`${where}: ${k} がない`);
  if (!Array.isArray(L.body) || L.body.length < 4) errors.push(`${where}: 本文が短い`);
  if (!Array.isArray(L.interp) || !L.interp.length) errors.push(`${where}: 解釈・諸説がない`);
  if (!L.quote || !L.quote.text || !L.quote.orig || !L.quote.type) errors.push(`${where}: 原典引用が不完全`);
  if (!Array.isArray(L.sources) || L.sources.length < 1) errors.push(`${where}: 出典がない`);
  (L.quiz || []).forEach((q, i) => { if (!(q.a >= 0 && q.a < q.c.length) || !q.e) errors.push(`${where}: 問${i + 1} が不正`); });
  if (!L.quiz || L.quiz.length !== 3) errors.push(`${where}: クイズは3問`);
}
if (errors.length) { console.error(errors.join("\n")); process.exit(1); }

// ふりがな辞書の検査：書式と、どの回にも出てこない語（綴りの誤り）を報告する
const rubySrc = fs.readFileSync(path.join(ROOT, "src/ruby.js"), "utf8");
const RUBY_SRC = new Function(rubySrc + "; return RUBY_SRC;")();
const allText = LESSONS.map(L => [L.title, L.lead, ...L.body, ...L.interp, L.quote.text, L.quote.orig, L.quote.note, L.think, ...L.quiz.flatMap(q => [q.q, ...q.c, q.e])].join("\n")).join("\n").replace(/<[^>]+>/g, "");
const rubyErr = [], unused = [];
for (const line of RUBY_SRC.split("\n").map(s => s.trim()).filter(Boolean)) {
  const [k, r] = [line.slice(0, line.indexOf(" ")), line.slice(line.indexOf(" ") + 1).trim()];
  if (!k || !r || line.indexOf(" ") < 0) rubyErr.push(`ふりがな辞書の書式: ${line}`);
  else if (r[0] !== "=" && !/^[ぁ-ゖァ-ヺー]+$/.test(r)) rubyErr.push(`よみが仮名でない: ${line}`);
  if (!allText.includes(k)) unused.push(k);
}
if (rubyErr.length) { console.error(rubyErr.join("\n")); process.exit(1); }
if (unused.length) console.warn("ふりがな辞書で本文に出てこない語:", unused.join(" "));

const data = `<script>\n${rubySrc}\n</script>\n` + files.map(f => `<script>\n${fs.readFileSync(path.join(dataDir, f), "utf8")}\n</script>`).join("\n");
const html = fs.readFileSync(path.join(ROOT, "src/app.html"), "utf8").replace("<!--DATA-->", () => data);
fs.writeFileSync(path.join(ROOT, "kyoyo-himekuri.html"), html);

// アプリ版（PWA）：docs/ に出力し、GitHub Pages でそのまま公開できるようにする
const pwa = path.join(ROOT, "src/pwa"), out = path.join(ROOT, "docs");
const body = html.replace(/^<meta charset="utf-8">\n<title>[^<]*<\/title>\n/, "");
if (body === html) { console.error("src/app.html の先頭が想定と違うため、アプリ版を作れません"); process.exit(1); }
const page = fs.readFileSync(path.join(pwa, "shell-head.html"), "utf8") + body + fs.readFileSync(path.join(pwa, "shell-foot.html"), "utf8");
const version = require("crypto").createHash("sha256").update(page).digest("hex").slice(0, 12);
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out);
fs.writeFileSync(path.join(out, "index.html"), page);
fs.writeFileSync(path.join(out, "sw.js"), fs.readFileSync(path.join(pwa, "sw.js"), "utf8").replace("__VERSION__", version));
for (const f of ["manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"]) fs.copyFileSync(path.join(pwa, f), path.join(out, f));
fs.writeFileSync(path.join(out, ".nojekyll"), "");
const by = {}; for (const L of LESSONS) by[L.field] = (by[L.field] || 0) + 1;
console.log(`OK: ${LESSONS.length} 回`, by, `${(Buffer.byteLength(html) / 1024).toFixed(0)} KB`, `アプリ版 docs/（版 ${version}）`);
