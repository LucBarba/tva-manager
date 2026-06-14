//
// models/User.js
// Schéma du document `users/{userId}` et helpers de (dé)sérialisation.
//

import { initials as computeInitials, formatPresence } from '../utils/format'

/**
 * @typedef {Object} User
 * @property {string} id            - UID Firebase Auth (= identifiant du document).
 * @property {string} displayName   - Nom affiché.
 * @property {string} email         - Adresse email.
 * @property {?string} photoURL     - URL de la photo de profil (Storage).
 * @property {boolean} isOnline     - Statut de présence.
 * @property {*} lastSeen           - Timestamp de dernière activité.
 * @property {?string} fcmToken     - Jeton FCM pour les notifications push.
 * @property {*} createdAt          - Timestamp de création du compte.
 */

/** Construit un objet User depuis un DocumentSnapshot Firestore. */
export function userFromDoc(snapshot) {
  if (!snapshot || !snapshot.exists()) return null
  const data = snapshot.data()
  return {
    id: snapshot.id,
    displayName: data.displayName ?? '',
    email: data.email ?? '',
    photoURL: data.photoURL ?? null,
    isOnline: data.isOnline ?? false,
    lastSeen: data.lastSeen ?? null,
    fcmToken: data.fcmToken ?? null,
    createdAt: data.createdAt ?? null,
  }
}

/** Données à écrire à la création d'un utilisateur. */
export function newUserPayload({ uid, displayName, email }) {
  return {
    displayName,
    email,
    photoURL: null,
    isOnline: true,
    fcmToken: null,
  }
}

export function userInitials(user) {
  return computeInitials(user?.displayName)
}

export function userPresenceText(user) {
  return formatPresence(user?.isOnline, user?.lastSeen)
}
