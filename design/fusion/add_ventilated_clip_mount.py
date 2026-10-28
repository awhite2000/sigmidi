"""Raise the Pololu on PETG clips; ventilate both main and modular electronics."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 if root.attributes.itemByName('MIDI_POWER','ventilated_clip'):raise RuntimeError('Ventilated clips already installed')
 assert root.attributes.itemByName('MIDI_POWER','dc_input')
 ao=next(o for o in root.occurrences if o.component.name.startswith('ALT Chainable'));alt=ao.component
 main=[o for o in root.occurrences if o!=ao and not o.component.name.startswith(('TEMP','Temporary'))]
 def find(prefix):return next(o.component for o in main if o.component.name.startswith(prefix))
 uc,bc,pc=find('01 '),find('02 '),find('Pololu')
 oldbase=next(b for b in bc.bRepBodies if 'RIGHT' in b.name);oldshell=next(b for b in uc.bRepBodies if 'RIGHT' in b.name)
 oldboard=pc.bRepBodies.item(0)
 elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'))
 ab=next(b for b in elec.bRepBodies if 'BASE' in b.name);au=next(b for b in elec.bRepBodies if 'SHELL' in b.name)
 ap=next(o.component for o in elec.occurrences if 'Pololu' in o.component.name)
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def stage(s):
  with open('/tmp/ventilated-clip-progress.json','w') as f:json.dump({'stage':s},f)
 def write(n,v):
  with open(out+n,'w') as f:json.dump(v,f,indent=2)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def op(a,b,k):
  if not mgr.booleanOperation(a,b,k):raise RuntimeError('BRep operation failed')
  return a
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def union(a,b):return op(a,b,bt.UnionBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def move(a,dz=0,dy=0):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,-dy/10,dz/10);mgr.transform(a,m);return a
 def hit(a,b):
  q,r=a.boundingBox,b.boundingBox
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(inter(mgr.copy(a),mgr.copy(b)))
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component;tc.name='TEMP ventilated spring clip'
 def polygon(points,plane,axis,position,width):
  sk=tc.sketches.add(plane)
  for a,b in zip(points,points[1:]+points[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(a),sk.modelToSketchSpace(b))
  tc.features.extrudeFeatures.addSimple(sk.profiles.item(0),adsk.core.ValueInput.createByReal(width/10),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
  a=mgr.copy(tc.bRepBodies.item(tc.bRepBodies.count-1));q=a.boundingBox;m=adsk.core.Matrix3D.create()
  xyz=[0.,0.,0.];xyz['xyz'.index(axis)]=position/10-getattr(q.minPoint,axis);m.translation=adsk.core.Vector3D.create(*xyz);mgr.transform(a,m)
  tc.bRepBodies.item(tc.bRepBodies.count-1).deleteMe();sk.deleteMe()
  return a
 stage('replacing the solid surround with raised edge supports and PETG clips')
 # Remove only the old carrier, preserving the 2mm floor below it.
 base=cut(mgr.copy(oldbase),box(217.9,23.9,-22,234.165,36.99,-15.9))
 board=move(mgr.copy(oldboard),dz=6)
 seats=[box(219.3,24.4,-22,221.7,26.8,-11),box(219.3,34.09,-22,221.7,36.49,-11)]
 # A wider root narrows over a 45-degree shoulder to the known bare right edge.
 yz=[(29.25,-22),(31.65,-22),(31.65,-12.65),(31,-12),(31,-11),(29.9,-11),(29.9,-12),(29.25,-12.65)]
 seats.append(polygon([p(0,y,z) for y,z in yz],tc.yZConstructionPlane,'x',231.265,2.4))
 # Small L-shaped locators on the three supports stop lateral sliding.
 locators=[(218,24.4,-22,219.6,26.8,-9.484),(219.3,24.1,-22,221.7,25.7,-9.484),(218,34.09,-22,219.6,36.49,-9.484),(219.3,35.19,-22,221.7,36.79,-9.484),(232.465,29.25,-22,234.065,31.65,-9.484)]
 seats.extend(box(*v) for v in locators)
 # Two relaxed upright leaves. Only the small hook overlaps the PCB edge;
 # the underside ramp ends outside the PCB, leaving 0.2mm retention clearance.
 yz=[(23.6,-22),(25.2,-22),(25.2,-10.384),(25.8,-9.784),(26.4,-9.784),(26.4,-8.984),(25.2,-7.784),(23.6,-7.784)]
 arms=[polygon([p(0,y,z) for y,z in yz],tc.yZConstructionPlane,'x',225,2.4),polygon([p(0,60.89-y,z) for y,z in reversed(yz)],tc.yZConstructionPlane,'x',225,2.4)]
 # 0.8mm 45-degree root gussets reduce the abrupt thickness change. They
 # occupy only the outside of each leaf, preserving the free flexing gap.
 for coords in [[(22.8,-22),(23.6,-22),(23.6,-21.2)],[(37.29,-22),(38.09,-22),(37.29,-21.2)]]:
  seats.append(polygon([p(0,y,z) for y,z in coords],tc.yZConstructionPlane,'x',225,2.4))
 for a in seats+arms:base=union(base,mgr.copy(a))
 mount=cut(mgr.copy(base),cut(mgr.copy(oldbase),box(217.9,23.9,-22,234.165,36.99,-15.9)))
 contact=hit(board,mount)
 stage('cutting inlet grilles beneath the two boards')
 def slot_floor(x0,x1,y0,y1):
  r=(y1-y0)/2;cy=(y0+y1)/2
  a=box(x0+r,y0,-24.1,x1-r,y1,-21.999)
  for x in [x0+r,x1-r]:a=union(a,mgr.createCylinderOrCone(p(x,cy,-24.1),r/10,p(x,cy,-21.999),r/10))
  return a
 floor_specs=[['Pololu',223.6,230.,27.,29.4],['Pololu',223.6,230.,31.4,33.8]]
 floor_specs += [['DFR1075',242.,259.4,y,y+2.4] for y in [16.,22.,28.,34.,40.,46.,52.]]
 floor_cuts=[]
 for label,x0,x1,y0,y1 in floor_specs:
  a=slot_floor(x0,x1,y0,y1);floor_cuts.append(a);base=cut(base,a)
 stage('cutting rear exhaust slots below the switch bodies')
 rear_specs=[]
 for x0 in [220.5,266.]:
  for z0 in [-3.,3.]:rear_specs.append([x0,x0+14.4,z0,z0+2.4])
 rear_specs.append([243.,257.4,3.,5.4])
 shell=mgr.copy(oldshell);rear_cuts=[]
 for x0,x1,z0,z1 in rear_specs:
  dz=(z1-z0)/2;zm=(z0+z1)/2
  xz=[(x0+dz,z0),(x1-dz,z0),(x1,zm),(x1-dz,z1),(x0+dz,z1),(x0,zm)]
  a=polygon([p(x,0,z) for x,z in xz],tc.xZConstructionPlane,'y',-2.05,2.1)
  rear_cuts.append(a);shell=cut(shell,a)
 if not all(a.isSolid and a.lumps.count==1 for a in [base,shell]):raise RuntimeError('A print part disconnected')
 # Updated nonphysical wire corridors follow the raised regulator only.
 with open(out+'aux-power.json') as f:power=json.load(f)
 routes=power['wire_routes'];routes=json.loads(json.dumps(routes))
 for name,points in routes:
  if name.startswith(('9V','Center')):points[-1][2]+=6;points[-2][2]=-6
  else:points[0][2]+=6
 wire_shapes=[]
 for name,pts in routes:
  for j,(a,b) in enumerate(zip(pts,pts[1:])):wire_shapes.append((name+' segment '+str(j+1),mgr.createCylinderOrCone(p(*a),.08,p(*b),.08)))
 stage('checking installed hardware, wiring and base removal')
 hits=[];wirehits=[];paths=[];near=[];clearance_bounds=[]
 def clearance_lower(a,b):
  q,r=a.boundingBox,b.boundingBox
  g=math.sqrt(sum(max(getattr(q.minPoint,k)-getattr(r.maxPoint,k),getattr(r.minPoint,k)-getattr(q.maxPoint,k),0)**2 for k in 'xyz'))*10
  if g>=3:return g
  center=adsk.core.Point3D.create(*[(getattr(q.minPoint,k)+getattr(q.maxPoint,k))/2 for k in 'xyz'])
  pad=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(center,adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),q.maxPoint.x-q.minPoint.x+.6,q.maxPoint.y-q.minPoint.y+.6,q.maxPoint.z-q.minPoint.z+.6))
  return 3.0 if vol(inter(mgr.copy(b),pad))<1e-7 else g
 for o in main:
  c=o.component
  if c in [bc,pc] or c.name.startswith('REF'):continue
  for b in c.bRepBodies:
   if c==uc and b==oldshell:b=shell
   for label,a in [('new carrier',mount),('raised Pololu',board)]:
    v=hit(a,b)
    if v>.001:hits.append([label,c.name,b.name,v])
    g=clearance_lower(a,b);clearance_bounds.append(g)
    if g<3-1e-5:near.append([label,c.name,b.name,g])
 if contact>.001:hits.append(['carrier versus actual converter',contact])
 for name,a in wire_shapes:
  for o in main:
   c=o.component
   if c in [pc,find('DFRobot')] or c.name.startswith('REF'):continue
   if name.startswith(('9V','Center')) and c.name.startswith('DC power'):continue
   for b in c.bRepBodies:
    if c==bc and b==oldbase:b=base
    if c==uc and b==oldshell:b=shell
    v=hit(a,b)
    if v>.001:wirehits.append([name,c.name,b.name,v])
 for i in range(41):
  dz=-i*.5
  if i%10==0:stage('checking base withdrawal sample '+str(i+1)+'/41')
  for label,a in [('added mount',mount),('raised converter',board)]:
   moving=move(mgr.copy(a),dz=dz)
   for u in uc.bRepBodies:
    if u==oldshell:u=shell
    v=hit(moving,u)
    if v>.001:paths.append([label,'floor withdrawal',dz,v])
 for i in range(41):
  moving=move(mgr.copy(board),dz=i*.25)
  for a in seats:
   v=hit(moving,a)
   if v>.001:paths.append(['board lowered onto edge seats',i*.25,v])
  for sign,a in zip([-1,1],arms):
   v=hit(moving,move(mgr.copy(a),dy=sign*.6))
   if v>.001:paths.append(['board inserted between flexed leaves',i*.25,v])
 # A rigid, outward-shifted leaf is conservative for the free upper portion.
 flex_hits=[]
 for sign,a in zip([-1,1],arms):
  moving=move(mgr.copy(a),dy=sign*.6)
  for o in main:
   if o.component in [bc,pc] or o.component.name.startswith('REF'):continue
   for b in o.component.bRepBodies:
    if o.component==uc and b==oldshell:b=shell
    v=hit(moving,b)
    if v>.001:flex_hits.append([o.component.name,b.name,v])
 # Mechanical keepouts: exhausts are below Z5.4, leaving an uninterrupted
 # 24.6mm rear top band. Actual raised switch bodies begin at Z12.
 switch_clear=[]
 for o in main:
  if not o.component.name.startswith('SW'):continue
  for b in o.component.bRepBodies:
   if not b.name.startswith('Actual'):continue
   q=b.boundingBox
   for a in rear_cuts:
    r=a.boundingBox;g=math.sqrt(sum(max(getattr(q.minPoint,k)-getattr(r.maxPoint,k),getattr(r.minPoint,k)-getattr(q.maxPoint,k),0)**2 for k in 'xyz'))*10
    switch_clear.append(g)
 # Vents must not sever any anchor footprint above the floor or USB pocket.
 anchor_loss=0
 for a in floor_cuts:anchor_loss+=hit(a,cut(mgr.copy(oldbase),box(190,0,-24.1,351,93,-22)))
 pocket=inter(mgr.copy(oldshell),box(240,2.01,-17,262,8,-3.21))
 pocket_loss=sum(hit(a,pocket) for a in rear_cuts)
 rear_removed=[vol(inter(mgr.copy(oldshell),mgr.copy(a))) for a in rear_cuts]
 expected_rear=[(x1-x0-1.2)*2.4*2 for x0,x1,_,_ in rear_specs]
 if any(abs(a-b)>.01 for a,b in zip(rear_removed,expected_rear)):raise RuntimeError('Rear vents do not open through the full 2mm skin: '+str(rear_removed))
 report={'revision':'ventilated_petg_clip','converter_raise_mm':6,'PCB_bottom_Z_mm':-11,'populated_Z_mm':[-12.349875,-8.184],
  'component_to_inside_floor_clearance_mm':9.650125,'support':'Three small bare-edge seats; two opposing relaxed PETG leaves, no adhesive required.',
  'positive_lateral_locators':True,'lateral_locator_boxes_mm':locators,'lateral_clearance_X_mm':.4,'lateral_clearance_Y_mm':.3,'spring_leaf_thickness_mm':1.6,'spring_leaf_width_mm':2.4,'leaf_height_mm':14.216,'root_gusset_mm':.8,'retaining_overlap_mm':.4,'PCB_top_retention_clearance_mm':.2,'required_outward_assembly_stroke_mm':.6,
  'clip_tip_underside':'0.6mm 45-degree ramp outside the PCB plus 0.6mm short ledge; 45-degree entry ramp',
  'floor_slots_XY_mm':floor_specs,'floor_slot_width_mm':2.4,'floor_slot_ends':'R1.2','floor_open_area_mm2':sum((x1-x0-2.4)*2.4+math.pi*1.2**2 for _,x0,x1,_,_ in floor_specs),
  'rear_slots_XZ_mm':rear_specs,'rear_removed_volume_mm3':rear_removed,'rear_slot_height_mm':2.4,'rear_open_area_mm2':sum((x1-x0-1.2)*2.4 for x0,x1,_,_ in rear_specs),'rear_slot_ends':'45 degrees to suit right-shell end-down printing',
  'continuous_rear_top_band_mm':24.6,'minimum_exhaust_to_actual_switch_body_AABB_clearance_mm':min(switch_clear),'minimum_base_web_between_DFR_slots_mm':3.6,
  'anchor_material_removed_mm3':anchor_loss,'USB_pocket_material_removed_mm3':pocket_loss,'component_clearances_below_3mm':near,'minimum_other_component_clearance_lower_bound_mm':min(clearance_bounds),'body_collisions':hits,'wire_collisions':wirehits,'assembly_collisions':paths,'outward_clip_sweep_collisions':flex_hits,
  'new_carrier_to_exact_converter_intersection_mm3':contact,'wire_routes':routes,'base_removal_samples':41,'withdrawal_scope':'New mount and raised regulator swept against the shell; the rest of the base is unchanged apart from material removal and retains its previously validated path.','main_and_modular_updated':True,'unchanged':'DFRobot and all control positions, joints, screw supports, outer dimensions',
  'backup':'archive/pre-ventilated-clip.zip','limits':'Geometric fit and slicer checks are not a thermal or spring-fatigue test. Verify retention and hot-operation temperature on the actual print. The leaves have clearance after seating to minimize sustained stress; do not glue or foam-wrap the module. Leave free air below the floor grilles in use.'}
 write('ventilated-clip-candidate.json',report)
 if hits or near or wirehits or paths or flex_hits or anchor_loss>.001 or pocket_loss>.001:raise RuntimeError('Ventilated clip fit failed; inspect candidate report')
 stage('committing matching main and modular electronics parts')
 # Delete temporary construction before obtaining the native references again.
 work.deleteMe()
 def replace(c,b,a,suffix=''):
  name=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(a));n.name=name+suffix
  if appearance:n.appearance=appearance
 for c,b,a in [(bc,oldbase,base),(uc,oldshell,shell),(elec,ab,base),(elec,au,shell)]:replace(c,b,a,' - ventilated clip revision')
 replace(pc,pc.bRepBodies.item(0),board)
 replace(ap,ap.bRepBodies.item(0),board)
 for parent in [root,alt]:
  wires=next(o.component for o in parent.occurrences if o.component.name.startswith('REF AUX DC'))
  for b in list(wires.bRepBodies):b.deleteMe()
  for name,a in wire_shapes:b=wires.bRepBodies.add(mgr.copy(a));b.name=name
  wires.isLightBulbOn=False
 with open(out+'converter-carrier.json') as f:carrier=json.load(f)
 carrier.update({'revision':'ventilated_petg_clip','PCB_bottom_Z_mm':-11,'populated_Z_mm':[-12.349875,-8.184],'under_component_floor_clearance_mm':9.650125,'carrier':report['support'],'carrier_outer_XY_mm':[[218,22.8],[234.065,38.09]],'PCB_edge_guide_clearance_mm':.8,'spring_clip_details':'ventilated-clip.json','body_collisions':hits,'assembly_collisions':paths,'converter_component_carrier_intersection_mm3':contact})
 power.update({'revision':'ventilated_petg_clip','wire_routes':routes,'wire_collisions':wirehits,'assembly_collisions':paths,'thermal_revision':'ventilated-clip.json'})
 # The previous socket separation table included the old converter elevation.
 power.pop('socket_component_clearance_lower_bounds_mm',None)
 power['socket_clearance_validation']='Socket unchanged; carrier and converter move only in the interior. Rechecked new-carrier, raised-board and wire interference in ventilated-clip.json; original socket hardware clearances remain in archive/pre-ventilated-clip.zip.'
 for name,v in [('converter-carrier.json',carrier),('aux-power.json',power),('ventilated-clip.json',report)]:write(name,v)
 for c in [root,alt]:c.attributes.add('MIDI_POWER','ventilated_clip',json.dumps(report));c.attributes.add('MIDI_POWER','converter_carrier',json.dumps(carrier));c.attributes.add('MIDI_POWER','dc_input',json.dumps(power))
 if not app.activeDocument.save('Raised Pololu 6mm on two PETG snap leaves and three open edge seats; added bottom and rear ventilation, preserving controls, screw supports and USB pocket in main and modular models.'):
  raise RuntimeError('Save failed')
 stage('complete')
