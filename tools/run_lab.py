"""Run real k6 processes and retain their complete merged output and exit codes."""

import argparse
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = 'http://127.0.0.1:8000/slow'
FAST = 'http://127.0.0.1:8000/fast'
RUNS = {
    'baseline': [
        ('baseline-05vu', 'script.js', LOCAL, []),
    ],
    'practice': [
        ('run-practice', 'script.js', 'https://test.k6.io', []),
    ],
    'load': [
        ('run-05vu', 'script.js', LOCAL, ['--vus', '5', '--duration', '1m']),
        ('run-30vu', 'script.js', LOCAL, ['--vus', '30', '--duration', '1m']),
        ('run-100vu', 'script.js', LOCAL, ['--vus', '100', '--duration', '1m']),
        ('run-stages', 'stages.js', LOCAL, []),
        ('run-fast-30vu', 'script.js', FAST, ['--vus', '30', '--duration', '1m']),
    ],
    'slo': [
        ('run-slo-pass', 'thresholds.js', LOCAL, []),
        ('run-slo-fail', 'thresholds.js', LOCAL, ['-e', 'STRICT_SLO=1']),
    ],
    'diagnostic': [
        ('run-practice-redirect', 'script.js', 'https://test.k6.io',
         ['--vus', '1', '--iterations', '1', '--http-debug']),
    ],
    'timeline': [
        ('run-stages-timeline', 'stages.js', LOCAL,
         ['--out', 'json=results/stages-timeline.json.gz']),
    ],
}


def now():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=RUNS)
    parser.add_argument('--k6', default=shutil.which('k6'))
    args = parser.parse_args()
    if not args.k6:
        parser.error('Install k6 or pass --k6 /path/to/k6')
    executable = str(Path(args.k6).resolve())
    os.chdir(ROOT)
    results = ROOT / 'results'
    results.mkdir(exist_ok=True)
    for name, script, target, overrides in RUNS[args.phase]:
        log = results / f'{name}.txt'
        if log.exists():
            raise SystemExit(f'{log.name} already exists; move old results before rerunning.')
        command = [executable, 'run', '--no-color', '--quiet', '--no-usage-report',
                   '--summary-time-unit', 'ms', '--summary-export', f'results/{name}.json',
                   '-e', f'TARGET_URL={target}', *overrides, script]
        started = now()
        print(f'{started} START {name}', flush=True)
        with log.open('w', encoding='utf-8', newline='') as output:
            process = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT,
                                     encoding='utf-8', check=False)
        metadata = {
            'started_at': started, 'finished_at': now(), 'target': target,
            'command': ['k6', *command[1:]], 'exit_code': process.returncode,
            'platform': platform.platform(), 'python_version': platform.python_version(),
        }
        (results / f'{name}.meta.json').write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'{metadata["finished_at"]} END {name}: exit={process.returncode}', flush=True)
        expected = 99 if name == 'run-slo-fail' else 0
        if process.returncode != expected:
            raise SystemExit(f'{name}: expected exit {expected}; inspect {log}')


if __name__ == '__main__':
    main()
