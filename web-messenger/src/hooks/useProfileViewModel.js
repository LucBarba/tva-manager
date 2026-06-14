//
// hooks/useProfileViewModel.js
// "ViewModel" de l'écran Profil : mise à jour du nom et de la photo de profil.
//

import { useState, useCallback } from 'react'
import { userRepository } from '../repositories/userRepository'
import { storageService } from '../services/storageService'
import { StoragePaths } from '../utils/constants'
import { validateDisplayName, validateMediaFile } from '../utils/validators'
import { toUserMessage } from '../utils/errors'

export function useProfileViewModel(currentUserId) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [info, setInfo] = useState(null)

  const updateName = useCallback(
    async (displayName) => {
      setError(null)
      setInfo(null)
      setSaving(true)
      try {
        const clean = validateDisplayName(displayName)
        await userRepository.updateProfile(currentUserId, { displayName: clean })
        setInfo('Nom mis à jour.')
        return true
      } catch (e) {
        setError(toUserMessage(e))
        return false
      } finally {
        setSaving(false)
      }
    },
    [currentUserId],
  )

  const updatePhoto = useCallback(
    async (file) => {
      setError(null)
      setInfo(null)
      setSaving(true)
      try {
        validateMediaFile(file)
        const ext = (file.name?.split('.').pop() || 'jpg').toLowerCase()
        const path = `${StoragePaths.profileImages}/${currentUserId}/avatar_${Date.now()}.${ext}`
        const url = await storageService.upload(path, file)
        await userRepository.updateProfile(currentUserId, { photoURL: url })
        setInfo('Photo de profil mise à jour.')
        return true
      } catch (e) {
        setError(toUserMessage(e))
        return false
      } finally {
        setSaving(false)
      }
    },
    [currentUserId],
  )

  return { saving, error, info, updateName, updatePhoto }
}
