import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        "name": "AexPy",
        "short_name": "AexPy",
        "icons": [
          {
            "src": "assets/icons/pwa-192x192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any"
          },
          {
            "src": "assets/icons/pwa-512x512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any"
          },
          {
            "src": "assets/icons/pwa-maskable-192x192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "maskable"
          },
          {
            "src": "assets/icons/pwa-maskable-512x512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "maskable"
          }
        ],
        "start_url": "/",
        "display": "standalone",
        "background_color": "#FFFFFF",
        "theme_color": "#4381b3",
        "description": "AexPy /eɪkspaɪ/ is Api EXplorer in PYthon for detecting API breaking changes in Python packages."
      },
      devOptions: {
        enabled: false
      }
    })
  ],
  build: {
    chunkSizeWarningLimit: 2000,
  },
  server: {
    port: 8001
  },
})
