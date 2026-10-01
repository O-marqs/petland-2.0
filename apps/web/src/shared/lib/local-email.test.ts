import { afterEach, expect, it, vi } from 'vitest';
import { localEmailUrl } from './local-email';

afterEach(() => vi.unstubAllEnvs());

it('offers the correct inbox only for the explicitly local development and demo origins', () => {
  vi.stubEnv('DEV', true);
  vi.stubEnv('VITE_DEMO_MODE', 'true');
  expect(localEmailUrl('https://localhost:8443')).toBe('http://localhost:8026');
  expect(localEmailUrl('http://127.0.0.1:5173')).toBe('http://127.0.0.1:8025');
  for (const origin of [
    'https://petland.example:8443',
    'https://localhost.evil.example:8443',
    'https://localhost:443',
    'http://localhost:8443',
    'http://localhost:3000',
  ])
    expect(localEmailUrl(origin)).toBeUndefined();
  vi.stubEnv('DEV', false);
  vi.stubEnv('VITE_DEMO_MODE', 'false');
  expect(localEmailUrl('https://localhost:8443')).toBeUndefined();
  expect(localEmailUrl('http://localhost:5173')).toBeUndefined();
});
