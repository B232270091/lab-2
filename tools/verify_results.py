"""Verify that the submitted report agrees with its retained k6 evidence."""

import json
import math
import re
from datetime import datetime
from pathlib import Path

from summarize_timeline import summarize

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / 'README.md').read_text(encoding='utf-8')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load(name):
    return json.loads((ROOT / 'results' / name).read_text(encoding='utf-8'))


def verify_run(stem):
    summary = load(stem + '.json')
    metrics = summary['metrics']
    text = (ROOT / 'results' / (stem + '.txt')).read_text(encoding='utf-8')
    duration_line = next(line for line in text.splitlines()
                         if line.strip().startswith('http_req_duration.'))
    for stat in ('avg', 'p(90)', 'p(95)', 'p(99)'):
        value = metrics['http_req_duration'][stat]
        require(math.isfinite(value), f'{stem}: invalid {stat}')
        require(f'{stat}={value:.2f}ms' in duration_line, f'{stem}: {stat} text/JSON mismatch')
    request_line = next(line for line in text.splitlines()
                        if line.strip().startswith('http_reqs.'))
    require(re.search(r':\s*' + str(metrics['http_reqs']['count']) + r'\s', request_line),
            f'{stem}: request count mismatch')
    require(f"{metrics['http_reqs']['rate']:.6f}/s" in request_line,
            f'{stem}: throughput mismatch')
    error_line = next(line for line in text.splitlines()
                      if line.strip().startswith('http_req_failed.'))
    require(f"{metrics['http_req_failed']['value'] * 100:.2f}%" in error_line,
            f'{stem}: error rate mismatch')
    meta = load(stem + '.meta.json')
    require(datetime.fromisoformat(meta['started_at']) < datetime.fromisoformat(meta['finished_at']),
            f'{stem}: invalid timestamps')
    require(meta['target'] in ('https://test.k6.io', 'http://127.0.0.1:8000/slow',
                              'http://127.0.0.1:8000/fast'), f'{stem}: unexpected target')
    expected_code = 99 if stem == 'run-slo-fail' else 0
    require(meta['exit_code'] == expected_code, f'{stem}: wrong exit code')
    if meta['target'].startswith('http://127.0.0.1:'):
        require(metrics['checks']['value'] == 1, f'{stem}: failed status check')
    return metrics


def main():
    all_runs = {}
    for meta in sorted((ROOT / 'results').glob('*.meta.json')):
        stem = meta.name.removesuffix('.meta.json')
        all_runs[stem] = verify_run(stem)
    require(len(all_runs) == 11, 'Expected 11 recorded k6 runs')

    for vu, stem in ((5, 'run-05vu'), (30, 'run-30vu'), (100, 'run-100vu')):
        metrics = all_runs[stem]
        duration, requests = metrics['http_req_duration'], metrics['http_reqs']
        prefix = (f"| {vu} | {duration['avg']:.2f} | {duration['p(90)']:.2f} | "
                  f"{duration['p(95)']:.2f} | {duration['p(99)']:.2f} | "
                  f"{requests['count']} | {requests['rate']:.6f} | "
                  f"{metrics['http_req_failed']['value'] * 100:.2f}% |")
        require(prefix in README, f'{stem}: README table mismatch')

    baseline_p95 = all_runs['baseline-05vu']['http_req_duration']['p(95)']
    slo = math.ceil(baseline_p95 * 1.5)
    require(f'{baseline_p95:.6f} ms' in README, 'Baseline p95 mismatch')
    require(f'p(95)<{slo}' in README, 'Baseline-derived SLO mismatch')
    for stem, threshold, failed, exit_code in (
            ('run-slo-pass', f'p(95)<{slo}', False, 0),
            ('run-slo-fail', 'p(95)<50', True, 99)):
        metrics = all_runs[stem]
        require(metrics['http_req_duration']['thresholds'] == {threshold: failed},
                f'{stem}: wrong threshold outcome')
        p95 = metrics['http_req_duration']['p(95)']
        require(f'| {p95:.2f} | 0.00% | {exit_code} |' in README,
                f'{stem}: README outcome mismatch')

    windows = summarize()
    require(windows == load('stages-windows.json'), 'Derived timeline is stale')
    for window in windows['windows']:
        require(f"| {window['p95_ms']:.2f} | {window['throughput_rps']:.6f} | "
                f"{window['requests']} |" in README, 'Timeline README mismatch')
    fast = all_runs['run-fast-30vu']
    require(f"| 1.61 | {fast['http_req_duration']['p(95)']:.2f} | "
            f"{fast['http_reqs']['rate']:.6f} | 0.00% |" in README,
            'Fast endpoint README mismatch')

    version = (ROOT / 'results/k6-version.txt').read_text(encoding='utf-8').strip()
    require(version in README, 'k6 version mismatch')
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', README):
        if not target.startswith(('http://', 'https://', '#')):
            require((ROOT / target).is_file(), f'Broken README link: {target}')
    screenshots = list((ROOT / 'screenshots').glob('*.jpg'))
    require(len(screenshots) == 8, 'Expected eight screenshots')
    for screenshot in screenshots:
        raw = screenshot.read_bytes()
        require(raw.startswith(b'\xff\xd8\xff') and len(raw) > 20000,
                f'Invalid JPEG screenshot: {screenshot.name}')
    print('Verified 11 runs, README measurements, baseline SLO, PASS/FAIL, timeline, links and 8 screenshots.')


if __name__ == '__main__':
    main()
