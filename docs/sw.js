/* 教養日めくり：オフライン用の Service Worker。VERSION はビルドのたびに変わり、新しい版を取り込む */
const VERSION = "7613a647d058";
const CACHE = "kyoyo-" + VERSION;
const FONTS = "kyoyo-fonts";
const CORE = ["./", "index.html", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE && k !== FONTS).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  // Google Fonts：手元の控えをすぐ返し、裏で新しいものに入れ替える
  if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") {
    e.respondWith(caches.open(FONTS).then(async c => {
      const hit = await c.match(req);
      const net = fetch(req).then(r => { if (r.ok || r.type === "opaque") c.put(req, r.clone()); return r; }).catch(() => hit);
      return hit || net;
    }));
    return;
  }
  if (url.origin !== location.origin) return;
  // ページ本体と付属ファイル：この版の控えを優先し、なければ取りに行く
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(req.mode === "navigate" ? "index.html" : req, { ignoreSearch: true });
    return hit || fetch(req);
  }));
});
