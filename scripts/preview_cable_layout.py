#!/usr/bin/env python3
"""Create a routing proposal using the Left enclosure's CAD footprints."""
from pathlib import Path
import json,html,hashlib
R=Path(__file__).resolve().parents[1];P=R/'previews';rows=json.loads((R/'design/fusion/mirrored/layout.json').read_text())['bodies']
rows=[r for r in rows if r['assembly']=='main'];groups={}
for r in rows:groups.setdefault(r['component_path'].split('/')[-1],[]).append(r)
colors={'dc':'#d65e21','supply':'#cf3144','ground':'#303a48','ladder':'#b47a00','pedal':'#008b95','display':'#2b74cc','encoder':'#45933b','led':'#9251c7'}
meta={
'dc':('9 V input','Sleeve +9 V → Nano VIN + Pololu VIN','2 wires · J-PWR', 'power'),
'supply':('Regulated 5 V','Pololu VOUT → optional LED rail only','Supply + return travel together','power'),
'ground':('Ground / returns','Common reference; LED return to supply','Dark lines beside power and signals','power'),
'ladder':('Footswitch ladder','Series taps T1–T10; each adds 1 kΩ','TAIL + GND between sections','controls'),
'pedal':('Expression pedals','Passive TRS → 2 resistors/input → A1 / GPIO2 and A3 / GPIO4','6 wires at sockets · bias D2 / GPIO5 and D3 / GPIO6','controls'),
'display':('LCD / SPI','D8–D12 / GPIO17, 18, 21, 38, 47; 3V3 + GND','7 wires · backlight tied to 3V3 locally','controls'),
'encoder':('Encoder + click','D4–D6 / GPIO7, 8, 9 + common GND','4 wires · J-ENC','controls'),
'led':('Optional Pololu 2535','D7 / GPIO10 → first LED DIN, directly','5V + GND + data; preserve tap assignments','led')}
S=4;OX=80;OY=202
X=lambda x:OX+x*S
Y=lambda y:OY+y*S
out=['<svg xmlns="http://www.w3.org/2000/svg" width="1560" height="1120" viewBox="0 0 1560 1120" role="img" aria-labelledby="title desc">',
'<title id="title">SIGMIDI Left enclosure cable bundle layout</title><desc id="desc">Top-down routing proposal using native component footprints, color coded by cable purpose. Rear edge at top. Main case 350 by 92 millimetres. Base-removal connectors and a modular four-net interface are shown.</desc>',
'<defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#e2e7ed" stroke-width=".65"/></pattern></defs>',
'<style>text{font-family:Arial,sans-serif;fill:#26354b}.tiny{font-size:11px}.nano-label{font-size:10px}.small{font-size:13px}.medium{font-size:16px}.label{font-size:14px;font-weight:700}.wire{fill:none;stroke-linejoin:round;stroke-linecap:round}.body{fill:#e4e9ed;stroke:#96a1af;stroke-width:1.3}.board{fill:#d5e8da;stroke:#72957b;stroke-width:1.5}.dim{fill:none;stroke:#7f8da0;stroke-width:1}.muted{fill:#617087}.route.dimmed{opacity:.08}.route{transition:opacity .15s}</style>',
'<rect width="1560" height="1120" fill="#f5f7fa"/>',
'<text x="80" y="54" font-size="16" font-weight="700" letter-spacing="3" fill="#19836b">SIGMIDI / HARNESS PLANNING</text>',
'<text x="80" y="99" font-size="34" font-weight="700">Cable bundles · Left enclosure</text>',
'<text x="80" y="129" class="medium muted">Top view, roof omitted · actual CAD footprints · proposed routing, disconnects and interface area</text>',
'<text x="1480" y="55" text-anchor="end" class="label">v0.1</text>',
'<text x="1480" y="80" text-anchor="end" class="small muted">PREVIEW / NOT A CUTTING OR PINOUT TEMPLATE</text>',
'<path d="M80 173H1480 M80 166V180 M1480 166V180" class="dim"/>',
'<rect x="729" y="158" width="102" height="27" fill="#f5f7fa"/><text x="780" y="177" text-anchor="middle" class="small">350 mm</text>',
'<rect x="80" y="202" width="1400" height="368" rx="24" fill="#edf1f5" stroke="#697a8d" stroke-width="2"/>',
'<rect x="88" y="210" width="1384" height="352" rx="18" fill="url(#grid)"/>',
'<path d="M80 338H1480" stroke="#b2bec9" stroke-dasharray="8 6"/><text x="1458" y="330" text-anchor="end" class="small muted">30 mm deck step</text>',
'<path d="M706 202V570" stroke="#a8b3c1" stroke-width="2" stroke-dasharray="4 5"/><text x="717" y="222" class="tiny muted">main split</text>']
def rect(x,y,w,h,cls='body',radius=3):out.append(f'<rect x="{X(x):.2f}" y="{Y(y):.2f}" width="{w*S:.2f}" height="{h*S:.2f}" rx="{radius}" class="{cls}"/>')
def txt(x,y,t,cls='small',anchor='middle',color=None):out.append(f'<text x="{X(x):.2f}" y="{Y(y):.2f}" text-anchor="{anchor}" class="{cls}"'+(f' style="fill:{color}"' if color else '')+'>'+html.escape(t)+'</text>')
def bbox(items):
 return [min(i['min_mm'][0] for i in items),-max(i['max_mm'][1] for i in items),max(i['max_mm'][0] for i in items),-min(i['min_mm'][1] for i in items)]
