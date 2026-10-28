#!/usr/bin/env python3
"""Build from a space-free staging directory, copying binaries into build/.
Set PIO to the PlatformIO executable and PLATFORMIO_CORE_DIR to a space-free
package cache. Publishes firmware and the local web flasher into distribution/. Never uploads to a device.
"""
import hashlib
from datetime import datetime, timezone
from firmware_artifacts import source_fingerprint, validate_images, project_version
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import struct
root = Path(__file__).resolve().parents[1]
version = project_version(root)
pio = os.environ.get('PIO') or shutil.which('pio')
if not pio:
    raise SystemExit('Install PlatformIO Core, or set PIO to its executable.')
cache = os.environ.get('PLATFORMIO_CORE_DIR', str(Path.home() / '.platformio'))
if ' ' in str(Path(cache).resolve()):
    raise SystemExit('PLATFORMIO_CORE_DIR must resolve to a path without spaces.')
# Use the same /tmp spelling in PlatformIO and CMake on macOS.
cache = cache.replace('/private/tmp/', '/tmp/')
env = dict(os.environ, PLATFORMIO_CORE_DIR=cache)
with tempfile.TemporaryDirectory(prefix='midi-foot-', dir='/tmp') as temp:
    stage = Path(temp)
    for name in ('src', 'web', 'CMakeLists.txt', 'platformio.ini', 'sdkconfig.defaults', 'partitions.csv'):
        source = root / name
        if source.is_dir():
            shutil.copytree(source, stage / name)
        else:
            shutil.copy2(source, stage / name)
    source_sha, source_files = source_fingerprint(stage)
    subprocess.run([pio, 'run', '--project-dir', str(stage)], env=env, check=True)
    if source_fingerprint(root)[0] != source_sha:
        raise SystemExit('Firmware sources changed during the build; rerun before packaging.')
    artifacts = stage / '.pio/build/firebeetle2_c6'
    output = root / 'build'
    output.mkdir(exist_ok=True)
    for name in ('firmware.bin', 'firmware.elf', 'bootloader.bin', 'partitions.bin', 'firmware.map'):
        if (artifacts / name).exists():
            shutil.copy2(artifacts / name, output / name)
    manifest = {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                for name in ('firmware.bin', 'firmware.elf', 'bootloader.bin', 'partitions.bin')}
    (output / 'SHA256.json').write_text(json.dumps(manifest, indent=2) + '\n')
    validate_images(*( (output / n).read_bytes() for n in ('bootloader.bin', 'firmware.bin', 'partitions.bin')))
    app = (output / 'firmware.bin').read_bytes()
    # esp_app_desc_t follows the 24-byte image header and 8-byte first segment header.
    if struct.unpack_from('<I', app, 32)[0] != 0xABCD5432 or app[48:80].split(b'\0')[0].decode() != version:
        raise ValueError('ESP-IDF application descriptor version does not match SIGMIDI_VERSION')
    firmware_name = f'sigmidi-foot-controller-{version}.bin'
    shutil.copy2(output / 'firmware.bin', output / firmware_name)
    (output / 'build-info.json').write_text(json.dumps({
        'name': 'SIGMIDI Foot Controller', 'version': version,
        'firmware_name': firmware_name, 'build_id': source_sha[:12],
        'built_at': datetime.now(timezone.utc).isoformat(),
        'source_sha256': source_sha, 'source_files': source_files,
        'sha256': manifest, 'chip': 'ESP32-C6', 'flash_bytes': 4194304,
        'flash_mode': 'dio', 'flash_frequency_mhz': 40,
    }, indent=2) + '\n')
    print(f'Build complete: {output}')

# Reuse the verified build to publish the local USB installer; never uploads.
from package_web_flasher import package
package(root)
