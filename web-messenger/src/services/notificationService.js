//
// services/notificationService.js
// Notifications Web Push via Firebase Cloud Messaging + notifications locales
// de repli lorsque l'onglet est ouvert.
//

import { getToken, onMessage } from 'firebase/messaging'
import { messagingPromise, vapidKey } from '../firebase/config'

export const notificationService = {
  /** Demande la permission et renvoie le jeton FCM (ou null). */
  async requestPermissionAndToken() {
    if (!('Notification' in window)) return null
    const messaging = await messagingPromise
    if (!messaging) return null

    const permission = await Notification.requestPermission()
    if (permission !== 'granted') return null

    try {
      const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js')
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
