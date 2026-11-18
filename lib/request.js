import http from 'k6/http';
import { check, sleep } from 'k6';

export const target = __ENV.TARGET_URL || 'https://test.k6.io';
const allowed = /^https:\/\/test\.k6\.io\/?$/.test(target)
  || /^http:\/\/127\.0\.0\.1:8000\/(fast|slow)$/.test(target);

if (!allowed) {
  throw new Error('TARGET_URL must be https://test.k6.io or the local /fast or /slow endpoint.');
}

export function request() {
  const response = http.get(target, { timeout: '10s', redirects: 0 });
  check(response, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
