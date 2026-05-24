const CACHE_NAME = "cajaaldia-cache-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/index.html",
  "/logo-192.png",
  "/logo-512.png",
  "/favicon.ico",
  "/manifest.json"
];

// Instalar SW y precachear assets base
self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[Service Worker] Precaching base shell...");
      return cache.addAll(ASSETS_TO_CACHE);
    }).then(() => self.skipWaiting())
  );
});

// Activar y purgar cachés antiguas
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("[Service Worker] Clearing old cache:", key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Estrategia Network-First con fallback a Cache para consistencia con SPA
self.addEventListener("fetch", (e) => {
  // Solo procesar llamadas del mismo origen y evitar endpoints de API
  if (e.request.url.startsWith(self.location.origin) && !e.request.url.includes("/api/")) {
    e.respondWith(
      fetch(e.request)
        .then((response) => {
          // Si la respuesta es válida, clonarla y guardarla en la caché
          if (response && response.status === 200 && response.type === "basic") {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(e.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // Si falla la red, buscar en la caché
          return caches.match(e.request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Si es una navegación HTML, retornar index.html en caché (SPA fallback)
            if (e.request.headers.get("accept")?.includes("text/html")) {
              return caches.match("/index.html");
            }
          });
        })
    );
  }
});
