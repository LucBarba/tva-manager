//
// repositories/userRepository.js
// Gestion des documents `users` : création, présence, profil, jeton FCM,
// et garde-fou des 2 utilisateurs maximum.
//

import { firestoreService as fs } from '../services/firestoreService'
import { Collections, Limits } from '../utils/constants'
import { userFromDoc, newUserPayload } from '../models/User'
import { AppError } from '../utils/errors'

export const userRepository = {
  /** Récupère un utilisateur par UID. */
  async getUser(uid) {
    const snap = await fs.getDoc(fs.docRef(Collections.users, uid))
    return userFromDoc(snap)
  },

  /** Nombre d'utilisateurs déjà inscrits. */
  async countUsers() {
    const snap = await fs.getDocs(fs.collectionRef(Collections.users))
    return snap.size
  },

  /**
   * Crée le document utilisateur après inscription Auth.
   * Refuse si le quota de 2 utilisateurs est déjà atteint (double sécurité,
   * la règle Firestore l'impose aussi côté serveur).
   */
  async createUserIfAllowed({ uid, displayName, email }) {
    const existing = await this.getUser(uid)
    if (existing) return existing

    const count = await this.countUsers()
    if (count >= Limits.maxUsers) {
      throw new AppError(
        `Inscriptions fermées : l'application est limitée à ${Limits.maxUsers} utilisateurs.`,
        'app/registration-closed',
      )
    }

    const payload = {
      ...newUserPayload({ uid, displayName, email }),
      lastSeen: fs.serverTimestamp(),
      createdAt: fs.serverTimestamp(),
    }
    await fs.setDoc(fs.docRef(Collections.users, uid), payload)
    return this.getUser(uid)
  },

  /** Met à jour le statut de présence. */
  async setOnline(uid, isOnline) {
    await fs.updateDoc(fs.docRef(Collections.users, uid), {
      isOnline,
      lastSeen: fs.serverTimestamp(),
    })
  },

  /** Met à jour le jeton FCM. */
  async setFcmToken(uid, token) {
    if (!token) return
    await fs.updateDoc(fs.docRef(Collections.users, uid), { fcmToken: token })
  },

  /** Met à jour le profil (nom et/ou photo). */
  async updateProfile(uid, { displayName, photoURL }) {
    const data = {}
    if (displayName !== undefined) data.displayName = displayName
    if (photoURL !== undefined) data.photoURL = photoURL
    if (Object.keys(data).length === 0) return
    await fs.updateDoc(fs.docRef(Collections.users, uid), data)
  },

  /** Écoute en temps réel un document utilisateur. Renvoie l'unsubscribe. */
  listenUser(uid, callback, onError) {
    return fs.listen(
      fs.docRef(Collections.users, uid),
      (snap) => callback(userFromDoc(snap)),
      onError,
    )
  },

  /** Écoute tous les utilisateurs (pour trouver le correspondant). */
  listenAllUsers(callback, onError) {
    return fs.listen(
      fs.collectionRef(Collections.users),
      (snap) => callback(snap.docs.map((d) => userFromDoc(d))),
      onError,
    )
  },
}
