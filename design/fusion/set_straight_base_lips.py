"""Replace all floor dovetails with straight reinforced butt-glue seams."""
import adsk.core
import adsk.fusion
import json


def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
    if root.attributes.itemByName('MIDI_FDM','straight_base_glue_lips'):raise RuntimeError('Straight base lips already applied')
    ao=next(o for o in root.occurrences if o.component.name.startswith('ALT Chainable'));alt=ao.component
    main=[o for o in root.occurrences if o!=ao and not o.component.name.startswith(('TEMP','Temporary'))]
    def find(prefix):return next(o.component for o in main if o.component.name.startswith(prefix))
    uc,bc=find('01 '),find('02 ')
    pair=next(o.component for o in alt.occurrences if o.component.name.startswith('Repeatable pair'))
    left=next(o.component for o in alt.occurrences if o.component.name.startswith('Leftmost pair'))
    elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'))
    cap=next(o.component for o in alt.occurrences if o.component.name.startswith('Closed left cap'))
    def get(c,s):return next(b for b in c.bRepBodies if s in b.name)
    specs=[('main-left',bc,get(bc,'LEFT'),0,193.65,[('right',193.65)]),
           ('main-right',bc,get(bc,'RIGHT'),193.9,350,[('left',193.9)]),
           ('pair',pair,get(pair,'BASE'),128.9,193.65,[('left',128.9),('right',193.65)]),
           ('pair-at-cap',left,get(left,'BASE'),128.9,193.65,[('left',128.9),('right',193.65)]),
           ('electronics',elec,get(elec,'BASE'),193.9,350,[('left',193.9)])]
    changed=[r[2] for r in specs]
    def unaffected():
        return [(o.fullPathName,list(o.transform2.asArray()),[(b.name,b.entityToken,list(b.boundingBox.minPoint.asArray()),list(b.boundingBox.maxPoint.asArray())) for b in o.component.bRepBodies if b not in changed]) for o in root.allOccurrences if not o.component.name.startswith('TEMP')]
    before=unaffected()
    mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
    def stage(s):
        with open('/tmp/straight-base-progress.json','w') as f:json.dump({'stage':s},f)
    def write(n,v):
        with open(out+n,'w') as f:json.dump(v,f,indent=2)
    def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
    def box(x0,y0,z0,x1,y1,z1):
        return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
    def move(a,dx=0,dz=0):
        m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,0,dz/10);mgr.transform(a,m);return a
    def op(a,b,k):
        if not mgr.booleanOperation(a,b,k):raise RuntimeError('BRep Boolean failed')
        return a
    def union(a,b):return op(a,b,bt.UnionBooleanType)
    def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
    def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
    def vol(a):return a.volume*1000 if a.faces.count else 0
    def collision(a,b):
        aa,bb=a.boundingBox,b.boundingBox
        if any(min(getattr(aa.maxPoint,k),getattr(bb.maxPoint,k))-max(getattr(aa.minPoint,k),getattr(bb.minPoint,k))<1e-7 for k in 'xyz'):return 0
        return vol(inter(mgr.copy(a),mgr.copy(b)))
    work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component;tc.name='TEMP straight base lip construction'
    def lip(side,x):
        x0,x1=(x,x+2) if side=='left' else (x-2,x)
        pts=[(x0,-22.02),(x1,-22.02),(x1,-22 if side=='left' else -20),(x0,-20 if side=='left' else -22)]
        sk=tc.sketches.add(tc.xZConstructionPlane)
        for a,b in zip(pts,pts[1:]+pts[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(p(a[0],0,a[1])),sk.modelToSketchSpace(p(b[0],0,b[1])))
        tc.features.extrudeFeatures.addSimple(sk.profiles.item(0),adsk.core.ValueInput.createByString('87.3 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        a=mgr.copy(tc.bRepBodies.item(tc.bRepBodies.count-1));q=a.boundingBox
        m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,-8.965-q.minPoint.y,0);mgr.transform(a,m);return a
    stage('building straight floor edges and continuous glue lands')
    candidates={};parts=[]
    for label,c,old,xmin,xmax,ends in specs:
        a=inter(mgr.copy(old),box(xmin,-1,-25,xmax,93,1))
        for side,x in ends:
            x0,x1=(x,x+6.5) if side=='left' else (x-6.5,x)
            a=union(a,box(x0,0,-24,x1,92,-22))
            # Replace the old interrupted lands without touching the posts.
            l0,l1=(x,x+2.001) if side=='left' else (x-2.001,x)
            a=cut(a,box(l0,2.35,-22,l1,89.65,-19.9))
            a=union(a,lip(side,x))
        if label=='pair-at-cap':
            difference=vol(cut(mgr.copy(a),mgr.copy(candidates['pair'])))+vol(cut(mgr.copy(candidates['pair']),mgr.copy(a)))
            if difference>.001:raise RuntimeError('Pair base differs beyond the old dovetails: '+str(difference))
            a=mgr.copy(candidates['pair'])
        if label=='electronics':a=mgr.copy(candidates['main-right'])
        if not a.isSolid or a.lumps.count!=1:raise RuntimeError('Disconnected '+label)
        candidates[label]=a
        parts.append({'part':label,'solid':True,'lumps':1,'volume_mm3':vol(a),'structural_X_mm':[xmin,xmax],'glue_sides':ends})
    stage('checking installed solids and hardware')
    mu=list(uc.bRepBodies);mb=[candidates['main-left'],candidates['main-right']]
    au=[move(mgr.copy(get(left,'SHELL')),dx=-65),get(pair,'SHELL'),get(elec,'SHELL')]
    ab=[move(mgr.copy(candidates['pair']),dx=-65),candidates['pair'],candidates['electronics']]
    ac=move(mgr.copy(next(iter(cap.bRepBodies))),dx=-65)
    hits=[]
    for group,shapes in [('main',mu+mb),('modular',au+ab+[ac])]:
        for i,a in enumerate(shapes):
            for j,b in enumerate(shapes[i+1:],i+1):
                v=collision(a,b)
                if v>.001:hits.append([group,i,j,v])
    def hardware(c):
        result=[]
        for o in c.occurrences:
            if o.component.name.startswith('REF'):continue
            for b in o.component.bRepBodies:
                a=mgr.copy(b);mgr.transform(a,o.transform2);result.append((o.component.name,b.name,a))
        return result
    hw=[(o.component.name,b.name,b) for o in main if o.component not in [uc,bc] and not o.component.name.startswith('REF') for b in o.component.bRepBodies]
    for label,c,old,*_ in specs:
        added=cut(mgr.copy(candidates[label]),mgr.copy(old))
        for cname,bname,b in (hw if label.startswith('main-') else hardware(c)):
            v=collision(added,b)
            if v>.001:hits.append([label,cname,bname,v])
    wiring=next(o.component for o in alt.occurrences if o.component.name.startswith('REF modular LED'))
    wires=[]
    for w in wiring.bRepBodies:
        for i,b in enumerate(ab):
            v=collision(w,b)
            if v>.001:wires.append([w.name,i,v])
    stage('checking removable floors and straight seam approach')
    paths=[]
    for name,uppers,bottoms in [('main',mu,mb),('modular',au+[ac],ab)]:
        for z in range(-20,1):
            for bi,b in enumerate(bottoms):
                for ui,u in enumerate(uppers):
                    v=collision(move(mgr.copy(b),dz=z),u)
                    if v>.001:paths.append([name,'base insertion',bi,ui,z,v])
    for name,l,r in [('main',mb[0],mb[1]),('repeat/electronics',ab[1],ab[2]),('repeat/repeat',ab[0],ab[1])]:
        for i in range(41):
            dx=-20+i*.5;v=collision(move(mgr.copy(l),dx=dx),r)
            if v>.001:paths.append([name,'straight approach',dx,v])
    report={'revision':'straight_base_glue_lips','base_dovetails':False,'base_floor_thickness_mm':2,'lip_height_above_floor_mm':2,'lip_inward_width_mm':2,
        'lip_runout_degrees':45,'lip_Y_mm':[2.35,89.65],'main_seam_X_mm':[193.65,193.9],'repeat_span_X_mm':[128.9,193.65],
        'nominal_seam_gap_mm':.25,'cap_floor_gap_mm':.30,'same_pair_base_for_all_positions':True,'pair_base_print_size_mm':[64.75,92,21],
        'glue_joint':'Straight vertical butt faces with continuous raised internal lands on each side; no interlocking projections or recesses.',
        'cap_interface':'Universal pair base fits the cap butt seam; leave the cap-to-removable-floor seam free of glue. Cap remains integral with upper chain.',
        'upper_shells_and_all_hardware_unchanged':True,'screw_mounts_unchanged':True,'bearing_base_outline_retained':True,
        'physical_collisions':hits,'wire_collisions':wires,'assembly_collisions':paths,'base_insertion_samples':21,'horizontal_approach_samples':41,'parts':parts,
        'backup':'archive/pre-straight-base-lips.zip','limits':'Geometric solids and sampled paths; printed fit and adhesive strength require physical validation.'}
    write('straight-base-lips-candidate.json',report)
    if hits or wires or paths:raise RuntimeError('Straight glue lip checks failed; see candidate report')
    # Remove construction before comparing untouched components.
    work.deleteMe()
    for label,c,old,*_ in specs:
        appearance=old.appearance
        name=('Base LEFT' if label=='main-left' else 'Base RIGHT')+' - straight glue lip - full bearing perimeter' if label.startswith('main-') else ('PAIR BASE - universal - two M2x6 - straight glue lips' if label.startswith('pair') else 'REUSED RIGHT BASE - straight glue lip - matches main')
        old.deleteMe();b=c.bRepBodies.add(mgr.copy(candidates[label]));b.name=name;b.appearance=appearance
        changed.append(b)
    if unaffected()!=before:raise RuntimeError('Upper shell or hardware changed')
    root.attributes.add('MIDI_FDM','straight_base_glue_lips',json.dumps(report))
    root.attributes.add('MIDI_FDM','glue_lips','Base: continuous 2mm high, 2mm inward lands with 45 degree runout; no dovetails. See straight_base_glue_lips.')
    with open(out+'modular/modular-design.json') as f:mod=json.load(f)
    mod.update({'base_dovetails':False,'base_joint':'Straight glue lips, 2mm high with 45 degree inward runout','universal_pair_base':True,'new_unique_print_parts':['pair-shell','pair-shell-at-cap','pair-base','left-cap'],
        'base_joint_verification':report,'main_revision':'straight_base_glue_lips','main_geometry_intentionally_updated':True,'main_geometry_unchanged':False})
    mod['one_piece_cap']['adjacent_base']='Use universal pair-base. Same floor, posts, ribs and two M2x6 holes as every repeat section; no special cap base required.'
    mod['assembly_order']='Glue upper chain with existing drop-down shell joint; fit cap via unchanged raised side approach. Glue straight base seams separately, aligning the flat outside floor faces. Install components and attach the connected base with existing M2x6 screws. Keep the removable floor-to-cap butt seam free of glue.'
    alt.attributes.add('MIDI_MODULAR','configuration',json.dumps(mod));write('modular/modular-design.json',mod)
    for n in ['straight-base-lips.json','print/straight-base-lips.json','modular/straight-base-lips.json']:write(n,report)
    baseline=[{'component':o.component.name,'transform':list(o.transform2.asArray()),'bodies':[{'name':b.name,'volume':b.volume,'min':list(b.boundingBox.minPoint.asArray()),'max':list(b.boundingBox.maxPoint.asArray())} for b in o.component.bRepBodies]} for o in main]
    write('modular/main-body-signatures-current.json',baseline)
    stage('saving')
    if not app.activeDocument.save('Replaced all base dovetails with straight continuous 2mm glue lips; one universal base fits every switch pair including cap-adjacent; shell joints and hardware retained.'):
        raise RuntimeError('Save failed')
    stage('complete')
