import path from "path";
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      "/health": "http://127.0.0.1:8001",
    },
  },
  build: {
    outDir: 'dist',
  },
  preview: {
    allowedHosts: ['cajaaldia.up.railway.app'],
  },
  resolve: {
    alias: {
      "@assets": path.resolve(__dirname, "./assets"),
    },
  },
});
