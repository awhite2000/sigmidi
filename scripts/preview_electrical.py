#!/usr/bin/env python3
"""Generate the SIGMIDI electrical review set (vector PDF, SVG, HTML and netlist).

No firmware, distribution bundle, native CAD or Git state is changed.
Run with the bundled Python runtime (ReportLab is required).
"""
from pathlib import Path
import csv
import base64
import html
import json
import math
import re
import hashlib
from collections import defaultdict
from reportlab.pdfgen import canvas
from reportlab.lib.colors import toColor as HexColor
from reportlab.lib.pagesizes import A0, A3, landscape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'design/electrical'
PDF = ROOT / 'output/pdf/sigmidi-electrical-diagram.pdf'
PREVIEW = ROOT / 'previews/electrical-diagram.html'
W, H = 1400, 990
INK = '#183044'
MUTED = '#526575'
GRID = '#d6e0e6'
BLUE = '#2164b4'
RED = '#ba344b'
ORANGE = '#a35b12'
PURPLE = '#8650aa'
TEAL = '#087e89'
GREEN = '#25734a'
AMBER = '#986300'
COLORS = {'+9V': ORANGE, '+5V': RED, '3V3': RED, 'GND': INK,
          'LADDER': AMBER, 'ENC_A': GREEN, 'ENC_B': GREEN, 'ENC_SW': GREEN,
          'LED_GPIO': PURPLE}
COMPONENTS = {}
NOTES = []
PAGES = []


def component(ref, value, pins, package='', note=''):
    assert ref not in COMPONENTS, ref
    COMPONENTS[ref] = {'value': value, 'package': package, 'pins': pins, 'note': note}


class Sheet:
    def __init__(self, title, subtitle, number):
        self.heading, self.number = title, number
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(title)}">']
        self.rect(0, 0, W, H, fill='white', stroke='none')
        self.text(42, 42, 'SIGMIDI', 25, bold=True)
        self.text(195, 41, 'FOOT CONTROLLER  /  v0.1', 13, color=MUTED)
        self.text(42, 78, title, 24, bold=True)
        self.text(42, 104, subtitle, 13, color=MUTED)
        self.line(42, 119, 1358, 119, GRID)
        self.line(42, 937, 1358, 937, GRID)
        self.text(42, 961, 'ELECTRICAL REVIEW  |  Prototype circuit; verify on hardware before final assembly.', 11, color=MUTED)
        self.text(1358, 961, f'{number} / 7  |  30 OCT 2026', 11, color=MUTED, anchor='end')

    def line(self, x1, y1, x2, y2, color=INK, width=1.8, dash=False):
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="6 5"' if dash else '')+'/>')
        C.setStrokeColor(HexColor(color)); C.setLineWidth(width)
        C.setDash([6, 5] if dash else [])
        C.line(x1, H-y1, x2, H-y2); C.setDash([])

    def path(self, points, color=INK, width=1.8, fill='none', closed=False):
        tag = 'polygon' if closed else 'polyline'
        pts = ' '.join(f'{x},{y}' for x,y in points)
        self.svg.append(f'<{tag} points="{pts}" fill="{fill}" stroke="{color}" stroke-width="{width}"/>')
        p = C.beginPath(); p.moveTo(points[0][0], H-points[0][1])
        for x,y in points[1:]: p.lineTo(x, H-y)
        if closed: p.close()
        C.setStrokeColor(HexColor(color)); C.setLineWidth(width)
        if fill != 'none': C.setFillColor(HexColor(fill))
        C.drawPath(p, stroke=1, fill=int(fill != 'none'))

    def rect(self, x, y, w, h, fill='none', stroke=GRID):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}"/>')
        if fill != 'none': C.setFillColor(HexColor(fill))
        if stroke != 'none': C.setStrokeColor(HexColor(stroke))
        C.setLineWidth(1)
        C.rect(x, H-y-h, w, h, stroke=int(stroke != 'none'), fill=int(fill != 'none'))

    def circle(self, x, y, r=3, color=INK, fill=True):
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" stroke="{color}" fill="{color if fill else "white"}"/>')
        C.setStrokeColor(HexColor(color)); C.setFillColor(HexColor(color if fill else 'white'))
        C.circle(x, H-y, r, stroke=1, fill=1)

    def text(self, x, y, text, size=14, color=INK, bold=False, anchor='start'):
        assert '\n' not in text
        self.svg.append(f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}" text-anchor="{anchor}">{html.escape(str(text))}</text>')
        C.setFillColor(HexColor(color)); C.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        {'start': C.drawString, 'middle': C.drawCentredString, 'end': C.drawRightString}[anchor](x, H-y, str(text))

    def lines(self, x, y, texts, size=14, color=INK, step=23):
        for i,t in enumerate(texts): self.text(x, y+i*step, t, size, color)

    def title(self, x, y, text): self.text(x, y, text, 17, bold=True)

    def net(self, x, y, name, side='right', color=None):
        color = color or COLORS.get(name, TEAL if name.startswith('P') else BLUE)
        self.circle(x, y, 2.6, color)
        self.text(x+(8 if side=='right' else -8), y-5, name, 12, color, bold=True, anchor='start' if side=='right' else 'end')

    def gnd(self, x, y):
        self.line(x,y,x,y+9)
        for dy, half in [(9,10),(14,6),(19,2)]: self.line(x-half,y+dy,x+half,y+dy)

    def resistor(self, x1,y1,x2,y2,ref,value,net1=None,net2=None, labelside=1):
        vert = x1==x2
        cx,cy=(x1+x2)/2,(y1+y2)/2
        if vert:
            self.line(x1,y1,cx,cy-19); self.line(cx,cy+19,x2,y2)
            self.rect(cx-7,cy-19,14,38,fill='white',stroke=INK)
            self.text(cx+13*labelside,cy-5,ref,11,anchor='start' if labelside==1 else 'end')
            self.text(cx+13*labelside,cy+11,value,12,anchor='start' if labelside==1 else 'end')
        else:
            self.line(x1,y1,cx-20,cy); self.line(cx+20,cy,x2,y2)
            self.rect(cx-20,cy-7,40,14,fill='white',stroke=INK)
            self.text(cx,cy-27,ref,11,anchor='middle'); self.text(cx,cy-12,value,12,anchor='middle')
        if net1 is not None: component(ref,value,{'1':net1,'2':net2},'1% resistor')

    def cap(self,x,y,ref,value,net,other='GND',height=75):
        self.line(x,y,x,y+24); self.line(x-11,y+24,x+11,y+24)
        self.line(x-11,y+31,x+11,y+31); self.line(x,y+31,x,y+height)
        self.text(x+17,y+26,ref,11);self.text(x+17,y+43,value,12)
        if 'uF /' in value:self.text(x-20,y+22,'+',12,bold=True)
        if other=='GND': self.gnd(x,y+height)
        else: self.net(x,y+height,other)
        component(ref,value,{'1':net,'2':other},'capacitor')

    def switch(self,x,y,ref,net,label):
        self.line(x,y,x,y+23); self.circle(x,y+23,3,fill=False)
        self.circle(x,y+59,3,fill=False);self.line(x,y+59,x-17,y+29)
        self.line(x,y+62,x,y+83);self.gnd(x,y+83)
        self.text(x+15,y+48,ref,11);self.text(x+15,y+66,label,13,bold=True)
        component(ref,'momentary NO',{'1':net,'2':'GND'},'12mm footswitch',label)

    def table(self,x,y,width,headers,rows,widths=None,rowh=29,size=12):
        widths = widths or [width/len(headers)]*len(headers)
        self.rect(x,y,width,rowh,fill='#e9f0f5')
        for ri,row in enumerate([headers]+list(rows)):
            yy=y+ri*rowh
            if ri and ri%2==0:self.rect(x,yy,width,rowh,fill='#f6f8fa',stroke='none')
            xx=x
            for ci,cell in enumerate(row):
                self.text(xx+9,yy+rowh*.68,str(cell),size,bold=ri==0)
                xx+=widths[ci]
            self.line(x,yy+rowh,x+width,yy+rowh,GRID,.6)

    def end(self):
        self.svg.append('</svg>')
        name=f'{self.number:02d}-'+['controller-display','power-encoder','modular-ladder','pedal-1','pedal-2','optional-leds','assembly-reference'][self.number-1]+'.svg'
        content='\n'.join(self.svg)
        (OUT/name).write_text(content)
        PAGES.append({'title':self.heading,'file':name,'svg':content})
        C.showPage()
        if self.number < 7:C.scale(SCALE,SCALE)


