#!/usr/bin/env python3
"""Build the assembly guide, validating wiring tables against exported net data.

Read-only with respect to CAD, KiCad and firmware. Reuses the manual's typography
and PDF outline helper; all newly generated artifacts belong to this guide.
"""
from pathlib import Path
import hashlib
import json
import os
import re

from PIL import Image as PILImage
from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String, Circle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, Spacer, Table, TableStyle

from build_user_manual import Manual, inline

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/assembly-guide.md'
OUTPUT = ROOT / 'output/pdf/sigmidi-foot-controller-0.1-assembly-guide.pdf'
WIDTH, HEIGHT = A4
MARGIN = 45
CONTENT = WIDTH - 2*MARGIN
INK = colors.HexColor('#162f32')
TEAL = colors.HexColor('#18786e')
PALE = colors.HexColor('#edf5f1')
PURPLE = colors.HexColor('#665f9b')
GRAY = colors.HexColor('#7b8587')

# Board label / GPIO / exported net, keyed by the manufacturer's header pad ID.
USED = {
    'JP1:2': ('3V3', '3V3', '3V3'),
    'JP1:4': ('A0', 'GPIO1', 'LADDER'),
    'JP1:5': ('A1', 'GPIO2', 'P1_ADC'),
    'JP1:7': ('A3', 'GPIO4', 'P2_ADC'),
    'JP1:8': ('A4', 'GPIO11', 'USB_SENSE'),
    'JP1:12': ('VBUS / VUSB', 'VBUS', 'USB_VBUS'),
    'JP1:14': ('GND', 'GND', 'GND'),
    'JP1:15': ('VIN', 'VIN', '+9V'),
    'JP2:15': ('D12', 'GPIO47', 'LCD_RST'),
    'JP2:14': ('D11', 'GPIO38', 'LCD_DIN'),
    'JP2:13': ('D10', 'GPIO21', 'LCD_CS'),
    'JP2:12': ('D9', 'GPIO18', 'LCD_DC'),
    'JP2:11': ('D8', 'GPIO17', 'LCD_CLK'),
    'JP2:10': ('D7', 'GPIO10', 'LED_GPIO'),
    'JP2:9': ('D6', 'GPIO9', 'ENC_SW'),
    'JP2:8': ('D5', 'GPIO8', 'ENC_B'),
    'JP2:7': ('D4', 'GPIO7', 'ENC_A'),
    'JP2:6': ('D3', 'GPIO6', 'P2_MODE'),
    'JP2:5': ('D2', 'GPIO5', 'P1_MODE'),
    'JP2:4': ('GND', 'GND', 'GND'),
}
TAP_LABELS = ['B', 'A', '2', '1', 'C', '3', 'D', '4', 'E', '5']
LCD = [('BL','3V3', 'JP1:2'), ('RST','D12','JP2:15'),
       ('D/C','D9','JP2:12'), ('CS','D10','JP2:13'),
       ('SCL / CLK','D8','JP2:11'), ('SDA / DIN','D11','JP2:14'),
       ('GND','GND','JP1:14'), ('VCC','3V3','JP1:2')]