footprints=[]
for name,items in groups.items():
 if 'SW' in name and 'Mirrored SW' in name:
  body=next(i for i in items if '30x13x15' in i['body']);x0,y0,x1,y1=bbox([body]);rect(x0,y0,x1-x0,y1-y0)
  shaft=next(i for i in items if 'shaft' in i['body'].lower());q=bbox([shaft]);cx=(q[0]+q[2])/2;cy=(q[1]+q[3])/2
  num=int(name.split('SW')[1][:2]);label=chr(65+5-num) if num<=5 else str(11-num)
  out.append(f'<circle cx="{X(cx)}" cy="{Y(cy)}" r="13" fill="#aeb9c4" stroke="#728296"/>');txt(cx,cy+1.2,label,'label')
  footprints.append({'component':name,'bounds_XY_mm':[x0,y0,x1,y1],'switch':label})
 elif 'Pololu 2535' in name:
  q=bbox(items);cx=(q[0]+q[2])/2;cy=(q[1]+q[3])/2
  out.append(f'<circle cx="{X(cx)}" cy="{Y(cy)}" r="10" fill="#e8dff4" stroke="#a58bc0"/>')
for needle,label,cls in [('LCD Waveshare','LCD / SPI','board'),('Double TRS','Dual TRS','body'),('Pololu S13V10F5','5V','board'),('Encoder 15x15','ENC','body'),('DC power socket','9 V DC','body')]:
 name,items=next((n,v) for n,v in groups.items() if needle in n);q=bbox(items);x0,y0,x1,y1=q
 rect(x0,max(0,y0),x1-x0,y1-max(0,y0),cls,5)
 txt((x0+x1)/2,(max(0,y0)+y1)/2+1.3,label,'tiny')
 footprints.append({'component':name,'bounds_XY_mm':q})
# Nano placement from its verified component-side-up direct-post pose.
fit=json.loads((R/'design/fusion/nano-esp32/mount-fit.json').read_text())
holes=fit['board_holes_XY_mm'];x0=min(q[0] for q in holes)-1.27;x1=max(q[0] for q in holes)+1.27
y0=-max(q[1] for q in holes)-1.27;y1=-min(q[1] for q in holes)+1.27
rect(x0,y0,x1-x0,y1-y0,'board',4)
nano_label_x=(x0+x1)/2
for hx,hy in holes:out.append(f'<circle cx="{X(hx)}" cy="{Y(-hy)}" r="3.32" fill="white" stroke="#72957b"/>')
footprints.append({'component':'Arduino Nano ESP32 ABX00083','bounds_XY_mm':[x0,y0,x1,y1],'source':'design/fusion/nano-esp32/mount-fit.json','component_face_down':False})
# USB connector and nominal rear socket centres.
rect(95,0,9,5,'body');txt(99.5,-4,'Nano ESP32 / USB-C','small')
txt(23,-4,'TRS 1 / 2','small');txt(140,-4,'9 V · centre negative','small')
# Existing vent area is crosshatched rather than available for tie mounts.
for x in [91,96,101,106,111,120,126]:
 out.append(f'<path d="M{X(x)} {Y(49)}V{Y(60)}" stroke="#adc3c1" stroke-width="5" opacity=".6"/>')
