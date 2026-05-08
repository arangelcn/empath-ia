import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/** Carrega .env da raiz do monorepo (empath-ia/.env) onde está GOOGLE_CLIENT_ID. */
function loadEnvFromRepoRoot(mode) {
  const repoRoot = path.resolve(__dirname, '../..')
  if (fs.existsSync(path.join(repoRoot, '.env'))) {
    return loadEnv(mode, repoRoot, '')
  }
  return {}
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const cwdEnv = loadEnv(mode, process.cwd(), '')
  const rootEnv = loadEnvFromRepoRoot(mode)
  const merged = { ...rootEnv, ...cwdEnv }

  // Ordem: Docker build (ENV) → apps/web-ui/.env → raiz GOOGLE_CLIENT_ID
  const viteGoogleClientId =
    process.env.VITE_GOOGLE_CLIENT_ID ||
    merged.VITE_GOOGLE_CLIENT_ID ||
    merged.GOOGLE_CLIENT_ID ||
    ''

  const apiUrl =
    merged.VITE_API_URL || cwdEnv.VITE_API_URL || 'http://localhost:8000'
  const voiceUrl =
    merged.VITE_VOICE_URL || cwdEnv.VITE_VOICE_URL || 'http://localhost:8004'

  return {
    define: {
      'import.meta.env.VITE_GOOGLE_CLIENT_ID': JSON.stringify(viteGoogleClientId),
    },
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
          target: apiUrl,
          changeOrigin: true,
          secure: false,
        },
        '/voice-service': {
          target: voiceUrl,
          changeOrigin: true,
          secure: false,
          rewrite: (p) => p.replace(/^\/voice-service/, ''),
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
    },
  }
})
