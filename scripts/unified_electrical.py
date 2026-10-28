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
    # Physical DFR1075 top view: P2 left (18 pads), P1 right (14 pads),
    # with P1 starting four pad pitches lower. Never reorder these terminals.
    box(1500,300,900,1250,'#f6f8fa')
    s.rect(1835,274,230,44,fill='white',stroke=m.INK)
    text(1950,305,'USB-C',22,anchor='middle',bold=True)
    text(1950,355,'U1  DFRobot DFR1075',29,anchor='middle',bold=True)
    text(1950,387,'Physical top view / USB-C up',19,anchor='middle',color=m.MUTED)
    up={};data=m.external_pin_data()
    for header,count,right in [('P2',18,False),('P1',14,True)]:
        x=2400 if right else 1500
        for n in range(1,count+1):
            ref=f'{header}:{n}';y=400+60*(n-1+(4 if right else 0))
            up[ref]=(x,y);pin('U1',ref,x,y)
            pad=data[ref];tx=x-25 if right else x+25;anchor='end' if right else 'start'
            subtitle=ref+(f' / {pad["logical_name"]}' if pad['net'] else '')
            text(tx,y-18,subtitle,18,anchor=anchor,color=color(pad['net']) if pad['net'] else m.MUTED)
            text(tx,y+8,pad['physical_label'],21,anchor=anchor,bold=True)
    assert [up[f'P2:{n}'][1] for n in range(1,19)]==list(range(400,1421,60))
    assert [up[f'P1:{n}'][1] for n in range(1,15)]==list(range(640,1421,60))
    assert up['P1:1'][1]-up['P2:1'][1]==4*60
    text(1950,1485,'All printed labels retained; unused pads left unwired.',18,anchor='middle',color=m.MUTED)
    # Power and return rails skirt the outside of the surrounding components.
    wire('3V3',(60,250),(3400,250))
    wire('3V3',(60,250),(60,1270),(760,1270),(760,1160),(700,1160))
    wire('3V3',up['P2:2'],(1100,460),(1100,250))
    wire('3V3',up['P1:2'],(2620,700),(2620,250))
    wire('3V3',(60,1270),(60,2445),(1100,2445),(1100,2140))
    wire('+5V',(80,200),(3700,200),(3700,410))
    wire('+5V',up['P1:1'],(2500,640),(2500,200))
    wire('+5V',(80,200),(80,1325),(500,1325),(500,2430))
    wire('GND',(40,330),(40,2460),(3750,2460),(3750,540),(2680,540))
    wire('GND',up['P2:4'],(1000,580),(1000,330),(40,330))
    wire('GND',up['P1:3'],(2680,760),(2680,540))
    wire('GND',(40,1315),(600,1315),(600,2460))
    text(1120,228,'3V3 / U1 logic supply',22,bold=True,color=color('3V3'))
    text(3716,228,'+5V',23,bold=True,color=m.RED)
    text(3710,2435,'COMMON GND',21,anchor='end',bold=True)
    # Preserve the display's physical eight-pin external connector order.
    box(100,490,600,750,'#edf4fc')
    text(125,535,'U2  Waveshare 24382',28,bold=True)
    text(125,569,'External P2 / GH1.25 / SPI',20)
    text(125,647,'Pin 1 at top / pin 8 at bottom',19,color=m.MUTED)
    lcd={n:600+(n-1)*80 for n in range(1,9)}
    for n,y in lcd.items():pin('U2',f'P2:{n}',700,y,f'{n}  {m.LCD[n-1][1]}')
    assert [lcd[n] for n in range(1,9)]==list(range(600,1161,80))
    wire('3V3',(1100,460),(900,460),(900,600),(700,600))
    wire('GND',(700,1080),(740,1080),(740,1315),(600,1315))
    for n,ref,ch in [(5,'P2:6',1080),(6,'P2:7',1200),
                     (3,'P2:10',1160),(4,'P2:12',1120),(2,'P2:15',1240)]:
        a=up[ref];y=lcd[n]
        wire(m.COMPONENTS['U2']['pins'][f'P2:{n}'],a,(ch,a[1]),(ch,y),(700,y))
    text(125,1211,'Pins 1-8 in connector order',20,color=m.BLUE)
    # Power entry stays entirely to the upper right of the controller.
    box(2800,290,300,190,'#fff8ef')
    text(2820,328,'J1  5.5 x 2.1mm',23,bold=True)
    pin('J1','CENTER',2950,480);text(2950,463,'CENTER (-)',21,anchor='middle',bold=True)
    pin('J1','SLEEVE',3100,410,'SLEEVE (+)')
    text(2815,365,'9V DC / center-negative',19)
    box(3300,290,350,190,'#fff8ef')
    text(3320,328,'U3  S13V10F5',25,bold=True)
    text(3320,356,'Pololu #4083 / 1178565',18)
    pin('U3','VIN',3300,410,'VIN',side='left')
    pin('U3','VOUT',3650,410,'5V OUT')
    pin('U3','GND',3480,480);text(3480,463,'GND',20,anchor='middle',bold=True)
    wire('+9V',(3100,410),(3300,410));cap('C1',(3160,410),(3160,540))
    wire('GND',(2950,480),(2950,540))
    wire('GND',(3480,480),(3480,540))
    wire('+5V',(3650,410),(3700,410))
    # The two pedal ports share one purchased socket housing and one outline.
    box(3300,760,360,1080,'#eef8f8')
    text(3480,812,'J2  ACJS-MHDC',26,anchor='middle',bold=True)
    text(3480,855,'Dual TRS socket',21,anchor='middle')
    text(3480,899,'TOP / pedal 1',23,anchor='middle',bold=True)
    pin('J2','11',3300,940,'11  RING',side='left')
    pin('J2','12',3300,1120,'12  TIP',side='left')
    pin('J2','10',3660,1180,'10  SLEEVE')
    text(3320,1222,'7/8/9: NC',18,color=m.MUTED)
    s.line(3320,1270,3640,1270,m.GRID)
    text(3480,1332,'BOTTOM / pedal 2',23,anchor='middle',bold=True)
    pin('J2','5',3300,1420,'5  RING',side='left')
    pin('J2','6',3300,1660,'6  TIP',side='left')
    pin('J2','4',3660,1740,'4  SLEEVE')
    text(3320,1788,'1/2/3: NC',18,color=m.MUTED)
    text(3320,1818,'Pad 13: mechanical / NC',18,color=m.MUTED)
    # Reference resistors are beside the socket; the reference trunk stays
    # outside the controller-to-encoder signal corridor.
    wire('3V3',(2740,250),(2740,600),(3220,600),(3220,1420))
    res('R20',(3220,940),(3300,940))
    res('R30',(3220,1420),(3300,1420))
    wire('P1_MODE',up['P1:4'],(2700,820));res('R21',(2700,820),(2800,820))
    wire('P1_ADC',(2800,820),(2860,820),(2860,1120),(3300,1120))
    wire('P1_ADC',up['P1:9'],(3300,1120))
    # GPIO21 follows the open corridor below both boards and the socket. Its
    # resistor is below J2, so the route avoids the power entry above the MCU.
    wire('P2_MODE',up['P2:8'],(1420,820),(1420,1980),(3120,1980))
    res('R31',(3120,1980),(3240,1980))
    wire('P2_ADC',(3240,1980),(3280,1980),(3280,1660),(3300,1660))
    wire('P2_ADC',up['P1:8'],(3180,1060),(3180,1660),(3300,1660))
    wire('GND',(3660,1180),(3750,1180))
    wire('GND',(3660,1740),(3750,1740))
    # Move the encoder beside its two physical A/B pins for straight wires.
    box(2700,1220,420,300,'#f1f8f3')
    text(2910,1261,'SW11  ENCODER',25,anchor='middle',bold=True)
    for p,ref,y in [('A','P1:12',1300),('B','P1:13',1360)]:
        pin('SW11',p,2700,y,p,side='left')
        wire(m.COMPONENTS['SW11']['pins'][p],up[ref],(2700,y))
    pin('SW11','SW1',2900,1520)
    text(2900,1504,'SW1 / click',21,anchor='middle',bold=True)
    wire('ENC_SW',up['P2:18'],(1460,1420),(1460,1580),(2900,1580),(2900,1520))
    for p,x in [('C',3040),('SW2',3090)]:
        pin('SW11',p,x,1520);text(x,1504,p,21,anchor='middle',bold=True)
        wire('GND',(x,1520),(x,1560),(3160,1560))
    wire('GND',(3160,1560),(3160,1880),(3750,1880))
    text(2750,1328,'20 detents',21)
    text(2750,1400,'Internal pull-ups',19)
    text(2750,1436,'No external R/C',19)
    # All ladder taps are below the component bodies, clear of the LED rails.
    text(1600,2070,'MODULAR FOOTSWITCH LADDER',25,bold=True,color=m.AMBER)
    res('R7',(1100,2140),(1250,2140))
    wire('LADDER',up['P2:13'],(1320,1120),(1320,2080),(1250,2080),(1250,2140))
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
    # Put the LED chain below the display, beside the real GPIO16/TX pad.
    text(800,1320,'Pololu 2535 / optional LEDs',25,bold=True,color=m.PURPLE)
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
    wire('LED_GPIO',up['P2:17'],(330,1360))
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
    s.text(42,178,'DFRobot and display pins keep physical order. DFRobot: P2 left, P1 right, USB-C up. Outlines and distances are schematic.',20,color=m.MUTED)
    s.line(42,2490,3750,2490,m.GRID)
    s.text(60,2520,'PASSIVE PEDALS',22,bold=True)
    s.lines(60,2550,['Pot: outer legs RING / SLEEVE; wiper TIP.', 'Variable resistor: TIP to SLEEVE; RING unused.', '0-10k per input. Bias HIGH in resistor mode;', 'high impedance in pot / disabled / boot states.'],17,step=22)
    s.text(1100,2520,'ASSEMBLY',22,bold=True)
    s.lines(1100,2550,['Set 4 / 6 / 8 / 10 switches; calibrate installed taps.', 'SW11 contact pin arrangement is functional.', 'U1 printed MO / MI mean MOSI / MISO.', 'USB-only supply does not power the external LED rail.'],17,step=22)
    s.text(2240,2520,'LED PACKAGE',22,bold=True)
    s.lines(2240,2550,['Lens left, leads right, flat side down.', 'Top to bottom: DIN / 5V / GND / DOUT.', 'Only LEDs and wires; direct GPIO16 data.', 'Check 3.3V data acceptance on the actual LED batch.'],17,step=22)
    s.text(60,2650,'Netlist, BOM and pin references: design/electrical/. All 44 components and 39 nets are checked against the connected wire drawing.',18,color=m.MUTED)
    s.svg.append('</svg>');content='\n'.join(s.svg)
    m.C.showPage();m.C.save()
    (m.OUT/'single-page.svg').write_text(content)
    (m.OUT/'single-page-wiring.json').write_text(json.dumps({'description':'Connected wire geometry validated against netlist.json','units':'schematic coordinates','components':len(m.COMPONENTS),'nets':len(bynet),'terminals':terminals,'wires':[{'net':n,'a':a,'b':b} for n,a,b in wires],'crossing_bridges':len(hops),'dfrobot_pin_layout':'Physical top view: P2 left, P1 right, USB-C up; 60-unit pitch and four-pitch P1 offset; all 32 pad positions and printed labels preserved','lcd_pin_layout':'External P2 pins 1-8 in physical connector order: BL, RST, D/C, CS, SCL/CLK, SDA/DIN, GND, VCC','pedal_socket_layout':'One ACJS-MHDC dual-TRS housing; pedal 1 above pedal 2 inside one J2 outline','dfrobot_connected_pin_label_pt':21,'dfrobot_header_gpio_label_pt':18,'validation':'All connected terminals present; each net continuous; no body crossings or overlapping different-net segments.'},indent=2)+'\n')
    (m.PREVIEW.parent/'electrical-single-page.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SIGMIDI v0.1 - unified electrical schematic</title><style>
*{box-sizing:border-box}body{margin:0;background:#eaf0f4;color:#183044;font:15px system-ui,sans-serif}header{padding:20px 28px;background:#183044;color:white;display:flex;justify-content:space-between;gap:20px}h1{font-size:22px;margin:0 0 7px}p{margin:0;color:#c5d4df}a{color:inherit}main{padding:22px;overflow:auto}svg{display:block;width:100%;min-width:2400px;height:auto;background:white;box-shadow:0 3px 22px #18304419}button{padding:8px 12px;margin:8px 6px 0 0;border:0;border-radius:5px;cursor:pointer}@media print{header{display:none}main{padding:0}svg{min-width:0;width:100%;box-shadow:none}@page{size:A0 landscape;margin:0}}
</style><header><div><h1>SIGMIDI Foot Controller / unified electrical schematic</h1><p>v0.1 - continuous wires from one DFRobot board to all components. Zoom or scroll for detail.</p><button id="fit">Fit width</button><button id="detail">Enlarge</button></div><a href="electrical-diagram.html">Detailed sheets</a></header><main>'''+content+'''</main><script>document.querySelector('#fit').onclick=()=>document.querySelector('svg').style.minWidth='0';document.querySelector('#detail').onclick=()=>document.querySelector('svg').style.minWidth='3800px';</script></html>''')
    m.W,m.H,m.C=old
