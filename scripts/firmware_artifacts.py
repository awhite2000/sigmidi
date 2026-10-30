"""Shared source fingerprint and ESP32-S3 artifact validation for releases."""
import hashlib
from pathlib import Path
import struct
import re

SOURCE_INPUTS = ('src', 'web', 'CMakeLists.txt', 'platformio.ini', 'sdkconfig.defaults', 'partitions.csv')
FLASH_BYTES = 16 * 1024 * 1024
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
        if len(data) < 24 or data[0] != 0xE9 or struct.unpack_from('<H', data, 12)[0] != 9:
            raise ValueError(f'{label}: expected an ESP32-S3 image (chip ID 9)')
        # Match the compiled image headers: DIO, 40MHz, 16MB. No upload-time patch required.
        if data[2] != 2 or data[3] != 0x40:
            raise ValueError(f'{label}: expected DIO / 40MHz / 16MB image headers')
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
        raise ValueError('Partition table differs from the supported 16MB controller layout')
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
    (firmware / 'TinyUSB-MIT.txt').write_bytes((root / 'licenses/TinyUSB-MIT.txt').read_bytes())
    (firmware / 'Apache-2.0.txt').write_bytes((root / 'LICENSE').read_bytes())
    release_info = {**info, 'sha256': {name: sha256(data) for name, data in images.items()}}
    (firmware / 'build-info.json').write_text(json.dumps(release_info, indent=2) + '\n')
    application = f"sigmidi-foot-controller-{info['version']}.bin"
    (output / application).write_bytes(images['firmware.bin'])
    guide = ('SIGMIDI Foot Controller v' + info['version'] + '\n\n'
             'Arduino Nano ESP32 / ESP32-S3. USB MIDI + BLE MIDI. Use the web flasher in ROM download mode.\n'
             'Pedal interface: two controller resistors per input (5.1k ring reference, 10k GPIO bias to TIP).\n'
             'TIP goes directly to ADC. Enabled resistor mode drives bias HIGH; pot/disabled mode is high impedance.\n'
             'Use passive 0-10k pedals and capture heel/toe after wiring; calibration stores raw ADC millivolts.\n'
             'Manual esptool write_flash offsets: bootloader.bin 0x0, partitions.bin 0x8000, firmware.bin 0x20000.\n'
             'Download mode: jumper B1 to GND, tap RST, remove jumper, then select the new USB serial port.\n'
             'The running application exposes native USB MIDI. Installation and updates use ROM download mode.\n'
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
