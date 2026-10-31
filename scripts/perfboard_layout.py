"""Carrier perfboard layout: U1-side passives, ladder top segment and the TRS MIDI buffer.

Grid: column c = 0..25 (left to right), row r = 0..5 (top to bottom) on a 6 x 26 hole,
2.54 mm perfboard, seen from the component side. check() validates every lead against
design/electrical/netlist.json, hole reuse, body overlap and per-net connectivity.
drawing() renders the placement or solder-side view as a ReportLab drawing.
"""
from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors

COLS, ROWS = 26, 6

PARTS = {
    # Ladder top: pull-up, pull-down, filter and the first 1k segment to tap T1.
    'R7':  {'pins': {'1': (3, 0), '2': (3, 1)}, 'body': '2'},
    'R9':  {'pins': {'1': (4, 1), '2': (4, 2)}, 'body': '2'},
    'C5':  {'pins': {'1': (3, 3), '2': (3, 4)}, 'kind': 'cer'},
    'R8':  {'pins': {'1': (4, 3), '2': (4, 4)}, 'body': '2'},
    # Pedal 1 and 2 bias networks.
    'R20': {'pins': {'1': (6, 0), '2': (6, 1)}, 'body': '2'},
    'R21': {'pins': {'1': (6, 3), '2': (6, 4)}, 'body': '1'},
    'R30': {'pins': {'1': (9, 0), '2': (9, 1)}, 'body': '2'},
    'R31': {'pins': {'1': (9, 3), '2': (9, 4)}, 'body': '1'},
    # USB VBUS sense divider.
    'R50': {'pins': {'1': (12, 2), '2': (12, 3)}, 'body': '1'},
    'R51': {'pins': {'1': (12, 4), '2': (12, 5)}, 'body': '1'},
    # VIN bulk capacitor, 6.3 mm radial.
    'C1':  {'pins': {'1': (1, 2), '2': (1, 3)}, 'kind': 'elko'},
    # MIDI OUT: idle pull-up, supply OR, bypass, buffer and loop resistors.
    'R52': {'pins': {'1': (11, 1), '2': (11, 2)}, 'body': '1'},
    'D2':  {'pins': {'A': (13, 1), 'K': (13, 0)}, 'body': 'A', 'kind': 'diode'},
    'D1':  {'pins': {'A': (14, 1), 'K': (14, 0)}, 'body': 'K', 'kind': 'diode'},
    'R53': {'pins': {'1': (15, 0), '2': (15, 1)}, 'body': '2'},
    'R55': {'pins': {'1': (16, 0), '2': (16, 1)}, 'body': '1'},
    'C6':  {'pins': {'1': (17, 3), '2': (17, 4)}, 'kind': 'cer'},
    'R54': {'pins': {'1': (15, 3), '2': (15, 4)}, 'body': '1'},
    'R56': {'pins': {'1': (25, 4), '2': (25, 5)}, 'body': '2'},
    'U4':  {'pins': {**{str(i): (17 + i, 4) for i in range(1, 8)},
                     **{str(15 - i): (17 + i, 1) for i in range(1, 8)}}, 'kind': 'dip'},
}