# Accepted map: Arduino ABX00083 V0.3 schematic header pad IDs and official
# component-side top-view pinout. JP2 numbers DESCEND from USB towards VIN.
P1 = [(1,'GPIO48','NC'),(2,'3V3','3V3'),(3,'GPIO46','NC'),(4,'GPIO1','LADDER'),(5,'GPIO2','P1_ADC'),(6,'GPIO3','NC'),(7,'GPIO4','P2_ADC'),(8,'GPIO11','USB_SENSE'),(9,'GPIO12','NC'),(10,'GPIO13','NC'),(11,'GPIO14','NC'),(12,'VBUS','USB_VBUS'),(13,'GPIO0','NC'),(14,'GND','GND'),(15,'VIN','+9V')]
P2 = [(15,'GPIO47','LCD_RST'),(14,'GPIO38','LCD_DIN'),(13,'GPIO21','LCD_CS'),(12,'GPIO18','LCD_DC'),(11,'GPIO17','LCD_CLK'),(10,'GPIO10','LED_GPIO'),(9,'GPIO9','ENC_SW'),(8,'GPIO8','ENC_B'),(7,'GPIO7','ENC_A'),(6,'GPIO6','P2_MODE'),(5,'GPIO5','P1_MODE'),(4,'GND','GND'),(3,'RST','NC'),(2,'GPIO44','NC'),(1,'GPIO43','NC')]
HEADERS = [('JP1',P1,False),('JP2',P2,True)]
PHYSICAL = {
    'JP1': ['D13','3V3','B0','A0','A1','A2','A3','A4','A5','A6','A7','VBUS / VUSB','B1','GND','VIN'],
    'JP2': ['D1 / TX0','D0 / RX0','RST','GND','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12'],
}
GPIO_ALIASES = {1:'A0',2:'A1',4:'A3',5:'D2',6:'D3',7:'D4',8:'D5',9:'D6',10:'D7',11:'A4',17:'D8',18:'D9',21:'D10',38:'D11',47:'D12'}


def logical_name(signal):
    name=signal.split(' / ')[0]
    return 'GPIO'+name[2:] if name.startswith('IO') else name


def external_pin_data():
    return {f'{h}:{n}': {'physical_label': PHYSICAL[h][n-1], 'logical_name': logical_name(signal), 'net': None if net.startswith('NC') else net}
            for h,rows,_ in HEADERS for n,signal,net in rows}


def gpio_label(gpio,ref):
    return f'{GPIO_ALIASES[gpio]} / GPIO{gpio} ({ref})'

LCD = [(1,'BL','3V3'),(2,'RST','LCD_RST'),(3,'D/C','LCD_DC'),(4,'CS','LCD_CS'),(5,'SCL / CLK','LCD_CLK'),(6,'SDA / DIN','LCD_DIN'),(7,'GND','GND'),(8,'VCC','3V3')]
TAPS = [('B',1),('A',2),('2',3),('1',4),('C',5),('3',6),('D',7),('4',8),('E',9),('5',10)]
SOURCES = [
 ('Arduino Nano ESP32 ABX00083 pinout', 'Component-side top view, USB-C up; all 30 header pads', 'https://docs.arduino.cc/resources/pinouts/ABX00083-full-pinout.pdf'),
 ('Arduino Nano ESP32 schematic V0.3', 'JP1: 1-15 top-down; JP2: 15-1 top-down', 'https://docs.arduino.cc/resources/schematics/ABX00083-schematics.pdf'),
 ('Waveshare 24382 external P2 connector', 'Local: design/fusion/datasheets/waveshare-24382-schematic.pdf', 'https://www.waveshare.com/wiki/1.69inch_LCD_Module'),
 ('Amphenol ACJS-MHDC socket drawing', 'Local: design/fusion/datasheets/double-trs-ACJS-MHDC.pdf', ''),
 ('Pololu S13V10F5 / #4083', '5V, 1A step-up/down regulator; retailer item 1178565', 'https://www.pololu.com/product/4083'),
 ('Pololu #2535', '5mm addressable RGB LED / WS2811 / 5V / 800kHz', 'https://www.pololu.com/product/2535'),
 ('Espressif self-powered USB devices', 'VBUS sense: 100k / 150k divider to A4 / GPIO11', 'https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html'),
]


