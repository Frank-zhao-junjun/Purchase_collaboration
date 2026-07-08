import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5000,
    proxy: {
      '/dashboard': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/suppliers': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/materials': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/products': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/purchase-orders': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/sales-orders': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/production': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/warehouses': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/supplier-portal': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/sourcing': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/contracts': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/contract-templates': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/announcements': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/logistics': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/financial': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/qualification': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/collaboration': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
