#!/usr/bin/env python3
"""Render asserted firmware menu routes and compose illustrated manual workflows."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/device-workflows'
JSON_DIR=Path(os.environ.get('IDF_PATH',Path(os.environ.get('PLATFORMIO_CORE_DIR','/tmp/midi-foot-toolchain'))/'packages/framework-espidf'))/'components/json/cJSON'
FONT=Path('/System/Library/Fonts/Supplemental')

def compose(rows,name):
    width,rowheight=1080,338
    canvas=Image.new('RGB',(width,len(rows)*rowheight+12),'white')
    d=ImageDraw.Draw(canvas)
    heading=ImageFont.truetype(str(FONT/'Arial Bold.ttf'),23)
    caption=ImageFont.truetype(str(FONT/'Arial.ttf'),22)
    for r,(route,steps) in enumerate(rows):
        y=r*rowheight
        d.text((18,y+2),route,font=heading,fill='#18786e')
        for col,(file,title,action) in enumerate(steps):
            x=18+col*354
            d.text((x,y+31),title,font=heading,fill='#162f32')
            screen=Image.open(OUT/(file+'.png'))
            canvas.paste(screen,(x+16,y+64))
            if col<len(steps)-1:
                d.line((x+300,y+179,x+339,y+179),fill='#665f9b',width=3)
                d.polygon([(x+344,y+179),(x+333,y+172),(x+333,y+186)],fill='#665f9b')
            assert d.textlength(action,font=caption)<=336,action
            d.text((x,y+309),action,font=caption,fill='#435a60')
    canvas.save(OUT/name)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sigmidi-menu-routes-') as name:
        temp=Path(name)
        subprocess.run(['cc','-x','c','-c',str(JSON_DIR/'cJSON.c'),'-o',str(temp/'json.o')],check=True)
        subprocess.run(['c++','-std=c++17','-Wall','-Wextra','-Werror','-Isrc','-Itests/stubs','-I'+str(JSON_DIR),'src/core.cpp','src/config.cpp','src/ui.cpp','src/display.cpp','tests/device_workflow_preview.cpp',str(temp/'json.o'),'-o',str(temp/'capture')],cwd=ROOT,check=True)
        subprocess.run([str(temp/'capture'),str(temp)],check=True)
        frames=json.loads((temp/'frames.json').read_text())
        assert len(frames)==20,len(frames)
        for f in frames:
            img=Image.open(temp/(f['file']+'.ppm')).convert('RGB');assert img.size==(280,240)
            img.save(OUT/(f['file']+'.png'))
    switch_rows=[
      ('START HERE: one path from Performance to a PC value',[
       ('performance','1  Performance','Click encoder when idle'),
       ('setup-edit','2  SETUP','Select EDIT CONFIG; click'),
       ('config-switches','3  Controller settings','Select SWITCHES list; click')]),
      ('CONTINUE from step 3 to the chosen message',[
       ('switch-list','4  Switch list','Choose A (example); click'),
       ('switch-press','5  Switch A','Select PRESS; click'),
       ('press-list','6  ON PRESS list','Select PC24/2; click')]),
      ('CONTINUE from step 6 to edit PROGRAM',[
       ('message-actions','7  MESSAGE ACTION','Select EDIT; click'),
       ('pc-editor','8  MIDI MESSAGE','Select PROGRAM; click'),
       ('program-edit','9  Value editing','Turn to change; click accepts')])]
    other_rows=[
      ('PEDALS: start at Controller settings (step 3 of the previous path)',[
       ('config-pedals','A1  Choose PEDALS','Select PEDALS; click'),
       ('pedal-list','A2  Choose input','Select 1 or 2; click'),
       ('pedal-settings','A3  Pedal settings','Click a field to edit')]),
      ('SWITCH CALIBRATION: start at Controller settings',[
       ('config-ladder','B1  Choose LADDER list','Choose the list, not MODULAR'),
       ('ladder-centers','B2  Voltage centers','Click Idle or a named switch')]),
      ('LED CHAIN: start at Controller settings',[
       ('config-leds','C1  Choose LED CHAIN','Select LED CHAIN; click'),
       ('led-settings','C2  LED settings','Click a field to edit')]),
      ('CONTROLLER PARAMETERS: no extra submenu',[
       ('config-enclosure','D1  Choose a parameter','Select ENCLOSURE; click'),
       ('enclosure-edit','D2  Value editing','Turn; click accepts')])]
    compose(switch_rows,'switch-message-workflow.png')
    compose(other_rows,'other-menus-workflow.png')
    compose([('SAVE: hold once per level to return to SETUP',[
       ('save-exit','Save the draft','Select SAVE & EXIT; click'),
       ('saved-performance','Back to Performance','Settings are now stored')])],'save-workflow.png')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    source=['src/ui.cpp','src/display.cpp','src/display.hpp','src/config.cpp','src/core.cpp','tests/device_workflow_preview.cpp','scripts/build_device_workflows.py']
    manifest={'renderer':'Production firmware UI and stripe renderer','variant':'Left','switch':'A','all_navigation_targets_asserted':True,'runtime_firmware_modified':False,'frames':frames,'source_sha256':{p:sha(ROOT/p) for p in source},'images':{p.name:sha(p) for p in sorted(OUT.glob('*.png'))}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'screens':len(frames),'flow_images':3,'directory':str(OUT),'navigation_assertions':'passed'},indent=2))
if __name__=='__main__':main()
