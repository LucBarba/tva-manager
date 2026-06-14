//
// components/Avatar.jsx
// Avatar utilisateur : photo si disponible, sinon initiales sur fond coloré.
//

import { initials } from '../utils/format'

export default function Avatar({ user, size = 'md' }) {
  const className = size === 'lg' ? 'avatar lg' : 'avatar'
  if (user?.photoURL) {
    return (
      <div className={className}>
        <img src={user.photoURL} alt={user.displayName || 'avatar'} />
      </div>
    )
  }
  return <div className={className} aria-hidden>{initials(user?.displayName)}</div>
}
