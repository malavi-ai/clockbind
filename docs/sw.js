// ClockBind offline service worker. VERSION and FILES are filled in by webapp/build.py (content hash),
// so every new release replaces the cache automatically.
const VERSION = "clockbind-1.3.0-2aa653d33f";
const FILES = ["./", "fonts/IBMPlexMono-Medium.woff2", "fonts/IBMPlexMono-Regular.woff2", "fonts/IBMPlexSans-Medium.woff2", "fonts/IBMPlexSans-Regular.woff2", "fonts/IBMPlexSans-SemiBold.woff2", "fonts/LICENSE-IBM-Plex.txt", "fonts/LICENSE-Newsreader.txt", "fonts/LICENSE-Vazirmatn.txt", "fonts/Newsreader-latin-ext.woff2", "fonts/Newsreader-latin.woff2", "fonts/Vazirmatn-arabic-400.woff2", "fonts/Vazirmatn-arabic-500.woff2", "fonts/Vazirmatn-arabic-700.woff2", "icon-180.png", "icon-192.png", "icon-512.png", "index.html", "manifest.webmanifest", "xlsx.full.min.js"];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(FILES.map((f) => new Request(f, { cache: "reload" })))));
  self.skipWaiting();
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSION).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;  // never touches other sites
  if (req.mode === "navigate") {  // pages: network first (fresh when online), cache when offline
    e.respondWith(fetch(req).then((r) => { const c = r.clone(); caches.open(VERSION).then((x) => x.put("./", c)); return r; })
      .catch(() => caches.match("./").then((r) => r || caches.match("index.html"))));
    return;
  }
  e.respondWith(caches.match(req, { ignoreSearch: true }).then((hit) => hit || fetch(req)));  // files: cache first
});
