"""Thicken the floor by 1mm inside the rectangular vent envelope plus 3mm."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 if root.attributes.itemByName('MIDI_POWER','reinforced_floor_grilles'):raise RuntimeError('Floor reinforcement already installed')
 assert root.attributes.itemByName('MIDI_POWER','rear_column_rib')
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 bc=next(c for c in main if c.name.startswith('02 '));old=next(b for b in bc.bRepBodies if 'RIGHT' in b.name)
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));ab=next(b for b in elec.bRepBodies if 'BASE' in b.name)
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 # Retain cached boxes: exact bounding queries on a thin Boolean difference
 # are expensive; object references prevent Python id reuse.
 bounds_cache={}
 def bounds(a):
  key=id(a)
  if key not in bounds_cache:bounds_cache[key]=(a,a.boundingBox)
  return bounds_cache[key][1]
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def op(a,b,k):
  if not mgr.booleanOperation(a,b,k):raise RuntimeError('Boolean failed')
  return a
 def union(a,b):return op(a,b,bt.UnionBooleanType)
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def shift(a,z):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,0,z/10);mgr.transform(a,m);return a
 def gap(a,b):
  q,r=bounds(a),bounds(b)
  return math.sqrt(sum(max(getattr(q.minPoint,k)-getattr(r.maxPoint,k),getattr(r.minPoint,k)-getattr(q.maxPoint,k),0)**2 for k in 'xyz'))*10
 def hit(a,b):
  q,r=bounds(a),bounds(b)
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(inter(mgr.copy(a),mgr.copy(b)))
 def certified_gap(a,b):
  low=gap(a,b)
  if low>=3:return low
  q=bounds(a);center=adsk.core.Point3D.create(*[(getattr(q.minPoint,k)+getattr(q.maxPoint,k))/2 for k in 'xyz'])
  expanded=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(center,adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),q.maxPoint.x-q.minPoint.x+.6,q.maxPoint.y-q.minPoint.y+.6,q.maxPoint.z-q.minPoint.z+.6))
  near=inter(mgr.copy(b),expanded)
  if not near.faces.count or vol(near)<1e-7:return 3.
  return min(3.,min(gap(a,lump) for lump in near.lumps))
 with open(out+'ventilated-clip.json') as f:cooling=json.load(f)
 slots=cooling['floor_slots_XY_mm'];assert len(slots)==13
 xmin=min(v[1] for v in slots)-3;xmax=max(v[2] for v in slots)+3
 ymin=min(v[3] for v in slots)-3;ymax=max(v[4] for v in slots)+3
 # Copy the original floor's 1mm upper layer upward. This carries every
 # original vent and screw bore through the new material without filling it.
 footprint=inter(mgr.copy(old),box(xmin,ymin,-23,xmax,ymax,-22))
 patch=shift(mgr.copy(footprint),1);base=union(mgr.copy(old),patch)
 assert base.isSolid and base.lumps.count==1
 added=cut(mgr.copy(base),mgr.copy(old));removed=vol(cut(mgr.copy(old),mgr.copy(base)))
 allowed=box(xmin,ymin,-22,xmax,ymax,-21)
 assert removed<.001 and vol(cut(mgr.copy(added),allowed))<.001
 assert vol(added)>1500,vol(added)
 # Even the added material stays outside the original floor openings.
 openings=shift(mgr.copy(footprint),1)
 assert vol(cut(mgr.copy(added),mgr.copy(openings)))<.001
 def slot(v):
  label,x0,x1,y0,y1=v;w=min(x1-x0,y1-y0);r=w/2
  if x1-x0>=y1-y0:
   a=box(x0+r,y0,-24.1,x1-r,y1,-20.9);ends=[(x0+r,(y0+y1)/2),(x1-r,(y0+y1)/2)]
  else:
   a=box(x0,y0+r,-24.1,x1,y1-r,-20.9);ends=[((x0+x1)/2,y0+r),((x0+x1)/2,y1-r)]
  for x,y in ends:a=union(a,mgr.createCylinderOrCone(p(x,y,-24.1),r/10,p(x,y,-20.9),r/10))
  return a
 blocked=[]
 for v in slots:
  amount=hit(slot(v),base)
  if amount>.001:blocked.append([v[0],amount])
 assert not blocked,blocked
 hits=[];near=[];wires=[];minimum=1e9;module_floor_gap=None
 for c in main:
  if c==bc:continue
  for b in c.bRepBodies:
   amount=hit(added,b)
   if c.name.startswith('REF'):
    if amount>.001:wires.append([c.name,b.name,amount])
    continue
   if amount>.001:hits.append([c.name,b.name,amount])
   low=certified_gap(added,b);minimum=min(minimum,low)
   if low<3-1e-5:near.append([c.name,b.name,low])
   if c.name.startswith('Pololu '):module_floor_gap=b.boundingBox.minPoint.z*10+21
 assert not hits and not near and not wires,[hits,near,wires]
 assert abs(module_floor_gap-8.650125)<.001,module_floor_gap
 # New material moves farther from the shell/boards as the base is removed.
 # Explicitly sample its original downward floor-removal path as well.
 assembly=[]
 for dz in [-i*.5 for i in range(41)]:
  a=shift(mgr.copy(added),dz)
  for c in main:
   if c==bc or c.name.startswith(('REF','PCB screws','Base fasteners')):continue
   for b in c.bRepBodies:
    amount=hit(a,b)
    if amount>.001:assembly.append([dz,c.name,b.name,amount])
 assert not assembly,assembly
 report={'revision':'reinforced_floor_grilles','rectangle_XY_mm':[xmin,ymin,xmax,ymax],'border_mm':3,'added_thickness_mm':1,'original_floor_thickness_mm':2,'reinforced_floor_thickness_mm':3,'original_floor_inside_Z_mm':-22,'reinforced_floor_inside_Z_mm':-21,'outside_floor_Z_mm':-24,'slot_count':13,'floor_slots_XY_mm':slots,'floor_open_area_mm2':cooling['floor_open_area_mm2'],'blocked_slots':blocked,'existing_floor_openings_and_bores_preserved':True,'added_material_mm3':vol(added),'original_material_removed_mm3':removed,'body_collisions':hits,'component_clearances_below_3mm':near,'wire_collisions':wires,'minimum_component_clearance_lower_bound_mm':minimum,'converter_to_reinforced_floor_clearance_mm':module_floor_gap,'assembly_collisions':assembly,'base_removal_samples':41,'original_mount_material_unchanged':True,'upper_shell_and_component_positions_unchanged':True,'exterior_envelope_unchanged':True,'main_and_modular_updated':True,'backup':'archive/pre-base-vent-reinforcement.zip','limits':'Geometric fit and slicing do not establish physical stiffness, spring retention or thermal performance.'}
 for c,b in [(bc,old),(elec,ab)]:
  name=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(base));n.name=name+' - local 3mm vent floor'
  if appearance:n.appearance=appearance
 with open(out+'base-vent-reinforcement.json','w') as f:json.dump(report,f,indent=2)
 cooling.update({'revision':'reinforced_floor_grilles','base_vent_reinforcement':'base-vent-reinforcement.json','component_to_inside_floor_clearance_mm':module_floor_gap,'floor_reinforcement_inside_Z_mm':-21,'floor_thickness_below_components_mm':3,'leaf_height_above_reinforced_floor_mm':cooling['leaf_height_mm']-1})
 with open(out+'ventilated-clip.json','w') as f:json.dump(cooling,f,indent=2)
 for c in [root,alt]:c.attributes.add('MIDI_POWER','reinforced_floor_grilles',json.dumps(report));c.attributes.add('MIDI_POWER','ventilated_clip',json.dumps(cooling))
 if not app.activeDocument.save('Thickened the base internally from 2mm to 3mm only in the ventilation rectangle plus 3mm border, preserving all 13 slots and bores; matched main/modular bases, exterior and component positions unchanged.'):
  raise RuntimeError('Save failed')
