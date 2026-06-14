//
// models/Conversation.js
// Schéma du document `conversations/{conversationId}`.
//

/**
 * @typedef {Object} Conversation
 * @property {string} id
 * @property {string[]} participants          - Les deux UID.
 * @property {?string} lastMessageText
 * @property {?string} lastMessageSenderId
 * @property {?string} lastMessageType
 * @property {*} lastMessageAt
 * @property {Object.<string, number>} unreadCounts
 * @property {*} createdAt
 */

/**
 * Identifiant déterministe de conversation à partir de deux UID.
 * Les UID sont triés pour garantir le même identifiant côté des deux users.
 */
export function conversationId(uidA, uidB) {
  return [uidA, uidB].sort().join('_')
}

/** Construit une Conversation depuis un DocumentSnapshot Firestore. */
export function conversationFromDoc(snapshot) {
  if (!snapshot || !snapshot.exists()) return null
  const data = snapshot.data()
  return {
    id: snapshot.id,
    participants: data.participants ?? [],
    lastMessageText: data.lastMessageText ?? null,
    lastMessageSenderId: data.lastMessageSenderId ?? null,
    lastMessageType: data.lastMessageType ?? null,
    lastMessageAt: data.lastMessageAt ?? null,
    unreadCounts: data.unreadCounts ?? {},
    createdAt: data.createdAt ?? null,
  }
}

/** UID de l'autre participant. */
export function otherParticipant(conversation, currentUserId) {
  return conversation?.participants?.find((p) => p !== currentUserId) ?? null
}

/** Nombre de messages non lus pour un utilisateur. */
export function unreadCount(conversation, userId) {
  return conversation?.unreadCounts?.[userId] ?? 0
}
