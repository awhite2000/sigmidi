"""Render the Left main assembly, carrier perfboard included, with the top shell hidden.

Run inside Fusion with the SIGMIDI archive open, after add_carrier_perfboard.py. Bodies
are copied into a temporary component at their world placement, moved clear of the
other assemblies and lifted so the base underside sits on the ground grid, and removed
again after capture; the native components are not changed.
"""
import adsk.core, adsk.fusion, json, math
from pathlib import Path

OUT = Path('/Users/ab/work/sigram/SigMidi/design/fusion/mirrored/main')

LIFT = 24.0                    # base underside at local Z -24 mm
SHIFT_Y = -1000.0              # render away from the other assemblies near the origin
EYE, TARGET = (-330.0, 300.0, 33.0), (135.0, -45.0, 24.0)
ANGLE = 13.0


def run(_context: str):
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    r = d.rootComponent
    mgr = adsk.fusion.TemporaryBRepManager.get()
    main = next(o for o in r.occurrences if o.component.name.startswith('ALT Mirrored MAIN'))
    origin = main.transform2.translation
    vis = [(o, o.isLightBulbOn) for o in r.occurrences]
    old_camera = app.activeViewport.camera
    old_style = app.activeViewport.visualStyle
    work = r.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    tc = work.component
    tc.name = 'TEMP open assembly render'
    report = {'native_bodies': []}

    def lifted(a):
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(0, SHIFT_Y / 10, LIFT / 10)
        assert mgr.transform(a, m)
        return a

    def add(a, name, look):
        b = tc.bRepBodies.add(lifted(a))
        b.name = name
        if look:
            b.appearance = look
        return b

    try:
        # Native bodies, top shell and non-physical references excluded.
        assert any(o.component.name.startswith('Carrier perfboard') for o in main.component.occurrences)
        prefix = main.fullPathName + '+'
        for o in r.allOccurrences:
            path = o.fullPathName
            if not path.startswith(prefix) or any(t in path for t in ('Chassis', 'REF ', 'DFRobot')):
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
                add(a, b.name, b.appearance)
                report['native_bodies'].append(b.name)

        def P(x, y, z):
            return adsk.core.Point3D.create(x / 10, y / 10, z / 10)

        # Camera from the left rear, above the floor and below the upper switch row.
        for o in r.occurrences:
            o.isLightBulbOn = o == work
        app.activeViewport.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
        cam = adsk.core.Camera.create()
        cam.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
        cam.eye = P(EYE[0], EYE[1] + SHIFT_Y, EYE[2])
        cam.target = P(TARGET[0], TARGET[1] + SHIFT_Y, TARGET[2])
        cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
        cam.perspectiveAngle = math.radians(ANGLE)
        cam.viewExtents = 2 * math.dist(EYE, TARGET) / 10 * math.tan(math.radians(ANGLE / 2))
        cam.isFitView = False
        cam.isSmoothTransition = False
        app.activeViewport.camera = cam
        adsk.doEvents()
        app.activeViewport.camera = cam
        adsk.doEvents()
        app.activeViewport.refresh()
        if not app.activeViewport.saveAsImageFile(str(OUT / 'open-assembly.png'), 1800, 760):
            raise RuntimeError('capture failed')
        report.update({'variant': 'Left main, ten switches', 'top_shell': 'hidden', 'eye_mm': EYE, 'target_mm': TARGET,
                       'view_angle_deg': ANGLE, 'eye_target_frame': 'local assembly XY, Z above the base underside', 'image': 'open-assembly.png'})
        (OUT / 'open-assembly.json').write_text(json.dumps(report, indent=1) + '\n')
    finally:
        work.deleteMe()
        for o, v in vis:
            o.isLightBulbOn = v
        app.activeViewport.camera = old_camera
        app.activeViewport.visualStyle = old_style
