/* Apenas o shell do app é pré-carregado.
 * O núcleo remoto de emulação ainda pode exigir conexão à internet.
 */
const CACHE = "gba-pocket-shell-v1";
const URLS = [
  "./", "./index.html", "./player.html", "./main.mjs",
  "./patch.mjs", "./manifest.webmanifest", "./icon.svg"
];
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(URLS)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", event => {
  event.waitUntil(Promise.all([
    caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith("gba-pocket-shell-") && k !== CACHE).map(k => caches.delete(k)))),
    self.clients.claim()
  ]));
});
self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || !url.pathname.includes("/app/")) return;
  if (request.mode === "navigate") {
    event.respondWith(fetch(request).then(response => {
      if (response.ok) {
        const copy = response.clone();
        caches.open(CACHE).then(c => c.put(request, copy)).catch(() => {});
      }
      return response;
    }).catch(() => caches.match(request).then(r => r || caches.match("./index.html"))));
  } else {
    event.respondWith(caches.match(request).then(cached => cached || fetch(request).then(response => {
      if (response.ok) {
        const copy = response.clone();
        caches.open(CACHE).then(c => c.put(request, copy)).catch(() => {});
      }
      return response;
    })));
  }
});
