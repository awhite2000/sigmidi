#!/usr/bin/env python3
"""Serve the generated web flasher on localhost (a Web Serial secure context)."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import hashlib


class FlasherHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.js': 'text/javascript', '.bin': 'application/octet-stream'}

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Permissions-Policy', 'serial=(self)')
        super().end_headers()

    def list_directory(self, path):
        self.send_error(404)
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parents[1] / 'distribution/web-flasher')
    args = parser.parse_args()
    directory = args.directory.resolve()
    try:
        for name, expected in json.loads((directory / 'SHA256.json').read_text()).items():
            path = (directory / name).resolve()
            if not path.is_relative_to(directory) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError('Checksum mismatch: ' + name)
    except (OSError, ValueError) as error:
        raise SystemExit(f'Flasher package is missing or invalid: {error}\nRun python3 scripts/build.py first.') from error
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(FlasherHandler, directory=str(directory)))
    except OSError as error:
        raise SystemExit(f'Cannot start flasher: {error}. Try another --port.') from error
    print(f'SIGMIDI Foot Controller firmware flasher: http://localhost:{args.port}/\nOpen in desktop Chrome or Edge. Ctrl+C stops the server.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
