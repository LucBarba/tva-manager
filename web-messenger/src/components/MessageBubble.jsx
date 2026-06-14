//
// components/MessageBubble.jsx
// Bulle de message : texte, image ou vidéo, alignée selon l'expéditeur, avec
// horodatage et coches de statut. Ouvre la visionneuse plein écran sur clic média.
//

import { MessageType } from '../utils/constants'
import { formatTime } from '../utils/format'
import { messageAspectRatio } from '../models/Message'
import Ticks from './Ticks'

export default function MessageBubble({ message, isOutgoing, onOpenMedia }) {
  const rowClass = `bubble-row ${isOutgoing ? 'out' : 'in'}`
  const time = formatTime(message.timestamp)

  const meta = (
    <span className="meta">
      <span>{time}</span>
      {isOutgoing && <Ticks status={message.status} />}
    </span>
  )

  if (message.type === MessageType.text) {
    return (
      <div className={rowClass}>
        <div className={`bubble ${isOutgoing ? 'out' : 'in'}`}>
          <span>{message.text}</span>
          {meta}
        </div>
      </div>
    )
  }

  const ratio = messageAspectRatio(message)
  const previewSrc = message.type === MessageType.video
    ? (message.thumbnailURL || null)
    : message.mediaURL

  return (
    <div className={rowClass}>
      <div className={`bubble media ${isOutgoing ? 'out' : 'in'}`}>
        <div style={{ position: 'relative' }} onClick={() => onOpenMedia(message)}>
          {message.type === MessageType.video ? (
            <>
              {previewSrc ? (
                <img className="media-el" src={previewSrc} alt="vidéo" style={{ aspectRatio: ratio }} />
              ) : (
                <video className="media-el" src={message.mediaURL} preload="metadata" />
              )}
              <PlayBadge />
            </>
          ) : (
            <img className="media-el" src={message.mediaURL} alt="image" style={{ aspectRatio: ratio }} />
          )}
          {meta}
        </div>
        {message.text && <div className="caption">{message.text}</div>}
      </div>
    </div>
  )
}

function PlayBadge() {
  return (
    <div
      style={{
        position: 'absolute', inset: 0, display: 'grid', placeItems: 'center',
        pointerEvents: 'none',
      }}
    >
      <div style={{
        width: 54, height: 54, borderRadius: '50%', background: 'rgba(0,0,0,0.55)',
        display: 'grid', placeItems: 'center',
      }}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="#fff">
          <path d="M8 5v14l11-7z" />
        </svg>
      </div>
    </div>
  )
}
