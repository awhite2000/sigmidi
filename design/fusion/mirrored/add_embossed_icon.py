"""Join the supplied 25mm icon to the preferred Left main/modular upper shells."""
import adsk.core, adsk.fusion
import json, os, datetime


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    out = '/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/mirrored/'
    assert root.attributes.itemByName('MIDI_MIRROR', 'logical_left_electronics')
    assert not root.attributes.itemByName('SIGMIDI', 'embossed_icon_25mm'), 'Emboss already installed'
    spec = json.load(open(out + '../../branding/sigmidi-mark-cad-25mm.json'))
    mirror = json.loads(root.attributes.itemByName('MIDI_MIRROR', 'logical_left_electronics').value)
    main = next(o.component for o in root.occurrences if o.component.name == mirror['new_main_component'])
    modular = next(o.component for o in root.occurrences if o.component.name == mirror['new_modular_component'])
    upper = next(o.component for o in main.occurrences if o.component.name.startswith('Mirrored 01 '))
    electronics = next(o.component for o in modular.occurrences if o.component.name.startswith('Existing LEFT'))
    targets = [(upper, next(b for b in upper.bRepBodies if 'LEFT' in b.name)),
               (electronics, next(b for b in electronics.bRepBodies if 'SHELL' in b.name))]
    manager = adsk.fusion.TemporaryBRepManager.get()
    boolean = adsk.fusion.BooleanTypes
    document_count = app.documents.count

    def stage(message):
        with open('/tmp/sigmidi-emboss-progress.json', 'w') as stream:
            json.dump({'stage': message}, stream)

    def bounds(body):
        box = body.boundingBox
        return [v * 10 for v in box.minPoint.asArray()] + [v * 10 for v in box.maxPoint.asArray()]

    def volume(body):
        return body.volume * 1000 if body.faces.count else 0

    def operation(first, second, kind):
        assert manager.booleanOperation(first, second, kind), 'Boolean failed'
        return first

    def moved(body, z):
        body = manager.copy(body)
        matrix = adsk.core.Matrix3D.create()
        matrix.translation = adsk.core.Vector3D.create(0, 0, z / 10)
        assert manager.transform(body, matrix)
        return body

    def resized_z(body, low, height):
        body = manager.copy(body)
        box = bounds(body)
        ratio = height / (box[5] - box[2])
        matrix = adsk.core.Matrix3D.create()
        matrix.setCell(2, 2, ratio)
        matrix.translation = adsk.core.Vector3D.create(0, 0, (low - box[2] * ratio) / 10)
        assert manager.transform(body, matrix)
        return body

    def signatures():
        result = []
        def walk(component, path):
            for body in component.bRepBodies:
                if (component == upper and 'LEFT' in body.name) or (component == electronics and 'SHELL' in body.name):
                    continue
                result.append((path, body.name, body.volume, bounds(body)))
            for occ in component.occurrences:
                result.append((path, occ.name, list(occ.transform2.asArray())))
                walk(occ.component, path + '/' + occ.component.name)
        for occ in root.occurrences:
            if not occ.component.name.startswith('TEMP'):
                result.append((occ.name, list(occ.transform2.asArray())))
                walk(occ.component, occ.component.name)
        return result

    before = signatures()
    backup = out + '../archive/pre-sigmidi-25mm-emboss.f3d'
    if not os.path.exists(backup):
        stage('saving native recovery archive')
        assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(backup))
    work = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    temporary = work.component
    temporary.name = 'TEMP SIGMIDI embossed icon tooling'
    work.isLightBulbOn = False
    checks = []
    try:
        stage('building the supplied icon outline with its interior opening')
        wires = []
        for loop in spec['loops_mm']:
            points = [adsk.core.Point3D.create(x / 10, y / 10, 0) for x, y in loop]
            curves = [adsk.core.Line3D.create(points[i], points[(i + 1) % len(points)]) for i in range(len(points))]
            wire, edge_map = manager.createWireFromCurves(curves)
            assert wire and wire.wires.count == 1
            wires.append(wire)
        face_body = manager.createFaceFromPlanarWires(wires)
        assert face_body and face_body.faces.count == 1
        assert face_body.faces.item(0).loops.count == 2, 'Original negative-space opening must remain'
        native_face = temporary.bRepBodies.add(face_body)
        feature = temporary.features.extrudeFeatures.addSimple(
            native_face.faces.item(0), adsk.core.ValueInput.createByReal(.065),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        tool = manager.copy(feature.bodies.item(0))
        tool = moved(tool, 29.95 - bounds(tool)[2])
        size = bounds(tool)
        assert abs(size[3] - size[0] - 25) < 1e-5
        assert abs(size[4] - size[1] - spec['height_mm']) < 1e-5
        assert abs(size[5] - 30.6) < 1e-5
        added_tools = []
        candidates = []
        for component, old in targets:
            stage('verifying full 3mm roof backing and connected union: ' + component.name)
            backing = resized_z(tool, 27, 3)
            missing = operation(backing, manager.copy(old), boolean.DifferenceBooleanType)
            assert volume(missing) < .001, ('Icon is not fully supported by the flat roof', volume(missing))
            candidate = operation(manager.copy(old), manager.copy(tool), boolean.UnionBooleanType)
            assert candidate.isSolid and candidate.lumps.count == 1
            removed = operation(manager.copy(old), manager.copy(candidate), boolean.DifferenceBooleanType)
            assert volume(removed) < .001
            added = operation(manager.copy(candidate), manager.copy(old), boolean.DifferenceBooleanType)
            assert volume(added) > 1
            assert abs(volume(added) - volume(tool) * .6 / .65) < .01
            added_tools.append(added)
            candidates.append((component, old, candidate))
            checks.append({'component': component.name, 'icon_bounds_mm': bounds(added),
                           'added_volume_mm3': volume(added), 'removed_volume_mm3': volume(removed),
                           'missing_roof_backing_mm3': volume(missing), 'solid': candidate.isSolid,
                           'connected_lumps': candidate.lumps.count})
        # Native main hardware is already rigidly positioned in assembly-local coordinates.
        stage('checking the new external material against every fitted main component')
        collisions = []
        closest_bbox = None
        a = added_tools[0]
        ab = bounds(a)
        for occurrence in main.occurrences:
            component = occurrence.component
            if component == upper or 'REF' in component.name:
                continue
            for body in component.bRepBodies:
                shape = manager.copy(body)
                assert manager.transform(shape, occurrence.transform2)
                bb = bounds(shape)
                gaps = [max(0, bb[i] - ab[i + 3], ab[i] - bb[i + 3]) for i in range(3)]
                lower_bound = sum(g * g for g in gaps) ** .5
                if closest_bbox is None or lower_bound < closest_bbox['lower_bound_mm']:
                    closest_bbox = {'component': component.name, 'body': body.name, 'lower_bound_mm': lower_bound}
                if lower_bound > .001:
                    continue
                intersection = operation(manager.copy(a), shape, boolean.IntersectionBooleanType)
                if volume(intersection) > .001:
                    collisions.append({'component': component.name, 'body': body.name, 'volume_mm3': volume(intersection)})
        assert not collisions, collisions
        assert closest_bbox['lower_bound_mm'] >= 2.999, closest_bbox
        stage('committing only the two interchangeable Left electronics upper shells')
        for component, old, candidate in candidates:
            name, appearance = old.name, old.appearance
            replacement = component.bRepBodies.add(candidate)
            replacement.name = name + ' - SIGMIDI icon 25mm raised 0.6mm'
            replacement.appearance = appearance
            old.deleteMe()
        # Changes to target names are intentionally omitted from the unrelated-geometry audit.
    finally:
        work.deleteMe()
    assert signatures() == before, 'Unrelated component or placement changed'
    assert app.documents.count == document_count
    result = {'revision': 'sigmidi_embossed_icon_25mm', 'version': '0.1',
              'width_mm': 25, 'height_mm': spec['height_mm'], 'raised_height_mm': .6,
              'center_XY_mm': [75.1, -18], 'roof_Z_mm': 30,
              'switch_A_X_mm': 42.6, 'switch_B_X_mm': 107.6,
              'flat_roof_backing_mm': 3, 'geometry_source': '../../branding/sigmidi-mark-cad-25mm.json',
              'top_view_shape_reflected': False, 'checks': checks, 'hardware_collisions': collisions,
              'minimum_hardware_AABB_distance': closest_bbox, 'unrelated_geometry_and_placements_unchanged': True,
              'main_and_modular_updated': True, 'original_Right_models_unchanged': True,
              'native_backup': '../archive/pre-sigmidi-25mm-emboss.f3d',
              'UTC': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    root.attributes.add('SIGMIDI', 'embossed_icon_25mm', json.dumps(result))
    stage('saving native document')
    assert app.activeDocument.save('SIGMIDI v0.1: supplied 25mm raised icon between A and B, preferred Left main and modular upper shells')
    result['document'] = app.activeDocument.name
    result['saved'] = app.activeDocument.isSaved
    with open(out + 'embossed-icon-25mm.json', 'w') as stream:
        json.dump(result, stream, indent=2)
    stage('emboss committed and verified')
