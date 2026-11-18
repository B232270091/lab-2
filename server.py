"""Loopback-only lab server: eight concurrent workers and a 100 ms slow route."""

import json
import platform
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WORKERS = 8
DELAY_SECONDS = 0.100
slots = threading.BoundedSemaphore(WORKERS)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self):
        if self.path not in ('/health', '/fast', '/slow'):
            self.reply(404, {'error': 'not found'})
            return
        if self.path == '/health':
            self.reply(200, {'status': 'ok', 'workers': WORKERS,
                             'delay_ms': DELAY_SECONDS * 1000})
            return
        started = time.perf_counter()
        with slots:
            queued_ms = (time.perf_counter() - started) * 1000
            if self.path == '/slow':
                time.sleep(DELAY_SECONDS)
            self.reply(200, {'path': self.path, 'queue_ms': round(queued_ms, 3),
                             'delay_ms': DELAY_SECONDS * 1000 if self.path == '/slow' else 0})

    def reply(self, status, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, _format, *_args):
        pass


class LabServer(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True


if __name__ == '__main__':
    server = LabServer(('127.0.0.1', 8000), Handler)
    print(f'Python {platform.python_version()} | http://127.0.0.1:8000', flush=True)
    print(f'{WORKERS} workers | /fast: 0 ms | /slow: {DELAY_SECONDS * 1000:.0f} ms', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
