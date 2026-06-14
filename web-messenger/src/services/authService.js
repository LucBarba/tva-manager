//
// services/authService.js
// Encapsule Firebase Authentication : inscription, connexion, déconnexion,
// réinitialisation et vérification d'email.
//

import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut as fbSignOut,
  sendPasswordResetEmail,
  sendEmailVerification,
  onAuthStateChanged,
  updateProfile,
  reload,
} from 'firebase/auth'
import { auth } from '../firebase/config'

export const authService = {
  /** Utilisateur Firebase Auth courant (ou null). */
  get currentUser() {
    return auth.currentUser
  },

  /** Inscription par email/mot de passe + définition du displayName. */
  async register({ email, password, displayName }) {
    const credential = await createUserWithEmailAndPassword(auth, email, password)
    if (displayName) {
      await updateProfile(credential.user, { displayName })
    }
    return credential.user
  },

  /** Connexion par email/mot de passe. */
  async signIn({ email, password }) {
    const credential = await signInWithEmailAndPassword(auth, email, password)
    return credential.user
  },

  /** Déconnexion. */
  async signOut() {
    await fbSignOut(auth)
  },

  /** Envoi d'un email de réinitialisation de mot de passe. */
  async sendPasswordReset(email) {
    await sendPasswordResetEmail(auth, email)
  },

  /** Envoi d'un email de vérification à l'utilisateur courant. */
  async sendVerificationEmail() {
    if (!auth.currentUser) return
    await sendEmailVerification(auth.currentUser)
  },

  /** Recharge l'utilisateur courant (rafraîchit emailVerified). */
  async reloadCurrentUser() {
    if (!auth.currentUser) return null
    await reload(auth.currentUser)
    return auth.currentUser
  },

  /** Abonnement aux changements d'état d'authentification. Renvoie l'unsubscribe. */
  onAuthChanged(callback) {
    return onAuthStateChanged(auth, callback)
  },
}
