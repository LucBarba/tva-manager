//
// App.jsx
// Routeur principal et garde d'authentification :
//   - initialisation      → SplashScreen
//   - non authentifié     → Login / Register / Reset
//   - email non vérifié   → VerifyEmail
//   - authentifié + vérifié → Conversation / Profil
//

import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthContext } from './context/AuthContext'
import { useTheme } from './hooks/useTheme'

import SplashScreen from './pages/SplashScreen'
import Login from './pages/Login'
import Register from './pages/Register'
import ResetPassword from './pages/ResetPassword'
import VerifyEmail from './pages/VerifyEmail'
import ConversationPage from './pages/ConversationPage'
import ProfilePage from './pages/ProfilePage'

export default function App() {
  const { initializing, isAuthenticated, isEmailVerified } = useAuthContext()
  const { theme, toggleTheme } = useTheme()

  let content

  if (initializing) {
    content = <SplashScreen />
  } else if (!isAuthenticated) {
    content = (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/reset" element={<ResetPassword />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  } else if (!isEmailVerified) {
    content = (
      <Routes>
        <Route path="*" element={<VerifyEmail />} />
      </Routes>
    )
  } else {
    content = (
      <Routes>
        <Route path="/" element={<ConversationPage onToggleTheme={toggleTheme} theme={theme} />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    )
  }

  return (
    <div className="app-shell">
      <div className="app-frame">{content}</div>
    </div>
  )
}
