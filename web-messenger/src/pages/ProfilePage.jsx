//
// pages/ProfilePage.jsx
// Écran de profil : photo, nom affiché, email, statut, déconnexion.
//

import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthContext } from '../context/AuthContext'
import { useProfileViewModel } from '../hooks/useProfileViewModel'
import { useAuthViewModel } from '../hooks/useAuthViewModel'
import { formatPresence, formatRelative, toDate } from '../utils/format'
import Avatar from '../components/Avatar'
import Spinner from '../components/Spinner'

export default function ProfilePage() {
  const navigate = useNavigate()
  const { authUser, profile } = useAuthContext()
  const { saving, error, info, updateName, updatePhoto } = useProfileViewModel(authUser?.uid)
  const { signOut } = useAuthViewModel()
  const [name, setName] = useState(profile?.displayName || '')
  const [editing, setEditing] = useState(false)
  const fileRef = useRef(null)

  const onPhoto = (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (file) updatePhoto(file)
  }

  const saveName = async () => {
    const ok = await updateName(name)
    if (ok) setEditing(false)
  }

  const lastSeenDate = toDate(profile?.lastSeen)

  return (
    <>
      <header className="topbar">
        <button onClick={() => navigate('/')} aria-label="Retour">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <div className="title">Profil</div>
      </header>

      <div className="profile">
        <div className="avatar-edit">
          <Avatar user={profile} size="lg" />
          <button className="btn-link" onClick={() => fileRef.current?.click()} disabled={saving}>
            Changer la photo
          </button>
          <input ref={fileRef} type="file" accept="image/*" hidden onChange={onPhoto} />
        </div>

        {error && <div className="alert error">{error}</div>}
        {info && <div className="alert info">{info}</div>}
        {saving && <div style={{ display: 'grid', placeItems: 'center' }}><Spinner dark /></div>}

        <div className="row">
          <div style={{ flex: 1 }}>
            <div className="label">Nom affiché</div>
            {editing ? (
              <input
                className="value"
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={{ width: '100%', padding: 8, borderRadius: 8, border: '1px solid var(--border)', background: 'var(--panel)', color: 'var(--text)' }}
              />
            ) : (
              <div className="value">{profile?.displayName}</div>
            )}
          </div>
          {editing ? (
            <button className="btn-link" onClick={saveName} disabled={saving}>Enregistrer</button>
          ) : (
            <button className="btn-link" onClick={() => { setName(profile?.displayName || ''); setEditing(true) }}>
              Modifier
            </button>
          )}
        </div>

        <div className="row">
          <div>
            <div className="label">Email</div>
            <div className="value">{profile?.email || authUser?.email}</div>
          </div>
        </div>

        <div className="row">
          <div>
            <div className="label">Statut</div>
            <div className="value">{formatPresence(profile?.isOnline, profile?.lastSeen)}</div>
          </div>
        </div>

        {lastSeenDate && (
          <div className="row">
            <div>
              <div className="label">Dernière connexion</div>
              <div className="value">{formatRelative(lastSeenDate)}</div>
            </div>
          </div>
        )}

        <button className="btn-ghost" style={{ color: 'var(--danger)', marginTop: 8 }} onClick={signOut}>
          Se déconnecter
        </button>
      </div>
    </>
  )
}
