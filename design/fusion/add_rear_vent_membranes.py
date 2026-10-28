"""Close rear vents with flush 0.6mm sacrificial internal membranes."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 if root.attributes.itemByName('MIDI_FDM','rear_vent_membranes'):raise RuntimeError('Vent membranes already installed')
 assert root.attributes.itemByName('MIDI_POWER','straight_rear_rib')
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 uc=next(c for c in main if c.name.startswith('01 '));bc=next(c for c in main if c.name.startswith('02 '))
 old=next(b for b in uc.bRepBodies if 'RIGHT' in b.name)
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));au=next(b for b in elec.bRepBodies if 'SHELL' in b.name)
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes;cache={}
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def bounds(a):
  key=id(a)
  if key not in cache:cache[key]=(a,a.boundingBox)
  return cache[key][1]
 def op(a,b,k):
  if not mgr.booleanOperation(a,b,k):raise RuntimeError('Boolean failed')
  return a
 def union(a,b):return op(a,b,bt.UnionBooleanType)
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def gap(a,b):
  q,r=bounds(a),bounds(b)
  return math.sqrt(sum(max(getattr(q.minPoint,k)-getattr(r.maxPoint,k),getattr(r.minPoint,k)-getattr(q.maxPoint,k),0)**2 for k in 'xyz'))*10
 def hit(a,b):
  q,r=bounds(a),bounds(b)
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(inter(mgr.copy(a),mgr.copy(b)))
 with open(out+'rear-grille-ribs.json') as f:grilles=json.load(f)
 slots=grilles['rear_slots_XZ_mm'];assert len(slots)==12
 shell=mgr.copy(old);patches=[];checks=[]
 for v in slots:
  x0,x1,z0,z1=v
  # The 0.15mm overlap is entirely inside existing wall material; the
  # actual new material is precisely the hexagonal opening, Y1.4..2.0.
  patch=box(x0-.15,1.4,z0-.15,x1+.15,2,z1+.15)
  new=cut(mgr.copy(patch),mgr.copy(old));amount=vol(new)
  assert abs(amount-19.008)<.001,[v,amount]
  shell=union(shell,patch);patches.append(new);checks.append({'slot_XZ_mm':v,'added_mm3':amount})
 assert shell.isSolid and shell.lumps.count==1
 added=cut(mgr.copy(shell),mgr.copy(old));removed=vol(cut(mgr.copy(old),mgr.copy(shell)))
 assert removed<.001 and abs(vol(added)-228.096)<.001
 # Exact virtual removal of the membranes must recover the pre-change shell.
 recovered=cut(mgr.copy(shell),mgr.copy(added));differences=[vol(cut(mgr.copy(a),mgr.copy(b))) for a,b in [(old,recovered),(recovered,old)]]
 assert max(differences)<.001,differences
 hits=[];near=[];wires=[];minimum=1e9
 for c in main:
  if c==uc:continue
  for b in c.bRepBodies:
   for i,a in enumerate(patches):
    amount=hit(a,b)
    if c.name.startswith('REF'):
     if amount>.001:wires.append([i,c.name,b.name,amount])
     continue
    if amount>.001:hits.append([i,c.name,b.name,amount])
    low=gap(a,b);minimum=min(minimum,low)
    if low<3-1e-5:near.append([i,c.name,b.name,low])
 assert not hits and not near and not wires,[hits,near,wires]
 q=bounds(added);assert abs(q.minPoint.y+.2)<1e-6 and abs(q.maxPoint.y+.14)<1e-6
 report={'revision':'rear_vent_membranes','membrane_count':12,'membrane_thickness_mm':.6,'membrane_layout_Y_span_mm':[1.4,2],'rear_wall_thickness_mm':2,'outside_slot_recess_depth_mm':1.4,'internal_face_flush':True,'cavity_projection_mm':0,'slot_checks':checks,'added_material_mm3':vol(added),'original_material_removed_mm3':removed,'virtual_removal_bidirectional_BRep_difference_mm3':differences,'finished_slot_geometry_unchanged':True,'body_collisions':hits,'component_clearances_below_3mm':near,'wire_collisions':wires,'minimum_added_material_component_clearance_lower_bound_mm':minimum,'rear_as_printed_open_area_mm2':0,'rear_open_area_after_membrane_removal_mm2':380.16,'base_geometry_and_component_positions_unchanged':True,'main_and_modular_updated':True,'backup':'archive/pre-rear-vent-membranes.zip','finishing':'Before assembling electronics, score around each recessed slot outline with a sharp hobby blade and remove the thin internal film; clean out all twelve openings. Preserve the permanent 2mm rear wall and the vertical reinforcing rib. Remove these temporary closures before operating the controller.','limits':'Slice verification confirms toolpath presence; cutting effort and printed membrane toughness require a first-print check.'}
 for c,b in [(uc,old),(elec,au)]:
  name=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(shell));n.name=name+' - 0.6mm rear vent cutaway membranes'
  if appearance:n.appearance=appearance
 with open(out+'rear-vent-membranes.json','w') as f:json.dump(report,f,indent=2)
 with open(out+'ventilated-clip.json') as f:cooling=json.load(f)
 cooling.update({'revision':'rear_vent_membranes','rear_vent_membranes':'rear-vent-membranes.json','rear_as_printed_open_area_mm2':0,'rear_open_area_after_membrane_removal_mm2':380.16,'rear_membranes_must_be_removed_before_use':True})
 with open(out+'ventilated-clip.json','w') as f:json.dump(cooling,f,indent=2)
 for c in [root,alt]:c.attributes.add('MIDI_FDM','rear_vent_membranes',json.dumps(report));c.attributes.add('MIDI_POWER','ventilated_clip',json.dumps(cooling))
 if not app.activeDocument.save('Added 0.6mm sacrificial membranes flush with the inside of all 12 rear slots in main and modular shells; cut out after printing to restore ventilation. Rib, exterior envelope, base and component positions retained.'):
  raise RuntimeError('Save failed')