# Off-board wire entry holes: label, net, hole, destination.
PADS = [
    ('3V3', '3V3', (0, 0), 'U1 JP1:2'),
    ('GND', 'GND', (0, 5), 'U1 JP1:14'),
    ('+9V', '+9V', (1, 1), 'J1, JP1:15, U3'),
    ('A0', 'LADDER', (2, 1), 'U1 JP1:4'),
    ('T1', 'T1', (5, 2), 'SW1, R10'),
    ('P1R', 'P1_RING', (7, 1), 'J2:11'),
    ('P1M', 'P1_MODE', (6, 2), 'U1 JP2:5 (D2)'),
    ('A1', 'P1_ADC', (7, 3), 'U1 JP1:5'),
    ('P1T', 'P1_ADC', (7, 4), 'J2:12'),
    ('P2R', 'P2_RING', (10, 1), 'J2:5'),
    ('P2M', 'P2_MODE', (9, 2), 'U1 JP2:6 (D3)'),
    ('A3', 'P2_ADC', (10, 3), 'U1 JP1:7'),
    ('P2T', 'P2_ADC', (10, 4), 'J2:6'),
    ('A4', 'USB_SENSE', (11, 3), 'U1 JP1:8'),
    ('VBUS', 'USB_VBUS', (12, 1), 'U1 JP1:12'),
    ('TX', 'MIDI_OUT_TX', (10, 2), 'U1 JP2:2 (D0)'),
    ('+5V', '+5V', (14, 2), 'U3 VOUT'),
    ('3R', 'J3_RING', (15, 2), 'J3 ring'),
    ('4R', 'J4_RING', (16, 2), 'J4 ring'),
    ('3T', 'J3_TIP', (14, 4), 'J3 tip'),
    ('4T', 'J4_TIP', (25, 5), 'J4 tip (R56 pad)'),
    ('3S', 'GND', (14, 5), 'J3 sleeve'),
    ('4S', 'GND', (16, 5), 'J4 sleeve'),
]

# Bare tinned-wire trails on the solder side; each is a straight run of adjacent holes.
def run(net, a, b):
    (c1, r1), (c2, r2) = a, b
    assert c1 == c2 or r1 == r2, (net, a, b)
    if c1 == c2:
        return net, [(c1, r) for r in range(min(r1, r2), max(r1, r2) + 1)]
    return net, [(c, r1) for c in range(min(c1, c2), max(c1, c2) + 1)]

TRAILS = [
    run('3V3', (0, 0), (11, 0)),              # 3V3 rail
    run('MIDI_5V', (13, 0), (18, 0)),         # MIDI_5V rail to U4 pin 14
    run('MIDI_5V', (18, 0), (18, 1)),
    run('GND', (0, 5), (11, 5)),              # GND rail, analog part
    run('GND', (13, 5), (24, 5)),             # GND rail, MIDI part
    run('GND', (11, 5), (13, 5)),
    run('+9V', (1, 1), (1, 2)),
    run('GND', (1, 3), (1, 5)),
    run('LADDER', (2, 1), (4, 1)),
    run('LADDER', (3, 1), (3, 3)),
    run('LADDER', (3, 3), (4, 3)),
    run('GND', (3, 4), (3, 5)),
    run('GND', (4, 4), (4, 5)),
    run('T1', (4, 2), (5, 2)),
    run('P1_RING', (6, 1), (7, 1)),
    run('P1_MODE', (6, 2), (6, 3)),
    run('P1_ADC', (6, 4), (7, 4)),
    run('P1_ADC', (7, 3), (7, 4)),
    run('P2_RING', (9, 1), (10, 1)),
    run('P2_MODE', (9, 2), (9, 3)),
    run('P2_ADC', (9, 4), (10, 4)),
    run('P2_ADC', (10, 3), (10, 4)),
    run('USB_SENSE', (11, 3), (12, 3)),
    run('USB_SENSE', (12, 3), (12, 4)),
    run('USB_VBUS', (12, 1), (13, 1)),
    run('USB_VBUS', (12, 1), (12, 2)),
    run('MIDI_OUT_TX', (10, 2), (11, 2)),
    run('3V3', (11, 0), (11, 1)),
    run('+5V', (14, 1), (14, 2)),
    run('J3_RING', (15, 1), (15, 2)),
    run('J4_RING', (16, 1), (16, 2)),
    run('J3_TIP', (14, 4), (15, 4)),
    run('MIDI_5V', (17, 0), (17, 3)),         # C6 feed beside U4
    run('GND', (17, 4), (17, 5)),
    # U4: unused inputs/enables on the top row tie under the body to pin 4.
    run('GND', (19, 1), (19, 2)),
    run('GND', (20, 1), (20, 2)),
    run('GND', (22, 1), (22, 2)),
    run('GND', (23, 1), (23, 2)),
    run('GND', (19, 2), (23, 2)),
    run('GND', (21, 2), (21, 4)),
    run('GND', (18, 4), (18, 5)),             # pins 1, 4, 7 to the GND rail
    run('GND', (21, 4), (21, 5)),
    run('GND', (24, 4), (24, 5)),
    run('TX_GATE2', (23, 3), (23, 4)),        # pin 6 under the body to R56
    run('TX_GATE2', (23, 3), (25, 3)),
    run('TX_GATE2', (25, 3), (25, 4)),
]

