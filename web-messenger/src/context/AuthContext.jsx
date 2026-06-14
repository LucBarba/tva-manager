//
// context/AuthContext.jsx
// Fournit l'état d'authentification global : utilisateur Auth, profil Firestore,
// présence et état de chargement. Gère aussi le quota de 2 utilisateurs.
//

import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { authService } from '../services/authService'
import { userRepository } from '../repositories/userRepository'
import { notificationService } from '../services/notificationService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [authUser, setAuthUser] = useState(null) // utilisateur Firebase Auth
  const [profile, setProfile] = useState(null) // document Firestore `users`
  const [initializing, setInitializing] = useState(true)
  const profileUnsub = useRef(null)

  // Suivi de l'état d'authentification.
  useEffect(() => {
    const unsubscribe = authService.onAuthChanged(async (user) => {
      // Nettoyage de l'écoute du profil précédent.
      if (profileUnsub.current) {
        profileUnsub.current()
        profileUnsub.current = null
      }

      if (!user) {
        setAuthUser(null)
        setProfile(null)
        setInitializing(false)
        return
      }

      setAuthUser(user)

      // Écoute temps réel du profil Firestore.
      profileUnsub.current = userRepository.listenUser(
        user.uid,
        (p) => {
          setProfile(p)
          setInitializing(false)
        },
        () => setInitializing(false),
      )

      // Présence + jeton FCM (uniquement si email vérifié).
      if (user.emailVerified) {
        try {
          await userRepository.setOnline(user.uid, true)
          const token = await notificationService.requestPermissionAndToken()
          if (token) await userRepository.setFcmToken(user.uid, token)
        } catch {
          /* non bloquant */
        }
      }
    })

    return () => {
      unsubscribe()
      if (profileUnsub.current) profileUnsub.current()
    }
  }, [])

  // Marque hors-ligne à la fermeture de l'onglet.
  useEffect(() => {
    function handleUnload() {
      if (authUser) {
        // navigator.sendBeacon n'est pas applicable à Firestore ; on tente une
        // mise à jour best-effort (peut ne pas aboutir selon le navigateur).
        userRepository.setOnline(authUser.uid, false).catch(() => {})
      }
    }
    window.addEventListener('beforeunload', handleUnload)
    return () => window.removeEventListener('beforeunload', handleUnload)
  }, [authUser])

  const value = useMemo(
    () => ({
      authUser,
      profile,
      initializing,
      isAuthenticated: !!authUser,
      isEmailVerified: !!authUser?.emailVerified,
      setProfile,
    }),
    [authUser, profile, initializing],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuthContext() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuthContext doit être utilisé dans un AuthProvider')
  return ctx
}
