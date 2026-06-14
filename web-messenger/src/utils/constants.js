//
// utils/constants.js
// Constantes globales : collections Firestore, chemins Storage, limites.
//

export const Collections = {
  users: 'users',
  conversations: 'conversations',
  messages: 'messages',
}

export const StoragePaths = {
  profileImages: 'profile_images',
  chatImages: 'chat_images',
  chatVideos: 'chat_videos',
  chatThumbnails: 'chat_thumbnails',
}

export const Limits = {
  maxUsers: 2,
  maxMediaBytes: 50 * 1024 * 1024, // 50 Mo
  maxMessageLength: 4000,
  minPasswordLength: 8,
  messagePageSize: 40,
}

export const MessageType = {
  text: 'text',
  image: 'image',
  video: 'video',
}

export const MessageStatus = {
  sending: 'sending',
  sent: 'sent',
  delivered: 'delivered',
  read: 'read',
}

export const AppInfo = {
  name: 'DuoChat',
}
