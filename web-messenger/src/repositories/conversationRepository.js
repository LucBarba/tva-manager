//
// repositories/conversationRepository.js
// Gestion du document `conversations/{conversationId}` unique entre 2 users.
//

import { firestoreService as fs } from '../services/firestoreService'
import { Collections } from '../utils/constants'
import { conversationId, conversationFromDoc } from '../models/Conversation'

export const conversationRepository = {
  /** Identifiant déterministe de la conversation. */
  idFor(uidA, uidB) {
    return conversationId(uidA, uidB)
  },

  /** Crée la conversation si elle n'existe pas encore. */
  async ensureConversation(uidA, uidB) {
    const id = conversationId(uidA, uidB)
    const ref = fs.docRef(Collections.conversations, id)
    const snap = await fs.getDoc(ref)
    if (snap.exists()) return conversationFromDoc(snap)

    await fs.setDoc(ref, {
      participants: [uidA, uidB].sort(),
      lastMessageText: null,
      lastMessageSenderId: null,
      lastMessageType: null,
      lastMessageAt: fs.serverTimestamp(),
      unreadCounts: { [uidA]: 0, [uidB]: 0 },
      createdAt: fs.serverTimestamp(),
    })
    const created = await fs.getDoc(ref)
    return conversationFromDoc(created)
  },

  /** Écoute en temps réel le document conversation. */
  listenConversation(id, callback, onError) {
    return fs.listen(
      fs.docRef(Collections.conversations, id),
      (snap) => callback(conversationFromDoc(snap)),
      onError,
    )
  },

  /** Remet à zéro le compteur de non-lus pour un utilisateur. */
  async resetUnread(id, uid) {
    await fs.updateDoc(fs.docRef(Collections.conversations, id), {
      [`unreadCounts.${uid}`]: 0,
    })
  },
}
