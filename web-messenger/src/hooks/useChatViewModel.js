//
// hooks/useChatViewModel.js
// "ViewModel" de l'écran Conversation : établit le canal unique entre les deux
// utilisateurs, écoute les messages en temps réel, gère l'envoi texte/média,
// les statuts (reçu/lu) et la présence du correspondant.
//

import { useState, useEffect, useCallback, useRef } from 'react'
import { conversationRepository } from '../repositories/conversationRepository'
import { messageRepository } from '../repositories/messageRepository'
import { userRepository } from '../repositories/userRepository'
import { MessageType, Limits } from '../utils/constants'
import { sanitizeMessage } from '../utils/validators'
import { toUserMessage } from '../utils/errors'
import { getImageDimensions, generateVideoThumbnail } from '../utils/media'
import { notificationService } from '../services/notificationService'

export function useChatViewModel(currentUser) {
  const [partner, setPartner] = useState(null)
  const [conversationId, setConversationId] = useState(null)
  const [messages, setMessages] = useState([])
  const [loadingPartner, setLoadingPartner] = useState(true)
  const [error, setError] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(null) // 0..1 ou null
  const seenMessageIds = useRef(new Set())

  const currentUserId = currentUser?.uid

  // 1) Trouver l'autre utilisateur (le correspondant) parmi les <= 2 users.
  useEffect(() => {
    if (!currentUserId) return undefined
    const unsub = userRepository.listenAllUsers(
      (users) => {
        const other = users.find((u) => u && u.id !== currentUserId) || null
        setPartner(other)
        setLoadingPartner(false)
      },
      (e) => {
        setError(toUserMessage(e))
        setLoadingPartner(false)
      },
    )
    return unsub
  }, [currentUserId])

  // 2) Dès que le correspondant est connu, garantir la conversation.
  useEffect(() => {
    if (!currentUserId || !partner?.id) return
    let active = true
    conversationRepository
      .ensureConversation(currentUserId, partner.id)
      .then((conv) => {
        if (active && conv) setConversationId(conv.id)
      })
      .catch((e) => setError(toUserMessage(e)))
    return () => {
      active = false
    }
  }, [currentUserId, partner?.id])

  // 3) Écoute des messages en temps réel + statuts reçu/lu.
  useEffect(() => {
    if (!conversationId || !currentUserId) return undefined
    const unsub = messageRepository.listenMessages(
      conversationId,
      Limits.messagePageSize,
      (list) => {
        setMessages(list)

        // Notifier les nouveaux messages entrants (premier plan).
        for (const m of list) {
          if (m.senderId !== currentUserId && m.id && !seenMessageIds.current.has(m.id)) {
            seenMessageIds.current.add(m.id)
            if (seenMessageIds.current.size > 1) {
              notifyIncoming(m, partner)
            }
          }
        }

        // Marquer reçus puis lus (l'écran est ouvert).
        messageRepository
          .markIncomingAsDelivered({ conversationId, currentUserId })
          .then(() => messageRepository.markIncomingAsRead({ conversationId, currentUserId }))
          .catch(() => {})
      },
      (e) => setError(toUserMessage(e)),
    )
    return unsub
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId, currentUserId])

  // --- Actions ---

  const sendText = useCallback(
    async (raw) => {
      setError(null)
      if (!conversationId || !partner?.id) return
      let text
      try {
        text = sanitizeMessage(raw)
      } catch (e) {
        setError(toUserMessage(e))
        return
      }
      if (!text) return
      try {
        await messageRepository.sendText({
          conversationId,
          senderId: currentUserId,
          recipientId: partner.id,
          text,
        })
      } catch (e) {
        setError(toUserMessage(e))
      }
    },
    [conversationId, partner?.id, currentUserId],
  )

  const sendMedia = useCallback(
    async (file) => {
      setError(null)
      if (!conversationId || !partner?.id || !file) return
      const isVideo = file.type.startsWith('video/')
      const type = isVideo ? MessageType.video : MessageType.image
      try {
        setUploadProgress(0)
        let width = null
        let height = null
        let thumbnailFile = null

        if (isVideo) {
          const thumb = await generateVideoThumbnail(file)
          thumbnailFile = thumb.blob
          width = thumb.width
          height = thumb.height
        } else {
          const dim = await getImageDimensions(file)
          width = dim.width
          height = dim.height
        }

        await messageRepository.sendMedia({
          conversationId,
          senderId: currentUserId,
          recipientId: partner.id,
          file,
          type,
          width,
          height,
          thumbnailFile,
          onProgress: setUploadProgress,
        })
      } catch (e) {
        setError(toUserMessage(e))
      } finally {
        setUploadProgress(null)
      }
    },
    [conversationId, partner?.id, currentUserId],
  )

  return {
    partner,
    messages,
    conversationId,
    loadingPartner,
    error,
    uploadProgress,
    sendText,
    sendMedia,
    clearError: () => setError(null),
  }
}

function notifyIncoming(message, partner) {
  const title = partner?.displayName || 'Nouveau message'
  let body = message.text || ''
  if (message.type === MessageType.image) body = '📷 Photo'
  if (message.type === MessageType.video) body = '🎥 Vidéo'
  notificationService.showLocalNotification(title, body, partner?.photoURL || '/favicon.svg')
}
