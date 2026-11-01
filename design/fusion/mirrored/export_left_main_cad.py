"""Export the Left main assembly, carrier perfboard included, as F3D and STEP.

Run inside Fusion with the SIGMIDI archive open. Physical bodies are copied at their
assembly placement into a temporary component, exported to
main/midi-foot-mirrored-main.f3d/.step, checked for a complete STEP solid count (one
per body lump) and removed again. The Left main entries in cad-export.json and emboss-complete-cad.json
are updated.
"""
import adsk.core, adsk.fusion, json
from pathlib import Path

P = Path('/Users/ab/work/sigram/SigMidi/design/fusion')
NAME = 'mirrored/main/midi-foot-mirrored-main'


def run(_context: str):
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    r = d.rootComponent
    mgr = adsk.fusion.TemporaryBRepManager.get()
    main = next(o for o in r.occurrences if o.component.name.startswith('ALT Mirrored MAIN'))
    assert any(o.component.name.startswith('Carrier perfboard') for o in main.component.occurrences)
    origin = main.transform2.translation
    work = r.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    tc = work.component
    tc.name = 'TEMP Left main CAD export'
    tc.isOriginFolderLightBulbOn = False
    try:
        prefix = main.fullPathName + '+'
        for o in r.allOccurrences:
            path = o.fullPathName
            if not path.startswith(prefix) or any(t in path for t in ('REF ', 'DFRobot')):
                continue
            m = o.transform2.copy()
            t = m.translation
            t.x -= origin.x; t.y -= origin.y; t.z -= origin.z
            m.translation = t
            for b in o.component.bRepBodies:
                if not b.isSolid or not b.isLightBulbOn or b.name.startswith('DFR1075 M1.6'):
                    continue
                a = mgr.copy(b)
                assert mgr.transform(a, m)
                n = tc.bRepBodies.add(a)
                n.name = b.name
                if b.appearance:
                    n.appearance = b.appearance
        f3d, step = P / (NAME + '.f3d'), P / (NAME + '.step')
        assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(f3d), tc))
        assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(str(step), tc))
        # STEP writes one solid per lump; merged perfboard bodies carry several lumps.
        expected = sum(b.lumps.count for b in tc.bRepBodies)
        bodies = tc.bRepBodies.count
        raw = step.read_text()
        solids = raw.count('MANIFOLD_SOLID_BREP(') + raw.count('BREP_WITH_VOIDS(')
        assert solids == expected, (solids, expected)
    finally:
        work.deleteMe()
    entry = {'file': NAME, 'native_bodies': bodies, 'native_solids': expected, 'STEP_solids': solids, 'complete': True,
             'physical_hardware_only': True}
    for path in (P / 'cad-export.json', P / 'mirrored/emboss-complete-cad.json'):
        report = json.loads(path.read_text())
        report['CAD'] = [entry if item['file'] == NAME else item for item in report['CAD']]
        path.write_text(json.dumps(report, indent=2) + '\n')