# Insulated wire links on the solder side (they may cross trails).
LINKS = [
    ('MIDI_OUT_TX', (11, 2), (19, 4)),        # R52 / TX entry to U4 pin 2
    ('MIDI_OUT_TX', (19, 4), (22, 4)),        # U4 pin 2 to pin 5
    ('TX_GATE1', (20, 4), (15, 3)),           # U4 pin 3 to R54
]


def body_shapes(ref, p):
    """Return top-side keep-out shapes in grid units: ('circle', cx, cy, r) or ('rect', x0, y0, x1, y1)."""
    kind = p.get('kind', 'res')
    pins = list(p['pins'].values())
    if kind == 'dip':
        return [('rect', 17.27, 1.27, 24.73, 3.73)]
    if kind == 'elko':
        (c1, r1), (c2, r2) = pins
        return [('circle', (c1 + c2) / 2, (r1 + r2) / 2, 1.24)]
    if kind == 'cer':
        (c1, r1), (c2, r2) = pins
        return [('rect', min(c1, c2) - 0.18, min(r1, r2) + 0.2, max(c1, c2) + 0.18, max(r1, r2) - 0.2)]
    c, r = p['pins'][p['body']]
    return [('circle', c, r, 0.53 if kind == 'diode' else 0.46)]


def inside(shape, c, r):
    if shape[0] == 'circle':
        return (c - shape[1]) ** 2 + (r - shape[2]) ** 2 < shape[3] ** 2 - 1e-9
    return shape[1] < c < shape[3] and shape[2] < r < shape[4]


def overlap(a, b):
    def box(s):
        return (s[1] - s[3], s[2] - s[3], s[1] + s[3], s[2] + s[3]) if s[0] == 'circle' else s[1:]
    if a[0] == b[0] == 'circle':
        return (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2 < (a[3] + b[3]) ** 2 - 1e-9
    if a[0] == 'rect' and b[0] == 'rect':
        return a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]
    circle, rect = (a, b) if a[0] == 'circle' else (b, a)
    nx = min(max(circle[1], rect[1]), rect[3]); ny = min(max(circle[2], rect[2]), rect[4])
    return (circle[1] - nx) ** 2 + (circle[2] - ny) ** 2 < circle[3] ** 2 - 1e-9


