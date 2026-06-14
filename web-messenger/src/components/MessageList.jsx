//
// components/MessageList.jsx
// Liste des messages avec séparateurs de jour et défilement automatique vers le bas.
//

import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'
import { formatDaySeparator, toDate, isSameDay } from '../utils/format'

export default function MessageList({ messages, currentUserId, onOpenMedia }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  if (messages.length === 0) {
    return (
      <div className="messages">
        <div className="empty">
          <div>
            <div style={{ fontSize: 40, marginBottom: 8 }}>💬</div>
            Aucun message pour l’instant.<br />Dites bonjour 👋
          </div>
        </div>
      </div>
    )
  }

  let lastDate = null

  return (
    <div className="messages">
      {messages.map((m) => {
        const date = toDate(m.timestamp)
        let separator = null
        if (date && (!lastDate || !isSameDay(date, lastDate))) {
          separator = <div className="day-sep" key={`sep-${m.id}`}>{formatDaySeparator(date)}</div>
          lastDate = date
        }
        return (
          <div key={m.id}>
            {separator}
            <MessageBubble
              message={m}
              isOutgoing={m.senderId === currentUserId}
              onOpenMedia={onOpenMedia}
            />
          </div>
        )
      })}
      <div ref={bottomRef} />
    </div>
  )
}
