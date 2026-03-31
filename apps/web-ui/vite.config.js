import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 3000,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://gateway:8000',
          changeOrigin: true,
          secure: false,
        },
        '/voice-service': {
          target: env.VITE_VOICE_URL || 'http://voice-service:8004',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/voice-service/, ''),
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
    },
  }
}) 