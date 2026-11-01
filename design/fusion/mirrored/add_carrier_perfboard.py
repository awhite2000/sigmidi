"""Add the populated carrier perfboard to the Left main assembly.

Run inside Fusion with the SIGMIDI archive open. The component is rebuilt from
scripts/perfboard_layout.py inside 'ALT Mirrored MAIN' each run: an 80.5 x 20 x 1.5 mm
board with the 6 x 28 hole field at 2.5 mm pitch, four 3 mm mounting holes, four
2 x 3.5 mm pads at each end, the upright parts, U4 in its socket and short wire-entry
stubs. It lies at base level under the dual TRS socket, rotated so column 0 faces the
Nano. Clashes with the other Left main bodies are written to carrier-perfboard.json.
"""
import adsk.core, adsk.fusion, importlib, json, math, sys
from pathlib import Path

ROOT = Path('/Users/ab/work/sigram/SigMidi')
OUT = ROOT / 'design/fusion/mirrored'
sys.path.insert(0, str(ROOT / 'scripts'))
import perfboard_layout as pl
importlib.reload(pl)

NAME = 'Carrier perfboard 80.5 x 20 - populated'
CENTRE = (48.75, -15.0)        # board centre in Left main coordinates, mm
BOARD_Z = -21.0                # underside on 1 mm insulating tape over the 2 mm floor
GRID_DRILL = 1.0
GRID_PAD = 1.8
COPPER = 0.05


