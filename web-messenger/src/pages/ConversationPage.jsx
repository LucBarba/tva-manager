//
// pages/ConversationPage.jsx
// Écran principal de discussion entre les deux utilisateurs.
//

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthContext } from '../context/AuthContext'
import { useChatViewModel } from '../hooks/useChatViewModel'
import { formatPresence } from '../utils/format'
import Avatar from '../components/Avatar'
import MessageList from '../components/MessageList'
import Composer from '../components/Composer'
import MediaViewer from '../components/MediaViewer'
import Spinner from '../components/Spinner'

export default function ConversationPage({ onToggleTheme, theme }) {
  const navigate = useNavigate()
  const { authUser } = useAuthContext()
  const {
    partner, messages, loadingPartner, error,
    uploadProgress, sendText, sendMedia,
  } = useChatViewModel(authUser)
  const [activeMedia, setActiveMedia] = useState(null)

  return (
    <>
      <header className="topbar">
        <button onClick={() => navigate('/profile')} aria-label="Profil"
          style={{ padding: 0, borderRadius: '50%' }}>
          <Avatar user={partner} />
        </button>
        <div>
          <div className="title">{partner?.displayName || 'En attente du contact…'}</div>
          <div className="subtitle">
            {partner ? formatPresence(partner.isOnline, partner.lastSeen) : 'Aucun second utilisateur'}
          </div>
        </div>
        <div className="spacer" />
        <button onClick={onToggleTheme} aria-label="Changer de thème">
          {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
        </button>
        <button onClick={() => navigate('/profile')} aria-label="Réglages">
          <GearIcon />
        </button>
      </header>

      {error && <div className="alert error" style={{ margin: 8 }}>{error}</div>}

      {loadingPartner ? (
        <div className="empty"><Spinner dark /></div>
      ) : !partner ? (
        <div className="empty">
          <div>
            <div style={{ fontSize: 40, marginBottom: 8 }}>👤</div>
            En attente du second utilisateur.<br />
            Demandez à votre contact de créer son compte.
          </div>
        </div>
      ) : (
        <MessageList
          messages={messages}
          currentUserId={authUser?.uid}
          onOpenMedia={setActiveMedia}
        />
      )}

      <Composer
        onSendText={sendText}
        onSendMedia={sendMedia}
        disabled={!partner}
        uploadProgress={uploadProgress}
      />

      {activeMedia && <MediaViewer message={activeMedia} onClose={() => setActiveMedia(null)} />}
    </>
  )
}

function GearIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.4 13a7.8 7.8 0 0 0 0-2l2-1.6-2-3.4-2.4 1a7.6 7.6 0 0 0-1.7-1l-.4-2.5H10l-.4 2.5a7.6 7.6 0 0 0-1.7 1l-2.4-1-2 3.4L3.6 11a7.8 7.8 0 0 0 0 2l-2 1.6 2 3.4 2.4-1c.5.4 1.1.8 1.7 1l.4 2.5h4l.4-2.5c.6-.2 1.2-.6 1.7-1l2.4 1 2-3.4-2-1.6zM12 15.5a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7z" />
    </svg>
  )
}
function MoonIcon() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></svg>
}
function SunIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  )
}
