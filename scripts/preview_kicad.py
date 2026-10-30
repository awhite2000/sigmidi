#!/usr/bin/env python3
"""Publish the verified native KiCad render in the local preview gallery."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
from verify_kicad_netlist import verify, verify_physical_order


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / 'design/kicad'
PREVIEWS = ROOT / 'previews'
SOURCE = ROOT / 'design/electrical/netlist.json'
STEM = 'sigmidi-foot-controller'


def main():
    result = verify(SOURCE, DESIGN / f'{STEM}.net')
    result.update(verify_physical_order(SOURCE, DESIGN / 'verification/pin-locations.json'))
    # KiCad exports trailing spaces after XML tags; normalize export whitespace.
    svg=DESIGN / f'{STEM}.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    for extension in ['svg', 'png']:
        shutil.copyfile(DESIGN / f'{STEM}.{extension}', PREVIEWS / f'kicad-schematic.{extension}')

    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SIGMIDI v0.1 — KiCad schematic</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#e4e9ed;color:#172e41;font:15px system-ui,sans-serif}
header{padding:18px 24px;background:#fff;border-bottom:1px solid #c8d2dc;position:sticky;top:0;z-index:2}
h1{font-size:21px;margin:0 0 6px}p{margin:6px 0;line-height:1.5}
.bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:12px}
button,a{font:inherit}button{padding:7px 12px;border:1px solid #b7c5d1;border-radius:6px;background:#f4f7fa;color:inherit;cursor:pointer}
button:hover{background:#e3edf7}a{color:#225a96}output{min-width:48px;font-variant-numeric:tabular-nums}
.links{margin-left:auto;display:flex;gap:16px}.viewport{padding:20px;overflow:auto;height:calc(100vh - 175px)}
.sheet{background:#f8f7f2;box-shadow:0 3px 18px #142c4820;line-height:0;min-width:400px}
img{display:block;width:100%;height:auto}small{color:#53697a} @media(max-width:700px){.links{margin-left:0}.viewport{height:70vh}}
</style></head><body>
<header><h1>SIGMIDI Foot Controller v0.1 · KiCad schematic</h1>
<p>External board pins only. Arduino Nano ESP32 and display connectors retain physical pin order.</p>
<small>__COMPONENTS__ components · __NETS__ nets · __TERMINALS__ connected terminals · connectivity and pin order verified against the electrical diagram.</small>
<div class="bar"><button id="fit">Fit</button><button id="minus" aria-label="Zoom out">−</button>
<output id="zoom">100%</output><button id="plus" aria-label="Zoom in">+</button>
<button id="detail">Readable detail</button><span class="links"><a href="kicad-schematic.svg" target="_blank" rel="noopener">Open vector drawing</a>
<a href="kicad-schematic.png" target="_blank" rel="noopener">PNG</a></span></div></header>
<main class="viewport" id="viewport"><div class="sheet" id="sheet"><img src="kicad-schematic.svg" alt="Complete SIGMIDI KiCad schematic with physically ordered Arduino Nano ESP32 and display pins"></div></main>
<script>
const view=document.getElementById('viewport'),sheet=document.getElementById('sheet');let scale=1;
function draw(){sheet.style.width=Math.max(400,(view.clientWidth-40)*scale)+'px';document.getElementById('zoom').textContent=Math.round(scale*100)+'%'}
document.getElementById('fit').onclick=()=>{scale=1;draw();view.scrollTo(0,0)};
document.getElementById('minus').onclick=()=>{scale=Math.max(0.5,scale/1.3);draw()};
document.getElementById('plus').onclick=()=>{scale=Math.min(8,scale*1.3);draw()};
document.getElementById('detail').onclick=()=>{scale=2.5;draw();view.scrollTo({left:sheet.clientWidth*0.28,top:sheet.clientWidth*0.06,behavior:'smooth'})};
window.addEventListener('resize',draw);draw();
</script></body></html>'''
    page = (page.replace('__COMPONENTS__', str(result['components']))
            .replace('__NETS__', str(result['nets']))
            .replace('__TERMINALS__', str(result['connected_terminals'])))
    (PREVIEWS / 'kicad-schematic.html').write_text(page)
    manifest_path = PREVIEWS / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    files = ['previews/kicad-schematic.html', 'previews/kicad-schematic.svg',
             'previews/kicad-schematic.png', f'design/kicad/{STEM}.kicad_sch',
             f'design/kicad/{STEM}.net']
    manifest['kicad_schematic'] = {
        'updated_UTC': datetime.now(timezone.utc).isoformat(),
        'preview': 'kicad-schematic.html',
        'source': f'design/kicad/{STEM}.kicad_sch',
        'validation': result,
        'sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                   for name in files},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
