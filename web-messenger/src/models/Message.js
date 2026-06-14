//
// models/Message.js
// Schéma du document `conversations/{conversationId}/messages/{messageId}`.
//

import { MessageType, MessageStatus } from '../utils/constants'

/**
 * @typedef {Object} Message
 * @property {string} id             - Identifiant Firestore.
 * @property {string} senderId       - UID de l'expéditeur.
 * @property {'text'|'image'|'video'} type
 * @property {?string} text          - Contenu texte / légende.
 * @property {?string} mediaURL      - URL du média (Storage).
 * @property {?string} thumbnailURL  - URL de la vignette (vidéos).
 * @property {?number} mediaWidth
 * @property {?number} mediaHeight
 * @property {'sending'|'sent'|'delivered'|'read'} status
 * @property {*} timestamp           - Timestamp serveur.
 */

/** Construit un Message depuis un DocumentSnapshot Firestore. */
export function messageFromDoc(snapshot) {
  const data = snapshot.data()
  return {
    id: snapshot.id,
    senderId: data.senderId,
    type: data.type ?? MessageType.text,
    text: data.text ?? null,
    mediaURL: data.mediaURL ?? null,
    thumbnailURL: data.thumbnailURL ?? null,
    mediaWidth: data.mediaWidth ?? null,
    mediaHeight: data.mediaHeight ?? null,
    status: data.status ?? MessageStatus.sent,
    timestamp: data.timestamp ?? null,
  }
}

/** Aperçu textuel d'un message pour la notification / dernier message. */
export function messagePreview(type, text) {
  if (type === MessageType.image) return '📷 Photo'
  if (type === MessageType.video) return '🎥 Vidéo'
  return text ?? ''
}

/** Ratio largeur/hauteur d'un média (1 par défaut). */
export function messageAspectRatio(message) {
  const w = message?.mediaWidth
  const h = message?.mediaHeight
  if (!w || !h) return 1
  return w / h
}
