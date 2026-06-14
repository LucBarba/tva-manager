//
// components/Spinner.jsx
// Indicateur de chargement circulaire.
//

export default function Spinner({ dark = false }) {
  return <div className={`spinner ${dark ? 'dark' : ''}`} role="status" aria-label="Chargement" />
}
