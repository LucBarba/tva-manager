//
// pages/Login.jsx
// Écran de connexion.
//

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthViewModel } from '../hooks/useAuthViewModel'
import Spinner from '../components/Spinner'

export default function Login() {
  const navigate = useNavigate()
  const { signIn, loading, error } = useAuthViewModel()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    const ok = await signIn({ email, password })
    if (ok) navigate('/', { replace: true })
  }

  return (
    <div className="auth fade-in">
      <div className="brand">
        <div className="logo">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="#fff">
            <path d="M12 2a10 10 0 0 0-8.7 14.9L2 22l5.3-1.4A10 10 0 1 0 12 2z" />
          </svg>
        </div>
        <h1>Bon retour 👋</h1>
        <p className="lead">Connectez-vous pour discuter</p>
      </div>

      {error && <div className="alert error">{error}</div>}

      <form className="auth" style={{ padding: 0, gap: 16 }} onSubmit={submit}>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            autoComplete="email" required placeholder="vous@exemple.com" />
        </div>
        <div className="field">
          <label htmlFor="password">Mot de passe</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password" required placeholder="••••••••" />
        </div>

        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? <Spinner /> : 'Se connecter'}
        </button>
      </form>

      <div style={{ textAlign: 'center' }}>
        <Link to="/reset" className="btn-link">Mot de passe oublié ?</Link>
      </div>
      <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
        Pas encore de compte ? <Link to="/register" className="btn-link">Créer un compte</Link>
      </div>
    </div>
  )
}
