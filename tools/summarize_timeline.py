"""Summarize k6 samples; split the ramp-down into finer 10-second windows."""

import gzip
import json
import math
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def percentile(values, fraction):
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def summarize():
    points = []
    last_time = None
    with gzip.open(ROOT / 'results/stages-timeline.json.gz', 'rt', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if row['type'] != 'Point':
                continue
            instant = datetime.fromisoformat(row['data']['time'])
            last_time = instant if last_time is None else max(last_time, instant)
            if row['metric'] in ('http_req_duration', 'http_reqs', 'vus'):
                points.append((row['metric'], instant, row['data']['value']))
    origin = min(t for metric, t, value in points if metric == 'http_req_duration')
    elapsed = (last_time - origin).total_seconds()
    windows = []
    boundaries = [0, 30, 60, 90, 120, 130, 140, elapsed + 0.000001]
    for lower, upper in zip(boundaries, boundaries[1:]):
        selected = [(metric, value) for metric, instant, value in points
                    if lower <= (instant - origin).total_seconds() < upper]
        durations = [value for metric, value in selected if metric == 'http_req_duration']
        users = [value for metric, value in selected if metric == 'vus']
        count = sum(value for metric, value in selected if metric == 'http_reqs')
        seconds = upper - lower
        windows.append({'from_s': lower, 'to_s': round(upper, 6),
                        'observed_vu_min': min(users), 'observed_vu_max': max(users),
                        'requests': count, 'throughput_rps': count / seconds,
                        'p95_ms': percentile(durations, 0.95)})
    summary = json.loads((ROOT / 'results/run-stages-timeline.json').read_text(encoding='utf-8'))
    all_durations = [v for metric, t, v in points if metric == 'http_req_duration']
    expected = summary['metrics']
    assert sum(w['requests'] for w in windows) == expected['http_reqs']['count']
    assert math.isclose(percentile(all_durations, .95),
                        expected['http_req_duration']['p(95)'], abs_tol=0.000001)
    return {'source': 'results/stages-timeline.json.gz',
            'time_origin': origin.isoformat(),
            'method': '30-second windows and 10-second ramp-down windows relative to first completed HTTP request; linear percentile interpolation',
            'windows': windows}


if __name__ == '__main__':
    data = summarize()
    output = ROOT / 'results/stages-windows.json'
    output.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    for window in data['windows']:
        print(f"{window['from_s']:3d}-{window['to_s']:7.2f}s: "
              f"VU {window['observed_vu_min']:.0f}-{window['observed_vu_max']:.0f}, "
              f"p95={window['p95_ms']:.2f} ms, "
              f"throughput={window['throughput_rps']:.6f}/s, requests={window['requests']:.0f}")
