import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

const headers = (development: boolean) => ({
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
  'X-Frame-Options': 'DENY',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'Content-Security-Policy': [
    "default-src 'self'",
    `script-src 'self'${development ? " 'unsafe-inline'" : ''}`,
    `connect-src 'self'${development ? ' ws:' : ''}`,
    `style-src-elem 'self'${development ? " 'unsafe-inline'" : ''}`,
    "style-src-attr 'unsafe-inline'",
    "img-src 'self' data:",
    "object-src 'none'",
    "base-uri 'none'",
    "frame-ancestors 'none'",
    "form-action 'self'",
  ].join('; '),
});

export default defineConfig({
  plugins: [react()],
  server: {
    headers: headers(true),
    port: 5173,
    strictPort: true,
    proxy: { '/api': process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000' },
  },
  preview: {
    headers: headers(false),
    port: 5173,
    strictPort: true,
    proxy: { '/api': process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000' },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    restoreMocks: true,
  },
});
