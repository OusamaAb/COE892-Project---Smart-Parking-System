import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// If `vite.config.js` is gitignored, copy this file to `vite.config.js` (README + GitHub Actions workflow do that).
// GitHub Actions builds with `--base=./` so assets resolve under your project path on Pages.
export default defineConfig({
  plugins: [react()],
})
