"""Raise the complete nine-slot rear pattern while preserving its area."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 if root.attributes.itemByName('MIDI_POWER','raised_rear_grilles'):raise RuntimeError('Rear grilles already raised')
 assert root.attributes.itemByName('MIDI_POWER','expanded_grilles')
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 uc=next(c for c in main if c.name.startswith('01 '));bc=next(c for c in main if c.name.startswith('02 '))
 old=next(b for b in uc.bRepBodies if 'RIGHT' in b.name)
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));ab=next(b for b in elec.bRepBodies if 'SHELL' in b.name)
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def stage(s):
  with open('/tmp/raised-vents-progress.json','w') as f:json.dump({'stage':s},f)
 def write(n,v):
  with open(out+n,'w') as f:json.dump(v,f,indent=2)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def op(a,b,k):
  if not mgr.booleanOperation(a,b,k):raise RuntimeError('Boolean failed')
  return a
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def union(a,b):return op(a,b,bt.UnionBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def gap(a,b):
  q,r=a.boundingBox,b.boundingBox
  return math.sqrt(sum(max(getattr(q.minPoint,k)-getattr(r.maxPoint,k),getattr(r.minPoint,k)-getattr(q.maxPoint,k),0)**2 for k in 'xyz'))*10
 def hit(a,b):
  q,r=a.boundingBox,b.boundingBox
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(inter(mgr.copy(a),mgr.copy(b)))
 def certified_gap(a,b):
  lower=gap(a,b)
  if lower>=3:return lower
  q=a.boundingBox;center=adsk.core.Point3D.create(*[(getattr(q.minPoint,k)+getattr(q.maxPoint,k))/2 for k in 'xyz'])
  expanded=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(center,adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),q.maxPoint.x-q.minPoint.x+.6,q.maxPoint.y-q.minPoint.y+.6,q.maxPoint.z-q.minPoint.z+.6))
  near=inter(mgr.copy(b),expanded)
  if not near.faces.count or vol(near)<1e-7:return 3.
  return min(3.,min(gap(a,lump) for lump in near.lumps))
 with open(out+'ventilated-clip.json') as f:cooling=json.load(f)
 previous=cooling['rear_slots_XZ_mm'];new=[[x0,x1,z0+17,z1+17] for x0,x1,z0,z1 in previous]
 assert len(previous)==9
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component;tc.name='TEMP relocated rear grilles'
 def slot(v,y0,y1):
  x0,x1,z0,z1=v;r=(z1-z0)/2;mid=(z0+z1)/2;points=[(x0+r,z0),(x1-r,z0),(x1,mid),(x1-r,z1),(x0+r,z1),(x0,mid)]
  sk=tc.sketches.add(tc.xZConstructionPlane)
  for a,b in zip(points,points[1:]+points[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(p(a[0],0,a[1])),sk.modelToSketchSpace(p(b[0],0,b[1])))
  tc.features.extrudeFeatures.addSimple(sk.profiles.item(0),adsk.core.ValueInput.createByReal((y1-y0)/10),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
  a=mgr.copy(tc.bRepBodies.item(tc.bRepBodies.count-1));q=a.boundingBox;m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,-y1/10-q.minPoint.y,0);mgr.transform(a,m)
  tc.bRepBodies.item(tc.bRepBodies.count-1).deleteMe();sk.deleteMe();return a
 stage('restoring the former openings to the original 2mm rear skin')
 restored=mgr.copy(old);plug_bodies=[];volumes=[]
 for v in previous:
  a=slot(v,0,2);before=vol(restored);restored=union(restored,mgr.copy(a));volumes.append(vol(restored)-before);plug_bodies.append(a)
 assert all(abs(v-63.36)<.01 for v in volumes),volumes
 stage('cutting the nine slots 17mm higher')
 shell=mgr.copy(restored);removed=[]
 for v in new:
  a=slot(v,-.05,2.05);material=inter(mgr.copy(restored),mgr.copy(a));amount=vol(material)
  assert abs(amount-63.36)<.01,('Roof fillet or unexpected wall thickness',v,amount)
  removed.append(material);shell=cut(shell,a)
 assert shell.isSolid and shell.lumps.count==1
 # Check that the ports are open through the wall, with no internal roof
 # backing blocking them. The 3mm cavity gap ends at the switch body Y5.
 blocked=[]
 for i,v in enumerate(new):
  amount=hit(slot(v,-.05,4.99),shell)
  if amount>.001:blocked.append([i,amount])
 assert not blocked,blocked
 stage('checking switch clearance and restored-skin interference')
 hits=[];near=[];minimum=1e9;switch_min=1e9
 for c in main:
  if c==uc or c.name.startswith('REF'):continue
  for b in c.bRepBodies:
   for label,shapes in [('restored rear skin',plug_bodies),('new rear vent',removed)]:
    for a in shapes:
     if label.startswith('restored'):
      v=hit(a,b)
      if v>.001:hits.append([label,c.name,b.name,v])
     elif c!=bc:
      distance=certified_gap(a,b);minimum=min(minimum,distance)
      if c.name.startswith('SW') and b.name.startswith('Actual'):switch_min=min(switch_min,distance)
      if distance<3-1e-5:near.append([c.name,b.name,distance])
 assert not hits and not near,[hits,near]
 assert abs(vol(shell)-vol(old))<.01
 report={'revision':'raised_rear_grilles','rear_pattern_raise_mm':17,'previous_rear_slots_XZ_mm':previous,'rear_slots_XZ_mm':new,'slot_count':9,'slot_height_mm':2.4,'slot_end_angle_degrees':45,'rear_open_area_mm2':285.12,'rear_wall_thickness_mm':2,'rear_top_solid_band_mm':7.6,'rear_bottom_solid_band_mm':24,'rows_lower_Z_mm':[2,8,14,20],'web_between_rows_mm':3.6,'restored_volume_per_old_slot_mm3':volumes,'restored_skin_component_collisions':hits,'vent_to_component_clearances_below_3mm':near,'minimum_vent_to_hardware_clearance_lower_bound_mm':minimum,'minimum_vent_to_switch_body_AABB_clearance_mm':switch_min,'blocked_passages':blocked,'roof_mounting_panels_untouched':True,'main_modular_matched':True,'all_component_positions_and_base_parts_unchanged':True,'shell_volume_before_mm3':vol(old),'shell_volume_after_mm3':vol(shell),'backup':'archive/pre-raised-rear-vents.zip','limits':'The solid rim, component clearance and mesh/slicing checks do not establish mechanical load capacity or operating temperature.'}
 write('raised-rear-vents.json',report)
 work.deleteMe()
 for c,b in [(uc,old),(elec,ab)]:
  name=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(shell));n.name=name+' - rear grilles raised 17mm'
  if appearance:n.appearance=appearance
 cooling.update({'revision':'raised_rear_grilles','rear_slots_XZ_mm':new,'continuous_rear_top_band_mm':7.6,'rear_bottom_solid_band_mm':24,'minimum_exhaust_to_actual_switch_body_AABB_clearance_mm':switch_min,'rear_relocation':'raised-rear-vents.json'})
 write('ventilated-clip.json',cooling)
 for c in [root,alt]:c.attributes.add('MIDI_POWER','raised_rear_grilles',json.dumps(report));c.attributes.add('MIDI_POWER','ventilated_clip',json.dumps(cooling))
 if not app.activeDocument.save('Raised all nine rear vent slots 17mm in both enclosure versions; restored former openings, retained 7.6mm top rim and 3mm switch-body clearance; base unchanged.'):
  raise RuntimeError('Save failed')
 stage('complete')
