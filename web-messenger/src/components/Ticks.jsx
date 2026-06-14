//
// components/Ticks.jsx
// Coches de statut façon WhatsApp : une coche (envoyé), deux coches (reçu),
// deux coches bleues (lu), horloge (en cours d'envoi).
//

import { MessageStatus } from '../utils/constants'

function SingleCheck() {
  return (
    <svg viewBox="0 0 16 11" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M1 6l3.2 3.2L11 2" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function DoubleCheck() {
  return (
    <svg viewBox="0 0 16 11" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M0.5 6l3 3L9.5 2.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5.5 6l3 3L15 2.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function Clock() {
  return (
    <svg viewBox="0 0 16 11" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="8" cy="5.5" r="4" stroke="currentColor" strokeWidth="1.2" />
      <path d="M8 3.5V5.5L9.5 6.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  )
}

export default function Ticks({ status }) {
  if (status === MessageStatus.sending) {
    return <span className="ticks"><Clock /></span>
  }
  if (status === MessageStatus.sent) {
    return <span className="ticks"><SingleCheck /></span>
  }
  const read = status === MessageStatus.read
  return <span className={`ticks ${read ? 'read' : ''}`}><DoubleCheck /></span>
}
