//
// utils/errors.js
// Traduction des erreurs Firebase en messages localisés (français).
//

const FIREBASE_ERROR_MESSAGES = {
  'auth/invalid-email': "L'adresse email est invalide.",
  'auth/user-disabled': 'Ce compte a été désactivé.',
  'auth/user-not-found': 'Aucun compte ne correspond à cette adresse.',
  'auth/wrong-password': 'Email ou mot de passe incorrect.',
  'auth/invalid-credential': 'Email ou mot de passe incorrect.',
  'auth/email-already-in-use': 'Un compte existe déjà avec cette adresse email.',
  'auth/weak-password': 'Le mot de passe est trop faible (8 caractères minimum).',
  'auth/too-many-requests': 'Trop de tentatives. Réessayez plus tard.',
  'auth/network-request-failed': 'Problème de connexion réseau.',
  'auth/requires-recent-login': 'Veuillez vous reconnecter pour effectuer cette action.',
  'permission-denied': "Vous n'êtes pas autorisé à effectuer cette action.",
  'storage/unauthorized': "Accès au fichier non autorisé.",
  'storage/canceled': "L'envoi a été annulé.",
  'storage/retry-limit-exceeded': "L'envoi du fichier a échoué. Réessayez.",
}

/** Erreur applicative présentable à l'utilisateur. */
export class AppError extends Error {
  constructor(message, code = 'app/unknown') {
    super(message)
    this.name = 'AppError'
    this.code = code
  }
}

/** Convertit n'importe quelle erreur en message lisible par l'utilisateur. */
export function toUserMessage(error) {
  if (!error) return 'Une erreur est survenue.'
  if (error instanceof AppError) return error.message
  const code = error.code || ''
  if (FIREBASE_ERROR_MESSAGES[code]) return FIREBASE_ERROR_MESSAGES[code]
  return error.message || 'Une erreur inattendue est survenue.'
}
