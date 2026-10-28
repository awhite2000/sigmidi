"""Shared source fingerprint and ESP32-C6 artifact validation for releases."""
import hashlib
from pathlib import Path
import struct
import re

SOURCE_INPUTS = ('src', 'web', 'CMakeLists.txt', 'platformio.ini', 'sdkconfig.defaults', 'partitions.csv')
FLASH_BYTES = 4 * 1024 * 1024
NVS_START, NVS_END = 0x9000, 0x19000
APP_OFFSET, APP_SIZE = 0x20000, 0x3E0000


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def project_version(root):
    """Read the same release version used by CMake, BLE and the LCD."""
    match = re.search(r'^#define SIGMIDI_VERSION "(\d+\.\d+(?:\.\d+)?)"$',
                      (root / 'src/branding.hpp').read_text(), re.MULTILINE)
    if not match:
        raise ValueError('Missing or invalid SIGMIDI_VERSION in src/branding.hpp')
    return match.group(1)


def source_fingerprint(root):
    files = {}
    for name in SOURCE_INPUTS:
        path = root / name
        paths = sorted(p for p in path.rglob('*') if p.is_file()) if path.is_dir() else [path]
        for item in paths:
            if '__pycache__' not in item.parts:
                files[item.relative_to(root).as_posix()] = sha256(item.read_bytes())
    return sha256((''.join(f'{n}\0{h}\n' for n, h in sorted(files.items()))).encode()), files


def validate_images(boot, app, table):
    for label, data in [('bootloader', boot), ('application', app)]:
        if len(data) < 24 or data[0] != 0xE9 or struct.unpack_from('<H', data, 12)[0] != 13:
            raise ValueError(f'{label}: expected an ESP32-C6 image (chip ID 13)')
        # Match the compiled image headers: DIO, 40MHz, 4MB. No upload-time patch required.
        if data[2] != 2 or data[3] != 0x20:
            raise ValueError(f'{label}: expected DIO / 40MHz / 4MB image headers')
    if len(boot) > 0x8000 or len(app) > APP_SIZE or len(table) > 0x1000:
        raise ValueError('Image exceeds its flash region')
    entries = {}
    for offset in range(0, len(table) - 31, 32):
        magic, kind, sub, address, size, label, flags = struct.unpack_from('<HBBII16sI', table, offset)
        if magic in (0xFFFF, 0xEBEB):
            break
        if magic != 0x50AA:
            raise ValueError('Invalid partition-table entry')
        entries[label.rstrip(b'\0').decode()] = (kind, sub, address, size, flags)
    expected = {'nvs': (1, 2, NVS_START, NVS_END-NVS_START, 0),
                'phy_init': (1, 1, 0x19000, 0x1000, 0),
                'factory': (0, 0, APP_OFFSET, APP_SIZE, 0)}
    if entries != expected:
        raise ValueError('Partition table differs from the supported 4MB controller layout')
    return entries


def preserve_firmware(root, info, images):
    """Publish flashable release files; keep compiler/debug intermediates in build/."""
    import json
    import zipfile
    output = root / 'distribution'
    firmware = output / 'firmware'
    firmware.mkdir(parents=True, exist_ok=True)
    validate_images(images['bootloader.bin'], images['firmware.bin'], images['partitions.bin'])
    for name, data in images.items():
        (firmware / name).write_bytes(data)
    release_info = {**info, 'sha256': {name: sha256(data) for name, data in images.items()}}
    (firmware / 'build-info.json').write_text(json.dumps(release_info, indent=2) + '\n')
    application = f"sigmidi-foot-controller-{info['version']}.bin"
    (output / application).write_bytes(images['firmware.bin'])
    guide = ('SIGMIDI Foot Controller v' + info['version'] + '\n\n'
             'ESP32-C6 / DFRobot DFR1075. For first installation, use the web flasher.\n'
             'Manual esptool write_flash offsets: bootloader.bin 0x0, partitions.bin 0x8000, firmware.bin 0x20000.\n'
             'The versioned application alone requires an existing compatible bootloader and partition table.\n'
             'Export controller settings before updating; avoid full erase to preserve compatible NVS settings.\n')
    (firmware / 'README.txt').write_text(guide)
    hashes = {p.name: sha256(p.read_bytes()) for p in sorted(firmware.iterdir()) if p.is_file() and p.name != 'SHA256.json'}
    (firmware / 'SHA256.json').write_text(json.dumps(hashes, indent=2) + '\n')
    archive = output / f"sigmidi-foot-controller-{info['version']}-firmware.zip"
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(firmware.iterdir()):
            if path.is_file():
                z.write(path, path.name)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('Firmware ZIP integrity failure')
        for name, digest in hashes.items():
            if sha256(z.read(name)) != digest:
                raise ValueError('Firmware ZIP checksum mismatch: ' + name)
    return archive
