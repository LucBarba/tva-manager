import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Configuration Vite pour l'application web DuoChat.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    host: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
