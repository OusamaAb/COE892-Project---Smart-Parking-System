import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// GitHub Actions builds with --base=./ so assets load under your project path
// even if the github.io URL casing differs from the repo name.
export default defineConfig({
  plugins: [react()],
})
