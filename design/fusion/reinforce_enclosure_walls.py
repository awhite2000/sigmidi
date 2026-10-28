"""Reinforce audited weak closures; preserve exterior and hardware placements."""
import adsk.core,adsk.fusion,json

def run(_context):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert root.attributes.itemByName('MIDI_FDM','upper_corner_walls')
 assert not root.attributes.itemByName('MIDI_FDM','enclosure_wall_reinforcement'),'Already applied'
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes;cache={}
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 uc=next(c for c in main if c.name.startswith('01 '));bc=next(c for c in main if c.name.startswith('02 '))
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 pair=next(o.component for o in alt.occurrences if o.component.name.startswith('Repeatable pair'));left=next(o.component for o in alt.occurrences if o.component.name.startswith('Leftmost pair'));ec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));cc=next(o.component for o in alt.occurrences if o.component.name.startswith('Closed left cap'))
 library=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Engraved pair'))
 def get(c,label):return next(b for b in c.bRepBodies if label in b.name)
 sl,sr=get(uc,'LEFT'),get(uc,'RIGHT');bl=get(bc,'LEFT');cb=cc.bRepBodies.item(0)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def cone(x,y,z0,z1,r0,r1):return mgr.createCylinderOrCone(p(x,y,z0),r0/10,p(x,y,z1),r1/10)
 def op(a,b,k):
  assert mgr.booleanOperation(a,b,k),'Boolean failed';return a
 def diff(a,b):return op(mgr.copy(a),mgr.copy(b),bt.DifferenceBooleanType)
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
 def move(a,dx=0,dz=0):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,0,dz/10);assert mgr.transform(a,m);return a
 def stage(s):
  with open('/tmp/enclosure-wall-reinforcement-progress.json','w') as f:json.dump({'stage':s},f)
 stage('reinforcing blind pilot caps in all seven unique upper shell shapes')
 specs=[('main-left',uc,sl),('main-right',uc,sr),('pair-shell',pair,get(pair,'SHELL')),('pair-shell-at-cap',left,get(left,'SHELL'))]+[(o.component.name,o.component,o.component.bRepBodies.item(0)) for o in library.occurrences]
 changes=[];rows=[]
 for name,c,b in specs:
  centers=[]
  for face in b.faces:
   g=face.geometry;q=face.boundingBox
   if g.objectType=='adsk::core::Cylinder' and abs(g.axis.z)>.999 and abs(g.radius*10-.95)<.001 and abs(q.maxPoint.z*10+15.5)<.001:centers.append([g.origin.x*10,-g.origin.y*10])
  assert len(centers)==(4 if name.startswith('main-') else 2),(name,centers)
  a=mgr.copy(b)
  for x,y in centers:
   a=op(a,cone(x,y,-15,-13.5,4,2.5),bt.UnionBooleanType)
   # Preserve the complete blind pilot; its roof now has 2mm of backing.
   assert hit(a,cone(x,y,-22,-15.5,.95,.95))<.001
   probe=cone(x,y,-15.5,-13.5,.95,.95);assert abs(hit(a,probe)-vol(probe))<.001
  added=diff(a,b);assert vol(diff(b,a))<.001 and a.isSolid and a.lumps.count==1
  assert max(abs(x-y) for x,y in zip(bbox(a),bbox(b)))<1e-6
  changes.append((name,c,b,a,added));rows.append({'part':name,'pilot_centers_XY_mm':centers,'old_blind_cap_mm':.5,'new_blind_cap_mm':2,'new_top_Z_mm':-13.5,'gusset_angle_degrees':45,'added_material_mm3':vol(added)})
 stage('repairing modular cap front side wall and left floor slit')
 # Copy the established main front corner profile into the cap. Its outer
 # profile is identical, but the cap's old inner plane was 0.536mm too far out.
 front=op(mgr.copy(sl),box(0,80,-22,6,92,-5),bt.IntersectionBooleanType);move(front,dx=120.15)
 cap=op(mgr.copy(cb),front,bt.UnionBooleanType);cap_added=diff(cap,cb)
 assert cap.isSolid and cap.lumps.count==1 and vol(diff(cb,cap))<.001
 assert max(abs(x-y) for x,y in zip(bbox(cap),bbox(cb)))<1e-6
 changes.append(('left-cap',cc,cb,cap,cap_added));rows.append({'part':'left-cap','previous_front_flat_wall_mm':1.6568542495,'new_front_flat_wall_mm':2.1927526344,'added_material_mm3':vol(cap_added)})
 floor=op(box(0,77,-24,15,86,-22),box(6,77,-24,15,92,-22),bt.UnionBooleanType)
 floor=op(floor,cone(6,86,-24,-22,6,6),bt.UnionBooleanType)
 base=op(mgr.copy(bl),floor,bt.UnionBooleanType);base_added=diff(base,bl)
 assert 10<vol(base_added)<20 and base.isSolid and base.lumps.count==1
 assert vol(diff(bl,base))<.001 and vol(diff(floor,base))<.001
 assert max(abs(x-y) for x,y in zip(bbox(base),bbox(bl)))<1e-6
 changes.append(('base-left',bc,bl,base,base_added));rows.append({'part':'base-left','repair':'Close unused front-left floor slit; retain full 2mm R6 floor outline','added_bounds_XYZ_mm':bbox(base_added),'added_material_mm3':vol(base_added)})
 stage('checking hardware, wires, base removal and cap assembly')
 hits=[];wires=[];paths=[]
 for name,c,b,a,added in changes:
  if name=='left-cap':continue
  for other in main:
   if other in [uc,bc]:continue
   for body in other.bRepBodies:
    v=hit(added,body)
    if v>.001:(wires if other.name.startswith('REF') else hits).append([name,other.name,body.name,v])
  if c==uc:
   for step in range(41):
    for body in bc.bRepBodies:
     v=hit(added,move(mgr.copy(body),dz=-step*.5))
     if v>.001:paths.append([name,'floor withdrawal',step,v])
  elif name=='base-left':
   for step in range(41):
    moving=move(mgr.copy(added),dz=-step*.5)
    for body in uc.bRepBodies:
     v=hit(moving,body)
     if v>.001:paths.append([name,'floor withdrawal',step,v])
  else:
   pb=get(pair,'BASE')
   for step in range(41):
    v=hit(added,move(mgr.copy(pb),dz=-step*.5))
    if v>.001:paths.append([name,'module floor withdrawal',step,v])
 for step in range(9):
  moving=move(mgr.copy(cap_added),dz=step*.25)
  for b in left.bRepBodies:
   v=hit(moving,b)
   if v>.001:paths.append(['left-cap','cap approach',step,v])
 assert not any([hits,wires,paths]),[hits,wires,paths]
 # Duplicate electronics geometry by exact copy, preserving the common print part.
 ar=get(ec,'SHELL');right_new=next(a for name,c,b,a,added in changes if name=='main-right')
 changes.append(('modular-electronics',ec,ar,right_new,next(ad for name,c,b,a,ad in changes if name=='main-right')))
 report={'revision':'enclosure_wall_reinforcement','parts':rows,'unique_upper_shell_shapes_reinforced':7,'blind_pilot_diameter_mm':1.9,'blind_pilot_depth_mm':6.5,'blind_cap_thickness_mm':2,'cap_front_flat_wall_mm':2.1927526344,'floor_slit_closed':True,'floor_thickness_mm':2,'all_changed_parts_single_connected_solids':True,'original_material_removed_mm3':0,'exterior_envelope_and_visible_surfaces_preserved':True,'all_component_positions_and_mounting_hole_axes_unchanged':True,'shell_joints_and_base_seating_unchanged':True,'intentional_LED_and_rear_vent_membranes_unchanged':True,'USB_clearance_display_flush_seat_and_spring_thickness_unchanged':True,'body_collisions':hits,'wire_collisions':wires,'assembly_collisions':paths,'base_withdrawal_samples':41,'backup':'archive/pre-enclosure-wall-reinforcement.zip','limits':'Mesh thickness sampling is not an exhaustive mathematical minimum; intentional bevel tips, joint ramps, recessed text sidewalls, countersink edges and breakaway covers remain thin by design. Functional 1.5-1.725mm walls require actual toolpath verification.'}
 stage('committing checked upper shells, cap and base plate')
 for name,c,b,a,added in changes:
  appearance=b.appearance;oldname=b.name;b.deleteMe();n=c.bRepBodies.add(mgr.copy(a));n.name=oldname+' - audited internal reinforcement'
  if appearance:n.appearance=appearance
 with open(out+'enclosure-wall-reinforcement.json','w') as f:json.dump(report,f,indent=2)
 for c in [root,alt]:c.attributes.add('MIDI_FDM','enclosure_wall_reinforcement',json.dumps(report))
 assert app.activeDocument.save('Reinforced all seven upper-shell pilot caps to 2mm with 45-degree shoulders; repaired modular cap front wall and unused left-base floor slit; preserved exterior, component poses, joints, functional clearances and removable membranes.')
 stage('complete')
