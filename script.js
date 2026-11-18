import { request } from './lib/request.js';

export const options = {
  vus: 5,
  duration: '30s',
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
};

export default request;
