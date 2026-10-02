// The shared inbox is only available on the explicitly supported local environments.
export function localEmailUrl(origin = window.location.origin): string | undefined {
  const url = new URL(origin);
  if (!['localhost', '127.0.0.1'].includes(url.hostname)) return;
  if (import.meta.env.VITE_DEMO_MODE === 'true' && url.protocol === 'https:' && url.port === '8443')
    return `http://${url.hostname}:8026`;
  if (import.meta.env.DEV && url.protocol === 'http:' && url.port === '5173')
    return `http://${url.hostname}:8025`;
}