def check(netlist):
    """Validate the layout against the netlist components; return hole nets and hole users."""
    NET = netlist['components']
    hole_net, hole_use = {}, {}
    def claim(hole, net, what):
        c, r = hole
        assert 0 <= c < COLS and 0 <= r < ROWS, (what, hole)
        if hole in hole_net and hole_net[hole] != net:
            raise AssertionError(f'{what} puts {net} on {hole}, already {hole_net[hole]}')
        hole_net[hole] = net
    for ref, p in PARTS.items():
        nets = {**{pin: None for pin in p['pins']}, **NET[ref]['pins']}
        for pin, net in nets.items():
            if net is None and pin not in p['pins']:
                continue
            hole = p['pins'][pin]
            assert hole not in hole_use, (ref, pin, hole, hole_use.get(hole))
            hole_use[hole] = f'{ref}.{pin}'
            claim(hole, net or f'NC:{ref}.{pin}', f'{ref}.{pin}')
    for label, net, hole, _ in PADS:
        if hole in hole_use:
            # A wire may share the solder-side pad of a same-net lead.
            assert hole_net[hole] == net, (label, hole, hole_use[hole])
            continue
        hole_use[hole] = f'pad {label}'
        claim(hole, net, f'pad {label}')
    for net, holes in TRAILS:
        for h in holes:
            claim(h, net, f'trail {net}')
    for net, a, b in LINKS:
        assert hole_net.get(a) == net and hole_net.get(b) == net, (net, a, b)
    # Bodies: no overlaps, and no foreign lead or pad inside a body.
    shapes = {ref: body_shapes(ref, p) for ref, p in PARTS.items()}
    refs = list(shapes)
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            for sa in shapes[a]:
                for sb in shapes[b]:
                    assert not overlap(sa, sb), (a, b)
        for hole, who in hole_use.items():
            if who.split('.')[0] == a:
                continue
            for s in shapes[a]:
                assert not inside(s, *hole), (a, who, hole)
    # Connectivity: union-find over trails and links.
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def join(a, b): parent[find(a)] = find(b)
    for net, holes in TRAILS:
        for a, b in zip(holes, holes[1:]):
            join(a, b)
    for net, a, b in LINKS:
        join(a, b)
    groups = {}
    for hole, net in hole_net.items():
        if hole in hole_use and not net.startswith('NC:'):
            groups.setdefault(net, set()).add(find(hole))
    split = {n: len(g) for n, g in groups.items() if len(g) > 1}
    assert not split, split
    # Every net that leaves the board has an entry pad, unless it ends on board.
    board_only = {'TX_GATE1', 'TX_GATE2', 'MIDI_5V'}
    padded = {net for _, net, _, _ in PADS}
    for net in groups:
        assert net in padded or net in board_only, f'{net} has no wire entry'
    # Scope: every resistor/capacitor on a U1 net, plus the complete buffered MIDI OUT stage.
    u1 = {net for net in NET['U1']['pins'].values() if net}
    direct = {ref for ref, c in NET.items() if ref[0] in 'RC' and u1 & set(c['pins'].values())}
    midi = {ref for ref, c in NET.items() if ref[0] in 'RCDU' and ref != 'U1'
            and {'MIDI_5V', 'TX_GATE1', 'TX_GATE2'} & set(c['pins'].values())}
    assert set(PARTS) == direct | midi, set(PARTS) ^ (direct | midi)
    return hole_net, hole_use


NET_COLORS = {'GND': '#183044', '3V3': '#a64932', 'MIDI_5V': '#ba344b', '+5V': '#ba344b', '+9V': '#a35b12',
              'USB_VBUS': '#2164b4', 'USB_SENSE': '#2164b4', 'LADDER': '#986300', 'T1': '#986300'}


def net_color(net):
    if net in NET_COLORS:
        return colors.HexColor(NET_COLORS[net])
    if net.startswith(('P1_', 'P2_')):
        return colors.HexColor('#087e89')
    return colors.HexColor('#8650aa')


