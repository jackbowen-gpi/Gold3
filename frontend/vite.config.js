import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  root: 'src',
  server: {
    port: 5173,
    strictPort: true
  },
  build: {
    outDir: resolve(__dirname, '../static/frontend'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'src/main.js')
      }
    }
  }
})
