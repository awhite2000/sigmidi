#!/usr/bin/env python3
"""Add SIGMIDI presentation borders to existing, unmodified Fusion renderings."""
from pathlib import Path
from firmware_artifacts import project_version
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'previews'
VIEWS = [
    ('left-main', 'Left variant · Main enclosure · Preferred', 'design/fusion/mirrored/main/assembled.png'),
    ('left-modular', 'Left variant · Modular enclosure · Preferred', 'design/fusion/mirrored/modular/assembled.png'),
    ('right-main', 'Right variant · Main enclosure', 'design/fusion/assembled.png'),
    ('right-modular', 'Right variant · Modular enclosure', 'design/fusion/modular/modular-assembled.png'),
]


def main():
    title = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 36)
    subtitle = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 22)
    mark = Image.open(ROOT / 'design/branding/sigmidi-mark-light.png').convert('RGBA')
    mark.thumbnail((82, 72), Image.Resampling.LANCZOS)
    records = []
    for name, caption, source in VIEWS:
        image = Image.open(ROOT / source).convert('RGB')
        canvas = Image.new('RGB', (image.width, image.height + 160), '#172b29')
        canvas.paste(image, (0, 110))
        canvas.paste(mark, (24, 20), mark)
        draw = ImageDraw.Draw(canvas)
        draw.text((126, 18), f'SIGMIDI Foot Controller v{project_version(ROOT)}', font=title, fill='#eaf2ed')
        draw.text((128, 64), caption, font=subtitle, fill='#a9c7b8')
        draw.text((34, image.height + 124), 'Fusion enclosure rendering · BLE MIDI · Wi-Fi setup', font=subtitle, fill='#a9c7b8')
        target = P / f'sigmidi-{name}.png'
        canvas.save(target)
        records.append(dict(version=project_version(ROOT), logo_source='design/branding/sigmidi-mark-light.png', logo_sha256=hashlib.sha256((ROOT/'design/branding/sigmidi-mark-light.png').read_bytes()).hexdigest(), source=source, source_sha256=hashlib.sha256((ROOT / source).read_bytes()).hexdigest(),
                            output=target.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                            geometry_modified=False))
    (P / 'sigmidi-enclosure-renders.json').write_text(json.dumps(records, indent=2) + '\n')
    print('Branded four enclosure variants; original Fusion renders retained.')


if __name__ == '__main__':
    main()
