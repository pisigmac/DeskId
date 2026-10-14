import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@deskid/core': path.resolve(__dirname, '../../packages/core/dist/index.js'),
      '@deskid/react': path.resolve(__dirname, '../../packages/react/dist/index.js')
    }
  },
  server: {
    port: 3000,
    host: true
  }
})
