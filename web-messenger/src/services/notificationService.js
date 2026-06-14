//
// services/notificationService.js
// Notifications Web Push via Firebase Cloud Messaging + notifications locales
// de repli lorsque l'onglet est ouvert.
//

import { getToken, onMessage } from 'firebase/messaging'
import { messagingPromise, vapidKey, firebaseConfig } from '../firebase/config'

// Le service worker n'a pas accès aux variables Vite : on lui transmet la
// configuration Firebase via les paramètres d'URL au moment de l'enregistrement.
// Ainsi, l'utilisateur n'a qu'UN seul fichier à configurer (.env).
function swUrlWithConfig() {
  const params = new URLSearchParams(firebaseConfig).toString()
  return `/firebase-messaging-sw.js?${params}`
}

export const notificationService = {
  /** Demande la permission et renvoie le jeton FCM (ou null). */
  async requestPermissionAndToken() {
    if (!('Notification' in window)) return null
    const messaging = await messagingPromise
    if (!messaging) return null

    const permission = await Notification.requestPermission()
    if (permission !== 'granted') return null

    try {
      const registration = await navigator.serviceWorker.register(swUrlWithConfig())
      const token = await getToken(messaging, {
        vapidKey,
        serviceWorkerRegistration: registration,
      })
      return token || null
    } catch (error) {
      console.warn('[notifications] Impossible d’obtenir le jeton FCM :', error)
      return null
    }
  },

  /**
   * Écoute les messages FCM reçus pendant que l'onglet est au premier plan.
   * Renvoie une fonction de désabonnement.
   */
  async onForegroundMessage(callback) {
    const messaging = await messagingPromise
    if (!messaging) return () => {}
    return onMessage(messaging, callback)
  },

  /** Affiche une notification locale (repli premier plan). */
  showLocalNotification(title, body, icon = '/favicon.svg') {
    if (!('Notification' in window) || Notification.permission !== 'granted') return
    try {
      // eslint-disable-next-line no-new
      new Notification(title, { body, icon })
    } catch {
      /* Certains navigateurs exigent le ServiceWorkerRegistration : ignoré. */
    }
  },
}
