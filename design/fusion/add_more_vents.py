"""Expand the Pololu inlet halo and add two low rear exhaust rows."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 if root.attributes.itemByName('MIDI_POWER','expanded_grilles'):raise RuntimeError('Expanded vents already installed')
 assert root.attributes.itemByName('MIDI_POWER','ventilated_clip')
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 uc=next(c for c in main if c.name.startswith('01 '));bc=next(c for c in main if c.name.startswith('02 '))
 oldshell=next(b for b in uc.bRepBodies if 'RIGHT' in b.name);oldbase=next(b for b in bc.bRepBodies if 'RIGHT' in b.name)
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'))
 ab=next(b for b in elec.bRepBodies if 'BASE' in b.name);au=next(b for b in elec.bRepBodies if 'SHELL' in b.name)
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def stage(s):
  with open('/tmp/more-vents-progress.json','w') as f:json.dump({'stage':s},f)
 def write(n,v):
  with open(out+n,'w') as f:json.dump(v,f,indent=2)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def op(a,b,k):
  if not mgr.booleanOperation(a,b,k):raise RuntimeError('Boolean failed')
  return a
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def union(a,b):return op(a,b,bt.UnionBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def slot(x0,x1,y0,y1):
  w=min(x1-x0,y1-y0);r=w/2
  if x1-x0>=y1-y0:
   a=box(x0+r,y0,-24.1,x1-r,y1,-21.999);ends=[(x0+r,(y0+y1)/2),(x1-r,(y0+y1)/2)]
  else:
   a=box(x0,y0+r,-24.1,x1,y1-r,-21.999);ends=[((x0+x1)/2,y0+r),((x0+x1)/2,y1-r)]
  for x,y in ends:a=union(a,mgr.createCylinderOrCone(p(x,y,-24.1),r/10,p(x,y,-21.999),r/10))
  return a
 stage('checking the perimeter of the Pololu mount for new inlets')
 floor_specs=[['Pololu surround - rear',216.4,235.6,17.,19.4],['Pololu surround - left',211.6,214.,22.,39.],['Pololu surround - right',237.2,239.6,22.,39.],['Pololu surround - front',216.4,225.2,41.2,43.6]]
 anchors=inter(mgr.copy(oldbase),box(190,0,-21.999,351,93,5));clearances=[];floor_removed=[];floor_area=0
 base=mgr.copy(oldbase)
 for label,x0,x1,y0,y1 in floor_specs:
  near=inter(mgr.copy(anchors),box(x0-3,y0-3,-21.999,x1+3,y1+3,5))
  lower=3.
  if near.faces.count:
   values=[]
   for lump in near.lumps:
    q=lump.boundingBox
    dx=max(x0-q.maxPoint.x*10,q.minPoint.x*10-x1,0);dy=max(y0-(-q.minPoint.y*10),(-q.maxPoint.y*10)-y1,0)
    values.append(math.hypot(dx,dy))
   lower=min(values)
  clearances.append([label,lower]);assert lower>=3-1e-5,(label,lower)
  a=slot(x0,x1,y0,y1);removed=vol(inter(mgr.copy(oldbase),mgr.copy(a)))
  w=min(x1-x0,y1-y0);length=max(x1-x0,y1-y0);area=(length-w)*w+math.pi*(w/2)**2
  assert abs(removed-area*2)<.01,('Floor opening depth',label,removed,area*2)
  floor_area+=area;floor_removed.append(removed);base=cut(base,a)
 stage('adding two rear rows below the existing slots')
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component;tc.name='TEMP expanded rear vents'
 def rear_slot(x0,x1,z0,z1):
  r=(z1-z0)/2;mid=(z0+z1)/2;points=[(x0+r,z0),(x1-r,z0),(x1,mid),(x1-r,z1),(x0+r,z1),(x0,mid)]
  sk=tc.sketches.add(tc.xZConstructionPlane)
  for a,b in zip(points,points[1:]+points[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(p(a[0],0,a[1])),sk.modelToSketchSpace(p(b[0],0,b[1])))
  tc.features.extrudeFeatures.addSimple(sk.profiles.item(0),adsk.core.ValueInput.createByString('2.1 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
  a=mgr.copy(tc.bRepBodies.item(tc.bRepBodies.count-1));q=a.boundingBox;m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,-.205-q.minPoint.y,0);mgr.transform(a,m)
  tc.bRepBodies.item(tc.bRepBodies.count-1).deleteMe();sk.deleteMe();return a
 rear_specs=[[x,x+14.4,z,z+2.4] for z in [-15.,-9.] for x in [220.5,266.]]
 shell=mgr.copy(oldshell);rear_removed=[];pocket=inter(mgr.copy(oldshell),box(240,2.001,-17,262,9,-3.21));pocket_loss=0
 for v in rear_specs:
  a=rear_slot(*v);amount=vol(inter(mgr.copy(oldshell),mgr.copy(a)));assert abs(amount-63.36)<.01,amount
  rear_removed.append(amount);pocket_loss+=vol(inter(mgr.copy(pocket),mgr.copy(a)));shell=cut(shell,a)
 assert pocket_loss<.001
 assert base.isSolid and shell.isSolid and base.lumps.count==shell.lumps.count==1
 added=[vol(cut(mgr.copy(a),mgr.copy(b))) for a,b in [(base,oldbase),(shell,oldshell)]]
 assert max(added)<.001,added
 report={'revision':'expanded_cooling_grilles','new_floor_slots_XY_mm':floor_specs,'new_rear_slots_XZ_mm':rear_specs,'extra_rear_rows':2,'new_slot_width_height_mm':2.4,'floor_slot_anchor_clearance_lower_bounds_mm':clearances,'minimum_slot_to_anchor_clearance_lower_bound_mm':min(r[1] for r in clearances),'new_floor_open_area_mm2':floor_area,'new_floor_removed_mm3':floor_removed,'new_rear_removed_mm3':rear_removed,'new_rear_open_area_mm2':4*31.68,'USB_pocket_material_removed_mm3':pocket_loss,'unintended_added_material_mm3':added,'rear_top_solid_band_mm':24.6,'rear_bottom_solid_band_mm':7,'rear_web_between_rows_mm':3.6,'main_and_modular_updated':True,'all_component_positions_unchanged':True,'clip_and_screw_support_geometry_unchanged':True,'assembly_path_argument':'Only material is removed, so previously validated collision-free component and assembly paths cannot acquire a new interference. Parts remain single connected solids; anchors retain at least 3mm solid floor margin.','backup':'archive/pre-expanded-vents.zip','limits':'Geometry and slicing checks do not establish stiffness under a specified load, air flow, operating temperatures or printed spring retention.'}
 write('expanded-vents.json',report)
 work.deleteMe()
 for c,b,a in [(bc,oldbase,base),(uc,oldshell,shell),(elec,ab,base),(elec,au,shell)]:
  name=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(a));n.name=name+' - expanded grilles'
  if appearance:n.appearance=appearance
 with open(out+'ventilated-clip.json') as f:cooling=json.load(f)
 cooling['revision']='expanded_cooling_grilles';cooling['floor_slots_XY_mm']+=floor_specs;cooling['rear_slots_XZ_mm']+=rear_specs
 cooling['floor_open_area_mm2']+=floor_area;cooling['rear_open_area_mm2']+=4*31.68;cooling['expanded_grilles']='expanded-vents.json';cooling['rear_bottom_solid_band_mm']=7
 write('ventilated-clip.json',cooling)
 for c in [root,alt]:c.attributes.add('MIDI_POWER','expanded_grilles',json.dumps(report));c.attributes.add('MIDI_POWER','ventilated_clip',json.dumps(cooling))
 if not app.activeDocument.save('Added four rounded inlet slots around Pololu mounts and two additional low rear exhaust rows; main/modular matched, supports retained with 3mm floor margins.'):
  raise RuntimeError('Save failed')
 stage('complete')
