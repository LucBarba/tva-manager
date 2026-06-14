/*
 * firebase-messaging-sw.js
 * Service Worker pour les notifications Web Push en arrière-plan (FCM).
 *
 * La configuration Firebase est transmise automatiquement par l'application via
 * les paramètres d'URL lors de l'enregistrement du service worker
 * (voir src/services/notificationService.js). AUCUNE édition manuelle requise :
 * il suffit de renseigner le fichier .env.
 */

importScripts('https://www.gstatic.com/firebasejs/11.0.0/firebase-app-compat.js')
importScripts('https://www.gstatic.com/firebasejs/11.0.0/firebase-messaging-compat.js')

// Lecture de la config depuis les paramètres d'URL du service worker.
const params = new URL(self.location).searchParams
const firebaseConfig = {
  apiKey: params.get('apiKey'),
  authDomain: params.get('authDomain'),
  projectId: params.get('projectId'),
  storageBucket: params.get('storageBucket'),
  messagingSenderId: params.get('messagingSenderId'),
  appId: params.get('appId'),
}

if (firebaseConfig.projectId) {
  firebase.initializeApp(firebaseConfig)
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
}

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