# Carrier area is a functional placeholder, clearly distinct from CAD components.
out.append(f'<rect x="{X(61)}" y="{Y(30)}" width="80" height="40" rx="6" fill="#fff" stroke="#6b7d91" stroke-width="1.7" stroke-dasharray="5 4"/>')
txt(71,29,'Pedal + USB resistors','tiny')
paths=[]
def route(kind,points,width=.8,label=''):
 pts=' '.join(f'{X(x):.2f},{Y(y):.2f}' for x,y in points)
 out.append(f'<g class="route" data-bundle="{kind}"><title>{html.escape(meta[kind][0]+": "+label)}</title><polyline points="{pts}" class="wire" stroke="#fff" stroke-width="{width*S+2.3}"/><polyline points="{pts}" class="wire" stroke="{colors[kind]}" stroke-width="{width*S}"/></g>')
 paths.append({'purpose':kind,'points_XY_mm':points,'description':label})
# Power follows the model's five-segment reference envelopes.
route('dc',[(142,12),(142,20),(114,20),(114,32.98),(119.21,32.98)],1,'Socket sleeve +9 V to converter VIN')
route('ground',[(138,12),(138,18),(116,18),(116,30.45),(119.21,30.45)],.65,'Socket centre negative to converter GND')
route('dc',[(142,20),(114,20),(114,51.5),(87.5,51.5),(87.5,45.5),(90.4,45.5)],1,'9V input to Nano VIN; no converter 5V connection to Nano')
route('ground',[(119.21,30.45),(116,30.45),(116,53),(86,53),(86,43.5),(90.4,43.5)],.65,'Converter return to Nano ground')
route('supply',[(119,28),(119,35),(81,35)],.8,'LED +5V distribution; pair with return')
route('ground',[(119,30.5),(120.5,36.5),(81,36.5)],.65,'LED supply return, routed directly to supply point')
route('pedal',[(27,27.4),(27,31),(56,31),(56,33),(61,33)],1.15,'Six TRS conductors to passive resistor connections')
route('pedal',[(81,32),(84,32),(90.4,36.5)],1.0,'Direct TIP ADC signals, two bias GPIOs, reference and ground to Nano')
route('display',[(108.2,44.5),(112,44.5),(112,54),(82.5,54),(82.5,42),(43,42),(43,46.23)],1.1,'Short SPI loom to display; J-LCD service disconnect')
route('encoder',[(12.5,57),(12.5,46),(57,46),(57,41),(84.5,41),(84.5,55.5),(113.5,55.5),(113.5,42.5),(108.2,42.5)],.95,'A, B, click and common ground to Nano')
# Lines mark harness corridors, not common electrical nets. Tap resistors stay in electrical order.
route('ladder',[(90.4,39.5),(83,39.5),(83,21),(338,21)],.95,'Raised-row switched ladder harness')
route('ladder',[(83,21),(55,21),(55,40.5),(64,40.5),(64,76),(338,76)],.95,'Base and lower-row ladder harness; descent proposal')
for x in [42.6,107.6,172.6,237.6,302.6]:
 route('ladder',[(x,18),(x,21)],.7,'Local switch branch / series tap resistor')
for x in [75.1,140.1,205.1,270.1,335.1]:
 route('ladder',[(x,73.5),(x,76)],.7,'Local switch branch / series tap resistor')
