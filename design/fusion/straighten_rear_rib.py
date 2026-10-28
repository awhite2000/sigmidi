"""Straighten the roof-to-base rib and merge it into the USB pocket chamfer."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 if root.attributes.itemByName('MIDI_POWER','straight_rear_rib'):raise RuntimeError('Rear rib already straightened')
 assert root.attributes.itemByName('MIDI_POWER','full_height_rear_rib')
 assert root.attributes.itemByName('MIDI_POWER','reinforced_floor_grilles')
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 uc=next(c for c in main if c.name.startswith('01 '));bc=next(c for c in main if c.name.startswith('02 '))
 old=next(b for b in uc.bRepBodies if 'RIGHT' in b.name);base=next(b for b in bc.bRepBodies if 'RIGHT' in b.name)
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));au=next(b for b in elec.bRepBodies if 'SHELL' in b.name)
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes;cache={}
 def stage(s):
  with open('/tmp/straight-rear-rib-progress.json','w') as f:json.dump({'stage':s},f)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def bounds(a):
  key=id(a)
  if key not in cache:cache[key]=(a,a.boundingBox)
  return cache[key][1]
 def known(a,b):cache[id(a)]=(a,b.boundingBox);return a
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
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component;tc.name='TEMP straight rear rib'
 def prism(x0,x1,z0,z1):
  # 2mm inward projection, 2mm crest and 45-degree flanks at each end.
  pts=[(x0,1.95),(x1,1.95),(x1,2),(x1-2,4),(x0+2,4),(x0,2)]
  sk=tc.sketches.add(tc.xYConstructionPlane)
  for a,b in zip(pts,pts[1:]+pts[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(p(*a,0)),sk.modelToSketchSpace(p(*b,0)))
  tc.features.extrudeFeatures.addSimple(sk.profiles.item(0),adsk.core.ValueInput.createByReal((z1-z0)/10),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
  a=mgr.copy(tc.bRepBodies.item(tc.bRepBodies.count-1));q=bounds(a);a=shift(a,z0-q.minPoint.z*10);cache.pop(id(a),None)
  tc.bRepBodies.item(tc.bRepBodies.count-1).deleteMe();sk.deleteMe();return known(a,box(x0,1.95,z0,x1,4,z1))
 stage('removing the lower offset and constructing the straight rib')
 straight=prism(258.7,264.7,-22,27.1)
 lower_old=prism(266.5,272.5,-22,0);bridge_old=prism(258.7,272.5,-1.5,0)
 offset_tool=union(mgr.copy(lower_old),mgr.copy(bridge_old))
 removal_tool=inter(cut(mgr.copy(offset_tool),mgr.copy(straight)),box(258.7,2,-22.001,272.51,4.01,.001))
 cleaned=cut(mgr.copy(old),removal_tool)
 candidate=cut(mgr.copy(straight),mgr.copy(base));shell=union(cleaned,candidate)
 assert shell.isSolid and shell.lumps.count==1
 added=known(cut(mgr.copy(shell),mgr.copy(old)),box(258.7,1.95,-22,264.7,4,27.1))
 removed=known(cut(mgr.copy(old),mgr.copy(shell)),box(262.7,2,-22.001,272.51,4.01,.001))
 assert vol(added)>40 and vol(removed)>100,[vol(added),vol(removed)]
 assert vol(cut(mgr.copy(removed),mgr.copy(offset_tool)))<.001
 pocket=inter(mgr.copy(old),box(240,2.001,-17,261.1,9,-3.21))
 pocket_loss=hit(removed,pocket);assert pocket_loss<.001
 merge_volume=hit(straight,pocket);assert merge_volume>.1,merge_volume
 assert hit(removed,box(240,0,-22.01,280,2,28))<.001
 # Preserve at least the specified 1mm envelope around the USB-C socket.
 connector_envelope=box(245.22,2.776,-13.5,256.17,12.526,-7.24)
 assert hit(added,connector_envelope)<.001
 stage('checking the straight rib against hardware and ventilation')
 hits=[];near=[];wires=[];local=[];minimum=1e9;general_min=1e9
 for c in main:
  if c in [uc,bc]:continue
  for b in c.bRepBodies:
   amount=hit(straight,b)
   if c.name.startswith('REF'):
    if amount>.001:wires.append([c.name,b.name,amount])
    continue
   if amount>.001:hits.append([c.name,b.name,amount])
   low=certified_gap(straight,b);minimum=min(minimum,low)
   # The user's straight pocket/rib merge uses the existing close PCB-front
   # area. Record its local 1mm clearance explicitly, rather than asserting 3.
   allowed=c.name.startswith(('DFRobot','PCB screws'))
   required=1 if allowed else 3
   if not allowed:general_min=min(general_min,low)
   if low<required-1e-5:near.append([c.name,b.name,low,required])
   if allowed and low<3-1e-5:local.append([c.name,b.name,low])
 assert not hits and not near and not wires,[hits,near,wires]
 with open(out+'rear-grille-ribs.json') as f:previous=json.load(f)
 blocked=[]
 for i,(x0,x1,z0,z1) in enumerate(previous['rear_slots_XZ_mm']):
  amount=hit(added,box(x0,-.05,z0,x1,4.99,z1))
  if amount>.001:blocked.append([i,amount])
 assert not blocked,blocked
 assembled_overlap=hit(candidate,base);assert assembled_overlap<.001
 stage('checking the straight base seat and downward removal')
 contact_slice=inter(mgr.copy(candidate),box(258.6,1.94,-22.01,264.8,4.01,-17))
 contact_volume=hit(contact_slice,shift(mgr.copy(base),.01));assert contact_volume>.025,contact_volume
 assembly=[];samples=[0,-.01,-.25,-.5,-1,-2,-5,-10,-20];bq=bounds(base)
 for dz in samples:
  moving=shift(mgr.copy(base),dz)
  qb=adsk.core.BoundingBox3D.create(adsk.core.Point3D.create(bq.minPoint.x,bq.minPoint.y,bq.minPoint.z+dz/10),adsk.core.Point3D.create(bq.maxPoint.x,bq.maxPoint.y,bq.maxPoint.z+dz/10));cache[id(moving)]=(moving,qb)
  amount=hit(candidate,moving)
  if amount>.001:assembly.append([dz,amount])
 assert not assembly,assembly
 q0,q1=bounds(old),bounds(shell)
 assert all(abs(getattr(a,k)-getattr(b,k))<1e-7 for a,b in [(q0.minPoint,q1.minPoint),(q0.maxPoint,q1.maxPoint)] for k in 'xyz')
 report={'revision':'straight_rear_rib','rib_count':1,'upper_rib_center_X_mm':261.7,'lower_leg_center_X_mm':261.7,'lower_leg_offset_X_mm':0,'rib_projection_inward_mm':2,'side_chamfers_mm':[2,2],'chamfer_angle_degrees':45,'rib_crest_width_mm':2,'rib_attachment_width_mm':6,'rib_Z_span_mm':[-22,27.1],'total_internal_height_mm':49.1,'base_seating_Z_mm':-22,'roof_inner_Z_mm':27,'merged_with_existing_USB_pocket_chamfer':True,'USB_pocket_original_material_removed_mm3':pocket_loss,'rib_intersection_with_original_pocket_mm3':merge_volume,'USB_socket_1mm_envelope_preserved':True,'base_contact_probe_translation_mm':.01,'base_contact_probe_volume_mm3':contact_volume,'base_contact_projected_area_mm2_approx':contact_volume/.01,'assembled_base_overlap_mm3':assembled_overlap,'body_collisions':hits,'component_clearances_below_required_minimum':near,'permitted_local_PCB_and_fastener_clearances_below_3mm':local,'local_required_clearance_mm':1,'minimum_component_clearance_lower_bound_mm':minimum,'minimum_other_component_clearance_lower_bound_mm':general_min,'wire_collisions':wires,'blocked_passages':blocked,'base_withdrawal_samples_Z_mm':samples,'assembly_collisions':assembly,'straightening_added_material_mm3':vol(added),'removed_offset_material_mm3':vol(removed),'slot_count':12,'rear_open_area_mm2':380.16,'base_geometry_unchanged':True,'component_positions_unchanged':True,'exterior_envelope_unchanged':True,'main_and_modular_updated':True,'backup':'archive/pre-straight-rear-rib.zip','limits':'The straight rib uses 1mm nominal local PCB-front clearance instead of the previous 3mm offset clearance; CAD seating and slicing do not establish printed contact pressure or load strength.'}
 stage('committing matched straight ribs in both shells')
 work.deleteMe()
 for c,b in [(uc,old),(elec,au)]:
  name=b.name.replace(' - roof to base rear rib','');appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(shell));n.name=name+' - straight rear rib merged into USB pocket'
  if appearance:n.appearance=appearance
 with open(out+'straight-rear-rib.json','w') as f:json.dump(report,f,indent=2)
 with open(out+'full-height-rear-rib.json','w') as f:json.dump(report,f,indent=2)
 previous.update({'revision':'straight_rear_rib','rib_type':'Straight roof-to-base internal support merged with the existing USB pocket chamfer','rib_Z_span_mm':[-22,27.1],'straightening':'straight-rear-rib.json','minimum_component_clearance_lower_bound_mm':minimum,'minimum_other_component_clearance_lower_bound_mm':general_min,'component_clearances_below_3mm':local,'component_clearances_below_required_minimum':near,'permitted_local_PCB_and_fastener_clearances_below_3mm':local})
 with open(out+'rear-grille-ribs.json','w') as f:json.dump(previous,f,indent=2)
 with open(out+'ventilated-clip.json') as f:cooling=json.load(f)
 cooling.update({'revision':'straight_rear_rib','straight_rear_rib':'straight-rear-rib.json'})
 with open(out+'ventilated-clip.json','w') as f:json.dump(cooling,f,indent=2)
 for c in [root,alt]:c.attributes.add('MIDI_POWER','straight_rear_rib',json.dumps(report));c.attributes.add('MIDI_POWER','full_height_rear_rib',json.dumps(report));c.attributes.add('MIDI_POWER','rear_column_rib',json.dumps(previous));c.attributes.add('MIDI_POWER','ventilated_clip',json.dumps(cooling))
 if not app.activeDocument.save('Straightened the rear roof-to-base rib at X261.7 and merged it into the USB pocket chamfer; removed the lower offset, retained USB socket clearance and local 1mm PCB-front gap, unchanged base and exterior.'):
  raise RuntimeError('Save failed')
 stage('complete')
