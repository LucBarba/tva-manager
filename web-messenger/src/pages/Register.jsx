//
// pages/Register.jsx
// Écran d'inscription (limité à 2 utilisateurs au total).
//

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthViewModel } from '../hooks/useAuthViewModel'
import Spinner from '../components/Spinner'

export default function Register() {
  const { register, loading, error, info } = useAuthViewModel()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    await register({ displayName, email, password })
    // En cas de succès, l'utilisateur est connecté et redirigé vers l'écran
    // de vérification d'email par le routeur principal.
  }

  return (
    <div className="auth fade-in">
      <div className="brand">
        <div className="logo">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="#fff">
            <path d="M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0 2c-5 0-9 2.5-9 5.5V22h18v-2.5C21 16.5 17 14 12 14z" />
          </svg>
        </div>
        <h1>Créer un compte</h1>
        <p className="lead">Rejoignez votre conversation privée</p>
      </div>

      {error && <div className="alert error">{error}</div>}
      {info && <div className="alert info">{info}</div>}

      <form className="auth" style={{ padding: 0, gap: 16 }} onSubmit={submit}>
        <div className="field">
          <label htmlFor="name">Nom affiché</label>
          <input id="name" type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)}
            autoComplete="name" required placeholder="Alex" />
        </div>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            autoComplete="email" required placeholder="vous@exemple.com" />
        </div>
        <div className="field">
          <label htmlFor="password">Mot de passe</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password" required placeholder="8+ caractères, lettre + chiffre" />
        </div>

        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? <Spinner /> : "S'inscrire"}
        </button>
      </form>

      <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
        Déjà un compte ? <Link to="/login" className="btn-link">Se connecter</Link>
      </div>
    </div>
  )
}
