"""Check release rejection of stale/invalid build artifacts before publication."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from firmware_artifacts import source_fingerprint, validate_images, sha256, project_version
from package_web_flasher import read_build


def image(length):
    data = bytearray(length)
    data[0] = 0xE9
    data[2:4] = bytes([2, 0x20])
    data[12] = 13
    return bytes(data)


def table():
    entries = [(1, 2, 0x9000, 0x10000, b'nvs'), (1, 1, 0x19000, 0x1000, b'phy_init'),
               (0, 0, 0x20000, 0x3E0000, b'factory')]
    return b''.join(struct.pack('<HBBII16sI', 0x50AA, kind, sub, address, size, label, 0)
                    for kind, sub, address, size, label in entries) + bytes([0xFF]) * 32


class FlasherArtifacts(unittest.TestCase):
    def test_project_version_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'src').mkdir()
            header = root / 'src/branding.hpp'
            header.write_text('#define SIGMIDI_VERSION "0.1"\n')
            self.assertEqual(project_version(root), '0.1')
            for value in ['prototype', '0.1 trailing', '']:
                header.write_text(f'#define SIGMIDI_VERSION "{value}"\n')
                with self.assertRaisesRegex(ValueError, 'SIGMIDI_VERSION'):
                    project_version(root)

    def test_valid_images(self):
        self.assertEqual(validate_images(image(256), image(1024), table())['nvs'][2], 0x9000)

    def test_wrong_chip_and_flash_settings(self):
        for index, value in [(0, 0), (12, 5), (2, 0), (3, 0x30)]:
            bad = bytearray(image(256)); bad[index] = value
            with self.assertRaises(ValueError):
                validate_images(bytes(bad), image(1024), table())

    def test_wrong_partitions(self):
        bad = bytearray(table()); struct.pack_into('<I', bad, 4, 0x8000)
        with self.assertRaisesRegex(ValueError, 'Partition table'):
            validate_images(image(256), image(1024), bytes(bad))

    def test_no_bootloader_overlap(self):
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            validate_images(image(0x8001), image(1024), table())

    def test_stale_and_modified_build_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('src', 'web', 'build'):
                (root / name).mkdir()
            for name in ('CMakeLists.txt', 'platformio.ini', 'sdkconfig.defaults', 'partitions.csv', 'src/main.cpp', 'web/index.html'):
                (root / name).write_text('fixture')
            (root / 'src/branding.hpp').write_text('#define SIGMIDI_VERSION "0.1"\n')
            digest, _ = source_fingerprint(root)
            files = {'bootloader.bin': image(256), 'firmware.bin': image(1024), 'partitions.bin': table()}
            for name, data in files.items():
                (root / 'build' / name).write_bytes(data)
            info = {'version': '0.1', 'source_sha256': digest, 'sha256': {name: sha256(data) for name, data in files.items()}}
            (root / 'build/build-info.json').write_text(json.dumps(info))
            read_build(root)
            info['version'] = '0.2'
            (root / 'build/build-info.json').write_text(json.dumps(info))
            with self.assertRaisesRegex(ValueError, 'Build version'):
                read_build(root)
            info['version'] = '0.1'
            (root / 'build/build-info.json').write_text(json.dumps(info))
            (root / 'src/main.cpp').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'sources changed'):
                read_build(root)
            (root / 'src/main.cpp').write_text('fixture')
            (root / 'build/firmware.bin').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                read_build(root)


if __name__ == '__main__':
    unittest.main()