def controller():
    s=Sheet('Controller and display - external pins','Arduino Nano ESP32 / ABX00083. Purchased boards stop at external pins; logical GPIO names accompany used board labels.',1)
    component('U1','Arduino Nano ESP32 ABX00083',{f'{h}:{n}':None if net.startswith('NC') else net for h,rows,_ in HEADERS for n,_,net in rows},'ESP32-S3 board')
    component('U2','Waveshare 24382',{f'P2:{n}':net for n,_,net in LCD},'1.69 inch ST7789V2 LCD module')
    s.title(42,154,'U1  Arduino Nano ESP32')
    s.text(42,180,'Component-side top view, USB-C up. All printed labels retained; unused outside callouts omitted.',12,color=MUTED)
    s.rect(300,211,270,595,fill='#f6f8fa',stroke=INK)
    s.rect(386,198,98,31,fill='white',stroke=INK)
    s.text(435,219,'USB-C',12,anchor='middle',bold=True)
    s.text(435,252,'NANO ESP32',15,anchor='middle',bold=True)
    for header,rows,right in HEADERS:
        for i,(n,signal,net) in enumerate(rows):
            y=280+i*34; x=558 if right else 312;end=595 if right else 275
            nc=net.startswith('NC');color=MUTED if nc else COLORS.get(net,TEAL if net.startswith('P') else BLUE)
            if not nc:s.line(x,y,end,y,color,1.5)
            s.circle(x,y,4,color,fill=False)
            s.text(543 if right else 327,y+4,PHYSICAL[header][n-1],10.5,anchor='end' if right else 'start',bold=True)
            if not nc:s.text(603 if right else 267,y+4,f'{header}:{n} | {logical_name(signal)} | {net}',10.5,color=color,anchor='start' if right else 'end')
    s.title(940,154,'U2  Waveshare 24382')
    s.text(940,180,'P2 - 8-pin GH1.25 connector',14)
    dest={'3V3':'3V3','GND':'GND','LCD_RST':'D12 / GPIO47','LCD_DC':'D9 / GPIO18','LCD_CS':'D10 / GPIO21','LCD_CLK':'D8 / GPIO17','LCD_DIN':'D11 / GPIO38'}
    s.table(940,202,418,['Pin','LCD label','Nano label / GPIO'],[(n,l,dest[net]) for n,l,net in LCD],[38,122,258],rowh=34,size=12)
    s.rect(940,503,418,133,fill='#edf4fc')
    s.lines(956,529,['SCL and SDA are SPI signals here.', 'No MISO connection is required.', 'BL ties to VCC (3V3) for always-on backlight.', 'Use the external P2, not the LCD FPC.'],13,step=25)
    s.title(940,684,'Display orientation')
    s.lines(940,711,['Landscape 280 x 240 pixels.', 'Left variant: firmware rotation 180 degrees.', 'Right variant: firmware rotation 0 degrees.', 'The electrical wiring stays identical.'],13,step=25)
    s.rect(42,831,855,83,fill='#edf4fc')
    s.lines(58,855,['JP1: 1-15 top-down; JP2: 15-1 top-down (official schematic pad numbering).', 'VBUS is labelled VUSB in the official pinout. RST is RESET in that pinout.', 'Native USB MIDI uses the USB-C connector. B1 / GND + RST enters the ROM flasher.'],12,step=23)
    s.end()


def power_encoder():
    s=Sheet('Power distribution and rotary encoder','9V center-negative input; 3V3 logic; VIN receives 9V; converter 5V powers only optional LEDs. USB VBUS is sensed, not joined to 5V.',2)
    s.title(42,158,'External power')
    s.rect(42,190,224,140,fill='#f6f8fa',stroke=INK)
    s.text(57,216,'J1  5.5 x 2.1mm socket',14)
    s.text(57,249,'CENTER = GND (-)',14)
    s.text(57,291,'SLEEVE = +9V (+)',14)
    s.text(57,318,'18mm overall, M8 thread',12)
    component('J1','5.5x2.1mm center-negative',{'CENTER':'GND','SLEEVE':'+9V'},'18mm barrel socket / M8')
    s.line(266,286,430,286,ORANGE); s.net(325,286,'+9V',color=ORANGE)
    s.line(266,244,340,244);s.gnd(340,244)
    s.rect(430,185,290,150,fill='white',stroke=INK)
    s.text(452,212,'U3  Pololu S13V10F5',14,bold=True)
    s.text(452,237,'#4083 / retailer 1178565',13)
    s.text(443,281,'VIN',13);s.text(710,281,'VOUT / 5V',13,anchor='end')
    s.text(575,322,'GND',13,anchor='middle')
    component('U3','Pololu S13V10F5 #4083',{'VIN':'+9V','GND':'GND','VOUT':'+5V'},'5V 1A step-up/down module')
    s.line(575,335,575,366);s.gnd(575,366)
    s.line(720,286,1280,286,RED);s.net(775,286,'+5V',color=RED)
    s.line(325,286,325,164,ORANGE);s.net(325,164,'U1 VIN / JP1:15',color=ORANGE)
    s.line(1280,286,1280,337,RED);s.net(1280,337,'+5V_LED (sheet 6)',side='left',color=RED)
    s.circle(370,286,3,ORANGE)
    s.line(370,286,370,340,ORANGE)
    s.cap(370,340,'C1','47uF / 35V','+9V',height=35)
    s.text(42,405,'C1: place close to VIN/GND; electrolytic positive terminal goes to +9V.',13)
    s.rect(770,330,370,106,fill='#f6f8fa')
    s.lines(786,354,['U1 external supply terminals:', 'VIN (JP1:15) = +9V input', '3V3 (JP1:2) = logic supply output', 'GND (JP1:14 / JP2:4) = common return'],13,step=23)
    s.title(42,461,'USB-C and VBUS sense')
    s.text(42,490,'Nano VBUS / JP1:12',13,bold=True)
    s.line(220,485,280,485,RED)
    s.resistor(280,485,460,485,'R50','100k','USB_VBUS','USB_SENSE')
    s.line(460,485,610,485,BLUE);s.net(610,485,'A4 / GPIO11 (JP1:8)',color=BLUE)
    s.resistor(540,485,540,580,'R51','150k','USB_SENSE','GND');s.circle(540,485,3,BLUE);s.gnd(540,580)
    s.lines(790,481,['Native USB-C: MIDI / ROM serial flashing.', 'B1 to GND, tap RST, remove jumper to flash.', 'VBUS divider: 3.0V at 5.0V USB input.', 'Keep converter +5V separate from USB VBUS.', 'USB-only power leaves the LED rail off.'],13,step=23)
    s.title(42,619,'SW11  20-detent encoder with click - direct wiring')
    component('SW11','20-detent rotary encoder + NO click',{'A':'ENC_A','B':'ENC_B','C':'GND','SW1':'ENC_SW','SW2':'GND'},'passive encoder', 'Functional pin names only; verify the selected encoder terminal order.')
    s.text(42,645,'No external resistors or capacitors. Firmware enables internal pull-ups on GPIO7, GPIO8 and GPIO9.',13)
    s.rect(80,673,260,193,fill='#f1f8f3',stroke=GREEN)
    s.title(97,700,'SW11  ENCODER')
    s.text(97,727,'20 detents + click',13)
    s.text(97,757,'Passive contacts',12,color=MUTED)
    s.rect(850,673,470,193,fill='#f6f8fa',stroke=INK)
    s.title(870,699,'U1  Arduino Nano ESP32')
    for y,pin,net,dest in [(721,'A','ENC_A',gpio_label(7,'JP2:7')),
                            (753,'B','ENC_B',gpio_label(8,'JP2:8')),
                            (785,'SW1','ENC_SW',gpio_label(9,'JP2:9'))]:
        s.text(325,y+4,pin,13,anchor='end',bold=True)
        s.circle(340,y,3,GREEN,False);s.line(340,y,850,y,GREEN)
        s.net(590,y,net,color=GREEN)
        s.circle(850,y,3,GREEN,False);s.text(870,y+4,dest,13,bold=True)
    for y,pin in [(817,'C'),(849,'SW2')]:
        s.text(325,y+4,pin,13,anchor='end',bold=True);s.circle(340,y,3,INK,False)
    s.path([(340,817),(600,817),(600,849)])
    s.line(340,849,850,849);s.circle(600,849);s.gnd(600,849)
    s.circle(850,849,3,INK,False);s.text(870,853,'GND (JP1:14 / JP2:4)',13,bold=True)
    s.text(80,900,'Functional pin arrangement: verify A/B/C and the two click terminals on the selected encoder.',13,color=MUTED)
    s.text(80,921,'Software decodes A/B and debounces the click. Keep the encoder harness short.',12,color=MUTED)
    s.end()


