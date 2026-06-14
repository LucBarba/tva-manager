//
// utils/format.js
// Formatage des dates et helpers d'affichage.
//

/** Convertit un Timestamp Firestore (ou Date) en objet Date. */
export function toDate(value) {
  if (!value) return null
  if (value instanceof Date) return value
  if (typeof value.toDate === 'function') return value.toDate()
  if (typeof value.seconds === 'number') return new Date(value.seconds * 1000)
  return null
}

const timeFormatter = new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit' })
const dayFormatter = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })

/** Heure courte, ex : "14:32". */
export function formatTime(value) {
  const date = toDate(value)
  return date ? timeFormatter.format(date) : ''
}

/** Libellé de séparateur de jour : "Aujourd'hui", "Hier", "12 juin 2026". */
export function formatDaySeparator(value) {
  const date = toDate(value)
  if (!date) return ''
  const today = new Date()
  const yesterday = new Date()
  yesterday.setDate(today.getDate() - 1)
  if (isSameDay(date, today)) return "Aujourd'hui"
  if (isSameDay(date, yesterday)) return 'Hier'
  return dayFormatter.format(date)
}

/** Texte de présence : "En ligne" ou "Vu il y a …". */
export function formatPresence(isOnline, lastSeen) {
  if (isOnline) return 'En ligne'
  const date = toDate(lastSeen)
  if (!date) return 'Hors ligne'
  return `Vu ${formatRelative(date)}`
}

const rtf = new Intl.RelativeTimeFormat('fr-FR', { numeric: 'auto' })

/** Temps relatif compact, ex : "il y a 5 minutes". */
export function formatRelative(date) {
  const diffSec = Math.round((date.getTime() - Date.now()) / 1000)
  const abs = Math.abs(diffSec)
  if (abs < 60) return rtf.format(Math.round(diffSec), 'second')
  if (abs < 3600) return rtf.format(Math.round(diffSec / 60), 'minute')
  if (abs < 86400) return rtf.format(Math.round(diffSec / 3600), 'hour')
  return rtf.format(Math.round(diffSec / 86400), 'day')
}

export function isSameDay(a, b) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

/** Initiales pour l'avatar de repli. */
export function initials(name) {
  return String(name || '')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join('')
}
