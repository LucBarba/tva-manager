//
// services/storageService.js
// Upload/suppression de médias sur Firebase Storage, avec suivi de progression.
//

import { ref, uploadBytesResumable, getDownloadURL, deleteObject } from 'firebase/storage'
import { storage } from '../firebase/config'
import { validateMediaFile } from '../utils/validators'

export const storageService = {
  /**
   * Téléverse un fichier (Blob/File) et renvoie l'URL de téléchargement.
   * @param {string} path      Chemin complet dans le bucket.
   * @param {Blob|File} file
   * @param {(progress:number)=>void} [onProgress] Progression 0..1.
   */
  async upload(path, file, onProgress) {
    validateMediaFile(file)
    const storageRef = ref(storage, path)
    const task = uploadBytesResumable(storageRef, file, {
      contentType: file.type || 'application/octet-stream',
    })

    return new Promise((resolve, reject) => {
      task.on(
        'state_changed',
        (snapshot) => {
          if (onProgress && snapshot.totalBytes > 0) {
            onProgress(snapshot.bytesTransferred / snapshot.totalBytes)
          }
        },
        (error) => reject(error),
        async () => {
          try {
            const url = await getDownloadURL(task.snapshot.ref)
            resolve(url)
          } catch (e) {
            reject(e)
          }
        },
      )
    })
  },

  /** Supprime un objet à partir de son chemin. */
  async remove(path) {
    await deleteObject(ref(storage, path))
  },

  /** Construit un chemin unique horodaté. */
  buildPath(folder, conversationId, extension) {
    const stamp = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    return `${folder}/${conversationId}/${stamp}.${extension}`
  },
}