def ladder():
    s=Sheet('Modular footswitch resistor ladder','A single series-tap ladder supports 4, 6, 8 or 10 normally-open switches. Only one switch is detected at a time.',3)
    s.net(80,185,'3V3',color=RED)
    s.resistor(80,185,80,300,'R7','10k','3V3','LADDER')
    s.line(80,300,390,300,AMBER);s.net(80,300,'LADDER / U1 A0 / GPIO1 (JP1:4)',color=AMBER)
    s.resistor(160,300,160,405,'R8','20k','LADDER','GND',labelside=-1);s.gnd(160,405)
    s.cap(280,300,'C5','100nF','LADDER',height=105)
    s.text(440,203,'BASE: T1-T4',15,bold=True,color=AMBER)
    s.text(810,203,'ADD TWO TAPS PER EXTENSION',15,bold=True,color=AMBER)
    # The resistor chain is folded only for page readability, with explicit tail nets.
    for start,y,x0,count in [(1,300,420,4),(5,565,100,6)]:
        prev='LADDER' if start==1 else 'T4'
        if start==5:
            s.line(x0,y-55,x0,y,AMBER);s.net(x0,y-55,'T4 / BASE TAIL',color=AMBER)
        for j in range(count):
            t=start+j;x=x0+j*200 if start==5 else x0+j*225
            if start==1 and j==0:s.line(390,300,x,300,AMBER)
            node=x+125
            s.resistor(x,y,node,y,f'R{8+t}','1k',prev,f'T{t}')
            s.switch(node,y,f'SW{t}',f'T{t}',TAPS[t-1][0])
            if j<count-1:s.line(node,y,x+(200 if start==5 else 225),y,AMBER)
            else:
                s.line(node,y,node,y-55,AMBER)
                s.net(node,y-55,f'T{t} / '+('EXTENSION TAIL' if start==1 else 'TAIL OPEN'),color=AMBER,side='left')
            s.text(node,y+132,f'T{t}  /  LED {t}',12,anchor='middle')
            prev=f'T{t}'
    s.rect(42,735,616,168,fill='#f6f8fa')
    s.title(58,762,'Modular harness and numbering')
    s.lines(58,790,['Each extension receives TAIL + GND and adds 2 x 1k.', 'Optional LED harness adds +5V and DOUT -> next DIN.', 'No terminating resistor at the final tail. All resistors 1%.', 'Select installed count in software, then capture calibration.', 'Left/right enclosure setting changes visual order only.'],13,step=23)
    s.table(690,713,668,['Tap','Name / LED','Expected mV','Tap','Name / LED','Expected mV'],[(t,TAPS[t-1][0]+f' / {t}',round(6600*t/(20+3*t)),t+5,TAPS[t+4][0]+f' / {t+5}',round(6600*(t+5)/(20+3*(t+5)))) for t in range(1,6)],[47,114,173,47,114,173],rowh=31,size=12)
    s.text(690,919,'Idle: 2200mV at 3.300V. Values are nominal; calibrate the assembled ladder.',11,color=MUTED)
    s.end()


