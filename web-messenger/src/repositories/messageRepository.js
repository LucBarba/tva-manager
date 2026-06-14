//
// repositories/messageRepository.js
// Envoi/réception des messages, statuts (envoyé/reçu/lu) et mise à jour
// transactionnelle du document conversation (dernier message + non-lus).
//

import { firestoreService as fs } from '../services/firestoreService'
import { storageService } from '../services/storageService'
import { Collections, StoragePaths, MessageType, MessageStatus } from '../utils/constants'
import { messageFromDoc, messagePreview } from '../models/Message'

function messagesCol(conversationId) {
  return fs.subCollectionRef(Collections.conversations, conversationId, Collections.messages)
}

export const messageRepository = {
  /**
   * Écoute en temps réel les derniers messages (ordre chronologique).
   * @param {string} conversationId
   * @param {number} max
   */
  listenMessages(conversationId, max, callback, onError) {
    const q = fs.query(
      messagesCol(conversationId),
      fs.orderBy('timestamp', 'desc'),
      fs.limit(max),
    )
    return fs.listen(
      q,
      (snap) => {
        const messages = snap.docs
          .map((d) => messageFromDoc(d))
          .reverse() // remettre en ordre ascendant pour l'affichage
        callback(messages)
      },
      onError,
    )
  },

  /** Envoie un message texte. */
  async sendText({ conversationId, senderId, recipientId, text }) {
    const ref = fs.docRef(`${Collections.conversations}/${conversationId}/${Collections.messages}`)
    await fs.setDoc(ref, {
      senderId,
      type: MessageType.text,
      text,
      mediaURL: null,
      thumbnailURL: null,
      status: MessageStatus.sent,
      timestamp: fs.serverTimestamp(),
    })
    await this._touchConversation({
      conversationId,
      senderId,
      recipientId,
      preview: messagePreview(MessageType.text, text),
      type: MessageType.text,
    })
    return ref.id
  },

  /**
   * Envoie un média (image/vidéo) : upload Storage puis écriture Firestore.
   * @param {(p:number)=>void} [onProgress]
   */
  async sendMedia({
    conversationId,
    senderId,
    recipientId,
    file,
    type,
    width,
    height,
    thumbnailFile,
    onProgress,
  }) {
    const folder = type === MessageType.video ? StoragePaths.chatVideos : StoragePaths.chatImages
    const ext = (file.name?.split('.').pop() || (type === MessageType.video ? 'mp4' : 'jpg')).toLowerCase()
    const path = storageService.buildPath(folder, conversationId, ext)
    const mediaURL = await storageService.upload(path, file, onProgress)

    let thumbnailURL = null
    if (thumbnailFile) {
      const thumbPath = storageService.buildPath(StoragePaths.chatThumbnails, conversationId, 'jpg')
      thumbnailURL = await storageService.upload(thumbPath, thumbnailFile)
    }

    const ref = fs.docRef(`${Collections.conversations}/${conversationId}/${Collections.messages}`)
    await fs.setDoc(ref, {
      senderId,
      type,
      text: null,
      mediaURL,
      thumbnailURL,
      mediaWidth: width ?? null,
      mediaHeight: height ?? null,
      status: MessageStatus.sent,
      timestamp: fs.serverTimestamp(),
    })

    await this._touchConversation({
      conversationId,
      senderId,
      recipientId,
      preview: messagePreview(type, null),
      type,
    })
    return ref.id
  },

  /**
   * Marque comme "lus" tous les messages entrants non lus.
   * Met à jour le statut des messages et remet le compteur à zéro.
   */
  async markIncomingAsRead({ conversationId, currentUserId }) {
    const q = fs.query(
      messagesCol(conversationId),
      fs.where('senderId', '!=', currentUserId),
      fs.where('status', 'in', [MessageStatus.sent, MessageStatus.delivered]),
    )
    const snap = await fs.getDocs(q)
    if (snap.empty) {
      await fs.updateDoc(fs.docRef(Collections.conversations, conversationId), {
        [`unreadCounts.${currentUserId}`]: 0,
      })
      return
    }
    const batch = fs.batch()
    snap.docs.forEach((d) => batch.update(d.ref, { status: MessageStatus.read }))
    batch.update(fs.docRef(Collections.conversations, conversationId), {
      [`unreadCounts.${currentUserId}`]: 0,
    })
    await batch.commit()
  },

  /** Marque les messages entrants comme "reçus" (delivered). */
  async markIncomingAsDelivered({ conversationId, currentUserId }) {
    const q = fs.query(
      messagesCol(conversationId),
      fs.where('senderId', '!=', currentUserId),
      fs.where('status', '==', MessageStatus.sent),
    )
    const snap = await fs.getDocs(q)
    if (snap.empty) return
    const batch = fs.batch()
    snap.docs.forEach((d) => batch.update(d.ref, { status: MessageStatus.delivered }))
    await batch.commit()
  },

  /** Met à jour le dernier message et incrémente les non-lus du destinataire. */
  async _touchConversation({ conversationId, senderId, recipientId, preview, type }) {
    await fs.updateDoc(fs.docRef(Collections.conversations, conversationId), {
      lastMessageText: preview,
      lastMessageSenderId: senderId,
      lastMessageType: type,
      lastMessageAt: fs.serverTimestamp(),
      [`unreadCounts.${recipientId}`]: fs.increment(1),
    })
  },
}
