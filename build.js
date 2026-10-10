// 教養日めくり：src/app.html に src/data/*.js を埋め込んで kyoyo-himekuri.html を生成し、データを検査する
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

const data = files.map(f => `<script>\n${fs.readFileSync(path.join(dataDir, f), "utf8")}\n</script>`).join("\n");
const html = fs.readFileSync(path.join(ROOT, "src/app.html"), "utf8").replace("<!--DATA-->", () => data);
fs.writeFileSync(path.join(ROOT, "kyoyo-himekuri.html"), html);
const by = {}; for (const L of LESSONS) by[L.field] = (by[L.field] || 0) + 1;
console.log(`OK: ${LESSONS.length} 回`, by, `${(Buffer.byteLength(html) / 1024).toFixed(0)} KB`);
