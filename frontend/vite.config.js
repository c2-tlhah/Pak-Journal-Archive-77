import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: process.env.NODE_ENV === 'production' ? '/Pak-Journal-Archive-77/' : '/',
  build: {
    outDir: 'dist',
  },
})
