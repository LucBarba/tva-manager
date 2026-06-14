//
// hooks/useAuthViewModel.js
// "ViewModel" des écrans d'authentification : inscription, connexion,
// réinitialisation et vérification d'email, avec validation et gestion d'erreurs.
//

import { useState, useCallback } from 'react'
import { authService } from '../services/authService'
import { userRepository } from '../repositories/userRepository'
import { validateEmail, validatePassword, validateDisplayName } from '../utils/validators'
import { toUserMessage } from '../utils/errors'

export function useAuthViewModel() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [info, setInfo] = useState(null)

  const reset = useCallback(() => {
    setError(null)
    setInfo(null)
  }, [])

  const register = useCallback(async ({ email, password, displayName }) => {
    reset()
    setLoading(true)
    try {
      const cleanEmail = validateEmail(email)
      const cleanPassword = validatePassword(password)
      const cleanName = validateDisplayName(displayName)

      const user = await authService.register({
        email: cleanEmail,
        password: cleanPassword,
        displayName: cleanName,
      })
      // Création du document Firestore (avec garde-fou des 2 utilisateurs).
      await userRepository.createUserIfAllowed({
        uid: user.uid,
        displayName: cleanName,
        email: cleanEmail,
      })
      // Envoi de l'email de vérification.
      await authService.sendVerificationEmail()
      setInfo('Compte créé. Un email de vérification vous a été envoyé.')
      return true
    } catch (e) {
      setError(toUserMessage(e))
      return false
    } finally {
      setLoading(false)
    }
  }, [reset])

  const signIn = useCallback(async ({ email, password }) => {
    reset()
    setLoading(true)
    try {
      const cleanEmail = validateEmail(email)
      await authService.signIn({ email: cleanEmail, password })
      return true
    } catch (e) {
      setError(toUserMessage(e))
      return false
    } finally {
      setLoading(false)
    }
  }, [reset])

  const sendPasswordReset = useCallback(async (email) => {
    reset()
    setLoading(true)
    try {
      const cleanEmail = validateEmail(email)
      await authService.sendPasswordReset(cleanEmail)
      setInfo('Un email de réinitialisation vous a été envoyé.')
      return true
    } catch (e) {
      setError(toUserMessage(e))
      return false
    } finally {
      setLoading(false)
    }
  }, [reset])

  const resendVerification = useCallback(async () => {
    reset()
    setLoading(true)
    try {
      await authService.sendVerificationEmail()
      setInfo('Email de vérification renvoyé.')
    } catch (e) {
      setError(toUserMessage(e))
    } finally {
      setLoading(false)
    }
  }, [reset])

  const refreshVerification = useCallback(async () => {
    const user = await authService.reloadCurrentUser()
    return !!user?.emailVerified
  }, [])

  const signOut = useCallback(async () => {
    try {
      const uid = authService.currentUser?.uid
      if (uid) await userRepository.setOnline(uid, false)
    } catch {
      /* non bloquant */
    }
    await authService.signOut()
  }, [])

  return {
    loading,
    error,
    info,
    reset,
    register,
    signIn,
    sendPasswordReset,
    resendVerification,
    refreshVerification,
    signOut,
  }
}
