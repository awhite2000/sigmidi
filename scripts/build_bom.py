#!/usr/bin/env python3
"""Generate the BOM document and shopping CSV; read only exported design data."""
from collections import Counter
from pathlib import Path
import csv
import hashlib
import json
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle

from build_user_manual import Manual, inline

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'docs/bom-items.json'
PDF = ROOT/'output/pdf/sigmidi-foot-controller-0.1-bill-of-materials.pdf'
PROFILES = ['modular_4','modular_6','modular_8','modular_10','main_10']
LABELS = ['Mod 4','Mod 6','Mod 8','Mod 10','Main 10']
WIDTH, HEIGHT = A4
MARGIN = 44
CONTENT = WIDTH-2*MARGIN
TEAL = colors.HexColor('#18786e')
INK = colors.HexColor('#162f32')


def main():
    data = json.loads(SOURCE.read_text())
    items = data['items']
    by_id = {i['id']:i for i in items}
    # Reconcile at the assembly boundary. Do not parse or edit KiCad source files.
    netlist = json.loads((ROOT/'design/electrical/netlist.json').read_text())
    refs = [ref for item in items for ref in item['electrical_refs']]
    assert len(refs) == len(set(refs)) == 44
    assert set(refs) == set(netlist['components'])
    for item in items:
        if item['electrical_refs']:
            assert item['quantity']['main_10'] == len(item['electrical_refs']), item['id']
    with (ROOT/'design/electrical/bom.csv').open(newline='') as f:
        old = list(csv.DictReader(f))
    exported = {ref for row in old for ref in row['References'].split()}
    assert exported == set(refs)
    cad = json.loads((ROOT/'design/fusion/mirrored/layout.json').read_text())['bodies']
    main = [b for b in cad if b['assembly']=='main']
    hardware_counts = {
        'base_M2x6':sum('Base fasteners' in b['component_path'] for b in main),
        'display_M2x5':sum('PCB screws' in b['component_path'] and b['body'].startswith('LCD24382') for b in main),
        'MCU_M1_6':sum('PCB screws' in b['component_path'] and b['body'].startswith('DFR1075') for b in main),
    }
    assert hardware_counts == {'base_M2x6':8,'display_M2x5':4,'MCU_M1_6':4}
    for p,n in data['profiles'].items():
        assert sum(i['quantity'][p] for i in items if i['electrical_refs']) == 14+3*n
        assert by_id['H01']['quantity'][p] == (8 if p=='main_10' else 4+2*((n-4)//2))
        printed = sum(i['quantity'][p] for i in items if i['group']=='Printed parts')
        assert printed == (6 if p=='main_10' else 5+2*((n-4)//2))
    headers = ['ID','Group','Part','Specification','Fit condition','References','Unit']+LABELS+['Purchase unit','Notes','Source']
    with (ROOT/'docs/bill-of-materials.csv').open('w',newline='') as f:
        writer = csv.writer(f, lineterminator='\n'); writer.writerow(headers)
        for i in items:
            writer.writerow([i['id'],i['group'],i['part'],i['specification'],i['fit_condition'],
                             ' '.join(i['electrical_refs']),i['unit']]+
                            [i['quantity'][p] for p in PROFILES]+
                            [i['purchase_unit'],i['notes'],i['source']])

    def qty(item):
        q = list(item['quantity'].values())
        return str(q[0]) if len(set(q))==1 else 'N'

    def table(group, notes=False):
        lines = ['| ID / references | Fitted qty | Part and specification |','|---|---|---|']
        for i in items:
            if i['group']!=group:continue
            ref = i['id']
            if i['electrical_refs']:
                r = i['electrical_refs'];ref += ' / '+(r[0]+'-'+r[-1] if len(r)>3 else ', '.join(r))
            description = '**'+i['part']+'**. '+i['specification']+'.'
            if notes and i['notes']:description += ' '+i['notes']
            fitted = 'See p.1' if i['id']=='H01' else qty(i)+' '+i['unit']
            lines.append('| '+ref+' | '+fitted+' | '+description+' |')
        return '\n'.join(lines)

    core = table('Core')
    pedals = table('Pedals')
    power = table('Power')
    leds = table('LEDs')
    hardware = table('Hardware')
    wiring = table('Wiring')
    accessories = table('External accessories')
    assembly = table('Assembly')
    print_rows = ['| ID / print item | Mod 4 | Mod 6 | Mod 8 | Mod 10 | Main 10 |','|---|---|---|---|---|---|']
    for i in items:
        if i['group']=='Printed parts':
            print_rows.append('| '+i['id']+' '+i['part']+' | '+' | '.join(str(i['quantity'][p]) for p in PROFILES)+' |')

    doc = f'''# SIGMIDI Foot Controller v0.1

## Bill of materials - one completed controller

Preferred build: **Left**, with electronics on the left and modular extensions to the right. The Right variant uses the same purchased electrical parts; select its matching printed files. Quantities are installed quantities, excluding spares. Prices, stock and shipping are not included.

| Profile | Installed switches N | Pair extensions | Base M2x6 screws | Printed enclosure pieces |
|---|---|---|---|---|
| Modular 4 | 4 | 0 | 4 | 5 |
| Modular 6 | 6 | 1 | 6 | 7 |
| Modular 8 | 8 | 2 | 8 | 9 |
| Modular 10 | 10 | 3 | 10 | 11 |
| Main 10, fixed split chassis | 10 | Not applicable | 8 | 6 |

Use **N** below for the chosen installed switch count. **AR** means as required. Optional feature quantities apply only when that feature is fitted. Parts inside boards are not itemized. Counts include the two Nano mounting adapters. Use the Nano GPIO/power map; retained DFR1075 schematics are reference only.

## 1. Required control electronics

{core}

E16/E17 form the required USB VBUS divider at A4/GPIO11. All discrete resistors are 1% metal-film; 0.25 W through-hole is a practical procurement choice. Higher precision is optional. The 100 nF capacitor belongs to the switch ladder. Four 1 kOhm sections are in the base; each two-switch extension adds two. No resistor terminates the final tap.

<!-- page -->

# 2. Feature-dependent electronics

## Two passive pedal inputs

{pedals}

Fit J2 once for one or both pedal inputs. Each populated input adds one 10 kOhm bias resistor and one 5.1 kOhm reference resistor. The table fits both inputs. Across the complete two-input build there are **three 10 kOhm resistors total**, including R7 on page 1. The external pedals are passive; no active interface or extra ADC board is fitted.

## Optional 9 V power input

{power}

J1, U3 and C1 are omitted as a group in a USB-only electrical build. The existing chassis still contains their openings and mount features. Pololu 4083 is a **buck-boost** module, not just a step-down regulator; Kamami's 1178565 listing refers to this part. Nano VIN takes the positive 9 V sleeve directly; Pololu VOUT supplies the LED rail only. The converter 1 A rating is subject to thermal conditions. Do not feed its 5 V to Nano VIN or USB VBUS. [S3]

## Optional LED feedback

{leds}

Pololu 2535 is sold as a **10-pack**: buy one pack for any single 4-10 switch build and fit N LEDs. The current chain has LEDs, +5 V, GND and data wiring only; no extra driver, buffer, series resistor or chain capacitor is specified. C1 is the converter input capacitor, not an LED-chain component. Direct 3.3 V data into 5 V LEDs requires verification with the actual batch and harness. [S4]

<!-- page -->

# 3. Mounting hardware

{hardware}

**Avoid double counting included hardware.** H04 is one complete footswitch hardware set per switch; the reference drawing shows two nuts and one washer. H06 is the encoder's nut/washer set. H07 is J2's two nickel nuts and two fiber washers, shown in the attached manufacturer drawing. H08 is J1's 2 mm retaining nut. Check the seller's package contents before ordering any of these separately.

**H01 quantity:** main enclosure = eight. Modular = four on the electronics base plus two per added pair. The cap has an integral floor and no base screws. Use countersunk heads for H01 and H02. No separate heat-set inserts or metal standoffs are specified in the current design.

**Display fit:** four M2x5 screws pass through the printed hollow mounts into the factory blind studs. Nominal engagement is 1.39 mm; confirm head seating and usable stud depth on the delivered display. Do not substitute the base's M2x6 screws for the display screws.

**Nano mounting:** four H03 M1.6x5 pan-head screws attach the board to its two adapters; two H09 M1.6x6 screws attach the bridge to existing base poles. Glue the USB-side adapter foot to the original floor. Print P09/P10 without supports, component face down in the assembled mount. Check screw fit and USB cable seating before bonding.

**Control fit remains to confirm:** no exact footswitch or encoder manufacturer SKU is selected. Match the specified switch body and shaft offset, actuator height, encoder bushing length through the 3 mm roof, shaft form and knob bore. The encoder's 6 mm shaft and 8 mm body height are CAD assumptions. These checks determine the final orderable parts, not a change to the enclosure geometry.

<!-- page -->

# 4. Printed enclosure and assembly materials

Choose **one enclosure family**, not both. Main 10 is 350 mm wide; modular widths are 164.85 / 229.85 / 294.85 / 359.85 mm for 4 / 6 / 8 / 10 switches. The ten-switch modular enclosure is wider than the fixed main enclosure.

{chr(10).join(print_rows)}

## Preferred Left print selection

Main uses one each of **shell-left, shell-right, base-left, base-right** in design/fusion/mirrored/main/. Modular uses the electronics shell/base and one **right-cap**; every extension uses the universal **pair-base**. Upper-shell labeling depends on position:

| Modular total | Repeatable upper(s) | Cap-adjacent upper |
|---|---|---|
| 4 | None | None |
| 6 | None | pair-shell-at-right-cap-C |
| 8 | pair-shell-C | pair-shell-at-right-cap-D |
| 10 | pair-shell-C, pair-shell-D | pair-shell-at-right-cap-E |

Use the matching files in design/fusion/mirrored/modular/. Right builds use design/fusion/print/ and design/fusion/modular/, a left end cap and their matching labeled uppers. The print guides are authoritative for filenames and orientations. Print only designated shell/base/cap solids, not modeled electronics or reference hardware.

## Stock and consumables

{assembly}

Current supplied profiles use Prusa MK3S+, PETG, a 0.6 mm nozzle and 0.3 mm layers. A 1 kg filament spool is a stock allowance, not an estimate of consumed mass. Slice the actual selected parts with supports, brim and fit coupons. Mounts, converter spring clips, positioning ribs, support pins and glue lands are integral printed features, not separate purchased parts.

<!-- page -->

# 5. Wiring and external accessories

## Harness materials

{wiring}

Plan about **5 m total of assorted signal wire** and **2 m total supply/return wire** for stock. These are procurement allowances, not measured cut lengths. Keep purpose colors consistent, insulate solder joints, and leave service slack between upper ports and base electronics. Connector families for optional detachable section harnesses and a carrier-board outline are not finalized. Direct solder wiring is the documented electrical baseline; do not assume a custom PCB exists.

## Equipment outside the enclosure

{accessories}

A04 allows up to two passive pedals; zero or one is also valid. A05 is needed for a direct HX Stomp DIN connection, not for connection to an iPad BLE MIDI application. The dongle must be able to act as a central for a third-party peripheral; interoperability has not been bench qualified. HX Stomp, iPad, printer, tools and their own power supplies are not included in the controller BOM.

USB and 9 V sources are alternative power options. Choose each supply for the complete measured load. Ten Pololu 2535 LEDs draw about 0.5 A at full white before the controller/display load. A higher-current input adapter does not increase the converter's 5 V output/thermal rating. Confirm how the LED 5 V branch is powered in a USB-only build; do not join independent positive supply outputs. [S3, S4]

<!-- page -->

# 6. Procurement notes and traceability

## Before placing the order

| Item | Required check |
|---|---|
| Arduino Nano ESP32 | ABX00083 without headers; direct wiring and two printed adapters. Recalibrate analog inputs on the new board. |
| Waveshare 24382 | Non-touch 1.69inch LCD Module; verify rear M2 studs and GH1.25 8-pin cable. Do not substitute a similar touch display. |
| Footswitch / encoder | Exact supplier SKUs remain open; match the dimensional and contact requirements on pages 1 and 3. |
| J1 power socket | Match 8 mm thread, 8 mm threaded length, 18 mm total envelope and 2 mm nut; flange and nut outside diameters still require fit confirmation. |
| MCU screws | Four M1.6x5 and two M1.6x6 pan head; verify printed pilot engagement. |
| Bundled hardware | Check cable, header, nuts and washers already supplied with the boards and controls. Do not buy duplicate sets. |

## Quantity and source checks

The existing maximum electrical BOM/netlist contains **44 shared reference component instances**: three purchased boards, two socket assemblies, one encoder, ten footswitches, sixteen resistors, two capacitors and ten LEDs. The Nano build adds two USB VBUS resistors, for 46 electrical instances at ten switches. The shared reference includes both pedals, 9 V power and LEDs. The similarly sized CSV line count is coincidental: CSV rows also include grouped hardware, printed parts and external accessories.

For all optional circuits fitted, electrical instance totals are **28 / 34 / 40 / 46** at 4 / 6 / 8 / 10 switches. Omitting LEDs subtracts N; omitting 9 V input subtracts three (J1/U3/C1). Omitting the complete pedal interface subtracts five (J2 and four resistors). Printed/hardware quantities are separate. The BOM generator checks all 44 reference designators against both electrical exports and verifies the main 8/4/4 base/display/MCU screw counts against the CAD body inventory.

## References

**[S1]** [Arduino Nano ESP32 documentation](https://docs.arduino.cc/hardware/nano-esp32/): board identity and manufacturer dimensions. **[S2]** [Waveshare 24382 documentation](https://www.waveshare.com/wiki/1.69inch_LCD_Module): module, connector and mechanical specification.

**[S3]** [Pololu S13V10F5 #4083](https://www.pololu.com/product/4083): regulator, current/thermal limits and input transient capacitor guidance. **[S4]** [Pololu 2535](https://www.pololu.com/product/2535): 10-pack, supply and LED package.

Local basis: design/electrical/bom.csv and netlist.json; design/fusion/mirrored/layout.json; enclosure assembly guides; docs/hardware.md and power.md; and design/fusion/datasheets/double-trs-ACJS-MHDC.pdf. The manufacturer's TRS drawing shows the included nuts/washers and optional PCB support hole; no extra saddle screw is specified in this assembly.

Prepared 30 October 2026 for SIGMIDI v0.1. The Nano firmware, harness and two adapters are specified here; original enclosure solids are retained. Values and CAD fit describe the current prototype; purchased-part fit, direct LED drive, power/thermal performance and physical assembly still require bench checks. Edit docs/bom-items.json and rerun scripts/build_bom.py to refresh the PDF, Markdown and shopping CSV.
'''
    markdown = ROOT/'docs/bill-of-materials.md'
    markdown.write_text(doc)
    render(doc)
    source_files = ['docs/bom-items.json','docs/bill-of-materials.md','scripts/build_bom.py',
                    'design/electrical/bom.csv','design/electrical/netlist.json',
                    'design/fusion/mirrored/layout.json','design/fusion/mirrored/README.md',
                    'design/fusion/README.md','design/fusion/datasheets/double-trs-ACJS-MHDC.pdf',
                    'docs/hardware.md','docs/power.md','scripts/build_user_manual.py']
    digest = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {'project':data['project'],'version':data['version'],'BOM_lines':len(items),
                'shared_electrical_reference_count':len(refs), 'total_electrical_instances_main':len(refs)+2,'shared_electrical_refs_match_reference_exports':True,'USB_VBUS_divider_BOM_ids':['E16','E17'],'Nano_mount_hardware':{'M1.6x5':4,'M1.6x6':2},
                'original_enclosure_reference_hardware_counts':hardware_counts,'profiles':data['profiles'],
                'source_sha256':{n:digest(ROOT/n) for n in source_files},
                'outputs':{n:digest(ROOT/n) for n in ['docs/bill-of-materials.csv',str(PDF.relative_to(ROOT))]},
                'physical_fit_qualified':False,'purchased_parts_inside_boards_itemized':False}
    (ROOT/'docs/bom-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'PDF':str(PDF),'pages':6,'BOM_lines':len(items),
                      'shared_reference_instances':len(refs), 'electrical_instances_main':len(refs)+2,'main_hardware':hardware_counts},indent=2))


def render(markdown):
    fonts = Path('/System/Library/Fonts/Supplemental')
    for name,file in [('Manual','Arial.ttf'),('ManualBold','Arial Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
    pdfmetrics.registerFontFamily('Manual',normal='Manual',bold='ManualBold',italic='Manual',boldItalic='ManualBold')
    styles = {
        'Chapter':ParagraphStyle('Chapter',fontName='ManualBold',fontSize=22,leading=26,textColor=INK,spaceAfter=13,keepWithNext=True),
        'Section':ParagraphStyle('Section',fontName='ManualBold',fontSize=12,leading=15,textColor=TEAL,spaceBefore=9,spaceAfter=6,keepWithNext=True),
        'Body':ParagraphStyle('Body',fontName='Manual',fontSize=9.8,leading=13,textColor=INK,spaceAfter=7),
        'Cell':ParagraphStyle('Cell',fontName='Manual',fontSize=8.6,leading=11.4,textColor=INK),
    }
    story=[]
    sections=markdown.split('<!-- page -->')
    for p,section in enumerate(sections):
        if p:story.append(PageBreak())
        lines=section.strip().splitlines();i=0
        while i<len(lines):
            line=lines[i].strip()
            if not line:i+=1;continue
            if line.startswith('# '):story.append(Paragraph(inline(line[2:]),styles['Chapter']));i+=1
            elif line.startswith('## '):story.append(Paragraph(inline(line[3:]),styles['Section']));i+=1
            elif line.startswith('|'):
                rows=[]
                while i<len(lines) and lines[i].strip().startswith('|'):
                    cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r'[-:]+',x) for x in cells):rows.append(cells)
                    i+=1
                n=len(rows[0]);head=rows[0][0]
                if head=='ID / references':widths=[CONTENT*.18,CONTENT*.12,CONTENT*.70]
                elif head=='ID / print item':widths=[CONTENT*.43]+[CONTENT*.114]*5
                elif head=='Profile':widths=[CONTENT*.30]+[CONTENT*.175]*4
                elif n==2:widths=[CONTENT*.26,CONTENT*.74]
                else:widths=[CONTENT/n]*n
                content=[[Paragraph(('<b>'+inline(x)+'</b>') if j==0 else inline(x),styles['Cell']) for x in row] for j,row in enumerate(rows)]
                t=Table(content,colWidths=widths,repeatRows=1,hAlign='LEFT')
                t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf5f1')),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f9f8')]),
                    ('LINEBELOW',(0,0),(-1,0),.8,TEAL),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#d6e1de')),
                    ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
                    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
                story.extend([t,Spacer(1,7)])
            else:
                text=[line];i+=1
                while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|')):
                    text.append(lines[i].strip());i+=1
                story.append(Paragraph(inline(' '.join(text)),styles['Body']))
    PDF.parent.mkdir(parents=True,exist_ok=True)
    document=Manual(str(PDF),pagesize=A4,leftMargin=MARGIN,rightMargin=MARGIN,topMargin=49,bottomMargin=43,
                    title='SIGMIDI Foot Controller v0.1 - Bill of materials',author='SIGMIDI project')
    document.chapters=[]
    def frame(c,d):
        c.setFillColor(TEAL);c.rect(0,HEIGHT-7,WIDTH,7,stroke=0,fill=1)
        c.setFont('ManualBold',8);c.setFillColor(INK);c.drawString(MARGIN,HEIGHT-28,'SIGMIDI / FOOT CONTROLLER')
        c.setFont('Manual',8);c.drawRightString(WIDTH-MARGIN,HEIGHT-28,'BILL OF MATERIALS  v0.1')
        c.setStrokeColor(colors.HexColor('#c9d8d3'));c.line(MARGIN,32,WIDTH-MARGIN,32)
        c.setFillColor(colors.HexColor('#506268'));c.drawString(MARGIN,20,'Installed quantities / feature-dependent options')
        c.drawRightString(WIDTH-MARGIN,20,str(d.page))
    document.build(story,onFirstPage=frame,onLaterPages=frame)
    assert [c['page'] for c in document.chapters]==list(range(1,7)),document.chapters


if __name__=='__main__':main()
