//
// Cloud Functions DuoChat
//   1. sendMessageNotification : envoie une notification push FCM au destinataire
//      à chaque nouveau message (texte, photo, vidéo).
//   2. enforceUserLimit : supprime tout compte au-delà de 2 utilisateurs.
//

import { onDocumentCreated } from 'firebase-functions/v2/firestore'
import { beforeUserCreated } from 'firebase-functions/v2/identity'
import { HttpsError } from 'firebase-functions/v2/identity'
import { initializeApp } from 'firebase-admin/app'
import { getFirestore } from 'firebase-admin/firestore'
import { getMessaging } from 'firebase-admin/messaging'
import { getAuth } from 'firebase-admin/auth'

initializeApp()
const db = getFirestore()

// --- 1) Notifications push à la réception d'un message ---
export const sendMessageNotification = onDocumentCreated(
  'conversations/{conversationId}/messages/{messageId}',
  async (event) => {
    const message = event.data?.data()
    if (!message) return

    const { conversationId } = event.params

    // Récupère la conversation pour identifier le destinataire.
    const convSnap = await db.collection('conversations').doc(conversationId).get()
    const participants = convSnap.get('participants') || []
    const recipientId = participants.find((uid) => uid !== message.senderId)
    if (!recipientId) return

    // Jetons FCM de l'expéditeur (nom) et du destinataire (cible).
    const [recipientSnap, senderSnap] = await Promise.all([
      db.collection('users').doc(recipientId).get(),
      db.collection('users').doc(message.senderId).get(),
    ])

    const token = recipientSnap.get('fcmToken')
    if (!token) return

    const senderName = senderSnap.get('displayName') || 'Nouveau message'

    let body
    switch (message.type) {
      case 'image': body = '📷 Photo'; break
      case 'video': body = '🎥 Vidéo'; break
      default: body = message.text || ''
    }

    await getMessaging().send({
      token,
      notification: { title: senderName, body },
      data: {
        conversationId,
        senderId: String(message.senderId),
        type: String(message.type),
      },
      webpush: {
        fcmOptions: { link: '/' },
        notification: { icon: '/favicon.svg' },
      },
    })
  },
)

// --- 2) Limite stricte de 2 utilisateurs (fonction bloquante) ---
// Nécessite Identity Platform activé (Authentication → Settings → Blocking functions).
export const enforceUserLimit = beforeUserCreated(async () => {
  const auth = getAuth()
  const list = await auth.listUsers(3)
  if (list.users.length >= 2) {
    throw new HttpsError(
      'resource-exhausted',
      "Inscriptions fermées : l'application est limitée à 2 utilisateurs.",
    )
  }
})
