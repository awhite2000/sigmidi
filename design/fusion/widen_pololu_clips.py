"""Double spring width while preserving bending thickness and PCB seating."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 assert not root.attributes.itemByName('MIDI_FDM','wide_pololu_clips'),'Already widened'
 assert root.attributes.itemByName('MIDI_FDM','base_corner_repair')
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes;cache={}
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 bc=next(c for c in main if c.name.startswith('02 '));uc=next(c for c in main if c.name.startswith('01 '));pc=next(c for c in main if c.name.startswith('Pololu'))
 old=next(b for b in bc.bRepBodies if 'RIGHT' in b.name);board=pc.bRepBodies.item(0)
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 ec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));ab=next(b for b in ec.bRepBodies if 'BASE' in b.name)
 with open(out+'ventilated-clip.json') as f:cooling=json.load(f)
 assert cooling['spring_leaf_width_mm']==2.4
 def stage(s):
  with open('/tmp/wide-pololu-clips-progress.json','w') as f:json.dump({'stage':s},f)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def op(a,b,k):
  assert mgr.booleanOperation(a,b,k),'Boolean failed';return a
 def sub(a,b):return op(mgr.copy(a),mgr.copy(b),bt.DifferenceBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def bounds(a):
  key=id(a)
  if key not in cache:cache[key]=(a,a.boundingBox)
  return cache[key][1]
 def bbox(a):
  q=bounds(a);return [q.minPoint.x*10,-q.maxPoint.y*10,q.minPoint.z*10,q.maxPoint.x*10,-q.minPoint.y*10,q.maxPoint.z*10]
 def hit(a,b):
  q,r=bounds(a),bounds(b)
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(op(mgr.copy(a),mgr.copy(b),bt.IntersectionBooleanType))
 def move(a,dy=0,dz=0):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,-dy/10,dz/10);assert mgr.transform(a,m);return a
 def clearance(a,b):
  q,r=bounds(a),bounds(b)
  low=10*math.sqrt(sum(max(getattr(q.minPoint,k)-getattr(r.maxPoint,k),getattr(r.minPoint,k)-getattr(q.maxPoint,k),0)**2 for k in 'xyz'))
  if low>=3:return low
  pad=box(q.minPoint.x*10-3,-q.maxPoint.y*10-3,q.minPoint.z*10-3,q.maxPoint.x*10+3,-q.minPoint.y*10+3,q.maxPoint.z*10+3)
  return 3. if hit(pad,b)<1e-7 else low
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component;tc.name='TEMP wide Pololu clip construction'
 def prism(yz):
  sk=tc.sketches.add(tc.yZConstructionPlane)
  for a,b in zip(yz,yz[1:]+yz[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(p(0,*a)),sk.modelToSketchSpace(p(0,*b)))
  tc.features.extrudeFeatures.addSimple(sk.profiles.item(0),adsk.core.ValueInput.createByReal(.48),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
  body=tc.bRepBodies.item(tc.bRepBodies.count-1);a=mgr.copy(body);q=a.boundingBox;m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(22.38-q.minPoint.x,0,0);assert mgr.transform(a,m)
  body.deleteMe();sk.deleteMe();return a
 try:
  stage('building 4.8mm-wide leaves and exposed floor-level root gussets')
  yz=[(23.6,-22),(25.2,-22),(25.2,-10.384),(25.8,-9.784),(26.4,-9.784),(26.4,-8.984),(25.2,-7.784),(23.6,-7.784)]
  arms=[prism(yz),prism([(60.89-y,z) for y,z in reversed(yz)])]
  gussets=[prism([(22.8,-21),(23.6,-21),(23.6,-20.2)]),prism([(37.29,-21),(38.09,-21),(37.29,-20.2)])]
  base=mgr.copy(old)
  for a in arms+gussets:base=op(base,mgr.copy(a),bt.UnionBooleanType)
  added=sub(base,old);loss=vol(sub(old,base));assert loss<.001
  assert 50<vol(added)<200 and base.isSolid and base.lumps.count==1
  assert max(abs(a-b) for a,b in zip(bbox(old),bbox(base)))<1e-6
  assert vol(sub(old,ab))<.001 and vol(sub(ab,old))<.001
  stage('checking installed converter, hardware, wiring and outward spring travel')
  collisions=[];near=[];wires=[];minimum=1e9
  for c in main:
   if c==bc:continue
   for b in c.bRepBodies:
    amount=hit(added,b)
    if c.name.startswith('REF'):
     if amount>.001:wires.append([c.name,b.name,amount])
     continue
    if amount>.001:collisions.append([c.name,b.name,amount])
    if c==pc:continue  # Intentional close PCB retention contact/clearance.
    low=clearance(added,b);minimum=min(minimum,low)
    if low<3-1e-5:near.append([c.name,b.name,low])
  flex_hits=[];insertion=[];withdrawal=[]
  fixed=op(mgr.copy(base),box(223.799,22.799,-20.201,228.601,38.091,-7.783),bt.DifferenceBooleanType)
  free=[op(mgr.copy(a),box(223,22,-20.19,230,39,-7),bt.IntersectionBooleanType) for a in arms]
  for i,(sign,a) in enumerate(zip([-1,1],free)):
   for travel in [0,.15,.3,.45,.6]:
    moving=move(mgr.copy(a),dy=sign*travel)
    if hit(moving,fixed)>.001:flex_hits.append([i,travel,'fixed base'])
    for c in main:
     if c==bc or c.name.startswith('REF'):continue
     for b in c.bRepBodies:
      v=hit(moving,b)
      if v>.001:flex_hits.append([i,travel,c.name,b.name,v])
  fixed_seats=op(mgr.copy(fixed),box(217,22,-20.19,235,39,0),bt.IntersectionBooleanType)
  for i in range(41):
   dz=i*.25;moving=move(mgr.copy(board),dz=dz)
   if hit(moving,fixed_seats)>.001:insertion.append([dz,'fixed seats'])
   for sign,a in zip([-1,1],arms):
    v=hit(moving,move(mgr.copy(a),dy=sign*.6))
    if v>.001:insertion.append([dz,'flexed leaf',v])
   down=move(mgr.copy(added),dz=-i*.5)
   for b in uc.bRepBodies:
    v=hit(down,b)
    if v>.001:withdrawal.append([-i*.5,b.name,v])
  # All existing slots remain clear through the floor and above it.
  blocked=[]
  for label,x0,x1,y0,y1 in cooling['floor_slots_XY_mm']:
   if hit(added,box(x0,y0,-24.1,x1,y1,0))>.001:blocked.append(label)
  floor_change=hit(added,box(190,0,-24.1,351,93,-21))
  assert not any([collisions,near,wires,flex_hits,insertion,withdrawal,blocked]),[collisions,near,wires,flex_hits,insertion,withdrawal,blocked]
  assert floor_change<.001
  report={'revision':'wide_pololu_clips','spring_count':2,'previous_width_mm':2.4,'spring_leaf_width_mm':4.8,'width_X_mm':[223.8,228.6],'spring_leaf_thickness_mm':1.6,'width_ratio':2,'root_gusset_mm':.8,'root_gusset_angle_degrees':45,'root_gusset_base_Z_mm':-21,'root_gusset_top_Z_mm':-20.2,'root_gussets_exposed_above_reinforced_floor':True,'retaining_overlap_mm':.4,'PCB_top_retention_clearance_mm':.2,'required_outward_assembly_stroke_mm':.6,'bending_profile_and_PCB_position_unchanged':True,'added_material_mm3':vol(added),'original_material_removed_mm3':loss,'base_floor_material_changed_mm3':floor_change,'body_collisions':collisions,'component_clearances_below_3mm':near,'minimum_other_component_clearance_lower_bound_mm':minimum,'wire_collisions':wires,'outward_clip_sweep_collisions':flex_hits,'outward_stroke_samples_mm':[0,.15,.3,.45,.6],'board_insertion_collisions':insertion,'board_insertion_samples':41,'assembly_collisions':withdrawal,'base_removal_samples':41,'blocked_floor_vents':blocked,'all_13_floor_vents_unchanged':True,'existing_corner_repair_preserved':True,'main_and_modular_updated':True,'all_parts_single_connected_solids':True,'backup':'archive/pre-wide-pololu-clips.zip','limits':'Nominal geometry and slicing verify clearance and printable width, not printed PETG fatigue life or clip insertion force. Width doubles while bending thickness and tip displacement are retained.'}
  with open(out+'wide-pololu-clips.json','w') as f:json.dump(report,f,indent=2)
 finally:work.deleteMe()
 stage('committing matched main and modular bases')
 for c,b in [(bc,old),(ec,ab)]:
  name=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(base));n.name=name+' - 4.8mm Pololu spring leaves'
  if appearance:n.appearance=appearance
 cooling.update({'revision':'wide_pololu_clips','spring_leaf_width_mm':4.8,'spring_leaf_X_span_mm':[223.8,228.6],'root_gusset_base_Z_mm':-21,'root_gusset_top_Z_mm':-20.2,'wide_leaf_verification':'wide-pololu-clips.json'})
 with open(out+'ventilated-clip.json','w') as f:json.dump(cooling,f,indent=2)
 with open(out+'converter-carrier.json') as f:carrier=json.load(f)
 carrier.update({'revision':'wide_pololu_clips','spring_leaf_width_mm':4.8,'spring_leaf_thickness_mm':1.6,'wide_leaf_verification':'wide-pololu-clips.json'})
 with open(out+'converter-carrier.json','w') as f:json.dump(carrier,f,indent=2)
 for c in [root,alt]:
  c.attributes.add('MIDI_FDM','wide_pololu_clips',json.dumps(report));c.attributes.add('MIDI_POWER','ventilated_clip',json.dumps(cooling));c.attributes.add('MIDI_POWER','converter_carrier',json.dumps(carrier))
 assert app.activeDocument.save('Doubled Pololu spring leaves from 2.4mm to 4.8mm; retained 1.6mm bending thickness and hooks, added exposed 0.8mm 45-degree root gussets above reinforced floor; checked converter insertion and shell clearance in main and modular bases.')
 stage('complete')
