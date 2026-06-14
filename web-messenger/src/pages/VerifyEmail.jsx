//
// pages/VerifyEmail.jsx
// Écran d'attente de vérification d'email. Vérifie périodiquement le statut.
//

import { useEffect, useState } from 'react'
import { useAuthViewModel } from '../hooks/useAuthViewModel'
import { useAuthContext } from '../context/AuthContext'
import Spinner from '../components/Spinner'

export default function VerifyEmail() {
  const { authUser } = useAuthContext()
  const { resendVerification, refreshVerification, signOut, loading, info, error } = useAuthViewModel()
  const [checking, setChecking] = useState(false)

  // Vérification automatique toutes les 5 secondes.
  useEffect(() => {
    const id = setInterval(async () => {
      const verified = await refreshVerification()
      if (verified) window.location.reload()
    }, 5000)
    return () => clearInterval(id)
  }, [refreshVerification])

  const checkNow = async () => {
    setChecking(true)
    const verified = await refreshVerification()
    setChecking(false)
    if (verified) window.location.reload()
  }

  return (
    <div className="auth fade-in">
      <div className="brand">
        <div className="logo">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="#fff">
            <path d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
          </svg>
        </div>
        <h1>Vérifiez votre email</h1>
        <p className="lead">
          Un email a été envoyé à<br /><strong>{authUser?.email}</strong>
        </p>
      </div>

      {info && <div className="alert info">{info}</div>}
      {error && <div className="alert error">{error}</div>}

      <p style={{ color: 'var(--text-muted)', textAlign: 'center', fontSize: 14 }}>
        Cliquez sur le lien reçu, puis revenez ici. La page se mettra à jour automatiquement.
      </p>

      <button className="btn-primary" onClick={checkNow} disabled={checking}>
        {checking ? <Spinner /> : "J'ai vérifié mon email"}
      </button>
      <button className="btn-ghost" onClick={resendVerification} disabled={loading}>
        Renvoyer l'email de vérification
      </button>
      <button className="btn-link" onClick={signOut} style={{ alignSelf: 'center' }}>
        Se déconnecter
      </button>
    </div>
  )
}
