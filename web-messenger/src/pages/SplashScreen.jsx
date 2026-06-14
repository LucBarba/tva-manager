//
// pages/SplashScreen.jsx
// Écran de démarrage affiché pendant l'initialisation de l'authentification.
//

import Spinner from '../components/Spinner'

export default function SplashScreen() {
  return (
    <div className="splash">
      <div className="logo">
        <svg width="60" height="60" viewBox="0 0 24 24" fill="#fff">
          <path d="M12 2a10 10 0 0 0-8.7 14.9L2 22l5.3-1.4A10 10 0 1 0 12 2zm0 2a8 8 0 1 1-4.1 14.9l-.3-.2-2.9.8.8-2.8-.2-.3A8 8 0 0 1 12 4z" />
        </svg>
      </div>
      <div className="name">DuoChat</div>
      <Spinner />
    </div>
  )
}
