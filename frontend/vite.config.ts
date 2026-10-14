import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/v1': {
        target: 'http://127.0.0.1:8090',
        changeOrigin: true
      },
      '/.well-known': {
        target: 'http://127.0.0.1:8090',
        changeOrigin: true
      },
      '/health': {
        target: 'http://127.0.0.1:8090',
        changeOrigin: true
      },
      '/metrics': {
        target: 'http://127.0.0.1:8090',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