def validate_sources(text, netlist):
    """Fail a rebuild if the guide's electrical or print selections drift."""
    firmware_check=netlist['firmware_pin_verification']
    assert firmware_check['all_assignments_match']
    assert firmware_check['sha256']==hashlib.sha256((ROOT/firmware_check['source']).read_bytes()).hexdigest()
    pins = netlist['nano_external_pins']
    assert {pad for pad,p in pins.items() if p['net']} == set(USED)
    for pad, (label, gpio, net) in USED.items():
        assert pins[pad] == {'physical_label':label, 'logical_name':gpio, 'net':net}, pad
    components = netlist['components']
    expected = {'R7':('10k','3V3','LADDER'), 'R8':('20k','LADDER','GND'),
                'R50':('100k','USB_VBUS','USB_SENSE'), 'R51':('150k','USB_SENSE','GND'),
                'R20':('5.1k','3V3','P1_RING'), 'R21':('10k','P1_MODE','P1_ADC'),
                'R30':('5.1k','3V3','P2_RING'), 'R31':('10k','P2_MODE','P2_ADC'),
                'C1':('47uF / 35V','+9V','GND'), 'C5':('100nF','LADDER','GND')}
    for ref, (value, a, b) in expected.items():
        c = components[ref]
        assert c['value'] == value and c['pins'] == {'1':a,'2':b}, ref
    for i, label in enumerate(TAP_LABELS, 1):
        r = components[f'R{i+8}']
        assert r['value']=='1k' and r['pins']=={'1':'LADDER' if i==1 else f'T{i-1}', '2':f'T{i}'}
        assert components[f'SW{i}']['pins']=={'1':f'T{i}','2':'GND'}
        assert components[f'SW{i}']['note']==label
        bottom = (i*1000*20000)/(i*1000+20000)
        mv = round(3300*bottom/(10000+bottom))
        assert f'| T{i} / R{i+8} | {label} | {i} | {mv} |' in text
        led = components[f'LED{i}']['pins']
        assert led['+5V']=='+5V' and led['GND']=='GND'
        assert led['DIN']==('LED_GPIO' if i==1 else f'L{i-1}')
    for i,(label,nano,pad) in enumerate(LCD,1):
        assert components['U2']['pins'][f'P2:{i}']==pins[pad]['net']
        assert f'| {i} - {label} | {nano} |' in text
    assert components['J2']['pins']=={
        '10':'GND','11':'P1_RING','12':'P1_ADC','7':None,'8':None,'9':None,
        '4':'GND','5':'P2_RING','6':'P2_ADC','1':None,'2':None,'3':None,'13':None}
    mount = json.loads((ROOT/'design/fusion/nano-esp32/mount-fit.json').read_text())
    assert mount['component_face_down'] and len(mount['board_holes_XY_mm'])==4
    assert mount['PCB_screws']=='Four M1.6x5 pan head'
    assert mount['bridge_fasteners']=='Two M1.6x6 pan head into existing far-end posts'
    prints=[]
    for folder,names in {
        'design/fusion/mirrored/main':['shell-left','shell-right','base-left','base-right'],
        'design/fusion/print':['shell-left','shell-right','base-left','base-right'],
        'design/fusion/mirrored/modular':['electronics-shell-left','electronics-base-left','right-cap',
            'pair-shell-C','pair-shell-D','pair-shell-at-right-cap-C','pair-shell-at-right-cap-D',
            'pair-shell-at-right-cap-E','pair-base'],
        'design/fusion/modular':['electronics-shell','electronics-base','left-cap','pair-shell',
            'pair-shell-D','pair-shell-at-cap-C','pair-shell-at-cap','pair-shell-at-cap-E','pair-base'],
        'design/fusion/nano-esp32':['usb-side-glue-insert','existing-pole-insert'],
    }.items():
        for name in names:
            assert name in text, name
            for ext in ['.stl','.3mf']:
                p=ROOT/folder/(name+ext)
                assert p.is_file(),p
                prints.append(p)
    bom=json.loads((ROOT/'docs/bom-items.json').read_text())
    by_id={item['id']:item for item in bom['items']}
    for profile,count in bom['profiles'].items():
        assert by_id['H01']['quantity'][profile]==(8 if profile=='main_10' else 4+2*((count-4)//2))
        total=sum(item['quantity'][profile] for item in bom['items'] if item['group']=='Printed parts')
        assert total==(6 if profile=='main_10' else 5+2*((count-4)//2))
    # Verify all local Markdown link/image targets without changing any native CAD.
    for target in re.findall(r'!?\[[^]]*\]\(([^)]+)\)',text):
        if '://' not in target:
            assert (SOURCE.parent/target).resolve().exists(), target
    return prints


def label(d, x, y, text, size=9, color=INK, anchor='start', bold=False):
    d.add(String(x,y,text,fontName='ManualBold' if bold else 'Manual',
                 fontSize=size,fillColor=color,textAnchor=anchor))


def wire(d, x1, y1, x2, y2, color=TEAL, width=1.3):
    d.add(Line(x1,y1,x2,y2,strokeColor=color,strokeWidth=width))


def nano_diagram(netlist):
    d=Drawing(CONTENT,365)
    bx,by,bw,bh=172,28,161,316
    d.add(Rect(bx,by,bw,bh,rx=9,ry=9,fillColor=PALE,strokeColor=TEAL))
    d.add(Rect(232,330,41,28,rx=4,ry=4,fillColor=colors.white,strokeColor=TEAL))
    label(d,252.5,340,'USB-C',8,anchor='middle',bold=True)
    label(d,190,322,'JP1',8,TEAL,bold=True);label(d,315,322,'JP2',8,TEAL,anchor='end',bold=True)
    pins=netlist['nano_external_pins']
    for row in range(15):
        y=303-row*18
        for side,n in [('JP1',row+1),('JP2',15-row)]:
            pad=f'{side}:{n}';p=pins[pad];left=side=='JP1'
            x=177 if left else 328
            used=p['net'] is not None
            color=TEAL if used else GRAY
            d.add(Circle(x,y+2,2.5,fillColor=color,strokeColor=color))
            board_label=p['physical_label'].replace(' / VUSB','/VUSB').replace(' / RX0','/RX0').replace(' / TX0','/TX0')
            label(d,187 if left else 318,y,board_label,8.5,color,
                  anchor='start' if left else 'end',bold=used)
            label(d,164 if left else 341,y+5,str(n),7.5,GRAY,anchor='end' if left else 'start')
            if used:
                end=151 if left else 354
                wire(d,x-4 if left else x+4,y+2,end,y+2,color)
                desc=p['logical_name']+' / '+p['net']
                if p['logical_name']==p['net']:desc=p['net']
                desc=desc.replace('USB_VBUS','USB 5V').replace('LED_GPIO','LED DIN')
                label(d,4 if left else 361,y,desc,8.7,color)
    label(d,252.5,13,'Component-side reference; mounted component-side down',8,GRAY,anchor='middle')
    return d


def power_diagram():
    d=Drawing(CONTENT,165)
    blocks=[(0,69,123,58,'DC INLET','Sleeve: +9V','Center: GND'),
            (249,105,115,47,'NANO ESP32','VIN: +9V',''),
            (249,37,115,47,'POLOLU 4083','VIN: +9V','VOUT: +5V'),
            (424,37,80,47,'LED CHAIN','+5V / GND','')]
    for x,y,w,h,t,a,b in blocks:
        d.add(Rect(x,y,w,h,rx=6,ry=6,fillColor=PALE,strokeColor=TEAL))
        label(d,x+w/2,y+h-16,t,9,anchor='middle',bold=True)
        label(d,x+w/2,y+h-30,a,8.5,anchor='middle')
        if b:label(d,x+w/2,y+9,b,8.5,anchor='middle')
    wire(d,123,109,185,109,PURPLE,2)
    wire(d,185,109,185,128,PURPLE,2);wire(d,185,128,249,128,PURPLE,2)
    wire(d,185,109,185,60,PURPLE,2);wire(d,185,60,249,60,PURPLE,2)
    label(d,186,143,'+9V split',8,PURPLE,anchor='middle')
    wire(d,364,60,424,60,PURPLE,2)
    label(d,394,72,'+5V',8,PURPLE,anchor='middle')
    label(d,249,22,'C1: 47 uF / 35 V across converter VIN and GND',8,TEAL)
    label(d,0,4,'Common GND: inlet center, Nano, converter and all peripherals.',9,bold=True)
    return d


def ladder_diagram():
    d=Drawing(CONTENT,125)
    label(d,0,110,'BASE: R7 / R8 / C5 at SENSE (see step 1)',9,bold=True)
    label(d,0,85,'SENSE',8,bold=True)
    wire(d,18,77,306,77)
    for idx,x in enumerate([91,154,217,280],1):
        d.add(Rect(x-36,72,26,10,fillColor=colors.white,strokeColor=TEAL))
        label(d,x-23,87,'1k',8,anchor='middle')
        d.add(Circle(x,77,2.3,fillColor=TEAL,strokeColor=TEAL))
        label(d,x+5,62,f'T{idx}',8,bold=True)
        wire(d,x,77,x,43)
        wire(d,x,43,x+8,30)
        wire(d,x,25,x,13)
        label(d,x+10,37,TAP_LABELS[idx-1],9,TEAL,bold=True)
    wire(d,50,13,306,13)
    label(d,0,10,'GND',8,bold=True)
    wire(d,306,77,343,77)
    d.add(Rect(343,22,161,77,rx=5,ry=5,fillColor=PALE,strokeColor=TEAL))
    label(d,354,84,'NEXT PAIR',9,bold=True)
    label(d,354,67,'TAIL IN - 1k - upper tap',8.5)
    label(d,354,51,'- 1k - lower tap - TAIL OUT',8.5)
    label(d,354,34,'Switches to common GND',8.5)
    wire(d,306,13,343,13);wire(d,343,13,343,22)
    label(d,326,86,'TAIL',7,TEAL,anchor='middle')
    return d


def pdf_inline(value):
    def target(match):
        title, link = match.groups()
        if '://' not in link:
            link = Path(os.path.relpath((SOURCE.parent/link).resolve(), OUTPUT.parent)).as_posix()
        return f'[{title}]({link})'
    return inline(re.sub(r'\[([^]]*)\]\(([^)]+)\)', target, value))


def main():
    for name,filename in [('Manual','Arial.ttf'),('ManualBold','Arial Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(Path('/System/Library/Fonts/Supplemental')/filename)))
    pdfmetrics.registerFontFamily('Manual',normal='Manual',bold='ManualBold',italic='Manual',boldItalic='ManualBold')
    text=SOURCE.read_text()
    netlist=json.loads((ROOT/'design/electrical/netlist.json').read_text())
    # Draw first so link validation includes the generated SVG illustrations.
    drawings={'assembly-nano-pins.svg':nano_diagram(netlist),
              'assembly-power.svg':power_diagram(),'assembly-ladder.svg':ladder_diagram()}
    for name,drawing in drawings.items():
        renderSVG.drawToFile(drawing,str(SOURCE.parent/name))
        asset=SOURCE.parent/name
        svg=asset.read_text().replace('font-family: ManualBold;', 'font-family: Arial; font-weight: bold;').replace('font-family: Manual;', 'font-family: Arial;')
        title={'assembly-nano-pins.svg':'Nano ESP32 physical header order and signal assignments', 'assembly-power.svg':'9 V center-negative power routing', 'assembly-ladder.svg':'Four-switch series-tap ladder and extension interface'}[name]
        svg=svg.replace('<title>...</title>', '<title>'+title+'</title>').replace('<desc>...</desc>', '<desc>SIGMIDI Foot Controller v0.1 assembly guide diagram</desc>')
        asset.write_text(svg)
    prints=validate_sources(text,netlist)
    styles={
        'Chapter':ParagraphStyle('Chapter',fontName='ManualBold',fontSize=23,leading=27,textColor=INK,spaceAfter=13,keepWithNext=True),
        'Section':ParagraphStyle('Section',fontName='ManualBold',fontSize=12,leading=15,textColor=TEAL,spaceBefore=8,spaceAfter=6,keepWithNext=True),
        'Copy':ParagraphStyle('Copy',fontName='Manual',fontSize=10,leading=13.2,textColor=INK,spaceAfter=7),
        'Cell':ParagraphStyle('Cell',fontName='Manual',fontSize=9,leading=11.7,textColor=INK,spaceAfter=0),
        'Caption':ParagraphStyle('Caption',fontName='Manual',fontSize=8.3,leading=10.5,textColor=GRAY,alignment=TA_CENTER,spaceBefore=4,spaceAfter=7),
        'Check':ParagraphStyle('Check',fontName='Manual',fontSize=10,leading=13.2,textColor=TEAL,spaceBefore=4,spaceAfter=8,borderColor=TEAL,borderWidth=.7,borderPadding=7,backColor=PALE),
    }
    story=[];images=[]
    sections=text.split('<!-- page -->')
    # Illustrations stay readable while preserving enough room for actual steps.
    max_heights={'sigmidi-left-main.png':227,'snug-fit-sections.png':142,
        'perimeter-ledge-detail.png':142,'display-m2x5-section.png':240,
        'installed.png':185,'exploded.png':185,'pololu-2535-pinout.jpg':108,
        'cable-bundles-left.png':260}
    for page_index,section in enumerate(sections):
        if page_index:story.append(PageBreak())
        lines=section.strip().splitlines();i=0
        while i<len(lines):
            line=lines[i].strip()
            if not line:i+=1;continue
            if line.startswith('# '):
                story.append(Paragraph(pdf_inline(line[2:]),styles['Chapter']));i+=1
            elif line.startswith('## '):
                story.append(Paragraph(pdf_inline(line[3:]),styles['Section']));i+=1
            elif line.startswith('!['):
                refs=re.findall(r'!\[([^]]*)\]\(([^)]+)\)',line);cells=[]
                for caption,relative in refs:
                    p=(SOURCE.parent/relative).resolve();images.append(p)
                    if relative in drawings:
                        graphic=drawings[relative]
                    else:
                        w,h=PILImage.open(p).size
                        available=(CONTENT-14)/2 if len(refs)==2 else CONTENT
                        target_h=min(available*h/w,max_heights.get(p.name,225))
                        graphic=Image(str(p),width=target_h*w/h,height=target_h)
                    group=[graphic,Paragraph(pdf_inline(caption),styles['Caption'])]
                    if len(refs)==2:cells.append(group)
                    else:story.append(KeepTogether(group))
                if cells:
                    t=Table([cells],colWidths=[CONTENT/2]*2)
                    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]))
                    story.append(t)
                i+=1
            elif line.startswith('|'):
                rows=[]
                while i<len(lines) and lines[i].strip().startswith('|'):
                    row=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r'[-:]+',v) for v in row):rows.append(row)
                    i+=1
                n=len(rows[0]);assert all(len(row)==n for row in rows)
                weights=[max(8,sum(min(len(row[c]),85) for row in rows)/len(rows))**.6 for c in range(n)]
                widths=[CONTENT*w/sum(weights) for w in weights]
                if page_index==0:widths=[CONTENT*.86,CONTENT*.14]
                if page_index==1 and n==4:widths=[58,135,235,CONTENT-428]
                if page_index==8:widths=[115,100,95,CONTENT-310]
                if page_index==9:widths=[110,197,CONTENT-307]
                cells=[[Paragraph(('<b>'+pdf_inline(v)+'</b>') if j==0 else pdf_inline(v),styles['Cell']) for v in row] for j,row in enumerate(rows)]
                t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
                t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f9f8')]),
                    ('LINEBELOW',(0,0),(-1,0),.7,TEAL),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#d6e1de')),
                    ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
                    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
                story.extend([t,Spacer(1,8)])
            else:
                paragraph=[line];i+=1;numbered=bool(re.match(r'\d+\. ',line))
                while not numbered and i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','![')):
                    paragraph.append(lines[i].strip());i+=1
                value=' '.join(paragraph)
                story.append(Paragraph(pdf_inline(value),styles['Check' if value.startswith('**Pass check:') else 'Copy']))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    doc=Manual(str(OUTPUT),pagesize=A4,leftMargin=MARGIN,rightMargin=MARGIN,
        topMargin=49,bottomMargin=43,title='SIGMIDI Foot Controller v0.1 - Assembly guide',author='SIGMIDI project')
    doc.chapters=[]
    def frame(canvas,current):
        canvas.saveState();canvas.setFillColor(TEAL);canvas.rect(0,HEIGHT-7,WIDTH,7,stroke=0,fill=1)
        canvas.setFont('ManualBold',8);canvas.setFillColor(INK)
        canvas.drawString(MARGIN,HEIGHT-28,'SIGMIDI  /  FOOT CONTROLLER')
        canvas.setFont('Manual',8);canvas.drawRightString(WIDTH-MARGIN,HEIGHT-28,'ASSEMBLY GUIDE  v0.1')
        canvas.setStrokeColor(colors.HexColor('#c9d8d3'));canvas.line(MARGIN,32,WIDTH-MARGIN,32)
        canvas.setFillColor(GRAY);canvas.drawString(MARGIN,20,'Nano ESP32  /  Left + Right  /  Main + Modular')
        canvas.drawRightString(WIDTH-MARGIN,20,str(current.page));canvas.restoreState()
    doc.build(story,onFirstPage=frame,onLaterPages=frame)
    assert [c['page'] for c in doc.chapters]==list(range(1,len(sections)+1)),doc.chapters
    from pypdf import PdfReader
    reader=PdfReader(OUTPUT)
    assert len(reader.pages)==len(sections)==15
    assert all(page.extract_text().strip() for page in reader.pages)
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    sources=[SOURCE,Path(__file__),ROOT/'scripts/build_user_manual.py',ROOT/'src/board.hpp',
        ROOT/'design/electrical/netlist.json',ROOT/'docs/bom-items.json',ROOT/'docs/power.md',
        ROOT/'docs/hardware.md',ROOT/'docs/leds.md',ROOT/'docs/resistor-ladders.md',
        ROOT/'design/fusion/nano-esp32/mount-fit.json',ROOT/'design/fusion/nano-esp32/README.md',
        ROOT/'design/fusion/mirrored/README.md',ROOT/'design/fusion/modular/README.md',
        ROOT/'design/fusion/printing-tolerances.md',ROOT/'docs/user-manual.md',ROOT/'docs/bringup.md']
    manifest={'title':'SIGMIDI Foot Controller v0.1 Assembly guide','pages':len(sections),'page_size':'A4',
        'preferred_variant':'Left','hardware':'Arduino Nano ESP32 ABX00083 + Waveshare 24382',
        'assemblies':['Left Main','Left Modular 4/6/8/10','Right Main','Right Modular 4/6/8/10'],
        'chapters':doc.chapters,'physical_fit_qualified':False,'electrical_bench_qualified':False,
        'checks':{'used_nano_pins':len(USED),'LCD_pins_in_physical_order':8,'tap_label_LED_rows':10,
                  'discrete_values_and_nets_match':True,'selected_print_files_exist':len(prints),'local_links_exist':True},
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},
        'images':{str(p.relative_to(ROOT)):sha(p) for p in sorted(set(images))},
        'outputs':{str(OUTPUT.relative_to(ROOT)):sha(OUTPUT)}}
    (ROOT/'docs/assembly-guide-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'pdf':str(OUTPUT),'pages':len(sections),'checks':manifest['checks']},indent=2))


if __name__=='__main__':main()
