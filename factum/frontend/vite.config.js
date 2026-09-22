import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// In dev, the backend runs on :8080; the built app is served by the backend itself.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:8080', '/ws': { target: 'ws://localhost:8080', ws: true } } },
});