def drawing(width, view, hole_use, font='Helvetica', bold='Helvetica-Bold'):
    """Return the 'placement' or 'wiring' (trails and links seen through the board) view."""
    pitch = width / (COLS + 1.2)
    x0, height = pitch * 1.1, pitch * (ROWS + 1.4)
    d = Drawing(width, height)
    def xy(c, r):
        return x0 + c * pitch, height - pitch * 0.85 - r * pitch
    def text(x, y, value, size, color, weight=font, anchor='middle'):
        d.add(String(x, y, value, fontName=weight, fontSize=size, fillColor=color, textAnchor=anchor))
    bx, top = xy(-0.7, -0.7)
    _, bottom = xy(0, ROWS - 0.3)
    d.add(Rect(bx, bottom, (COLS + 0.4) * pitch, top - bottom, rx=4, ry=4,
               fillColor=colors.HexColor('#e9dcc0'), strokeColor=colors.HexColor('#9c8a62'), strokeWidth=0.8))
    label = colors.HexColor('#7a6a48')
    for c in range(COLS):
        x, _ = xy(c, 0)
        text(x, bottom - pitch * 0.45, str(c), pitch * 0.32, label)
    for r in range(ROWS):
        _, y = xy(0, r)
        text(bx - pitch * 0.15, y - pitch * 0.11, str(r), pitch * 0.32, label, anchor='end')
    if view == 'wiring':
        for net, holes in TRAILS:
            (xa, ya), (xb, yb) = xy(*holes[0]), xy(*holes[-1])
            d.add(Line(xa, ya, xb, yb, strokeColor=net_color(net), strokeWidth=pitch * 0.24, strokeLineCap=1))
    for c in range(COLS):
        for r in range(ROWS):
            x, y = xy(c, r)
            used = (c, r) in hole_use
            d.add(Circle(x, y, pitch * (0.2 if used else 0.15), fillColor=colors.HexColor('#c9a64a' if used else '#d9c79c'),
                         strokeColor=colors.HexColor('#8a7440'), strokeWidth=0.4))
            d.add(Circle(x, y, pitch * 0.06, fillColor=colors.HexColor('#5a4a2a'), strokeColor=None))
    if view == 'wiring':
        for net, a, b in LINKS:
            (xa, ya), (xb, yb) = xy(*a), xy(*b)
            sag = pitch * 0.55 if a[1] == b[1] else 0
            d.add(PolyLine([xa, ya, (xa + xb) / 2, (ya + yb) / 2 - sag, xb, yb], strokeColor=net_color(net),
                           strokeWidth=pitch * 0.09, strokeDashArray=[pitch * 0.25, pitch * 0.15]))
    for ref, p in PARTS.items():
        kind = p.get('kind', 'res')
        for shape in body_shapes(ref, p):
            if shape[0] == 'rect':
                (xa, ya), (xb, yb) = xy(shape[1], shape[2]), xy(shape[3], shape[4])
                fill = '#2b2b2b' if kind == 'dip' else '#d98c2b'
                d.add(Rect(xa, yb, xb - xa, ya - yb, rx=2, ry=2, fillColor=colors.HexColor(fill), strokeColor=None,
                           fillOpacity=0.85 if view == 'wiring' else 1))
            else:
                x, y = xy(shape[1], shape[2])
                fill = {'elko': '#1f3f73', 'diode': '#2b2b2b'}.get(kind, '#9cc5e0')
                d.add(Circle(x, y, shape[3] * pitch, fillColor=colors.HexColor(fill), strokeColor=colors.HexColor('#183044'),
                             strokeWidth=0.5, fillOpacity=0.8 if view == 'wiring' else 1))
        if kind == 'dip':
            x, y = xy(21, 2.5)
            text(x, y - pitch * 0.15, 'U4  74HCT125', pitch * 0.5, colors.white, bold)
            x, y = xy(17.6, 2.5)
            d.add(Circle(x, y, pitch * 0.15, fillColor=colors.HexColor('#666666'), strokeColor=None))
            for pin, (c, r) in p['pins'].items():
                x, y = xy(c, r)
                text(x, y + (-pitch * 0.62 if r == 1 else pitch * 0.38), pin, pitch * 0.3, colors.white)
            continue
        if kind == 'elko':
            x, y = xy(*p['pins']['1'])
            text(x - pitch * 0.6, y - pitch * 0.18, '+', pitch * 0.55, colors.white, bold)
        if kind == 'diode':
            x, y = xy(*p['pins'][p['body']])
            if p['body'] == 'K':
                d.add(Rect(x - pitch * 0.3, y - pitch * 0.08, pitch * 0.6, pitch * 0.16, fillColor=colors.HexColor('#dddddd'), strokeColor=None))
        if kind == 'cer':
            pins = list(p['pins'].values())
            x, y = xy(sum(c for c, _ in pins) / len(pins) - 0.55, sum(r for _, r in pins) / len(pins))
        else:
            shape = body_shapes(ref, p)[0]
            x, y = xy(shape[1], shape[2])
        light = kind in ('elko', 'diode')
        text(x, y - pitch * 0.12, ref, pitch * 0.34, colors.white if light else colors.HexColor('#111111'), bold)
    for label_text, net, (c, r), _ in PADS:
        if (c, r) in {h for p in PARTS.values() for h in p['pins'].values()}:
            continue
        x, y = xy(c, r)
        d.add(Rect(x - pitch * 0.46, y - pitch * 0.22, pitch * 0.92, pitch * 0.44, rx=1.5, ry=1.5,
                   fillColor=net_color(net), strokeColor=None))
        text(x, y - pitch * 0.11, label_text, pitch * 0.3, colors.white, bold)
    return d
