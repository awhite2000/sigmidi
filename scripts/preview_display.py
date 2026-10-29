#!/usr/bin/env python3
"""Render real firmware UI views through the production 280x240 stripe renderer.

Requires a C++17 compiler, ESP-IDF cJSON sources and Pillow. The generated native
screens and contact sheets are written to previews/; no hardware is required.
"""
from pathlib import Path
from firmware_artifacts import project_version
import os
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IDF = Path(os.environ.get("PLATFORMIO_CORE_DIR", "/tmp/midi-foot-toolchain")) / "packages/framework-espidf"
JSON_DIR = Path(os.environ.get("IDF_PATH", DEFAULT_IDF)) / "components/json/cJSON"
TITLES = ["Performance", "Setup", "Press / release message list", "PC message: Program", "CC message: Control + Value", "Wi-Fi setup", "Browser editing", "Pololu 2535 LED chain", "Switch / LED assignment", "Enclosure variant: Left", "Left variant: switches", "Left variant: calibration", "Left: switches, scrolled down", "Left: calibration, scrolled down", "Right variant: switches", "Right: switches, scrolled down", "Right variant: calibration", "Right: calibration, scrolled down", "PC counter message list", "PC mode: INCR", "PC mode: DECR"]


def main():
    if not (JSON_DIR / "cJSON.c").is_file():
        raise SystemExit("Set IDF_PATH or PLATFORMIO_CORE_DIR to an installed ESP-IDF.")
    out = ROOT / "previews"
    out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="midi-preview-") as name:
        tmp = Path(name)
        subprocess.run(["cc", "-x", "c", "-c", str(JSON_DIR / "cJSON.c"), "-o", str(tmp / "json.o")], check=True)
        subprocess.run(["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-Isrc", "-Itests/stubs", "-I" + str(JSON_DIR), "src/core.cpp", "src/config.cpp", "src/ui.cpp", "src/display.cpp", "tests/display_preview.cpp", str(tmp / "json.o"), "-o", str(tmp / "render")], cwd=ROOT, check=True)
        subprocess.run([str(tmp / "render"), str(tmp)], check=True)
        screens = []
        for index, ppm in enumerate(sorted(tmp.glob("*.ppm")), 1):
            img = Image.open(ppm).convert("RGB")
            assert img.size == (280, 240)
            img.save(out / f"{index:02}.png")
            screens.append(img)
        assert len(screens) == len(TITLES)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    mark = Image.open(ROOT / 'design/branding/sigmidi-mark-light.png').convert('RGBA')
    mark.thumbnail((24, 20), Image.Resampling.LANCZOS)
    def sheet(indices, filename):
        canvas = Image.new("RGB", (20 + min(2, len(indices)) * 580, 20 + ((len(indices) + 1) // 2) * 530), "#171d20")
        draw = ImageDraw.Draw(canvas)
        for position, index in enumerate(indices):
            x, y = 20 + (position % 2) * 580, 20 + (position // 2) * 530
            canvas.paste(mark, (x, y), mark)
            draw.text((x + 32, y), f"SIGMIDI v{project_version(ROOT)} · " + TITLES[index], font=font, fill="#dce9e3")
            canvas.paste(screens[index].resize((560, 480), Image.Resampling.NEAREST), (x, y + 30))
        canvas.save(out / filename)
    sheet(list(range(len(TITLES))), "display-preview.png")
    sheet([0, 2, 3, 4], "display-overview.png")
    sheet([3, 4], "menu-editor-preview.png")
    sheet([7, 8], "led-menu-preview.png")
    sheet([9, 10, 11], "enclosure-menu-preview.png")
    sheet([10, 14, 11, 16], "enclosure-menus-both-variants.png")
    sheet([12, 15, 13, 17], "enclosure-menus-scrolled.png")
    sheet([18, 19, 20], "pc-counter-menu-preview.png")
    print(out / "display-preview.png")


if __name__ == "__main__":
    main()
