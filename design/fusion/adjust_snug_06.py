"""Tighten printed mating interfaces for a calibrated 0.6mm PETG process."""
import adsk.core, adsk.fusion, json, math


def run(_context):
    app=adsk.core.Application.get();design=adsk.fusion.Design.cast(app.activeProduct);root=design.rootComponent
    assert app.activeDocument.name.startswith('MIDI Foot Controller - VERIFIED')
    assert root.attributes.itemByName('MIDI_FDM','refined_positioning_ribs')
    assert not root.attributes.itemByName('MIDI_FDM','snug_06_tolerances'),'Already applied'
    out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
    mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes;cache={}
    for o in list(root.occurrences):
        if o.component.name=='TEMP snug 0.6mm mating surfaces':o.deleteMe()
    main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
    uc=next(c for c in main if c.name.startswith('01 '));bc=next(c for c in main if c.name.startswith('02 '))
    alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
    pair=next(o.component for o in alt.occurrences if o.component.name.startswith('Repeatable pair'))
    left=next(o.component for o in alt.occurrences if o.component.name.startswith('Leftmost pair'))
    ec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'))
    cc=next(o.component for o in alt.occurrences if o.component.name.startswith('Closed left cap'))
    library=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Engraved pair'))
    def get(c,s):return next(b for b in c.bRepBodies if s in b.name)
    sl,sr=get(uc,'LEFT'),get(uc,'RIGHT');bl,br=get(bc,'LEFT'),get(bc,'RIGHT')
    fixed=[(o.fullPathName,list(o.transform2.asArray()),[(b.name,b.entityToken,b.volume) for b in o.component.bRepBodies]) for o in root.allOccurrences if o.component not in [uc,bc,pair,left,ec] and o.component not in [o.component for o in library.occurrences]]
    def stage(s):
        with open('/tmp/snug-06-progress.json','w') as f:json.dump({'stage':s},f)
    def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
    def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
    def op(a,b,k):
        assert mgr.booleanOperation(a,b,k),'BRep Boolean failed';return a
    def union(a,b):return op(a,mgr.copy(b),bt.UnionBooleanType)
    def cut(a,b):return op(a,mgr.copy(b),bt.DifferenceBooleanType)
    def inter(a,b):return op(a,mgr.copy(b),bt.IntersectionBooleanType)
    def volume(a):return a.volume*1000 if a.faces.count else 0
    def bounds(a):
        if id(a) not in cache:cache[id(a)]=(a,a.boundingBox)
        return cache[id(a)][1]
    def collision(a,b):
        q,r=bounds(a),bounds(b)
        if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
        return volume(inter(mgr.copy(a),b))
    def move(a,dx=0,dy=0,dz=0):
        matrix=adsk.core.Matrix3D.create();matrix.translation=adsk.core.Vector3D.create(dx/10,-dy/10,dz/10);assert mgr.transform(a,matrix);return a
    stage('building exact 0.20mm normal-clearance receiving surfaces')
    work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());temp=work.component;temp.name='TEMP snug 0.6mm mating surfaces'
    cu_y = 32 - 5*math.tan(math.radians(40)) + 8
    cl = (32 + 30/math.tan(math.radians(80)) + 2*math.tan(math.radians(40)) + 8, 2)
    tangent40 = math.tan(math.radians(40))
    seam = 193.65
    gap = .25
    bottom = -19.5
    floor_clearance = math.sqrt(2)*.30
    # Keep all profile edge counts consistent for exact ruled lofts. Eroded
    # convex corners retain R0.4 instead of collapsing to a knife edge.
    def profile(x, s, stop=bottom):
        r = max(.4, 2-s)
        rear = (2+s+r, 27-s-r)
        vertex = (cu_y + (2-s)*tangent40, 27-s)
        upper = (vertex[0]-r*tangent40, vertex[1]-r)
        front = (90-s-r, -3-s-r)
        plane_input = temp.constructionPlanes.createInput()
        plane_input.setByOffset(temp.yZConstructionPlane, adsk.core.ValueInput.createByString(f'{x} mm'))
        plane = temp.constructionPlanes.add(plane_input)
        sketch = temp.sketches.add(plane)
        def sp(q): return sketch.modelToSketchSpace(p(x, q[0], q[1]))
        def radial(center, radius, angle):
            a = math.radians(angle)
            return (center[0]+radius*math.cos(a), center[1]+radius*math.sin(a))
        def line(a, b):
            if math.dist(a, b) > 1e-8:
                sketch.sketchCurves.sketchLines.addByTwoPoints(sp(a), sp(b))
        def arc(center, radius, a, b):
            sketch.sketchCurves.sketchArcs.addByThreePoints(
                sp(radial(center, radius, a)), sp(radial(center, radius, (a+b)/2)), sp(radial(center, radius, b)))
        start = (2+s, stop)
        line(start, radial(rear, r, 180))
        arc(rear, r, 180, 90)
        line(radial(rear, r, 90), radial(upper, r, 90))
        arc(upper, r, 90, 10)
        line(radial(upper, r, 10), radial(cl, 5+s, 190))
        arc(cl, 5+s, 190, 270)
        line(radial(cl, 5+s, 270), radial(front, r, 90))
        arc(front, r, 90, 0)
        line(radial(front, r, 0), (90-s, stop))
        line((90-s, stop), start)
        if sketch.profiles.count != 1:
            raise RuntimeError(f'Profile not closed at X{x}, inset {s}')
        return sketch.profiles.item(0)

    def loft(sections, stop=bottom):
        inp = temp.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        for x, inset in sections:
            inp.loftSections.add(profile(x, inset, stop))
        inp.isSolid = True
        feature = temp.features.loftFeatures.add(inp)
        # In direct mode feature.bodies may include previously made bodies.
        return mgr.copy(temp.bRepBodies.item(temp.bRepBodies.count-1))

    def linear_loft(x0, s0, x1, s1, stop=bottom):
        sections = [(x0, s0)]
        if min(s0, s1) < 1.6 < max(s0, s1):
            t = (1.6-s0)/(s1-s0)
            sections.append((x0+t*(x1-x0), 1.6))
        sections.append((x1, s1))
        return loft(sections, stop)

    def band(x0, x1, floor0, floor1, inner0, inner1):
        outside = linear_loft(x0, floor0, x1, floor1)
        inside = linear_loft(x0, inner0, x1, inner1)
        return cut(outside, inside)

    old_floor=math.sqrt(2)*.30;new_floor=math.sqrt(2)*.20
    receiver_addition=band(seam-4,seam-2,new_floor,new_floor,old_floor,old_floor)
    receiver_addition=union(receiver_addition,band(seam-2,seam+gap,new_floor,new_floor+2+gap,old_floor,old_floor+2+gap))
    # Preserve the cap-specific side-entry sweep when tightening its receiver.
    cap_receiver_addition=move(mgr.copy(receiver_addition),dx=-65)
    envelope=box(124.60,-1,-24.05,128.65,93,30.05)
    native_cap=temp.bRepBodies.add(mgr.copy(cc.bRepBodies.item(0)))
    tip_faces=[f for f in native_cap.faces if abs(f.boundingBox.minPoint.x-12.865)<1e-7 and abs(f.boundingBox.maxPoint.x-12.865)<1e-7]
    assert tip_faces,'Missing cap bevel end face'
    entry_tools=[]
    for face in tip_faces:
        n=temp.bRepBodies.count
        temp.features.extrudeFeatures.addSimple(face,adsk.core.ValueInput.createByString('-4.3 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        for j in range(n,temp.bRepBodies.count):entry_tools.append(mgr.copy(temp.bRepBodies.item(j)))
    for tool in entry_tools:
        for dy,dz in [(0,0),(-.15,0),(.15,0),(0,-.15),(0,.15)]:
            shape=inter(move(mgr.copy(tool),dy=dy,dz=2+dz),envelope)
            if shape.faces.count:cap_receiver_addition=cut(cap_receiver_addition,shape)
    # Tiny local cap-corner blends also project into the generic profile.
    # Trim only new material; preserve all original receiver material/clearances.
    cap_core=inter(mgr.copy(cc.bRepBodies.item(0)),box(124.4,-1,-25,129,93,31))
    for dz0 in [0,.5,1,1.5,2]:
        for dy,dz in [(0,0),(-.2,0),(.2,0),(0,-.2),(0,.2)]:
            cap_receiver_addition=cut(cap_receiver_addition,move(mgr.copy(cap_core),dy=dy,dz=dz0+dz))
    upper_specs=[('main-right',uc,sr,0),('pair-shell',pair,get(pair,'SHELL'),-65),('pair-shell-at-cap',left,get(left,'SHELL'),-65)]
    upper_specs += [(o.component.name,o.component,o.component.bRepBodies.item(0),-65) for o in library.occurrences]
    changes=[];candidates={};rows=[]
    for name,c,b,dx in upper_specs:
        a=union(mgr.copy(b),mgr.copy(cap_receiver_addition) if 'at-cap' in name else move(mgr.copy(receiver_addition),dx=dx))
        added=cut(mgr.copy(a),b);removed=cut(mgr.copy(b),a)
        assert volume(removed)<.001 and a.isSolid and a.lumps.count==1,(name,'upper receiver disconnected')
        q0,q1=b.boundingBox,a.boundingBox
        assert max(abs(getattr(q0.minPoint,k)-getattr(q1.minPoint,k)) for k in 'xyz')<1e-7
        assert max(abs(getattr(q0.maxPoint,k)-getattr(q1.maxPoint,k)) for k in 'xyz')<1e-7
        # Verify the actual ruled loft at the upper deck, including points on
        # either side. Fusion may represent a flat loft face as a NURBS surface.
        x=seam+dx-1;z=26-new_floor
        boundary=a.pointContainment(p(x,15,z))
        inside=a.pointContainment(p(x,15,z-.01))
        outside=a.pointContainment(p(x,15,z+.01))
        assert boundary==adsk.fusion.PointContainment.PointOnPointContainment,(name,'bevel boundary',boundary)
        assert inside==adsk.fusion.PointContainment.PointInsidePointContainment,(name,'inside',inside)
        assert outside==adsk.fusion.PointContainment.PointOutsidePointContainment,(name,'outside',outside)
        expected=seam+dx+25-new_floor
        changes.append((name,c,b,a,added));candidates[name]=a
        rows.append({'part':name,'interface':'receiving hook','added_mm3':volume(added),'removed_mm3':volume(removed),'inclined_clearance_normal_mm':.2,'verified_plane_constant_mm':expected,'boundary_point_native_XYZ_mm':[x,15,z]})
    stage('shifting 1.8mm locating ribs outward by 0.15mm')
    rib_specs=[('base-left',bc,bl,[('rear',20,100),('rear',137,157),('front',48,83),('front',140,175),('left',20,55)]),
               ('base-right',bc,br,[('rear',203,236.799886096949),('rear',264.699886096949,325),('front',203,315),('right',20,55)]),
               ('pair-base',pair,get(pair,'BASE'),[(side,x0,x1) for side in ['rear','front'] for x0,x1 in [(138,149.15),(169,186)]])]
    for name,c,b,ribs in rib_specs:
        a=mgr.copy(b)
        for side,v0,v1 in ribs:
            if side in ['front','rear']:
                y0,y1=(87.85,89.65) if side=='front' else (2.35,4.15)
                mask=box(v0,y0,-22,v1,y1,-18.99);dx=0;dy=.15 if side=='front' else -.15
            else:
                x0,x1=(2.35,4.15) if side=='left' else (345.85,347.65)
                mask=box(x0,v0,-22,x1,v1,-18.99);dx=-.15 if side=='left' else .15;dy=0
            rib=inter(mgr.copy(b),mask);assert volume(rib)>1,(name,side,v0,v1)
            a=cut(a,mask);a=union(a,move(rib,dx=dx,dy=dy))
        assert a.isSolid and a.lumps.count==1,(name,'base disconnected')
        added=cut(mgr.copy(a),b);removed=cut(mgr.copy(b),a)
        assert collision(added,box(-1,-1,-25,351,93,-22))<.001
        assert collision(removed,box(-1,-1,-25,351,93,-22))<.001
        changes.append((name,c,b,a,added));candidates[name]=a
        rows.append({'part':name,'interface':'locating ribs','shift_towards_wall_mm':.15,'rib_thickness_mm':1.8,'nominal_wall_clearance_mm':.2,'added_mm3':volume(added),'removed_mm3':volume(removed),'rib_runs':ribs})
    stage('checking hardware, wiring, installed shells and floors')
    hits=[];wires=[];paths=[]
    for name,c,b,a,added in changes:
        for other in main:
            if other in [uc,bc]:continue
            for body in other.bRepBodies:
                amount=collision(added,body)
                if amount>.001:(wires if other.name.startswith('REF') else hits).append([name,other.name,body.name,amount])
    # Installed main and chainable assemblies, including universal floor/cap interfaces.
    main_u=[sl,candidates['main-right']];main_b=[candidates['base-left'],candidates['base-right']]
    mod_u=[move(mgr.copy(candidates['pair-shell-at-cap']),dx=-65),candidates['pair-shell'],candidates['main-right'],move(mgr.copy(cc.bRepBodies.item(0)),dx=-65)]
    mod_b=[move(mgr.copy(candidates['pair-base']),dx=-65),candidates['pair-base'],candidates['base-right']]
    for group,us,bs in [('main',main_u,main_b),('modular',mod_u,mod_b)]:
        for i,a in enumerate(us+bs):
            for j,b in enumerate((us+bs)[i+1:],i+1):
                amount=collision(a,b)
                if amount>.001:hits.append([group,i,j,amount])
        for z in [0,-.01,-.1,-.2,-.3,-.5,-1,-2,-3,-5,-10,-20]:
            for i,b in enumerate(bs):
                moving=move(mgr.copy(b),dz=z)
                for j,u in enumerate(us):
                    amount=collision(moving,u)
                    if amount>.001:paths.append([group,'floor withdrawal',i,j,z,amount])
    stage('checking sliding upper joints and cap side entry')
    joins=[('main',sl,candidates['main-right']),('pair/electronics',candidates['pair-shell'],candidates['main-right']),('pair/pair',move(mgr.copy(candidates['pair-shell']),dx=-65),candidates['pair-shell'])]
    for label,a,b in joins:
        # Only overlapping X slabs can intersect in a vertical (-Z) assembly.
        # Cropping to that slab keeps the exact geometry and avoids evaluating
        # unrelated engraved roofs at every step of the swept fit check.
        qa,qb=bounds(a),bounds(b);x0=max(qa.minPoint.x,qb.minPoint.x)*10-.001;x1=min(qa.maxPoint.x,qb.maxPoint.x)*10+.001
        mask=box(x0,-1,-25,x1,93,31);aa=inter(mgr.copy(a),mask);bb=inter(mgr.copy(b),mask)
        for i in range(121):
            amount=collision(move(mgr.copy(aa),dz=i*.5),bb)
            if amount>.001:paths.append([label,'vertical slide',i*.5,amount])
    cap=inter(mgr.copy(cc.bRepBodies.item(0)),box(124.4,-1,-25,129,93,31))
    for name in ['pair-shell-at-cap','pair-shell-at-cap-C','pair-shell-at-cap-E']:
        b=inter(mgr.copy(candidates[name]),box(124.59,-1,-25,128.651,93,31))
        for i in range(81):
            dx=-20+i*.25;amount=collision(move(mgr.copy(cap),dx=dx,dz=2),b)
            if amount>.001:paths.append([name,'cap side entry',dx,amount])
        for i in range(21):
            dz=i*.1;amount=collision(move(mgr.copy(cap),dz=dz),b)
            if amount>.001:paths.append([name,'cap seating',dz,amount])
    report={'revision':'snug_06_tolerances','nozzle_mm':.6,'material':'PETG','printer':'Prusa MK3S+','layer_mm':.3,'old_hook_clearance_normal_mm':.3,'hook_clearance_normal_mm':.2,'old_locator_wall_clearance_mm':.35,'locator_wall_clearance_mm':.2,'locator_rib_thickness_mm':1.8,'locator_top_lead_in_mm':.5,'outer_seam_gap_mm':.25,'cap_floor_butt_clearance_mm':.3,'base_M2_clearance_diameter_mm':2.6,'M2_pilot_diameter_mm':1.9,'hardware_holes_unchanged':True,'all_upper_exterior_surfaces_and_component_positions_unchanged':True,'all_floor_mounts_vents_and_glue_lips_unchanged':True,'cap_side_entry_relief_retained':True,'all_changed_parts_single_connected_solids':True,'parts':rows,'physical_collisions':hits,'wire_collisions':wires,'assembly_collisions':paths,'joint_vertical_samples':121,'cap_side_entry_samples':81,'cap_seating_samples':21,'backup':'archive/pre-snug-06-tolerances.zip','physical_fit_status':'Nominal snug sliding fit; requires printing the matching coupons with the actual filament/flow/first-layer settings. Nozzle diameter alone does not guarantee dimensional accuracy.','basis':'https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135'}
    with open(out+'snug-06-tolerances-candidate.json','w') as f:json.dump(report,f,indent=2)
    assert not any([hits,wires,paths]),[hits,wires,paths]
    # Byte-exact reusable native geometry for the modular electronics and pair floors.
    changes.extend([('modular-electronics-shell',ec,get(ec,'SHELL'),candidates['main-right'],None),('modular-electronics-base',ec,get(ec,'BASE'),candidates['base-right'],None),('pair-at-cap-base',left,get(left,'BASE'),candidates['pair-base'],None)])
    stage('committing checked mating surfaces')
    work.deleteMe()
    for name,c,b,a,added in changes:
        oldname=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(a));n.name=oldname+' - snug 0.6mm fit'
        if appearance:n.appearance=appearance
    after=[(o.fullPathName,list(o.transform2.asArray()),[(b.name,b.entityToken,b.volume) for b in o.component.bRepBodies]) for o in root.allOccurrences if o.component not in [uc,bc,pair,left,ec] and o.component not in [o.component for o in library.occurrences]]
    assert fixed==after,'Fixed components changed'
    for c in [root,alt]:c.attributes.add('MIDI_FDM','snug_06_tolerances',json.dumps(report))
    with open(out+'snug-06-tolerances.json','w') as f:json.dump(report,f,indent=2)
    with open(out+'modular/modular-design.json') as f:mod=json.load(f)
    mod.update({'main_revision':'snug_06_tolerances','nozzle_mm':.6,'hook_clearance_normal_mm':.2,'locator_wall_clearance_mm':.2,'fit_report':'../snug-06-tolerances.json'})
    with open(out+'modular/modular-design.json','w') as f:json.dump(mod,f,indent=2)
    alt.attributes.add('MIDI_MODULAR','configuration',json.dumps(mod))
    assert app.activeDocument.save('Tightened sliding hook faces to 0.20mm normal clearance and base locating ribs to 0.20mm wall clearance for calibrated 0.6mm PETG prints; retained 1.8mm rib thickness, glue seams, screws and all hardware poses.')
    stage('complete')
