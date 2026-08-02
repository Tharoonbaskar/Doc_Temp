import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return undefined
          }

          if (id.includes('@tiptap') || id.includes('prosemirror')) {
            return 'vendor-tiptap'
          }

          if (id.includes('@mui') || id.includes('@emotion')) {
            return 'vendor-mui'
          }

          if (
            id.includes('@reduxjs') ||
            id.includes('react-redux') ||
            id.includes('@tanstack/react-query')
          ) {
            return 'vendor-state'
          }

          if (
            id.includes('react-hook-form') ||
            id.includes('@hookform/resolvers') ||
            id.includes('zod') ||
            id.includes('axios')
          ) {
            return 'vendor-forms-api'
          }

          if (
            id.includes('react-router') ||
            id.includes('react-dom') ||
            id.includes('/react/') ||
            id.includes('scheduler')
          ) {
            return 'vendor-react'
          }

          return 'vendor-misc'
        },
      },
    },
  },
})
