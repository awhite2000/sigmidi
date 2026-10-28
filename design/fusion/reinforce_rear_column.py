"""Restore original rear vents, complete the middle column, and add one internal rib."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 if root.attributes.itemByName('MIDI_POWER','rear_column_rib'):raise RuntimeError('Column rib already installed')
 assert root.attributes.itemByName('MIDI_POWER','rear_grille_ribs')
 assert root.attributes.itemByName('MIDI_POWER','raised_rear_grilles')
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 uc=next(c for c in main if c.name.startswith('01 '));bc=next(c for c in main if c.name.startswith('02 '))
 old=next(b for b in uc.bRepBodies if 'RIGHT' in b.name)
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));au=next(b for b in elec.bRepBodies if 'SHELL' in b.name)
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def op(a,b,k):
  if not mgr.booleanOperation(a,b,k):raise RuntimeError('Boolean failed')
  return a
 def union(a,b):return op(a,b,bt.UnionBooleanType)
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def gap(a,b):
  q,r=a.boundingBox,b.boundingBox
  return math.sqrt(sum(max(getattr(q.minPoint,k)-getattr(r.maxPoint,k),getattr(r.minPoint,k)-getattr(q.maxPoint,k),0)**2 for k in 'xyz'))*10
 def hit(a,b):
  q,r=a.boundingBox,b.boundingBox
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(inter(mgr.copy(a),mgr.copy(b)))
 def certified_gap(a,b):
  low=gap(a,b)
  if low>=3:return low
  q=a.boundingBox;center=adsk.core.Point3D.create(*[(getattr(q.minPoint,k)+getattr(q.maxPoint,k))/2 for k in 'xyz'])
  expanded=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(center,adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),q.maxPoint.x-q.minPoint.x+.6,q.maxPoint.y-q.minPoint.y+.6,q.maxPoint.z-q.minPoint.z+.6))
  near=inter(mgr.copy(b),expanded)
  if not near.faces.count or vol(near)<1e-7:return 3.
  return min(3.,min(gap(a,lump) for lump in near.lumps))
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component;tc.name='TEMP rear column rib'
 def slot(v,y0,y1):
  x0,x1,z0,z1=v;r=(z1-z0)/2;mid=(z0+z1)/2;points=[(x0+r,z0),(x1-r,z0),(x1,mid),(x1-r,z1),(x0+r,z1),(x0,mid)]
  sk=tc.sketches.add(tc.xZConstructionPlane)
  for a,b in zip(points,points[1:]+points[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(p(a[0],0,a[1])),sk.modelToSketchSpace(p(b[0],0,b[1])))
  tc.features.extrudeFeatures.addSimple(sk.profiles.item(0),adsk.core.ValueInput.createByReal((y1-y0)/10),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
  a=mgr.copy(tc.bRepBodies.item(tc.bRepBodies.count-1));q=a.boundingBox;m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,-y1/10-q.minPoint.y,0);mgr.transform(a,m)
  tc.bRepBodies.item(tc.bRepBodies.count-1).deleteMe();sk.deleteMe();return a
 with open(out+'raised-rear-vents.json') as f:raised=json.load(f)
 slots=raised['rear_slots_XZ_mm'];restored=mgr.copy(old)
 for v in slots:restored=cut(restored,slot(v,-.05,2.05))
 removed_bar_volume=vol(old)-vol(restored)
 assert abs(removed_bar_volume-72)<.01,removed_bar_volume
 assert abs(vol(restored)-raised['shell_volume_after_mm3'])<.01
 new_slots=[[243,257.4,z,z+2.4] for z in [2,8,14]];slot_material=[]
 for v in new_slots:
  tool=slot(v,-.05,2.05);slot_material.append(inter(mgr.copy(restored),mgr.copy(tool)));restored=cut(restored,tool)
 assert all(abs(vol(a)-63.36)<.01 for a in slot_material)
 slots+=new_slots
 # 2mm projection inward. Both flanks are 45 degrees, with a 2mm flat
 # crest and 6mm attachment footprint centered in the 8.6mm solid gap.
 x=261.7;points=[(x-3,1.95),(x+3,1.95),(x+3,2),(x+1,4),(x-1,4),(x-3,2)]
 sk=tc.sketches.add(tc.xYConstructionPlane)
 for a,b in zip(points,points[1:]+points[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(p(a[0],a[1],0)),sk.modelToSketchSpace(p(b[0],b[1],0)))
 tc.features.extrudeFeatures.addSimple(sk.profiles.item(0),adsk.core.ValueInput.createByString('25.4 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
 rib=mgr.copy(tc.bRepBodies.item(tc.bRepBodies.count-1));q=rib.boundingBox;m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,0,-q.minPoint.z);mgr.transform(rib,m)
 shell=union(mgr.copy(restored),rib)
 assert shell.isSolid and shell.lumps.count==1
 added=cut(mgr.copy(shell),mgr.copy(restored));removed=vol(cut(mgr.copy(restored),mgr.copy(shell)))
 assert removed<.001 and abs(vol(added)-203.2)<.1,[removed,vol(added)]
 blocked=[]
 for i,v in enumerate(slots):
  amount=hit(slot(v,-.05,4.99),shell)
  if amount>.001:blocked.append([i,amount])
 assert not blocked,blocked
 hits=[];near=[];minimum=1e9
 for c in main:
  if c==uc or c.name.startswith('REF'):continue
  for b in c.bRepBodies:
   v=hit(added,b)
   if v>.001:hits.append([c.name,b.name,v])
   if c!=bc:
    for shape in [added]+slot_material:
     low=certified_gap(shape,b);minimum=min(minimum,low)
     if low<3-1e-5:near.append([c.name,b.name,low])
 assert not hits and not near,[hits,near]
 q=added.boundingBox
 assert q.minPoint.y>=-.4000001 and q.maxPoint.y<=-.1999999
 q0,q1=restored.boundingBox,shell.boundingBox
 assert all(abs(getattr(a,k)-getattr(b,k))<1e-7 for a,b in [(q0.minPoint,q1.minPoint),(q0.maxPoint,q1.maxPoint)] for k in 'xyz')
 report={'revision':'rear_column_rib','rib_type':'One internal vertical reinforcement between middle and rightmost slot columns','rib_count':1,'rib_center_X_mm':261.7,'rib_projection_inward_mm':2,'original_wall_depth_mm':2,'reinforced_wall_depth_mm':4,'rib_crest_width_mm':2,'rib_attachment_width_mm':6,'rib_Z_span_mm':[0,25.4],'side_chamfers_mm':[2,2],'chamfer_angle_degrees':45,'exterior_envelope_unchanged':True,'original_nine_slots_preserved':True,'slot_count':12,'columns':3,'slots_per_column':4,'added_middle_slots_XZ_mm':new_slots,'new_slot_material_removed_mm3':sum(vol(a) for a in slot_material),'rear_slots_XZ_mm':slots,'blocked_passages':blocked,'rear_open_area_mm2':380.16,'previous_slot_bars_removed_mm3':removed_bar_volume,'added_material_mm3':vol(added),'original_material_removed_mm3':removed,'body_collisions':hits,'component_clearances_below_3mm':near,'minimum_component_clearance_lower_bound_mm':minimum,'base_parts_and_component_positions_unchanged':True,'main_and_modular_updated':True,'backup':'archive/pre-column-rib.zip','limits':'Geometry and slicing do not establish mechanical load capacity or operating temperature.'}
 with open(out+'rear-grille-ribs.json','w') as f:json.dump(report,f,indent=2)
 work.deleteMe()
 for c,b in [(uc,old),(elec,au)]:
  name=b.name.replace(' - 2mm vertical grille bars','');appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(shell));n.name=name+' - one internal rear column rib'
  if appearance:n.appearance=appearance
 with open(out+'ventilated-clip.json') as f:cooling=json.load(f)
 cooling.update({'revision':'rear_column_rib','rear_open_area_mm2':380.16,'rear_grille_ribs':'rear-grille-ribs.json','rear_opening_count_after_ribs':12,'rear_slots_XZ_mm':slots})
 with open(out+'ventilated-clip.json','w') as f:json.dump(cooling,f,indent=2)
 for c in [root,alt]:
  obsolete=c.attributes.itemByName('MIDI_POWER','rear_grille_ribs')
  if obsolete:obsolete.deleteMe()
  c.attributes.add('MIDI_POWER','rear_column_rib',json.dumps(report));c.attributes.add('MIDI_POWER','ventilated_clip',json.dumps(cooling))
 if not app.activeDocument.save('Restored all nine rear slots, added three matching middle-column slots, and replaced the dividing bars with one internal 2mm reinforcement between the middle and rightmost columns, with 2mm 45-degree side chamfers; exterior envelope and component positions unchanged.'):
  raise RuntimeError('Save failed')
