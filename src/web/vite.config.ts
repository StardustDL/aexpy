import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import loadVersion from 'vite-plugin-package-version'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), loadVersion()],
  build: {
    chunkSizeWarningLimit: 1000,
    brotliSize: false,
  },
  server: {
    port: 3000
  }
})