def pedal(n):
    s=Sheet(f'Continuous pedal input {n} - passive', 'Two resistors inside the controller. External pedal: passive variable resistor or potentiometer, 0-10k.',3+n)
    prefix=f'P{n}';mode=prefix+'_MODE';adc=prefix+'_ADC'
    adc_gpio=2 if n==1 else 4;adc_pin='JP1:5' if n==1 else 'JP1:7'
    mode_gpio=5 if n==1 else 6;mode_pin='JP2:5' if n==1 else 'JP2:6'
    offset=20+(n-1)*10
    if n==1:
        component('J2','Amphenol ACJS-MHDC',{'10':'GND','11':'P1_RING','12':'P1_ADC','7':None,'8':None,'9':None,'4':'GND','5':'P2_RING','6':'P2_ADC','1':None,'2':None,'3':None,'13':None},'dual switched TRS', 'TOP=pedal1, BOTTOM=pedal2; pad13 mechanical. All normal contacts NC.')
    tp,rp,sp=(12,11,10) if n==1 else (6,5,4)
    s.title(42,155,'Inside the controller - only two resistors')
    s.rect(700,190,230,390,fill='#f6f8fa',stroke=INK)
    s.text(715,217,'J2  '+('TOP' if n==1 else 'BOTTOM'),16,bold=True)
    s.text(715,241,f'Pedal {n} TRS socket',13)
    s.net(80,280,'3V3',color=RED)
    s.resistor(180,280,470,280,f'R{offset}','5.1k','3V3',prefix+'_RING')
    s.line(80,280,180,280,RED);s.line(470,280,700,280,TEAL)
    s.circle(700,280,4,TEAL,False);s.text(715,285,f'{rp}  RING / reference',13)
    s.net(80,365,adc,color=TEAL);s.line(80,365,700,365,TEAL)
    s.text(80,398,'U1 '+gpio_label(adc_gpio,adc_pin),13,bold=True)
    s.circle(700,365,4,TEAL,False);s.text(715,370,f'{tp}  TIP / signal',13)
    s.net(80,475,mode,color=TEAL)
    s.line(80,475,180,475,TEAL)
    s.resistor(180,475,470,475,f'R{offset+1}','10k',mode,adc)
    s.line(470,475,550,475,TEAL);s.line(550,475,550,365,TEAL);s.circle(550,365,3,TEAL)
    s.text(80,509,'U1 '+gpio_label(mode_gpio,mode_pin),13,bold=True)
    s.line(80,550,700,550);s.gnd(80,550)
    s.circle(700,550,4,INK,False);s.text(715,555,f'{sp}  SLEEVE / GND',13)
    s.rect(970,190,388,390,fill='#edf4fc')
    s.title(987,222,'Firmware bias state')
    s.lines(987,253,['Resistor mode: mode GPIO = HIGH.', 'Pot mode: mode GPIO = high impedance.', 'Disabled / boot: high impedance.', 'Internal pull-up and pull-down OFF.', 'Never drive the bias GPIO LOW.'],13,step=26)
    s.title(987,414,'Nominal values at 3.300V')
    s.lines(987,443,['10k variable resistor: TIP = 1650mV.', '10k pot, full travel: TIP = 2185mV.', 'Ring short current: about 0.65mA.', 'ADC measures TIP directly (gain = 1).'],13,step=27)
    # These are alternative user-supplied passive pedals, not controller BOM parts.
    s.rect(42,621,632,285,fill='white',stroke=GRID)
    s.title(60,651,'Option A - three-wire potentiometer pedal')
    s.net(240,694,'RING',color=TEAL)
    s.resistor(240,694,240,829,'POT','0-10k',labelside=-1)
    s.net(240,829,'SLEEVE',side='left',color=INK)
    s.line(510,761,247,761,TEAL)
    s.path([(260,752),(247,761),(261,767)],color=TEAL)
    s.net(510,761,'TIP / wiper',side='left',color=TEAL)
    s.text(60,875,'Capture actual heel and toe voltages after connecting.',13)
    s.rect(714,621,644,285,fill='white',stroke=GRID)
    s.title(732,651,'Option B - two-wire variable resistor pedal')
    s.net(770,761,'TIP',color=TEAL)
    s.resistor(770,761,1115,761,'PEDAL R','0-10k')
    s.line(1115,761,1230,761);s.gnd(1230,761)
    s.text(1230,807,'SLEEVE',12,anchor='middle')
    s.text(732,851,'RING unused; a TS plug may connect it to SLEEVE.',13)
    s.text(732,875,'Select resistor mode and configure maximum resistance.',13)
    s.text(42,927,'No active pedal interface, scaling divider or external filter capacitors. J2 switched contacts remain NC; pad13 mechanical.',12,color=MUTED)
    s.end()


