importScripts(
  "https://storage.googleapis.com/workbox-cdn/releases/6.4.1/workbox-sw.js"
);

const { registerRoute } = workbox.routing;
const { CacheFirst, NetworkFirst } = workbox.strategies;
const { CacheableResponsePlugin } = workbox.cacheableResponse;
const { ExpirationPlugin } = workbox.expiration;

// Cache name
workbox.core.setCacheNameDetails({
  prefix: "xbox-media",
  suffix: "v2",
  precache: "install-time",
  runtime: "run-time",
});

// Precaching
workbox.precaching.precacheAndRoute([
  { url: "/", revision: "1" },
  { url: "/home", revision: "1" },
  { url: "/media_page/1", revision: "1" },
  { url: "/static/manifest.json", revision: "1" },
  { url: "/static/icon-192x192.png", revision: "1" },
  { url: "/static/icon-512x512.png", revision: "1" },
]);

// Runtime caching
registerRoute(
  ({ request }) => {
    console.log(request);
    return request.destination === "jpeg";
  },
  new CacheFirst({
    cacheName: "images",
    plugins: [
      new ExpirationPlugin({
        maxEntries: 60,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 Days
      }),
    ],
  })
);

registerRoute(
  ({ request }) =>
    request.destination === "script" || request.destination === "style",
  new CacheFirst({
    cacheName: "static-resources",
  })
);

registerRoute(
  ({ url }) => url.pathname.startsWith("/static/"),
  async (options) => {
    console.log(`Request made for: ${options.request.url}`);
    return new NetworkFirst({
      cacheName: "static-cache", // Fixed typo in 'staic-cache'
      plugins: [
        new CacheableResponsePlugin({
          statuses: [0, 200],
        }),
      ],
    }).handle(options);
  }
);

// Push notifications
self.addEventListener("push", (event) => {
  const options = {
    body: event.data ? event.data.text() : "Default notification body",
    data: {
      url: "https://streamitnow.site/stream/20240921_020",
    },
  };

  event.waitUntil(
    self.registration.showNotification("Notification Title", options)
  );
});

// Notification click event
self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  event.waitUntil(
    clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clientList) => {
        const existingClient = clientList.find(
          (client) =>
            client.url === event.notification.data.url && "focus" in client
        );
        if (existingClient) {
          return existingClient.focus();
        } else {
          return clients.openWindow(event.notification.data.url);
        }
      })
  );
});

// Caching video streams (m3u8 and ts files)
registerRoute(
  ({ url }) =>
    url.pathname.startsWith("/static/") &&
    (url.pathname.endsWith(".m3u8") || url.pathname.endsWith(".ts")),
  new CacheFirst({
    cacheName: "video-cache",
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200],
      }),
      new ExpirationPlugin({
        maxEntries: 50, // Adjust as needed
        maxAgeSeconds: 60 * 60 * 24, // 1 Day
      }),
    ],
  })
);

self.addEventListener("fetch", (e) => {
  console.log(`[Service Worker] Fetched resource ${e.request.url}`);
});