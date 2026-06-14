//
// components/Composer.jsx
// Barre de saisie : texte multi-ligne, sélection galerie, capture caméra
// (photo et vidéo via l'attribut `capture`), et envoi.
//

import { useRef, useState } from 'react'

export default function Composer({ onSendText, onSendMedia, disabled, uploadProgress }) {
  const [text, setText] = useState('')
  const galleryRef = useRef(null)
  const cameraPhotoRef = useRef(null)
  const cameraVideoRef = useRef(null)
  const [showMenu, setShowMenu] = useState(false)

  const submit = () => {
    const value = text
    if (!value.trim()) return
    setText('')
    onSendText(value)
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const pick = (ref) => {
    setShowMenu(false)
    ref.current?.click()
  }

  const onFile = (e) => {
    const file = e.target.files?.[0]
    e.target.value = '' // permet de re-sélectionner le même fichier
    if (file) onSendMedia(file)
  }

  const uploading = uploadProgress !== null && uploadProgress !== undefined

  return (
    <div>
      {uploading && (
        <div className="progress-bar" style={{ width: `${Math.round(uploadProgress * 100)}%` }} />
      )}
      <div className="composer">
        <div style={{ position: 'relative' }}>
          <button className="icon-btn" onClick={() => setShowMenu((s) => !s)} aria-label="Joindre" disabled={disabled}>
            <PaperclipIcon />
          </button>
          {showMenu && (
            <div style={menuStyle}>
              <MenuItem label="📷 Photo (caméra)" onClick={() => pick(cameraPhotoRef)} />
              <MenuItem label="🎥 Vidéo (caméra)" onClick={() => pick(cameraVideoRef)} />
              <MenuItem label="🖼️ Galerie" onClick={() => pick(galleryRef)} />
            </div>
          )}
        </div>

        <div className="input-wrap">
          <textarea
            rows={1}
            value={text}
            placeholder="Message"
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKey}
            disabled={disabled}
          />
        </div>

        <button className="send-btn" onClick={submit} aria-label="Envoyer" disabled={disabled}>
          <SendIcon />
        </button>

        {/* Entrées fichier masquées */}
        <input ref={galleryRef} type="file" accept="image/*,video/*" hidden onChange={onFile} />
        <input ref={cameraPhotoRef} type="file" accept="image/*" capture="environment" hidden onChange={onFile} />
        <input ref={cameraVideoRef} type="file" accept="video/*" capture="environment" hidden onChange={onFile} />
      </div>
    </div>
  )
}

const menuStyle = {
  position: 'absolute', bottom: '52px', left: 0, background: 'var(--panel)',
  borderRadius: 12, boxShadow: '0 4px 20px rgba(0,0,0,0.2)', overflow: 'hidden',
  width: 200, zIndex: 5,
}

function MenuItem({ label, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{ display: 'block', width: '100%', textAlign: 'left', padding: '12px 14px', color: 'var(--text)' }}
    >
      {label}
    </button>
  )
}

function PaperclipIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 11.5l-8.5 8.5a5 5 0 0 1-7-7l8.5-8.5a3.3 3.3 0 0 1 4.7 4.7l-8.5 8.5a1.7 1.7 0 0 1-2.3-2.3l7.8-7.8" />
    </svg>
  )
}

function SendIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
      <path d="M2 21l21-9L2 3v7l15 2-15 2z" />
    </svg>
  )
}