def leds():
    s=Sheet('Pololu 2535 - direct LED chain','Only LEDs and wires: Nano D7 / GPIO10 drives the first DIN directly. All boxes use the manufacturer side-view lead order.',6)
    def dot(x,y,color=INK):s.circle(x,y,3,color)
    def wire(points,color=INK,width=1.8):s.path(points,color,width)
    def ground_hop(x,y):
        # The ground wire passes over +5V without an electrical connection.
        points=[(x-10,y),(x-7,y-7),(x,y-10),(x+7,y-7),(x+10,y)]
        s.path(points,'white',7);s.path(points,INK,1.8)
    # Sources and Nano external pins only.
    s.rect(42,150,420,150,fill='#f6f8fa',stroke=INK)
    s.title(60,180,'U1  Arduino Nano ESP32')
    s.text(445,215,'D7 / GPIO10 (JP2:10)',14,anchor='end',bold=True)
    s.text(445,280,'GND (JP1:14 / JP2:4)',13,anchor='end')
    s.circle(462,210,4,PURPLE,False);s.circle(462,275,4,INK,False)
    wire([(462,210),(540,210),(540,170),(870,170),(870,202),(830,202)],PURPLE)
    wire([(462,275),(500,275),(500,915),(1200,915),(1200,145)],INK,2.1)
    s.line(1000,145,1000,890,RED,2.4)
    s.net(1000,145,'Regulated +5V',side='left',color=RED)
    s.net(1200,145,'Supply GND',color=INK)
    s.gnd(1200,915)
    # Reproduce the actual manufacturer reference unchanged.
    s.rect(42,350,420,177,fill='white',stroke=GRID)
    s.title(58,376,'Pololu package orientation')
    photo=OUT/'pololu-2535-pinout.jpg'
    encoded=base64.b64encode(photo.read_bytes()).decode()
    s.svg.append(f'<image x="58" y="392" width="388" height="97" href="data:image/jpeg;base64,{encoded}"/>')
    C.drawImage(str(photo),58,H-392-97,width=388,height=97)
    s.text(58,510,'Manufacturer side view: lens left, flat side down.',11,color=MUTED)
    C.linkURL('https://a.pololu-files.com/picture/0J5433.1200.jpg',(58,H-489,446,H-392),relative=0,thickness=0)
    s.rect(42,550,420,258,fill='#edf4fc')
    s.title(58,580,'Direct wiring')
    s.lines(58,613,['D7 / GPIO10 -> LED1 DIN.', 'Each DOUT -> next LED DIN.', 'Every 5V lead -> regulated +5V.', 'Every GND lead -> common GND.', 'Last DOUT -> leave unconnected.', 'RGB / 2535 / 800 kbit/s.', 'The driver is integrated into each LED.'],14,step=27)
    s.rect(42,835,420,72,fill='#f6f8fa')
    s.lines(58,858,['Direct 3.3V GPIO drive at a 5V LED supply', 'requires verification with the actual LED batch.', 'No additional LED-chain components are fitted.'],12,step=19)
    # Every pixel has its four leads on the RIGHT, in the actual side-view order.
    for i in range(1,11):
        y=190+(i-1)*70
        component(f'LED{i}','Pololu 2535',{'DIN':'LED_GPIO' if i==1 else f'L{i-1}','DOUT':f'L{i}' if i<10 else None,'+5V':'+5V','GND':'GND'},'5mm WS2811 pixel',f'Physical side view: lens left, flat down; right-side leads top-to-bottom DIN, 5V, GND, DOUT. Switch {TAPS[i-1][0]} / tap T{i}.')
        s.rect(600,y,230,60,fill='#f9f5fd',stroke=PURPLE)
        s.text(612,y+25,f'LED{i} / {TAPS[i-1][0]}',14,bold=True)
        s.text(612,y+44,'Pololu 2535',11)
        # Heavy bottom edge denotes the flat-side reference.
        s.line(600,y+60,830,y+60,PURPLE,3)
        for dy,name,color in [(12,'DIN',PURPLE),(24,'5V',RED),(36,'GND',INK),(48,'DOUT',PURPLE)]:
            s.text(817,y+dy+4,name,11,anchor='end',color=color,bold=True)
            s.circle(830,y+dy,2.5,color,False)
        s.line(830,y+24,1000,y+24,RED);dot(1000,y+24,RED)
        s.line(830,y+36,990,y+36)
        s.line(1010,y+36,1200,y+36);dot(1200,y+36)
        ground_hop(1000,y+36)
        if i<10:
            wire([(830,y+48),(870,y+48),(870,y+82),(830,y+82)],PURPLE)
            s.path([(865,y+64),(870,y+69),(875,y+64)],PURPLE,1.4)
        else:
            s.line(830,y+48,870,y+48,PURPLE)
            s.line(866,y+44,874,y+52,PURPLE);s.line(866,y+52,874,y+44,PURPLE)
            s.text(883,y+52,'NC',11,color=PURPLE)
    s.text(600,932,'Lead order is physical; outlines and lead spacing are schematic, not to scale. Hops do not connect to the red rail.',10,color=MUTED)
    s.end()


def reference():
    s=Sheet('Assembly reference, options and sources','The accompanying netlist and connection schedule include every external component terminal shown in this set.',7)
    s.title(42,155,'Harness and assembly rules')
    s.lines(42,185,[
      'All GND symbols are the same electrical net. Run analog returns separately to the controller ground point.',
      'Keep LADDER and pedal signals away from LED power/data and the DC converter. Pair signals with ground.',
      'Feed LED +5V/GND directly from the power distribution, rather than through the Nano headers.',
      'The 10-pixel chain can draw about 0.5A at full white. Keep total load within the 1A converter rating.',
      'LED lead order, lens pointing left and leads right, flat side down: top DIN, +5V, GND, bottom DOUT.',
      'The LED chain contains only Pololu 2535 LEDs and wiring: GPIO10 directly to the first DIN.',
      'Encoder terminal labels are functions; a specific encoder package pin numbering has not been selected.',
      'GPIO numbers are logical; D/A labels and SCK/MOSI/TX names identify the external board pins.'
    ],13,step=25)
    s.title(42,428,'Prototype verification')
    s.lines(42,457,[
      'With power disconnected: continuity-check TRS terminals, power polarity, ground and all off-sheet nets.',
      'Verify regulated +5V, then U1 3V3. Flash the passive-input firmware and recalibrate both pedals.',
      'Check resistor-mode HIGH / pot-mode high impedance, ADC ranges, ladder taps, encoder, USB MIDI and BLE MIDI.',
      'Each passive pedal input uses two resistors. Connect only unpowered variable-resistor or pot pedals.',
      'This document does not establish ESD compliance, measured analog accuracy or simultaneous-supply qualification.'
    ],13,step=25)
    s.title(42,596,'Source documents checked')
    for i,(name,note,url) in enumerate(SOURCES):
        yy=623+i*27
        s.text(42,yy,name,12,bold=True)
        s.text(445,yy,note,11,color=MUTED)
        if url:
            # Human-readable title hyperlinks avoid pages of long URLs.
            C.linkURL(url,(42,H-yy-4,430,H-yy+12),relative=0,thickness=0)
    s.text(42,918,'Source URLs, BOM, exact terminal connectivity and generated SVG sheets are in design/electrical/.',12,color=MUTED)
    s.end()


def single_page():
    """Draw the unified connected schematic from the same component netlist."""
    import sys
    sys.dont_write_bytecode=True
    from unified_electrical import render
    render(sys.modules[__name__])


def verify_firmware_pins():
    source=(ROOT/'src/board.hpp').read_text()
    names={'Ladder':'LADDER','Pedal1':'P1_ADC','Pedal2':'P2_ADC',
           'Pedal1Bias':'P1_MODE','Pedal2Bias':'P2_MODE','EncoderA':'ENC_A',
           'EncoderB':'ENC_B','EncoderClick':'ENC_SW','LedData':'LED_GPIO',
           'LcdClock':'LCD_CLK','LcdDc':'LCD_DC','LcdCs':'LCD_CS',
           'LcdMosi':'LCD_DIN','LcdReset':'LCD_RST','UsbVbusSense':'USB_SENSE'}
    pads=external_pin_data()
    for name,net in names.items():
        match=re.search(r'\b'+name+r'\s*=\s*(\d+)',source)
        assert match,name
        actual=[p['logical_name'] for p in pads.values() if p['net']==net]
        assert actual==['GPIO'+match.group(1)],(name,actual)
    return {'source':'src/board.hpp','sha256':hashlib.sha256(source.encode()).hexdigest(),
            'used_signal_pins':len(names),'all_assignments_match':True}


