"""Match front locating ribs to rear thickness; join unobstructed neighboring runs."""
import adsk.core, adsk.fusion, json


def run(_context):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert app.activeDocument.name.startswith('MIDI Foot Controller - VERIFIED')
 assert not root.attributes.itemByName('MIDI_FDM','refined_positioning_ribs'),'Already applied'
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 uc=next(c for c in main if c.name.startswith('01 '));bc=next(c for c in main if c.name.startswith('02 '))
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 pair=next(o.component for o in alt.occurrences if o.component.name.startswith('Repeatable pair'))
 left=next(o.component for o in alt.occurrences if o.component.name.startswith('Leftmost pair'))
 ec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'))
 cc=next(o.component for o in alt.occurrences if o.component.name.startswith('Closed left cap'))
 def get(c,s):return next(b for b in c.bRepBodies if s in b.name)
 bl,br=get(bc,'LEFT'),get(bc,'RIGHT');pb,lb,eb=get(pair,'BASE'),get(left,'BASE'),get(ec,'BASE')
 targets=[bl,br,pb,lb,eb]
 def signatures():
  return [(o.fullPathName,list(o.transform2.asArray()),[(b.name,b.volume,list(b.boundingBox.minPoint.asArray()),list(b.boundingBox.maxPoint.asArray())) for b in o.component.bRepBodies if b not in targets]) for o in root.allOccurrences if not o.component.name.startswith('TEMP')]
 before=signatures()
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes;cache={}
 def stage(s):
  with open('/tmp/positioning-ribs-progress.json','w') as f:json.dump({'stage':s},f)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def op(a,b,k):
  assert mgr.booleanOperation(a,b,k),'BRep Boolean failed';return a
 def diff(a,b):return op(mgr.copy(a),mgr.copy(b),bt.DifferenceBooleanType)
 def inter(a,b):return op(mgr.copy(a),mgr.copy(b),bt.IntersectionBooleanType)
 def union(a,b):return op(a,mgr.copy(b),bt.UnionBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def bounds(a):
  if id(a) not in cache:cache[id(a)]=(a,a.boundingBox)
  return cache[id(a)][1]
 def hit(a,b):
  q,r=bounds(a),bounds(b)
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(inter(a,b))
 def move(a,dx=0,dz=0):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,0,dz/10);assert mgr.transform(a,m);return a
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component;tc.name='TEMP positioning rib refinement'
 def rib(x0,x1,side):
  y0,y1=(87.85,89.65) if side=='front' else (2.35,4.15)
  b=tc.bRepBodies.add(box(x0,y0,-22.02,x1,y1,-19));edges=adsk.core.ObjectCollection.create()
  for e in b.edges:
   q=e.boundingBox
   if abs(q.minPoint.z+1.9)<1e-7 and abs(q.maxPoint.z+1.9)<1e-7:edges.add(e)
  assert edges.count==4
  inp=tc.features.chamferFeatures.createInput2();inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges,adsk.core.ValueInput.createByString('0.5 mm'),False);tc.features.chamferFeatures.add(inp)
  a=mgr.copy(b);b.deleteMe();return a
 stage('narrowing front ribs and joining four unobstructed gaps')
 specs=[('base-left',bc,bl,[(48,83),(140,175)]),('base-right',bc,br,[(203,238),(252,287),(290,315)]),('pair-base',pair,pb,[(140,175)])]
 candidates={};rows=[];changes=[]
 for name,c,b,oldruns in specs:
  a=mgr.copy(b)
  for x0,x1 in ([] if name=='pair-base' else oldruns):a=op(a,box(x0,81.85,-22,x1,89.65,-18.99),bt.DifferenceBooleanType)
  if name=='base-right':
   # Preserve the established 0.3mm relief around the split-adjacent screw web.
   gate=union(mgr.copy(b),box(211,87.85,-22.02,315,89.65,-18.99))
   a=union(a,inter(rib(203,315,'front'),gate))
   # The rear MCU/USB relief is retained exactly; only the clear 287..300 gap is joined.
   a=op(a,box(264.699886096949,2.35,-22,325,4.15,-18.99),bt.DifferenceBooleanType)
   gate=union(mgr.copy(b),box(270,2.35,-22.02,325,4.15,-18.99))
   a=union(a,inter(rib(264.699886096949,325,'rear'),gate))
  elif name=='base-left':
   for x0,x1 in oldruns:a=union(a,inter(rib(x0,x1,'front'),b))
  if name=='base-left':
   a=op(a,box(20,2.35,-22,100,4.15,-18.99),bt.DifferenceBooleanType)
   a=union(a,rib(20,100,'rear'))
  assert a.isSolid and a.lumps.count==1,name
  added=diff(a,b);removed=diff(b,a)
  assert hit(added,box(-1,-1,-25,351,93,-22))<.001
  assert hit(removed,box(-1,-1,-25,351,93,-22))<.001
  # Removed material is restricted to the obsolete thick front ribs and end chamfers.
  allowed=box(0,81.8499,-22.0001,350,89.6501,-18.99)
  allowed=union(allowed,box(19.9999,2.3499,-22.0001,100.0001,4.1501,-18.99))
  allowed=union(allowed,box(264.6997,2.3499,-22.0001,325.0001,4.1501,-18.99))
  assert vol(diff(removed,allowed))<.001
  candidates[name]=a;changes.append((name,c,b,a,added,removed))
  rows.append({'part':name,'single_connected_solid':True,'old_front_rib_thickness_mm':1.8 if name=='pair-base' else 7.8,'new_front_rib_thickness_mm':1.8,'added_mm3':vol(added),'removed_mm3':vol(removed),'new_volume_mm3':vol(a)})
 stage('checking installed ribs, screws, hardware and wire clearances')
 hits=[];wires=[];paths=[]
 for name,c,b,a,added,removed in changes:
  uppers=list(uc.bRepBodies) if name.startswith('base-') else [get(pair,'SHELL'),get(left,'SHELL')]
  for u in uppers:
   amount=hit(a,u)
   if amount>.001:hits.append([name,'upper shell',u.name,amount])
  for other in main:
   if other in [uc,bc]:continue
   for body in other.bRepBodies:
    amount=hit(added,body)
    if amount>.001:(wires if other.name.startswith('REF') else hits).append([name,other.name,body.name,amount])
  # Added rib material must retain removable-floor insertion clearance.
  for step in range(41):
   moving=move(mgr.copy(added),dz=-step*.5)
   for u in uppers:
    amount=hit(moving,u)
    if amount>.001:paths.append([name,'floor withdrawal',step*.5,u.name,amount])
 assert not any([hits,wires,paths]),[hits,wires,paths]
 # Main and chainable examples share the exact reusable electronics and pair floors.
 changes.extend([('pair-at-cap-base',left,lb,candidates['pair-base'],None,None),('modular-electronics-base',ec,eb,candidates['base-right'],None,None)])
 # Check pair/cap/base neighbours in the assembled eight-switch example.
 ab=[move(mgr.copy(candidates['pair-base']),dx=-65),candidates['pair-base'],candidates['base-right']]
 cap=move(mgr.copy(cc.bRepBodies.item(0)),dx=-65)
 au=[move(mgr.copy(get(left,'SHELL')),dx=-65),get(pair,'SHELL'),get(ec,'SHELL'),cap]
 for i,b in enumerate(ab):
  for j,u in enumerate(au):
   amount=hit(b,u)
   if amount>.001:hits.append(['modular',i,j,amount])
  for j,c in enumerate(ab[i+1:],i+1):
   amount=hit(b,c)
   if amount>.001:hits.append(['modular bases',i,j,amount])
 for o in alt.occurrences:
  if o.component.name.startswith('REF modular LED'):
   for wire in o.component.bRepBodies:
    for i,b in enumerate(ab):
     amount=hit(wire,b)
     if amount>.001:wires.append(['modular',i,wire.name,amount])
 assert not hits and not wires,[hits,wires]
 report={'revision':'refined_positioning_ribs','front_thickness_before_mm':7.8,'front_and_rear_rib_thickness_mm':1.8,'rib_height_above_floor_mm':3,'top_chamfer_mm':.5,'nominal_shell_side_clearance_mm':.35,
 'joined_gaps':[{'part':'base-left','side':'rear','X_mm':[55,70]},{'part':'base-right','side':'rear','X_mm':[287,300]},{'part':'base-right','side':'front','X_mm':[238,252]},{'part':'base-right','side':'front','X_mm':[287,290]}],
 'continuous_joined_runs':[{'part':'base-left','side':'rear','X_mm':[20,100]},{'part':'base-right','side':'rear','X_mm':[264.699886096949,325]},{'part':'base-right','side':'front','X_mm':[203,315],'start_relief':'Existing screw-boss/web relief retained'}],
 'remaining_breaks':'Screw-boss webs interrupt the main left front/rear ribs and both modular pair locating ribs; MCU/USB support interrupts the right rear rib. These reliefs are retained.',
 'parts':rows,'physical_collisions':hits,'wire_collisions':wires,'assembly_collisions':paths,'base_withdrawal_samples':41,
 'floor_mounts_vents_screw_holes_and_seam_glue_lips_unchanged':True,'all_upper_shells_and_component_poses_unchanged':True,'all_models_updated':True,'universal_pair_base_retained':True,'pair_base_profile_retained':True,
 'backup':'archive/pre-positioning-rib-refinement.zip'}
 stage('committing matching main and modular base solids')
 work.deleteMe()
 for name,c,b,a,*_ in changes:
  appearance=b.appearance;oldname=b.name;b.deleteMe();n=c.bRepBodies.add(mgr.copy(a));n.name=oldname+' - 1.8mm streamlined locating ribs'
  if appearance:n.appearance=appearance
  targets.append(n)
 assert signatures()==before,'Unrelated geometry or occurrence transforms changed'
 with open(out+'positioning-rib-refinement.json','w') as f:json.dump(report,f,indent=2)
 for c in [root,alt]:c.attributes.add('MIDI_FDM','refined_positioning_ribs',json.dumps(report))
 with open(out+'modular/modular-design.json') as f:mod=json.load(f)
 mod.update({'main_revision':'refined_positioning_ribs','positioning_rib_thickness_mm':1.8,'positioning_rib_report':'../positioning-rib-refinement.json','universal_pair_base':True})
 with open(out+'modular/modular-design.json','w') as f:json.dump(mod,f,indent=2)
 alt.attributes.add('MIDI_MODULAR','configuration',json.dumps(mod))
 assert app.activeDocument.save('Reduced all front base positioning ribs from 7.8mm to the rear 1.8mm thickness; joined four clear gaps into three continuous locating runs; preserved screw/USB reliefs, 0.5mm lead-ins, all floor details, shells and hardware.')
 stage('complete')
