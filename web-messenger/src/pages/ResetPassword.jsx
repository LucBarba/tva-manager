//
// pages/ResetPassword.jsx
// Écran de réinitialisation du mot de passe.
//

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthViewModel } from '../hooks/useAuthViewModel'
import Spinner from '../components/Spinner'

export default function ResetPassword() {
  const { sendPasswordReset, loading, error, info } = useAuthViewModel()
  const [email, setEmail] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    await sendPasswordReset(email)
  }

  return (
    <div className="auth fade-in">
      <div className="brand">
        <div className="logo">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="#fff">
            <path d="M12 1a5 5 0 0 0-5 5v3H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2h-1V6a5 5 0 0 0-5-5zm3 8H9V6a3 3 0 0 1 6 0v3z" />
          </svg>
        </div>
        <h1>Mot de passe oublié</h1>
        <p className="lead">Recevez un lien de réinitialisation par email</p>
      </div>

      {error && <div className="alert error">{error}</div>}
      {info && <div className="alert info">{info}</div>}

      <form className="auth" style={{ padding: 0, gap: 16 }} onSubmit={submit}>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            autoComplete="email" required placeholder="vous@exemple.com" />
        </div>
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? <Spinner /> : 'Envoyer le lien'}
        </button>
      </form>

      <div style={{ textAlign: 'center' }}>
        <Link to="/login" className="btn-link">← Retour à la connexion</Link>
      </div>
    </div>
  )
}
