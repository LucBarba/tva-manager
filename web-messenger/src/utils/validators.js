//
// utils/validators.js
// Validation des entrées utilisateur.
//

import { AppError } from './errors'
import { Limits } from './constants'

const EMAIL_REGEX = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i

/** Valide et normalise une adresse email. */
export function validateEmail(raw) {
  const email = String(raw || '').trim().toLowerCase()
  if (!EMAIL_REGEX.test(email)) {
    throw new AppError("L'adresse email est invalide.", 'app/invalid-email')
  }
  return email
}

/** Valide un mot de passe : longueur min + au moins une lettre et un chiffre. */
export function validatePassword(password) {
  const value = String(password || '')
  const hasLetter = /[A-Za-z]/.test(value)
  const hasDigit = /[0-9]/.test(value)
  if (value.length < Limits.minPasswordLength || !hasLetter || !hasDigit) {
    throw new AppError(
      `Le mot de passe doit contenir au moins ${Limits.minPasswordLength} caractères, dont une lettre et un chiffre.`,
      'app/weak-password',
    )
  }
  return value
}

/** Valide un nom affiché (2 à 40 caractères). */
export function validateDisplayName(raw) {
  const name = String(raw || '').trim()
  if (name.length < 2 || name.length > 40) {
    throw new AppError('Le nom affiché doit contenir entre 2 et 40 caractères.', 'app/invalid-name')
  }
  return name
}

/** Nettoie et valide un message texte. Renvoie null si vide. */
export function sanitizeMessage(raw) {
  const text = String(raw || '').trim()
  if (!text) return null
  if (text.length > Limits.maxMessageLength) {
    throw new AppError(`Le message est trop long (max ${Limits.maxMessageLength} caractères).`, 'app/message-too-long')
  }
  return text
}

/** Vérifie la taille d'un fichier média avant upload. */
export function validateMediaFile(file) {
  if (!file) throw new AppError('Aucun fichier sélectionné.', 'app/no-file')
  if (file.size > Limits.maxMediaBytes) {
    throw new AppError('Le fichier est trop volumineux (max 50 Mo).', 'app/media-too-large')
  }
  return file
}
