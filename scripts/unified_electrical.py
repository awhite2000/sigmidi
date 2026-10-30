"""Draw and electrically validate a unified external-pin wiring schematic.

Called by preview_electrical.py after its component/netlist definitions exist.
Every connected terminal is placed once. Wire geometry, including rail branches,
is checked against that netlist before PDF/SVG export.
"""
import json
from collections import defaultdict


def render(m):
    old=m.W,m.H,m.C
    m.W,m.H=3800,2687
    pdf=m.PDF.with_name('sigmidi-electrical-single-page.pdf')
    m.C=m.canvas.Canvas(str(pdf),pagesize=m.landscape(m.A0),pageCompression=1)
    m.C.setTitle('SIGMIDI Foot Controller v0.1 - unified electrical schematic')
    m.C.setAuthor('SIGMIDI Foot Controller project')
    m.C.scale(m.landscape(m.A0)[0]/m.W,m.landscape(m.A0)[0]/m.W)
    s=m.Sheet.__new__(m.Sheet)
    s.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {m.W} {m.H}" role="img" aria-label="SIGMIDI unified electrical schematic">']
    s.rect(0,0,m.W,m.H,fill='white',stroke='none')
    wires=[];terminals={};bodies=[];labels=[]
    colors={**m.COLORS,'3V3':'#a64932'}
    def color(net):
        if net and net.startswith('LCD_'):return m.BLUE
        if net and net.startswith('T') and net[1:].isdigit():return m.AMBER
        return colors.get(net,m.PURPLE if net and net.startswith('L') and net[1:].isdigit() else m.TEAL)
    def text(x,y,t,size=17,**kw):labels.append((x,y,t,size,kw))
    def box(x,y,w,h,fill):
        bodies.append((x,y,x+w,y+h))
        s.rect(x,y,w,h,fill=fill,stroke=m.INK)
    def pin(ref,p,x,y,label=None,side='right'):
        key=f'{ref}.{p}'
        assert key not in terminals,key
        net=m.COMPONENTS[ref]['pins'][p]
        terminals[key]={'net':net,'xy':(x,y)}
        s.circle(x,y,4,color(net) if net else m.MUTED,False)
        if label:text(x+(14 if side=='left' else -14),y+7,label,21,anchor='start' if side=='left' else 'end',bold=True)
        return (x,y)
    def wire(net,*pts):
        for a,b in zip(pts,pts[1:]):
            assert a[0]==b[0] or a[1]==b[1],(net,a,b)
            if a!=b:wires.append((net,a,b))
    def res(ref,a,b):
        neta=m.COMPONENTS[ref]['pins']['1'];netb=m.COMPONENTS[ref]['pins']['2']
        pin(ref,'1',*a);pin(ref,'2',*b)
        x=(a[0]+b[0])/2;y=(a[1]+b[1])/2
        if a[1]==b[1]:
            direction=1 if b[0]>a[0] else -1
            wire(neta,a,(x-22*direction,y));wire(netb,(x+22*direction,y),b)
            box(x-22,y-9,44,18,'white')
            text(x,y-43,ref,19,anchor='middle');text(x,y-18,m.COMPONENTS[ref]['value'],21,anchor='middle')
        else:
            wire(neta,a,(x,y-25));wire(netb,(x,y+25),b)
            box(x-9,y-25,18,50,'white')
            text(x+20,y-6,ref,19);text(x+20,y+21,m.COMPONENTS[ref]['value'],21)
    def cap(ref,a,b):
        pin(ref,'1',*a);pin(ref,'2',*b)
        x=a[0];y=(a[1]+b[1])/2
        wire(m.COMPONENTS[ref]['pins']['1'],a,(x,y-6))
        wire(m.COMPONENTS[ref]['pins']['2'],(x,y+6),b)
        s.line(x-15,y-6,x+15,y-6);s.line(x-15,y+6,x+15,y+6)
        text(x+24,y-48 if ref=='C1' else y-10,ref,19);text(x+24,y-23 if ref=='C1' else y+18,m.COMPONENTS[ref]['value'],21)
        if ref=='C1':text(x-20,y-10,'+',18,bold=True)
    # Physical Nano top view, USB up. Header pad IDs are from Arduino's schematic.
    box(1500,300,900,1050,'#f6f8fa')
    s.rect(1835,274,230,44,fill='white',stroke=m.INK)
    text(1950,305,'USB-C / MIDI',22,anchor='middle',bold=True)
    text(1950,355,'U1  Arduino Nano ESP32',29,anchor='middle',bold=True)
    text(1950,387,'Component-side top view / USB-C up',19,anchor='middle',color=m.MUTED)
    up={};data=m.external_pin_data()
    for header,rows,right in m.HEADERS:
        x=2400 if right else 1500
        for i,(n,_,_) in enumerate(rows):
            ref=f'{header}:{n}';y=400+60*i
            up[ref]=(x,y);pin('U1',ref,x,y)
            pad=data[ref];tx=x-25 if right else x+25;anchor='end' if right else 'start'
            subtitle=ref+(f' / {pad["logical_name"]}' if pad['net'] else '')
            text(tx,y-18,subtitle,18,anchor=anchor,color=color(pad['net']) if pad['net'] else m.MUTED)
            text(tx,y+8,pad['physical_label'],21,anchor=anchor,bold=True)
    assert [up[f'JP1:{n}'][1] for n in range(1,16)]==list(range(400,1241,60))
    assert [up[f'JP2:{n}'][1] for n in range(15,0,-1)]==list(range(400,1241,60))
    text(1950,1310,'All printed labels retained; unused pads left unwired.',18,anchor='middle',color=m.MUTED)
    # Power and return rails run outside component outlines.
    wire('3V3',(60,250),(2740,250))
    wire('3V3',up['JP1:2'],(1100,460),(1100,250))
    wire('3V3',(60,250),(60,2445),(1100,2445),(1100,2140))
    wire('3V3',(1100,460),(1100,550),(780,550),(780,900))
    wire('+5V',(80,200),(3700,200))
    wire('+5V',(80,200),(80,1325),(500,1325),(500,2430))
    wire('GND',(40,480),(40,2460),(3750,2460),(3750,1060))
    wire('GND',up['JP1:14'],(1400,1180),(1400,1500),(1080,1500))
    wire('GND',up['JP2:4'],(3750,1060))
    wire('GND',(600,1325),(600,2460))
    text(1120,228,'3V3 / Nano logic supply',22,bold=True,color=color('3V3'))
    text(3700,228,'+5V LED',23,bold=True,color=m.RED,anchor='end')
    text(3710,2435,'COMMON GND',21,anchor='end',bold=True)
    # The display stays in actual physical connector order, pin 1 at top.
    box(2800,350,600,650,'#edf4fc')
    text(3070,390,'U2  Waveshare 24382',26,anchor='middle',bold=True)
    lcd={n:410+(n-1)*80 for n in range(1,9)}
    for n,y in lcd.items():pin('U2',f'P2:{n}',2800,y,f'{n}  {m.LCD[n-1][1]}',side='left')
    wire('3V3',(2740,250),(2740,410),(2800,410))
    wire('3V3',(2720,250),(2720,970),(2800,970))
    wire('GND',(2800,890),(2700,890),(2700,1100),(3750,1100))
    for n,ref,ch in [(2,'JP2:15',2500),(6,'JP2:14',2540),(4,'JP2:13',2580),(3,'JP2:12',2620),(5,'JP2:11',2660)]:
        a=up[ref];wire(m.COMPONENTS['U2']['pins'][f'P2:{n}'],a,(ch,a[1]),(ch,lcd[n]),(2800,lcd[n]))
    text(3070,1028,'P2 / GH1.25 / SPI / pins 1-8',19,anchor='middle',color=m.BLUE)
    # External DC feeds Nano VIN and converter VIN; converter 5V feeds LEDs only.
    box(100,290,300,160,'#fff8ef')
    text(120,328,'J1  5.5 x 2.1mm',23,bold=True)
    text(115,365,'9V DC / center-negative',19)
    pin('J1','CENTER',250,450);text(250,433,'CENTER (-)',21,anchor='middle',bold=True)
    pin('J1','SLEEVE',400,410,'SLEEVE (+)')
    box(700,290,300,160,'#fff8ef')
    text(720,328,'U3  S13V10F5',25,bold=True)
    text(720,356,'Pololu #4083 / 1178565',18)
    pin('U3','VIN',700,410,'VIN',side='left')
    pin('U3','VOUT',1000,410,'5V OUT')
    pin('U3','GND',850,450);text(850,433,'GND',20,anchor='middle',bold=True)
    wire('+9V',(400,410),(700,410));cap('C1',(500,410),(500,480))
    wire('+9V',(650,410),(650,280),(1360,280),(1360,1480),(1380,1480),(1380,1240),up['JP1:15'])
    wire('GND',(250,450),(250,480),(40,480))
    wire('GND',(850,450),(850,480),(250,480))
    wire('+5V',(1000,410),(1040,410),(1040,200))
    # USB host VBUS is isolated from the external LED rail.
    res('R50',(900,1220),(1000,1220))
    res('R51',(1000,1220),(1000,1340))
    wire('USB_VBUS',up['JP1:12'],(1300,1060),(1300,1180),(900,1180),(900,1220))
    wire('USB_SENSE',up['JP1:8'],(1120,820),(1120,1220),(1000,1220))
    wire('GND',(1000,1340),(1080,1340),(1080,2460))
    text(900,1150,'USB VBUS sense / 3.0V at 5V',19,color=m.BLUE)
    # Both pedal ports in one purchased dual-TRS housing.
    box(100,490,600,650,'#eef8f8')
    text(120,535,'J2  ACJS-MHDC / passive pedals',25,bold=True)
    text(120,570,'TOP / pedal 1',21,bold=True)
    for p,y,label in [('11',600,'11 RING'),('12',720,'12 TIP'),('5',900,'5 RING'),('6',1020,'6 TIP')]:pin('J2',p,700,y,label)
    for p,y in [('10',780),('4',1080)]:
        pin('J2',p,100,y,f'{p} SLEEVE',side='left');wire('GND',(100,y),(40,y))
    text(120,835,'BOTTOM / pedal 2',21,bold=True)
    text(120,1120,'1/2/3/7/8/9: NC; pad 13: mechanical / NC',18,color=m.MUTED)
    res('R20',(780,600),(700,600));res('R30',(780,900),(700,900))
    wire('P1_ADC',up['JP1:5'],(1200,640),(1200,720),(700,720))
    wire('P2_ADC',up['JP1:7'],(1160,760),(1160,1020),(700,1020))
    wire('P1_MODE',up['JP2:5'],(2480,1000),(2480,1580),(920,1580))
    res('R21',(920,1580),(800,1580));wire('P1_ADC',(800,1580),(800,720))
    wire('P2_MODE',up['JP2:6'],(2520,940),(2520,1660),(920,1660))
    res('R31',(920,1660),(820,1660));wire('P2_ADC',(820,1660),(820,1020))
    # Encoder pins align with the digital header neighborhood.
    box(2800,1200,500,400,'#f1f8f3')
    text(3050,1240,'SW11  ENCODER',25,anchor='middle',bold=True)
    for p,ref,y,ch in [('A','JP2:7',1280,2560),('B','JP2:8',1360,2600),('SW1','JP2:9',1440,2640)]:
        pin('SW11',p,2800,y,p,side='left');a=up[ref]
        wire(m.COMPONENTS['SW11']['pins'][p],a,(ch,a[1]),(ch,y),(2800,y))
    for p,y in [('C',1500),('SW2',1560)]:
        pin('SW11',p,3300,y,p);wire('GND',(3300,y),(3750,y))
    text(2840,1320,'20 detents + click',20)
    text(2840,1400,'Internal pull-ups',19)
    text(2840,1480,'No external R/C',19)
    # All ladder taps are below the component bodies, clear of the LED rails.
    text(1600,2070,'MODULAR FOOTSWITCH LADDER',25,bold=True,color=m.AMBER)
    res('R7',(1100,2140),(1250,2140))
    wire('LADDER',up['JP1:4'],(1440,580),(1440,2080),(1250,2080),(1250,2140))
    res('R8',(1250,2140),(1250,2350));wire('GND',(1250,2350),(1250,2460))
    wire('LADDER',(1250,2140),(1350,2140));cap('C5',(1350,2140),(1350,2350));wire('GND',(1350,2350),(1350,2460))
    previous=(1350,2140)
    for i in range(1,11):
        node=(1450+200*(i-1),2140)
        res(f'R{8+i}',(previous[0],2140),node)
        ref=f'SW{i}';x=node[0]
        pin(ref,'1',x,2175);pin(ref,'2',x,2320)
        wire(f'T{i}',node,(x,2175),(x,2210))
        s.circle(x,2210,4,fill=False);s.circle(x,2260,4,fill=False);s.line(x,2260,x-22,2217)
        wire('GND',(x,2260),(x,2320),(x,2460))
        text(x+18,2232,ref,20);text(x+18,2270,m.TAPS[i-1][0],25,bold=True)
        text(x,2410,f'T{i} / LED{i}',18,anchor='middle')
        previous=node
    # The LED lead order follows the actual Pololu side view.
    text(100,1298,'Pololu 2535 / optional LEDs',25,bold=True,color=m.PURPLE)
    for i in range(1,11):
        y=1342+(i-1)*110
        box(100,y,230,100,'#f9f5fd')
        text(114,y+34,f'LED{i} / {m.TAPS[i-1][0]}',22,bold=True);text(114,y+65,'2535',18)
        s.line(100,y+100,330,y+100,m.PURPLE,3)
        for p,dy,label in [('DIN',18,'DIN'),('+5V',42,'5V'),('GND',66,'GND'),('DOUT',90,'DOUT')]:pin(f'LED{i}',p,330,y+dy,label)
        wire('+5V',(330,y+42),(500,y+42));wire('GND',(330,y+66),(600,y+66))
        if i<10:wire(f'L{i}',(330,y+90),(380,y+90),(380,y+128),(330,y+128))
        else:
            s.line(330,y+90,380,y+90,m.PURPLE)
            s.line(375,y+85,385,y+95,m.PURPLE);s.line(375,y+95,385,y+85,m.PURPLE)
            text(392,y+96,'NC',19,color=m.PURPLE)
    wire('LED_GPIO',up['JP2:10'],(2440,700),(2440,1400),(720,1400),(720,1360),(330,1360))
    # The generated wire model must cover every connected netlist terminal and
    # must form exactly one continuous external wire network for each net.
    expected={f'{r}.{p}':n for r,c in m.COMPONENTS.items() for p,n in c['pins'].items() if n is not None}
    assert {k:v['net'] for k,v in terminals.items() if v['net'] is not None}==expected
    def on(p,a,b):return min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1]) and (a[0]==b[0]==p[0] or a[1]==b[1]==p[1])
    def intersect(a,b,c,d):
        ah=a[1]==b[1];ch=c[1]==d[1]
        if ah==ch:
            return next((p for p in (a,b,c,d) if on(p,a,b) and on(p,c,d)),None)
        p=(c[0],a[1]) if ah else (a[0],c[1])
        return p if on(p,a,b) and on(p,c,d) else None
    bynet=defaultdict(list)
    for i,(n,a,b) in enumerate(wires):bynet[n].append(i)
    dots=set();hops=set()
    for n,ids in bynet.items():
        seen={ids[0]};pending=set(ids[1:])
        while pending:
            found={j for j in pending if any(intersect(*wires[i][1:],*wires[j][1:]) is not None for i in seen)}
            assert found,('Disconnected wire network',n,[wires[i] for i in pending])
            seen.update(found);pending-=found
        for k,t in terminals.items():
            if t['net']==n:assert any(on(t['xy'],*wires[i][1:]) for i in ids),('Unwired pin',k)
    for i,(n,a,b) in enumerate(wires):
        for x,y,x2,y2 in bodies:
            # A wire may meet a component boundary, but not pass through a body.
            assert not (a[1]==b[1] and y<a[1]<y2 and max(min(a[0],b[0]),x)<min(max(a[0],b[0]),x2)),('Wire through body',n,a,b,(x,y,x2,y2))
            assert not (a[0]==b[0] and x<a[0]<x2 and max(min(a[1],b[1]),y)<min(max(a[1],b[1]),y2)),('Wire through body',n,a,b,(x,y,x2,y2))
        for j in range(i):
            other,c,d=wires[j];p=intersect(a,b,c,d)
            if p is None:continue
            if n==other:
                if p in (a,b,c,d):dots.add((n,p))
            else:
                assert (a[0]==b[0]) != (c[0]==d[0]),('Different nets overlap',n,other,a,b,c,d)
                assert p not in (a,b) and p not in (c,d),('Different nets meet at endpoint',n,other,p)
                hops.add((n if a[1]==b[1] else other,p))
    # Render wires first, then crossing bridges, junction dots, terminal labels.
    for n,a,b in wires:s.line(*a,*b,color(n),3 if n in ['GND','+5V','3V3'] else 2.1)
    for n,(x,y) in sorted(hops):
        s.line(x-7,y,x+7,y,'white',9)
        s.path([(x-7,y),(x-5,y-6),(x,y-8),(x+5,y-6),(x+7,y)],color(n),2.3)
    for n,p in sorted(dots):
        directions=set()
        for net,a,b in wires:
            if net==n and on(p,a,b):
                for q in (a,b):
                    if q!=p:directions.add(((q[0]>p[0])-(q[0]<p[0]),(q[1]>p[1])-(q[1]<p[1])))
        if len(directions)>=3:s.circle(*p,4,color(n))
    for k,t in terminals.items():
        if t['net'] is not None:s.circle(*t['xy'],3.7,color(t['net']),False)
    for x,y,t,size,kw in labels:s.text(x,y,t,size,**kw)
    s.text(42,64,'SIGMIDI FOOT CONTROLLER',36,bold=True)
    s.text(42,104,'v0.1  /  UNIFIED ELECTRICAL SCHEMATIC  /  external board pins only',22)
    s.text(42,142,'Continuous wires connect every fitted terminal. Dots = junctions; arched crossings = no connection. Component placement is schematic.',19,color=m.MUTED)
    s.text(42,178,'Nano and LCD pins keep physical order. Nano: JP1 left 1-15, JP2 right 15-1, USB-C up. Outlines are schematic.',20,color=m.MUTED)
    s.line(42,2490,3750,2490,m.GRID)
    s.text(60,2520,'PASSIVE PEDALS',22,bold=True)
    s.lines(60,2550,['Pot: outer legs RING / SLEEVE; wiper TIP.', 'Variable resistor: TIP to SLEEVE; RING unused.', '0-10k per input. Bias HIGH in resistor mode;', 'high impedance in pot / disabled / boot states.'],17,step=22)
    s.text(1100,2520,'ASSEMBLY',22,bold=True)
    s.lines(1100,2550,['Set 4 / 6 / 8 / 10 switches; calibrate installed taps.', 'SW11 contact pin arrangement is functional.', 'Native USB-C carries USB MIDI and ROM flashing.', 'USB-only supply does not power the external LED rail.'],17,step=22)
    s.text(2240,2520,'LED PACKAGE',22,bold=True)
    s.lines(2240,2550,['Lens left, leads right, flat side down.', 'Top to bottom: DIN / 5V / GND / DOUT.', 'Only LEDs and wires; direct D7 / GPIO10 data.', 'Check 3.3V data acceptance on the actual LED batch.'],17,step=22)
    s.text(60,2650,f'Netlist, BOM and pin references: design/electrical/. All {len(m.COMPONENTS)} components and {len(bynet)} nets checked against the connected drawing.',18,color=m.MUTED)
    s.svg.append('</svg>');content='\n'.join(s.svg)
    m.C.showPage();m.C.save()
    (m.OUT/'single-page.svg').write_text(content)
    (m.OUT/'single-page-wiring.json').write_text(json.dumps({'description':'Connected wire geometry validated against netlist.json','units':'schematic coordinates','components':len(m.COMPONENTS),'nets':len(bynet),'terminals':terminals,'wires':[{'net':n,'a':a,'b':b} for n,a,b in wires],'crossing_bridges':len(hops),'nano_pin_layout':'Component-side top view: JP1 left 1-15, JP2 right 15-1, USB-C up; 60-unit pitch, aligned rows; all 30 header pads and printed labels preserved','lcd_pin_layout':'External P2 pins 1-8 in physical connector order: BL, RST, D/C, CS, SCL/CLK, SDA/DIN, GND, VCC','pedal_socket_layout':'One ACJS-MHDC dual-TRS housing; pedal 1 above pedal 2 inside one J2 outline','nano_connected_pin_label_pt':21,'nano_header_gpio_label_pt':18,'validation':'All connected terminals present; each net continuous; no body crossings or overlapping different-net segments.'},indent=2)+'\n')
    (m.PREVIEW.parent/'electrical-single-page.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SIGMIDI v0.1 - unified electrical schematic</title><style>
*{box-sizing:border-box}body{margin:0;background:#eaf0f4;color:#183044;font:15px system-ui,sans-serif}header{padding:20px 28px;background:#183044;color:white;display:flex;justify-content:space-between;gap:20px}h1{font-size:22px;margin:0 0 7px}p{margin:0;color:#c5d4df}a{color:inherit}main{padding:22px;overflow:auto}svg{display:block;width:100%;min-width:2400px;height:auto;background:white;box-shadow:0 3px 22px #18304419}button{padding:8px 12px;margin:8px 6px 0 0;border:0;border-radius:5px;cursor:pointer}@media print{header{display:none}main{padding:0}svg{min-width:0;width:100%;box-shadow:none}@page{size:A0 landscape;margin:0}}
</style><header><div><h1>SIGMIDI Foot Controller / unified electrical schematic</h1><p>v0.1 - continuous wires from one Arduino Nano ESP32 to all components. Zoom or scroll for detail.</p><button id="fit">Fit width</button><button id="detail">Enlarge</button></div><a href="electrical-diagram.html">Detailed sheets</a></header><main>'''+content+'''</main><script>document.querySelector('#fit').onclick=()=>document.querySelector('svg').style.minWidth='0';document.querySelector('#detail').onclick=()=>document.querySelector('svg').style.minWidth='3800px';</script></html>''')
    m.W,m.H,m.C=old