def export_data():
    nets=defaultdict(list)
    for ref,part in COMPONENTS.items():
        for pin,net in part['pins'].items():
            if net is not None:nets[net].append(f'{ref}.{pin}')
    payload={'project':'SIGMIDI Foot Controller','version':'0.1','status':'electrical review - not bench qualified','board_detail':'external pins only; passive pedals use two controller resistors per input','nano_external_pins':external_pin_data(),'firmware_pin_verification':verify_firmware_pins(),'units':{'resistors':'ohms (k = 1000)','capacitors':'farads (nF/uF as labelled)'},'components':COMPONENTS,'nets':dict(sorted(nets.items())),'sources':[{'title':a,'description':b,'url':c} for a,b,c in SOURCES]}
    (OUT/'netlist.json').write_text(json.dumps(payload,indent=2)+'\n')
    with (OUT/'connections.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(['Component','Value','Terminal','Physical board label','Logical GPIO / signal','Net','Note'])
        for ref,p in COMPONENTS.items():
            for pin,net in p['pins'].items():
                labels=external_pin_data().get(pin,{}) if ref=='U1' else {}
                if ref.startswith('LED'):
                    position={'DIN':'top / farthest from flat','+5V':'second','GND':'third','DOUT':'bottom / nearest flat'}[pin]
                    labels={'physical_label':position+' (lens left, flat down)','logical_name':'5V' if pin=='+5V' else pin}
                w.writerow([ref,p['value'],pin,labels.get('physical_label',''),labels.get('logical_name',''),net or 'NC',p['note']])
    groups=defaultdict(list)
    for ref,p in COMPONENTS.items():groups[(p['value'],p['package'])].append(ref)
    with (OUT/'bom.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(['Quantity (10-switch maximum)','References','Value','Package / type'])
        for (value,package),refs in groups.items():w.writerow([len(refs),' '.join(refs),value,package])
    # Structural checks catch transcription errors between named connector nets.
    assert COMPONENTS['U2']['pins']['P2:5']==COMPONENTS['U1']['pins']['JP2:11']=='LCD_CLK'
    assert COMPONENTS['U2']['pins']['P2:6']==COMPONENTS['U1']['pins']['JP2:14']=='LCD_DIN'
    assert COMPONENTS['U1']['pins']['JP2:5']=='P1_MODE'
    assert COMPONENTS['U1']['pins']['JP2:6']=='P2_MODE'
    for i in range(1,11):
        assert COMPONENTS[f'SW{i}']['pins']['1']==f'T{i}'
        assert COMPONENTS[f'R{8+i}']['pins']['1']==('LADDER' if i==1 else f'T{i-1}')
        assert COMPONENTS[f'LED{i}']['pins']['DIN']==('LED_GPIO' if i==1 else f'L{i-1}')
    for n in [1,2]:
        offset=20+(n-1)*10
        assert COMPONENTS[f'R{offset}']['pins']=={'1':'3V3','2':f'P{n}_RING'}
        assert COMPONENTS[f'R{offset+1}']['pins']=={'1':f'P{n}_MODE','2':f'P{n}_ADC'}
        assert COMPONENTS['J2']['pins']['12' if n==1 else '6']==f'P{n}_ADC'
    assert not any(ref in COMPONENTS for ref in ['U4','Q1','Q2','D1','D2'])
    assert not any(ref in COMPONENTS for ref in ['U5','R40','R41']+[f'C{i}' for i in range(16,28)])
    for i in range(1,11):
        assert COMPONENTS[f'LED{i}']['pins']['+5V']=='+5V'
        assert COMPONENTS[f'LED{i}']['pins']['GND']=='GND'
        if i<10:assert COMPONENTS[f'LED{i}']['pins']['DOUT']==COMPONENTS[f'LED{i+1}']['pins']['DIN']
    assert COMPONENTS['LED1']['pins']['DIN']==COMPONENTS['U1']['pins']['JP2:10']=='LED_GPIO'
    assert COMPONENTS['LED10']['pins']['DOUT'] is None
    for pin,header,net in [('A','JP2:7','ENC_A'),('B','JP2:8','ENC_B'),('SW1','JP2:9','ENC_SW')]:
        assert COMPONENTS['SW11']['pins'][pin]==COMPONENTS['U1']['pins'][header]==net
    assert COMPONENTS['SW11']['pins']['C']==COMPONENTS['SW11']['pins']['SW2']=='GND'
    assert not any(ref in COMPONENTS for ref in [f'R{i}' for i in range(1,7)]+['C2','C3','C4'])
    # Every named net must reach at least two component terminals.
    assert all(len(v)>=2 for v in nets.values()),{k:v for k,v in nets.items() if len(v)<2}
    assert COMPONENTS['U1']['pins']['JP1:15']==COMPONENTS['U3']['pins']['VIN']=='+9V'
    assert COMPONENTS['U1']['pins']['JP1:12']=='USB_VBUS'
    assert COMPONENTS['R50']['pins']=={'1':'USB_VBUS','2':'USB_SENSE'}
    assert COMPONENTS['R51']['pins']=={'1':'USB_SENSE','2':'GND'}
    (OUT/'README.md').write_text("""# SIGMIDI Foot Controller v0.1 — electrical diagrams

The Nano ESP32 assembly has a [unified A0 schematic](../../output/pdf/sigmidi-electrical-single-page.pdf), [seven detailed A3 sheets](../../output/pdf/sigmidi-electrical-diagram.pdf), [browser preview](../../previews/electrical-single-page.html), terminal CSV and machine-readable netlist. Purchased boards stop at external pins. These are assembly wiring drawings, not PCB fabrication files. Bench verification is required.

U1 is Arduino Nano ESP32 ABX00083, component-side top view with USB-C up. JP1 is left, pads 1–15 top-down; JP2 is right, pads 15–1 top-down. Pad IDs follow Arduino's V0.3 schematic, while printed D/A labels follow its official top-view pinout. VBUS is called VUSB in that pinout. Every printed header label remains visible; unused outside callouts are omitted. Connected pins show both the board label and ESP32 GPIO. GPIO numbers match `src/board.hpp`, independently of Arduino pin-numbering preferences.

U2 is Waveshare 24382. Its external P2 connector stays in physical order: 1 BL, 2 RST, 3 D/C, 4 CS, 5 SCL/CLK, 6 SDA/DIN, 7 GND, 8 VCC. SCL/SDA are SPI signals. BL and VCC connect to Nano 3V3. Left/Right enclosure selection changes screen rotation and visual switch order, not wiring or physical tap identity.

Nano A0/GPIO1 reads the ladder; A1/GPIO2 and A3/GPIO4 read pedal TIPs. Each RING receives 3V3 through 5.1k (R20/R30), each TIP receives its bias output through 10k (R21/R31). Bias is D2/GPIO5 or D3/GPIO6: HIGH in resistor mode, high impedance in pot/disabled/boot states, never LOW. Pedals are passive 0–10k variable resistors (TIP–SLEEVE) or pots (outer legs RING/SLEEVE, wiper TIP). ADC voltages are used directly without a gain multiplier. Capture actual endpoints after assembly.

J2 is Amphenol ACJS-MHDC: manufacturer TOP is pedal 1 (10 SLEEVE, 11 RING, 12 TIP), BOTTOM is pedal 2 (4 SLEEVE, 5 RING, 6 TIP). Normal contacts stay unconnected; pad 13 is mechanical. SW11 uses A/B/click on D4/GPIO7, D5/GPIO8, D6/GPIO9 with internal pull-ups and common GND. Its pin labels are functional; verify terminal order on the purchased encoder.

The optional Pololu 2535 chain contains only LEDs and wires. D7/GPIO10 goes directly to LED1 DIN; each DOUT goes to the next DIN. Final DOUT stays open. Supply every LED from regulated 5V and common GND, rather than Nano 3V3. Physical side view: lens left, leads right, flat side down; top to bottom DIN, 5V, GND, DOUT. The manufacturer photograph is included unchanged as orientation reference. Verify 3.3V data acceptance with the actual batch.

Populate four ladder stages for the base; each extension adds two 1k resistors and switches. Select 4/6/8/10 in software and calibrate the installed taps. No end termination is fitted. Fixed tap/LED identity: T1=B, T2=A, T3=2, T4=1, T5=C, T6=3, T7=D, T8=4, T9=E, T10=5.

J1 accepts 9V DC center-negative: center GND, sleeve +9V. +9V feeds both Nano VIN (JP1:15) and Pololu S13V10F5 VIN. C1 is 47uF/35V across converter VIN/GND. Converter VOUT supplies the optional 5V LED rail only. Never join it to USB VBUS. Nano VBUS (JP1:12) feeds R50 100k, then A4/GPIO11; R51 150k connects that node to GND. This divider is required for self-powered USB detection. USB-C carries native USB MIDI and ROM flashing; GPIO19/20 are reserved internally for USB. For flashing, join B1 to GND, tap RST, remove the jumper, then select the ROM serial port.

`single-page-wiring.json` records terminals and wire geometry. The generator checks full net coverage, continuous routes, body crossings, and foreign-net overlaps. Dots indicate junctions; arched crossings remain separate. Both pedal ports share one socket outline. Reference numbering has deliberate gaps. Rebuild with `scripts/preview_electrical.py`; connectivity, routing and firmware-pin agreement are checked during generation. Manufacturer links are in `netlist.json`. Physical tolerances, noise, electrical protection and simultaneous-supply performance require hardware tests.
""")
    single_page()
    options=''.join(f'<button data-sheet="{i}" {"aria-current=true" if i==0 else ""}>{i+1}. {html.escape(p["title"])}</button>' for i,p in enumerate(PAGES))
    sheets=''.join(f'<section id="sheet-{i}" {"" if i==0 else "hidden"}>{p["svg"]}</section>' for i,p in enumerate(PAGES))
    PREVIEW.write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SIGMIDI v0.1 - electrical diagram</title><style>
*{box-sizing:border-box}body{margin:0;background:#eaf0f4;color:#183044;font:15px system-ui,sans-serif}header{padding:22px 28px;background:#183044;color:white;display:flex;justify-content:space-between;gap:20px}h1{font-size:23px;margin:0 0 7px}p{margin:0;color:#c5d4df}nav{padding:16px 24px;display:flex;gap:8px;flex-wrap:wrap}button{border:1px solid #bdccd7;background:white;color:#183044;padding:10px 14px;border-radius:7px;cursor:pointer}button[aria-current=true]{background:#2164b4;color:white;border-color:#2164b4}main{padding:0 24px 30px}section{background:white;box-shadow:0 3px 22px #18304419}svg{display:block;width:100%;height:auto}.hint{font-size:13px;color:#c5d4df}a{color:inherit}@media print{header,nav{display:none}main{padding:0}section{display:block!important;break-after:page;box-shadow:none}section[hidden]{display:block!important}@page{size:A3 landscape;margin:0}}
</style><header><div><h1>SIGMIDI Foot Controller / electrical diagram</h1><p>v0.1 - connector pin assignments and complete external wiring</p></div><div class="hint"><a href="electrical-single-page.html">Single-page diagram</a><br>7 detailed vector sheets<br>Prototype circuit / not bench qualified</div></header><nav>'''+options+'</nav><main>'+sheets+'''</main><script>document.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('section').forEach((s,i)=>s.hidden=i!==Number(b.dataset.sheet));document.querySelectorAll('button').forEach(x=>x.setAttribute('aria-current',String(x===b)));}));</script></html>''')
    print(json.dumps({'pages':len(PAGES),'components':len(COMPONENTS),'named_nets':len(nets),'pdf':str(PDF),'preview':str(PREVIEW)},indent=2))


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True);PDF.parent.mkdir(parents=True,exist_ok=True)
    C=canvas.Canvas(str(PDF),pagesize=landscape(A3),pageCompression=1)
    C.setTitle('SIGMIDI Foot Controller v0.1 - Electrical diagram')
    C.setAuthor('SIGMIDI Foot Controller project')
    SCALE=landscape(A3)[0]/W
    # A3 has a 1.414 aspect ratio; this logical page has the same dimensions to rounding.
    C.scale(SCALE,SCALE)
    controller();power_encoder();ladder();pedal(1);pedal(2);leds();reference()
    C.save()
    export_data()
