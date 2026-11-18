import { request, target } from './lib/request.js';

if (target !== 'http://127.0.0.1:8000/slow') {
  throw new Error('The saved baseline and SLO apply only to the local /slow endpoint.');
}

const baseline = JSON.parse(open('./results/baseline-05vu.json'));
const baselineP95 = baseline.metrics.http_req_duration['p(95)'];
if (!Number.isFinite(baselineP95) || baselineP95 <= 0) {
  throw new Error('Run the baseline phase first and provide a valid measured p95.');
}
export const sloMs = __ENV.STRICT_SLO === '1' ? 50 : Math.ceil(baselineP95 * 1.5);

export const options = {
  vus: 30,
  duration: '1m',
  thresholds: {
    http_req_duration: [`p(95)<${sloMs}`],
    http_req_failed: ['rate<0.01'],
    checks: ['rate==1'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
};

export default request;
