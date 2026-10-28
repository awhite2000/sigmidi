#!/usr/bin/env python3
"""Vendor the integrity-pinned, self-contained ESP Web Tools browser distribution."""
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

VERSION = '10.4.0'
URL = f'https://registry.npmjs.org/esp-web-tools/-/esp-web-tools-{VERSION}.tgz'
INTEGRITY = '3pwkeFFm5Fj7UQo8SJNYK5RXrtNCpq6X9QoI6bMT4GBZWgrJqjn0YvM9ihG74BtMoSFYXfmDtkehuxe50PTMPQ=='


def vendor(data, target):
    if base64.b64encode(hashlib.sha512(data).digest()).decode() != INTEGRITY:
        raise ValueError('ESP Web Tools package integrity check failed')
    target.mkdir(parents=True, exist_ok=True)
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for item in archive.getmembers():
            if not item.isfile():
                continue
            if item.name.startswith('package/dist/web/'):
                name = item.name.removeprefix('package/dist/web/')
            elif item.name == 'package/LICENSE':
                name = 'LICENSE'
            else:
                continue
            if Path(name).name != name:
                raise ValueError('Unexpected nested vendor path')
            content = archive.extractfile(item).read()
            (target / name).write_bytes(content)
            files[name] = hashlib.sha256(content).hexdigest()
    (target / 'provenance.json').write_text(json.dumps({
        'name': 'esp-web-tools', 'version': VERSION, 'url': URL,
        'npm_integrity': 'sha512-' + INTEGRITY, 'files': files,
        'source': 'https://github.com/esphome/esp-web-tools',
        'license': 'Apache-2.0; dependency licenses are retained in ../THIRD_PARTY_NOTICES.txt',
    }, indent=2) + '\n')
    return files


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Use an already downloaded npm tarball')
    args = parser.parse_args()
    data = args.archive.read_bytes() if args.archive else urllib.request.urlopen(URL, timeout=30).read()
    target = Path(__file__).resolve().parents[1] / 'flasher/vendor/esp-web-tools'
    print(f'Vendored {len(vendor(data, target))} verified files into {target}')