route('ladder',[(42.6,21),(65,21)],.95,'Base A branch')
# Optional pixel harness follows the model's left descent and upper/lower wire envelopes.
route('led',[(108.2,39.5),(115,39.5),(115,56.5),(84,56.5),(84,38),(54,38),(54,32.4),(9.5,32.4),(9.5,26.2),(305,26.2)],1.15,'Upper LED harness in CAD reference envelope Z17..21')
route('led',[(9.5,32.4),(9.5,84.5),(338,84.5)],1.15,'Left descent / lower LED harness; lower bus Z-12..-9')
for x in [42.6,107.6,172.6,237.6,302.6]:route('led',[(x,26.2),(x,28)],.65,'LED branch; connect DIN/DOUT in electrical tap order')
for x in [75.1,140.1,205.1,270.1,335.1]:route('led',[(x,84.5),(x,81.7)],.65,'LED branch; connect DIN/DOUT in electrical tap order')
# Proposed detachable plugs are printed as white blocks along each loom.
for x,y,name in [(132,20,'J-PWR'),(59,31,'J-PED'),(61,42,'J-LCD'),(42,46,'J-ENC'),(83,21,'J-SW'),(54,32.4,'J-LED')]:
 out.append(f'<rect x="{X(x)-7}" y="{Y(y)-5}" width="14" height="10" rx="2" fill="#fff" stroke="#34465c"/>')
 lx,ly={'J-PED':(59,26),'J-LED':(45,36),'J-LCD':(61,47),'J-ENC':(42,49)}.get(name,(x,y-3))
 txt(lx,ly,name,'tiny')
# Draw raised-row controls last so the lower PCB/socket footprints cannot hide A/B.
for i,x in enumerate([42.6,107.6,172.6,237.6,302.6]):
 out.append(f'<rect x="{X(x-9)}" y="{Y(5)}" width="120" height="52" rx="3" fill="#d9e0e7" fill-opacity=".5" stroke="#7b899a" stroke-width="1.2"/>')
 out.append(f'<circle cx="{X(x)}" cy="{Y(11.5)}" r="13" fill="#aeb9c4" stroke="#728296"/>')
 txt(x,12.7,chr(65+i),'label')
# Keep the board identity readable above the harness corridors.
out.append(f'<rect x="{X(nano_label_x-8)}" y="{Y(28)}" width="64" height="25" rx="3" fill="#f5faf7" fill-opacity=".95"/>')
txt(nano_label_x,30.4,'Nano ESP32','nano-label')
txt(nano_label_x,33.2,'components up','nano-label')
# Section interfaces and routing tier annotation below the plan.
out += ['<text x="80" y="602" class="small muted">REAR ↑  /  FRONT ↓   ·   Looking down into the case, not a mirrored underside view</text>',
'<text x="1480" y="602" text-anchor="end" class="small muted">92 mm depth · upper row +30 mm</text>',
'<rect x="80" y="624" width="1400" height="79" rx="12" fill="#e8eef5"/>',
'<text x="103" y="650" class="label">Modular joint / 4-net interface</text>',
'<text x="103" y="674" class="small">TAIL + GND + optional 5V + LED DATA. Each pair adds 2 × 1 kΩ; final TAIL stays open.</text>',
'<text x="103" y="692" class="tiny muted">LED data sequence: B(T1) → A(T2) → 2(T3) → 1(T4) → C(T5) → 3(T6) → D(T7) → 4(T8) → E(T9) → 5(T10).</text>',
'<text x="1125" y="650" class="label">Service loops</text>',
'<text x="1125" y="674" class="small">Disconnect shell-mounted controls</text>',
'<text x="1125" y="692" class="small">before withdrawing the base / USB.</text>']
for i,(kind,(title,details,note,group)) in enumerate(meta.items()):
 col=i%2;row=i//2;x=80+col*710;y=727+row*74
 out += [f'<g data-legend="{kind}"><rect x="{x}" y="{y}" width="690" height="65" rx="9" fill="#fff" stroke="#e1e6ed"/>',f'<path d="M{x+18} {y+21}H{x+47}" stroke="{colors[kind]}" stroke-width="5" stroke-linecap="round"/>',f'<text x="{x+60}" y="{y+25}" class="label">{html.escape(title)}</text>',f'<text x="{x+60}" y="{y+44}" class="small">{html.escape(details)}</text>',f'<text x="{x+60}" y="{y+59}" class="tiny muted">{html.escape(note)}</text></g>']