def run(_context: str):
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    r = d.rootComponent
    mgr = adsk.fusion.TemporaryBRepManager.get()
    union, cut = adsk.fusion.BooleanTypes.UnionBooleanType, adsk.fusion.BooleanTypes.DifferenceBooleanType
    looks = {a.name: a for a in d.appearances}
    main = next(o for o in r.occurrences if o.component.name.startswith('ALT Mirrored MAIN'))
    for o in list(main.component.occurrences):
        if o.component.name.startswith('Carrier perfboard'):
            o.deleteMe()

    def P(x, y, z):
        return adsk.core.Point3D.create(x / 10, y / 10, z / 10)

    def local(bx, by):
        # Board millimetres from its centre to Left main XY; the board is turned 180 degrees.
        return CENTRE[0] - bx, CENTRE[1] + by

    def hole(c, rr):
        return local(*pl.board_xy(c, rr))

    def box(x0, y0, z0, x1, y1, z1):
        obb = adsk.core.OrientedBoundingBox3D.create(P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                                                     adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0),
                                                     abs(x1 - x0) / 10, abs(y1 - y0) / 10, abs(z1 - z0) / 10)
        return mgr.createBox(obb)

    def cyl(a, b, radius):
        return mgr.createCylinderOrCone(P(*a), radius / 10, P(*b), radius / 10)

    def merge(shapes):
        body = shapes[0]
        for s in shapes[1:]:
            assert mgr.booleanOperation(body, s, union)
        return body

    top = BOARD_Z + pl.BOARD_MM[2]
    parts = []

    # Board with drilled holes, and its component-side copper.
    x0, y0 = local(-pl.BOARD_MM[0] / 2, -pl.BOARD_MM[1] / 2)
    x1, y1 = local(pl.BOARD_MM[0] / 2, pl.BOARD_MM[1] / 2)
    board = box(x0, y0, BOARD_Z, x1, y1, top)
    drills = [(hole(c, rr), GRID_DRILL / 2) for c in range(pl.COLS) for rr in range(pl.ROWS)]
    drills += [(local(hx, hy), pl.MOUNT_HOLE_MM / 2) for hx, hy in pl.MOUNT_HOLES_MM]
    for (x, y), radius in drills:
        assert mgr.booleanOperation(board, cyl((x, y, BOARD_Z - 0.1), (x, y, top + 0.1), radius), cut)
    parts.append(('Board 80.5 x 20 x 1.5', board, 'Opaque(207,201,181)'))
    copper = [cyl((x, y, top), (x, y, top + COPPER), GRID_PAD / 2) for c in range(pl.COLS) for rr in range(pl.ROWS)
              for x, y in [hole(c, rr)]]
    for px, py in pl.END_PADS_MM:
        x, y = local(px, py)
        w, h = pl.END_PAD_MM[0] / 2, pl.END_PAD_MM[1] / 2
        copper.append(box(x - w, y - h, top, x + w, y + h, top + COPPER))
    copper = merge(copper)
    for c in range(pl.COLS):
        for rr in range(pl.ROWS):
            x, y = hole(c, rr)
            assert mgr.booleanOperation(copper, cyl((x, y, top - 0.1), (x, y, top + 0.2), GRID_DRILL / 2), cut)
    parts.append(('Copper pads', copper, 'Opaque(199,145,29)'))

    lead_look = 'Opaque(192,192,192)'
    for ref, p in pl.PARTS.items():
        kind = p.get('kind', 'res')
        pins = list(p['pins'].values())
        leads = []

        def wire(path, radius=0.3):
            leads.extend(cyl(a, b, radius) for a, b in zip(path, path[1:]))

        if kind in ('res', 'diode'):
            x, y = hole(*p['pins'][p['body']])
            ox, oy = hole(*next(h for pin, h in p['pins'].items() if pin != p['body']))
            radius, length = (1.35, 5.2) if kind == 'diode' else (1.15, 6.2)
            z0, z1 = top + 0.5, top + 0.5 + length
            if kind == 'diode':
                # The cathode band marks the K end: at the board for a K-body part, on top otherwise.
                band = (z0, z0 + 0.9) if p['body'] == 'K' else (z1 - 0.9, z1)
                for a, b, look, name in ((z0, band[0], 'Opaque(26,26,26)', ref), (band[0], band[1], 'Opaque(228,228,228)', ref + ' band'),
                                         (band[1], z1, 'Opaque(26,26,26)', ref)):
                    if b > a + 1e-6:
                        parts.append((name, cyl((x, y, a), (x, y, b), radius), look))
            else:
                parts.append((ref, cyl((x, y, z0), (x, y, z1), radius), 'Opaque(203,210,239)'))
            wire([(x, y, top), (x, y, z0)])
            wire([(x, y, z1), (x, y, z1 + 0.8), (ox, oy, z1 + 0.8), (ox, oy, top)])
        elif kind == 'elko':
            (xa, ya), (xb, yb) = hole(*p['pins']['1']), hole(*p['pins']['2'])
            x, y = (xa + xb) / 2, (ya + yb) / 2
            parts.append((ref, cyl((x, y, top + 0.3), (x, y, top + 10.8), 3.15), 'Modular pair shell blue'))
            parts.append((ref + ' vent', cyl((x, y, top + 10.8), (x, y, top + 11.0), 3.0), 'Steel - Satin'))
        elif kind == 'cer':
            (xa, ya), (xb, yb) = hole(*pins[0]), hole(*pins[1])
            x, y = (xa + xb) / 2, (ya + yb) / 2
            parts.append((ref, cyl((x - 0.45, y, top + 4.2), (x + 0.45, y, top + 4.2), 2.3), 'Opaque(218,165,32)'))
            for hx, hy in ((xa, ya), (xb, yb)):
                wire([(hx, hy, top), (hx + (x - hx) * 0.5, hy + (y - hy) * 0.5, top + 2.5)], 0.25)
        elif kind == 'dip':
            xs = [hole(c, rr)[0] for c, rr in pins]
            ys = sorted({hole(c, rr)[1] for c, rr in pins})
            xa, xb = min(xs) - 1.6, max(xs) + 1.6
            parts.append(('U4 DIP-14 socket', box(xa, ys[0] - 1.3, top, xb, ys[1] + 1.3, top + 3.0), 'Opaque(51,51,51)'))
            parts.append(('U4 74HCT125', box(xa + 0.4, ys[0] + 0.8, top + 3.6, xb - 0.4, ys[1] - 0.8, top + 6.8), 'Opaque(18,18,18)'))
            pins_body = []
            for c, rr in pins:
                hx, hy = hole(c, rr)
                inner = hy + (0.8 if hy == ys[0] else -0.8)
                pins_body.append(box(hx - 0.25, min(hy, inner), top + 3.0, hx + 0.25, max(hy, inner), top + 5.2))
            parts.append(('U4 pins', merge(pins_body), 'Steel - Satin'))
        if leads:
            parts.append((ref + ' leads', merge(leads), lead_look))

    net_look = {'GND': 'Opaque(26,26,26)', '3V3': 'Opaque(235,0,0)', '+5V': 'Opaque(235,0,0)', '+9V': 'Opaque(235,0,0)',
                'USB_VBUS': 'Opaque(235,0,0)', 'LADDER': 'Opaque(255,255,0)', 'T1': 'Opaque(255,255,0)'}
    for label, net, (c, rr), _ in pl.PADS:
        x, y = hole(c, rr)
        look = net_look.get(net) or ('Opaque(0,128,0)' if net.startswith(('P1_', 'P2_')) else 'Opaque(255,205,126)')
        parts.append(('wire ' + label + ' ' + net, cyl((x, y, top), (x, y, top + 5.0), 0.7), look))

    # Clash check against every other physical Left main body.
    others = []
    for o in main.component.allOccurrences:
        if 'REF ' in o.fullPathName or 'DFRobot' in o.fullPathName:
            continue
        m = o.transform2.copy()
        t, base = m.translation, main.transform2.translation
        t.x -= base.x; t.y -= base.y; t.z -= base.z
        m.translation = t
        for b in o.component.bRepBodies:
            if b.isSolid and b.isLightBulbOn:
                a = mgr.copy(b)
                assert mgr.transform(a, m)
                others.append((o.component.name, b.name, a))
    clashes = []
    for name, a, _ in parts:
        for comp, other, n in others:
            probe = mgr.copy(a)
            if mgr.booleanOperation(probe, mgr.copy(n), adsk.fusion.BooleanTypes.IntersectionBooleanType) and probe.volume > 1e-6:
                clashes.append({'part': name, 'component': comp, 'body': other, 'volume_mm3': round(probe.volume * 1000, 3)})

    occ = main.component.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = NAME
    comp.isOriginFolderLightBulbOn = False
    for name, a, look in parts:
        b = comp.bRepBodies.add(a)
        b.name = name
        b.appearance = looks[look]
    (OUT / 'carrier-perfboard.json').write_text(json.dumps({
        'component': NAME, 'assembly': main.component.name, 'source': 'scripts/perfboard_layout.py',
        'board_mm': list(pl.BOARD_MM), 'pitch_mm': pl.PITCH_MM, 'hole_field': [pl.ROWS, pl.COLS],
        'mounting_holes': {'diameter_mm': pl.MOUNT_HOLE_MM, 'rectangle_mm': [76.0, 16.0]},
        'end_pads': {'size_mm': list(pl.END_PAD_MM), 'per_end': 4},
        'centre_local_mm': list(CENTRE), 'underside_local_Z_mm': BOARD_Z, 'rotation_deg': 180,
        'column_0_faces': 'Nano (+X)', 'bodies': len(parts), 'clashes': clashes}, indent=1) + '\n')
