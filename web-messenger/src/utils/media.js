//
// utils/media.js
// Traitement média côté client : dimensions d'image et génération de vignette
// vidéo (première image) pour l'aperçu dans le chat.
//

/** Renvoie { width, height } d'un fichier image. */
export function getImageDimensions(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      resolve({ width: img.naturalWidth, height: img.naturalHeight })
      URL.revokeObjectURL(url)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Image illisible'))
    }
    img.src = url
  })
}

/**
 * Génère une vignette JPEG à partir de la première image d'une vidéo.
 * Renvoie { blob, width, height }.
 */
export function generateVideoThumbnail(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.muted = true
    video.playsInline = true
    video.src = url

    const cleanup = () => URL.revokeObjectURL(url)

    video.onloadeddata = () => {
      // Se positionner légèrement après le début pour éviter une image noire.
      try {
        video.currentTime = Math.min(0.1, video.duration || 0.1)
      } catch {
        captureFrame()
      }
    }

    video.onseeked = captureFrame

    function captureFrame() {
      try {
        const canvas = document.createElement('canvas')
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        const ctx = canvas.getContext('2d')
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
        canvas.toBlob(
          (blob) => {
            cleanup()
            if (!blob) {
              reject(new Error('Vignette indisponible'))
              return
            }
            resolve({ blob, width: video.videoWidth, height: video.videoHeight })
          },
          'image/jpeg',
          0.8,
        )
      } catch (e) {
        cleanup()
        reject(e)
      }
    }

    video.onerror = () => {
      cleanup()
      reject(new Error('Vidéo illisible'))
    }
  })
}
