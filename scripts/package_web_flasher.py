#!/usr/bin/env python3
"""Create a portable, offline-capable web flasher from a current firmware build."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
from firmware_artifacts import sha256, source_fingerprint, validate_images, APP_OFFSET, NVS_START, project_version, preserve_firmware


def esptool_command():
    executable = shutil.which('esptool') or shutil.which('esptool.py')
    if executable:
        return [executable]
    cache = Path(os.environ.get('PLATFORMIO_CORE_DIR', Path.home() / '.platformio'))
    script = cache / 'packages/tool-esptoolpy/esptool.py'
    pio = os.environ.get('PIO') or shutil.which('pio')
    python = Path(pio).parent / ('python.exe' if os.name == 'nt' else 'python') if pio else Path(sys.executable)
    if script.exists() and python.exists():
        return [str(python), str(script)]
    raise ValueError('Install esptool or set PIO and PLATFORMIO_CORE_DIR to the firmware build tools.')


def build_directory(root):
    build = root / 'build'
    return build if (build / 'build-info.json').exists() else root / 'distribution/firmware'


def read_build(root):
    output = build_directory(root)
    info = json.loads((output / 'build-info.json').read_text())
    source_sha, _ = source_fingerprint(root)
    if source_sha != info['source_sha256']:
        raise ValueError('Firmware sources changed since the last build. Run python3 scripts/build.py first.')
    if info.get('version') != project_version(root):
        raise ValueError('Build version does not match SIGMIDI_VERSION; rebuild the firmware.')
    images = {n: (output / n).read_bytes() for n in ('bootloader.bin', 'partitions.bin', 'firmware.bin')}
    for name, data in images.items():
        if sha256(data) != info['sha256'].get(name):
            raise ValueError(f'{name}: build checksum does not match; rebuild the firmware.')
    validate_images(images['bootloader.bin'], images['firmware.bin'], images['partitions.bin'])
    return info, images


def package(root):
    info, images = read_build(root)
    source = root / 'flasher'
    provenance = json.loads((source / 'vendor/esp-web-tools/provenance.json').read_text())
    for name, checksum in provenance['files'].items():
        if sha256((source / 'vendor/esp-web-tools' / name).read_bytes()) != checksum:
            raise ValueError(f'Vendored installer checksum failed: {name}')
    build_output = build_directory(root)
    output = root / 'distribution'
    output.mkdir(exist_ok=True)
    target = output / 'web-flasher'
    archive_name = f"sigmidi-foot-controller-{info['version']}-web-flasher.zip"
    with tempfile.TemporaryDirectory(prefix='web-flasher-', dir=output) as temp:
        site = Path(temp) / 'site'
        shutil.copytree(source, site, ignore=shutil.ignore_patterns('package.json'))
        page = site / 'index.html'
        page.write_text(page.read_text().replace('__PROJECT_VERSION__', info['version']))
        firmware = site / 'firmware'
        firmware.mkdir()
        # Merge only the boot/partition region, deliberately stopping before NVS.
        subprocess.run(esptool_command() + [
            '--chip', 'esp32c6', 'merge_bin', '--flash_mode', 'dio', '--flash_freq', '40m',
            '--flash_size', '4MB', '-o', str(firmware / 'boot-region.bin'),
            '0x0', str(build_output / 'bootloader.bin'), '0x8000', str(build_output / 'partitions.bin'),
        ], check=True)
        boot_region = (firmware / 'boot-region.bin').read_bytes()
        if (len(boot_region) > NVS_START or boot_region[:len(images['bootloader.bin'])] != images['bootloader.bin'] or
                boot_region[0x8000:] != images['partitions.bin']):
            raise ValueError('Merged boot image does not match the verified build or overlaps NVS')
        (firmware / 'application.bin').write_bytes(images['firmware.bin'])
        parts = [{'path': 'firmware/boot-region.bin', 'offset': 0},
                 {'path': 'firmware/application.bin', 'offset': APP_OFFSET}]
        manifest = {'name': 'SIGMIDI Foot Controller', 'version': info['version'], 'new_install_prompt_erase': True,
                    'builds': [{'chipFamily': 'ESP32-C6', 'improv': False, 'parts': parts}]}
        manifest_bytes = (json.dumps(manifest, indent=2) + '\n').encode()
        (site / 'manifest.json').write_bytes(manifest_bytes)
        release = {'schema': 1, 'name': 'SIGMIDI Foot Controller', 'version': info['version'],
                   'built_at': info['built_at'], 'packaged_at': datetime.now(timezone.utc).isoformat(),
                   'chip': 'ESP32-C6', 'flash_bytes': 4194304, 'source_sha256': info['source_sha256'],
                   'manifest_sha256': sha256(manifest_bytes), 'installer': 'esp-web-tools@' + provenance['version'],
                   'preserved_regions': [{'name': 'nvs', 'offset': 0x9000, 'bytes': 0x10000},
                                         {'name': 'phy_init', 'offset': 0x19000, 'bytes': 0x1000}],
                   'files': [{**part, 'bytes': (site / part['path']).stat().st_size,
                              'sha256': sha256((site / part['path']).read_bytes())} for part in parts]}
        (site / 'release.json').write_text(json.dumps(release, indent=2) + '\n')
        hashes = {p.relative_to(site).as_posix(): sha256(p.read_bytes()) for p in sorted(site.rglob('*')) if p.is_file()}
        (site / 'SHA256.json').write_text(json.dumps(hashes, indent=2) + '\n')
        archive_path = Path(temp) / archive_name
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(site.rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(site).as_posix())
        with zipfile.ZipFile(archive_path) as archive:
            if archive.testzip() is not None:
                raise ValueError('Web-flasher ZIP integrity failure')
            for name, checksum in hashes.items():
                if sha256(archive.read(name)) != checksum:
                    raise ValueError('Packaged flasher file mismatch: ' + name)
        # Replace only this script's generated output directory after all checks pass.
        previous = Path(temp) / 'previous'
        if target.exists():
            target.rename(previous)
        try:
            site.rename(target)
        except OSError:
            if previous.exists():
                previous.rename(target)
            raise
        shutil.move(str(archive_path), output / archive_path.name)
    report = {'version': info['version'], 'directory': str(target), 'ZIP': str(output / archive_name),
              'ZIP_sha256': sha256((output / archive_name).read_bytes()), 'files': len(hashes) + 1,
              'preserves_NVS_when_erase_unchecked': True, 'chip': 'ESP32-C6', 'hardware_flash_tested': False}
    preserve_firmware(root, info, images)
    (output / 'web-flasher-package.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        package(Path(__file__).resolve().parents[1])
    except (ValueError, FileNotFoundError, KeyError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