out += ['<text x="80" y="1045" class="small">Lines represent bundle corridors, not electrical junctions. Connect ladder taps and pixels in the stated order.</text>',
'<text x="80" y="1068" class="small muted">Nano is components-up on verified integral posts; other footprints from Fusion. Different Z levels overlap in this view.</text>',
'<text x="80" y="1090" class="small muted">Routes are bundle corridors, not pin positions. VBUS → 100k → A4; A4 → 150k → GND. Verify service-loop clearances.</text>','</svg>']
svg='\n'.join(out);(P/'cable-bundles-left.svg').write_text(svg)
detail_inner=svg[svg.index('>')+1:svg.rindex('</svg>')]
(P/'cable-bundles-left-detail.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1560" height="1000" viewBox="0 0 1560 1000"><rect width="1560" height="1000" fill="#f5f7fa"/><text x="40" y="44" font-family="Arial,sans-serif" font-size="26" fill="#26354b">SIGMIDI · electronics harness detail · Left</text><svg x="20" y="70" width="1520" height="860" viewBox="60 193 655 390">'+detail_inner+'</svg><text x="40" y="970" font-family="Arial,sans-serif" font-size="18" fill="#617087">Routing proposal. Dashed interface is not a fitted CAD part; vertical clearances require review.</text></svg>')
data={'variant':'Left main, ten switches','source':'design/fusion/mirrored/layout.json','nano_mount_source':'design/fusion/nano-esp32/mount-fit.json','nano_mount_sha256':hashlib.sha256((R/'design/fusion/nano-esp32/mount-fit.json').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((R/'design/fusion/mirrored/layout.json').read_bytes()).hexdigest(),'status':'routing proposal; no native CAD changes','component_footprints':footprints,'bundles':meta,'colors':colors,'routes':paths,'notes':['XY corridors only; crossings do not connect nets','Native LED/power references used; other routing and unmodeled interface carrier need clearance validation','Electrical tap and LED assignments remain unchanged','Disconnect shell controls and withdraw MCU USB before base removal']}
(P/'cable-bundles-left.json').write_text(json.dumps(data,indent=2)+'\n')
buttons=''.join(f'<button data-focus="{k}" style="--bundle:{colors[k]}">{html.escape(meta[k][0])}</button>' for k in meta)
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>SIGMIDI cable routing preview</title><style>body{margin:0;background:#f5f7fa;color:#26354b;font:14px Arial,sans-serif}nav{padding:18px 5%;display:flex;gap:8px;flex-wrap:wrap;align-items:center;border-bottom:1px solid #dae1e8}button,a{font:inherit}button{border:1px solid #c6ced8;border-left:5px solid var(--bundle,#26354b);background:white;color:#26354b;padding:8px 12px;border-radius:6px;cursor:pointer}button[aria-pressed=true]{background:#26354b;color:white}nav a{margin-left:auto;color:#265f99}main{max-width:1700px;margin:auto}svg{width:100%;height:auto;display:block}footer{padding:12px 5%;color:#617087}</style><nav aria-label="Cable bundle filters"><strong>Show:</strong><button data-focus="all" aria-pressed="true">All bundles</button>'''+buttons+'''<a href="cable-bundles-left-detail.svg">Electronics zoom</a><a href="cable-bundles-left.svg">Download SVG</a></nav><main>'''+svg+'''</main><footer>Routing preview only. No firmware settings or Fusion geometry changed.</footer><script>for(const b of document.querySelectorAll('button[data-focus]'))b.addEventListener('click',()=>{const k=b.dataset.focus;for(const p of document.querySelectorAll('.route'))p.classList.toggle('dimmed',k!=='all'&&p.dataset.bundle!==k);for(const q of document.querySelectorAll('button[data-focus]'))q.setAttribute('aria-pressed',String(q===b));});</script></html>'''
(P/'cable-bundles-left.html').write_text(page)
print('Created SVG, interactive HTML and routing data from',len(footprints),'CAD component footprints.')
if __name__=='__main__':pass
