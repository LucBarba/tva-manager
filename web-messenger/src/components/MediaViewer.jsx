//
// components/MediaViewer.jsx
// Visionneuse plein écran : zoom pour les photos, lecteur pour les vidéos.
//

import { useState, useEffect } from 'react'
import { MessageType } from '../utils/constants'

export default function MediaViewer({ message, onClose }) {
  const [zoomed, setZoomed] = useState(false)

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  if (!message) return null

  return (
    <div className="viewer" onClick={onClose}>
      <button className="close" onClick={onClose} aria-label="Fermer">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      </button>

      {message.type === MessageType.video ? (
        <video
          src={message.mediaURL}
          controls
          autoPlay
          playsInline
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <img
          src={message.mediaURL}
          alt="media"
          className={`zoomable ${zoomed ? 'zoomed' : ''}`}
          onClick={(e) => {
            e.stopPropagation()
            setZoomed((z) => !z)
          }}
        />
      )}
    </div>
  )
}
