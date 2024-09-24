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
    return request.destination === "image";
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



// Push notifications
self.addEventListener("push", (event) => {
  if (event.data) {
    const data = JSON.parse(event.data.text());
    const options = {
      body: data.body,
      icon: "/static/icon-192x192.png",
      data: {
        url: data.url, // Use the URL from the push notification data
      },
    };

    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
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
    (url.pathname.endsWith(".m3u8")),
  new CacheFirst({
    cacheName: "video-cache",
  })
);
