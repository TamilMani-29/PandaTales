import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
      '/minio': {
        target: process.env.VITE_MINIO_PROXY_TARGET || 'http://localhost:9000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/minio/, ''),
      },
    },
  },
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
});
