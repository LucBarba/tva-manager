/*
 * firebase-messaging-sw.js
 * Service Worker pour les notifications Web Push en arrière-plan (FCM).
 *
 * IMPORTANT : un service worker n'a pas accès à import.meta.env. Renseignez
 * ci-dessous les MÊMES valeurs que dans votre fichier .env (config Firebase Web).
 */

importScripts('https://www.gstatic.com/firebasejs/11.0.0/firebase-app-compat.js')
importScripts('https://www.gstatic.com/firebasejs/11.0.0/firebase-messaging-compat.js')

firebase.initializeApp({
  apiKey: 'REMPLACER_PAR_VITE_FIREBASE_API_KEY',
  authDomain: 'REMPLACER_PAR_VITE_FIREBASE_AUTH_DOMAIN',
  projectId: 'REMPLACER_PAR_VITE_FIREBASE_PROJECT_ID',
  storageBucket: 'REMPLACER_PAR_VITE_FIREBASE_STORAGE_BUCKET',
  messagingSenderId: 'REMPLACER_PAR_VITE_FIREBASE_MESSAGING_SENDER_ID',
  appId: 'REMPLACER_PAR_VITE_FIREBASE_APP_ID',
})

const messaging = firebase.messaging()

// Notification reçue alors que l'application est en arrière-plan / fermée.
messaging.onBackgroundMessage((payload) => {
  const title = (payload.notification && payload.notification.title) || 'DuoChat'
  const options = {
    body: (payload.notification && payload.notification.body) || 'Nouveau message',
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    data: payload.data || {},
  }
  self.registration.showNotification(title, options)
})

// Focus / ouverture de l'onglet au clic sur la notification.
self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        if ('focus' in client) return client.focus()
      }
      if (clients.openWindow) return clients.openWindow('/')
      return undefined
    }),
  )
})
