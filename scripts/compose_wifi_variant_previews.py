#!/usr/bin/env python3
"""Compose readable comparisons from real browser screenshots and DOM crop bounds.

Capture metadata and full-page originals live in previews/wifi-variants-captures.json.
No application UI is redrawn or restyled; complete content panels are retained.
"""
from pathlib import Path
from firmware_artifacts import project_version
import json, math, hashlib
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'previews'
rows=json.loads((P/'wifi-variants-captures.json').read_text())
by_key={(r['variant'],r['view']):r for r in rows}
assert by_key['left','switches']['order']==list('ABCDE')+list('12345')
assert by_key['right','switches']['order']==list('EDCBA')+list('54321')
cal={side:dict(zip(by_key[side,'calibration']['region']['labels'],by_key[side,'calibration']['region']['values'])) for side in ['left','right']}
assert cal['left']==cal['right'] and len(cal['left'])==11
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',22)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
mark=Image.open(ROOT/'design/branding/sigmidi-mark-light.png').convert('RGBA')
mark.thumbnail((24,20),Image.Resampling.LANCZOS)
outputs=[]
for view in ['switches','calibration']:
    crops=[]
    for side in ['left','right']:
        r=by_key[side,view]
        image=Image.open(P/r['path']).convert('RGB')
        region=r['region'].get('focus',r['region'])
        # Keep labels, all menu buttons and inputs; exclude the unused wide right side.
        x,y=math.floor(region['x']),math.floor(region['y'])
        width=min(440,math.ceil(region['width'])) if view=='calibration' else math.ceil(region['width'])
        height=math.ceil(region['height'])
        assert x+width<=image.width and y+height<=image.height
        crops.append(image.crop((x,y,x+width,y+height)))
        r['comparison_crop_px']=[x,y,width,height]
        r['source_sha256']=hashlib.sha256((P/r['path']).read_bytes()).hexdigest()
    h=max(c.height for c in crops)
    panel_width=max(c.width for c in crops)
    canvas=Image.new('RGB',(panel_width*2+60,h+100),'#101719');draw=ImageDraw.Draw(canvas)
    for i,side in enumerate(['Left','Right']):
        x=20+i*(panel_width+20)
        draw.text((x,15),f'{side} variant · {view}',font=font,fill='#e9f0ed')
        canvas.paste(crops[i],(x,53))
    canvas.paste(mark,(20,h+66),mark)
    draw.text((54,h+68),f'SIGMIDI v{project_version(ROOT)} · Wi-Fi editor · simulated controller · 10 switches',font=small,fill='#a9bcb6')
    filename=f'wifi-{view}-both-variants.png';canvas.save(P/filename);outputs.append(filename)
(P/'wifi-variants-captures.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Compared both switch orders; all 11 per-label calibration values identical.')
for f in outputs:print(P/f)
