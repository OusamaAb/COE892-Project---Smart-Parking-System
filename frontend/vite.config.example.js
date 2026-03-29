import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// For GitHub project Pages, production builds use --base="/<repo-name>/" in CI.
// Local dev keeps default base "/".
export default defineConfig({
  plugins: [react()],
})
