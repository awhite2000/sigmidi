"""Capture the active main/modular CAD and export their current print solids."""
import adsk.core,adsk.fusion
import json,math,hashlib,datetime


def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 for old in list(root.occurrences):
  if old.component.name=='TEMP switch label tools' and old.component.bRepBodies.count==0:old.deleteMe()
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 revision='display_m2x5' if root.attributes.itemByName('MIDI_FDM','display_m2x5') else 'snug_06_tolerances' if root.attributes.itemByName('MIDI_FDM','snug_06_tolerances') else 'refined_positioning_ribs' if root.attributes.itemByName('MIDI_FDM','refined_positioning_ribs') else 'enclosure_wall_reinforcement' if root.attributes.itemByName('MIDI_FDM','enclosure_wall_reinforcement') else 'upper_corner_walls' if root.attributes.itemByName('MIDI_FDM','upper_corner_walls') else 'wide_pololu_clips' if root.attributes.itemByName('MIDI_FDM','wide_pololu_clips') else 'base_corner_repair' if root.attributes.itemByName('MIDI_FDM','base_corner_repair') else 'recessed_switch_labels' if root.attributes.itemByName('MIDI_FDM','recessed_switch_labels') else 'extra_right_base_screws' if root.attributes.itemByName('MIDI_FDM','extra_right_base_screws') else 'rear_vent_membranes' if root.attributes.itemByName('MIDI_FDM','rear_vent_membranes') else 'straight_rear_rib' if root.attributes.itemByName('MIDI_POWER','straight_rear_rib') else 'full_height_rear_rib' if root.attributes.itemByName('MIDI_POWER','full_height_rear_rib') else 'reinforced_floor_grilles' if root.attributes.itemByName('MIDI_POWER','reinforced_floor_grilles') else 'rear_column_rib' if root.attributes.itemByName('MIDI_POWER','rear_column_rib') else 'raised_rear_grilles' if root.attributes.itemByName('MIDI_POWER','raised_rear_grilles') else 'expanded_cooling_grilles' if root.attributes.itemByName('MIDI_POWER','expanded_grilles') else 'ventilated_petg_clip' if root.attributes.itemByName('MIDI_POWER','ventilated_clip') else ('aux_dc_power' if root.attributes.itemByName('MIDI_POWER','dc_input') else 'straight_base_glue_lips')
 ao=next(o for o in root.occurrences if o.component.name.startswith('ALT Chainable'));alt=ao.component
 with open(out+'modular/modular-design.json') as f:alt.attributes.add('MIDI_MODULAR','configuration',json.dumps(json.load(f)))
 main=[o for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 def find(prefix):return next(o.component for o in main if o.component.name.startswith(prefix))
 def get(c,s):return next(b for b in c.bRepBodies if s in b.name)
 uc,bc=find('01 '),find('02 ');sl,sr=get(uc,'LEFT'),get(uc,'RIGHT');bl,br=get(bc,'LEFT'),get(bc,'RIGHT')
 pair=next(o.component for o in alt.occurrences if o.component.name.startswith('Repeatable pair'))
 left=next(o.component for o in alt.occurrences if o.component.name.startswith('Leftmost pair'))
 cap=next(o.component for o in alt.occurrences if o.component.name.startswith('Closed left cap'))
 es=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'))
 ps,pb=get(pair,'SHELL'),get(pair,'BASE');ls=get(left,'SHELL');cb=next(iter(cap.bRepBodies))
 if not root.attributes.itemByName('MIDI_FDM','straight_base_glue_lips'):raise RuntimeError('Wrong model revision')
 def stage(s):
  with open('/tmp/current-views-progress.json','w') as f:json.dump({'stage':s},f)
 def write(n,data):
  with open(out+n,'w') as f:json.dump(data,f,indent=2)
 original=app.activeViewport.camera;visibility=[(o,o.isLightBulbOn) for o in root.occurrences]
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());temp=work.component;temp.name='TEMP current views';temp.isOriginFolderLightBulbOn=False
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def move(a,dx=0,dy=0,dz=0):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,-dy/10,dz/10);mgr.transform(a,m);return a
 def clear():
  for b in list(temp.bRepBodies):b.deleteMe()
 def add(b,name=None,dx=0,dy=0,dz=0):
  a=move(mgr.copy(b),dx,dy,dz);n=temp.bRepBodies.add(a);n.name=name or ('Current section' if b.isTemporary else b.name)
  if not b.isTemporary:n.appearance=b.appearance
  return n
 def camera(eye,target,bodies=None):
  direction=adsk.core.Vector3D.create(*[target[i]-eye[i] for i in range(3)]);direction.normalize()
  upseed=adsk.core.Vector3D.create(0,1,0) if abs(direction.z)>.999 else adsk.core.Vector3D.create(0,0,1)
  bodies=list(temp.bRepBodies) if bodies is None else bodies
  if not bodies:raise RuntimeError('No bodies to frame')
  if temp.isValid and temp.bRepBodies.count and direction.z>0:
   rot=adsk.core.Matrix3D.create();rot.setToRotation(math.pi,adsk.core.Vector3D.create(1,0,0),adsk.core.Point3D.create(0,0,0))
   for b in list(temp.bRepBodies):
    a=mgr.copy(b);appearance=b.appearance;name=b.name;mgr.transform(a,rot);move(a,dz=100);b.deleteMe();n=temp.bRepBodies.add(a);n.name=name;n.appearance=appearance
   direction.transformBy(rot);upseed.transformBy(rot);bodies=list(temp.bRepBodies)
  right=direction.crossProduct(upseed);right.normalize();up=right.crossProduct(direction);up.normalize()
  pts=[]
  for b in bodies:
   q=b.boundingBox
   for x in [q.minPoint.x,q.maxPoint.x]:
    for y in [q.minPoint.y,q.maxPoint.y]:
     for z in [q.minPoint.z,q.maxPoint.z]:pts.append(adsk.core.Vector3D.create(x,y,z))
  ranges=[]
  for axis in [right,up,direction]:
   dots=[v.dotProduct(axis) for v in pts];ranges.append((min(dots),max(dots)))
  mid=[(a+b)/2 for a,b in ranges]
  center=adsk.core.Point3D.create(*[getattr(right,k)*mid[0]+getattr(up,k)*mid[1]+getattr(direction,k)*mid[2] for k in 'xyz'])
  cam=adsk.core.Camera.create();cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
  cam.target=center;cam.eye=adsk.core.Point3D.create(center.x-direction.x*100,center.y-direction.y*100,center.z-direction.z*100);cam.upVector=up
  aspect=min(1800/1100,app.activeViewport.width/app.activeViewport.height);h=max(ranges[1][1]-ranges[1][0],(ranges[0][1]-ranges[0][0])/aspect)*1.12
  cam.setExtents(h*aspect,h);cam.isFitView=False;cam.isSmoothTransition=False;app.activeViewport.camera=cam;adsk.doEvents();app.activeViewport.refresh()
 images=[]
 def capture(name):
  if not app.activeViewport.saveAsImageFile(out+name,1800,1100):raise RuntimeError('Capture failed '+name)
  images.append(name)
 def native_visible(modular=False):
  result=[]
  for o in root.allOccurrences:
   if o.component==temp:continue
   if modular != o.fullPathName.startswith(ao.name+'+'):continue
   for b in o.bRepBodies:
    if b.isVisible:result.append(b)
  return result
 def hide():
  for o,_ in visibility:o.isLightBulbOn=False
 stage('exporting revised shell and base STLs')
 def export(name,b,rotation=0):
  a=mgr.copy(b)
  if rotation:
   m=adsk.core.Matrix3D.create();m.setToRotation(rotation*math.pi/2,adsk.core.Vector3D.create(0,1,0),adsk.core.Point3D.create(0,0,0));mgr.transform(a,m)
  q=a.boundingBox;m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(-q.minPoint.x,-q.minPoint.y,-q.minPoint.z);mgr.transform(a,m)
  n=temp.bRepBodies.add(a);opt=d.exportManager.createSTLExportOptions(n,out+name+'.stl');opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh;opt.isBinaryFormat=True
  if not d.exportManager.execute(opt):raise RuntimeError('STL failed '+name)
  n.deleteMe()
 for name,b in [('print/base-left',bl),('print/base-right',br),('modular/pair-base',pb)]:export(name,b)
 export('print/shell-right',sr,1)
 export('print/shell-left',sl,-1)
 # Exact upper-deck coupons, including seating lands and the tightened receiver.
 for name,b,rotation in [('left',sl,-1),('right',sr,1)]:
  coupon=mgr.copy(b);assert mgr.booleanOperation(coupon,box(183.65,20,20,203.65,26,30.01),bt.IntersectionBooleanType)
  assert coupon.isSolid and coupon.lumps.count==1
  export('print/fit-coupon-'+name,coupon,rotation)
 export('modular/pair-shell',ps,1);export('modular/pair-shell-at-cap',ls,1);export('modular/left-cap',cb,-1)
 library=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Engraved pair'))
 variants=[(o.component.name,next(iter(o.component.bRepBodies))) for o in library.occurrences]
 for name,b in variants:export('modular/'+name,b,1)
 def size(b,rotate=False):
  q=b.boundingBox;s=[(getattr(q.maxPoint,k)-getattr(q.minPoint,k))*10 for k in 'xyz'];return [s[2],s[1],s[0]] if rotate else s
 mainparts=[{'name':n,'size_mm':size(b,'shell' in n),'solid':b.isSolid,'lumps':b.lumps.count,'orientation':'outer end on bed; seam up' if 'shell' in n else 'outside floor down; posts up'} for n,b in [('shell-left',sl),('shell-right',sr),('base-left',bl),('base-right',br)]]
 write('print/print-export.json',{'revision':revision,'parts':mainparts,'unchanged_meshes':['shell-left','shell-right','base-left','fit-coupon-left','fit-coupon-right'],'base_joint':'straight-base-lips.json'})
 modparts=[{'name':n,'size_mm':size(b,n!='pair-base'),'solid':b.isSolid,'lumps':b.lumps.count,'orientation':'outside floor down; posts up' if n=='pair-base' else ('closed left end on bed; +X print up' if n=='left-cap' else 'right edge on bed; -X print up')} for n,b in [('pair-shell',ps),('pair-base',pb),('pair-shell-at-cap',ls),('left-cap',cb)]]
 for name,b in variants:modparts.append({'name':name,'size_mm':size(b,True),'solid':b.isSolid,'lumps':b.lumps.count,'orientation':'right edge on bed; -X print up'})
 write('modular/print-export.json',{'revision':revision,'parts':modparts,'universal_pair_base':True})
 stage('capturing populated main enclosure and exact top projection')
 hide()
 for o in main:o.isLightBulbOn=not o.component.name.startswith('REF')
 camera((40,-32,24),(17.5,-4.6,0),native_visible());capture('assembled.png')
 camera((38,22,18),(17.5,-4.6,0),native_visible());capture('rear.png')
 camera((17.5,-4.6,45),(17.5,-4.6,0),native_visible());capture('panel-top.png')
 for o in main:
  if o.component==uc:o.isLightBulbOn=False
 camera((40,-32,26),(17.5,-4.6,-.5),native_visible());capture('internal.png')
 for o in main:o.isLightBulbOn=o.component==bc or o.component.name.startswith(('LCD ','DFRobot','Double TRS','PCB screws','Pololu','DC power'))
 camera((40,-32,26),(17.5,-4.6,-.5),native_visible());capture('mounted-boards.png')
 stage('capturing recessed switch labels')
 hide();clear();add(sl);add(sr)
 camera((17.5,-4.6,45),(17.5,-4.6,0));capture('switch-labels.png');clear()
 stage('capturing shell underside, supports and seam details')
 hide();clear()
 for b in [sl,sr]:add(b)
 camera((40,-25,-30),(17.5,-4.6,0));capture('base-open.png');clear()
 for b in [bl,br]:add(b,dz=24)
 camera((40,-25,28),(17.5,-4.6,2));capture('base-supports.png');clear()
 for b in [sl,sr]:add(b)
 for b in [bl,br]:add(b,dz=-12)
 camera((40,-30,22),(17.5,-4.6,-.5));capture('print/split-exploded.png');clear()
 for b in [bl,br]:
  a=mgr.copy(b)
  if not mgr.booleanOperation(a,box(186,10,-24.01,202,32,-18.5),bt.IntersectionBooleanType):raise RuntimeError('Lip detail crop failed')
  if a.faces.count:add(a)
 camera((18,-8,10),(19.4,-2.1,-2.15));capture('print/straight-base-lips.png');clear()
 for b in [sl,bl]:
  a=mgr.copy(b)
  if not mgr.booleanOperation(a,box(100,82,-24.01,115,93,-16),bt.IntersectionBooleanType):raise RuntimeError('Bearing detail crop failed')
  if a.faces.count:add(a)
 camera((9,-11,-3),(10.75,-8.75,-2.05));capture('print/perimeter-ledge-detail.png');clear()
 stage('capturing repaired continuous front-right floor')
 add(br)
 cam=adsk.core.Camera.create();cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
 cam.target=p(335,83,-22);cam.eye=p(395,210,120);cam.upVector=adsk.core.Vector3D.create(0,0,1)
 cam.setExtents(5.2,5.2*1100/1800);cam.isSmoothTransition=False;app.activeViewport.camera=cam;adsk.doEvents();app.activeViewport.refresh()
 capture('base-corner-detail.png');clear()
 stage('capturing repaired upper rear corner section')
 a=mgr.copy(sr)
 if not mgr.booleanOperation(a,box(338,0,-22,350.01,12,-14),bt.IntersectionBooleanType):raise RuntimeError('Upper corner section failed')
 if a.faces.count:add(a)
 camera((32,-12,12),(34.4,-.6,-1.8));capture('upper-corner-wall-detail.png');clear()
 stage('capturing reinforced blind screw cap section')
 a=mgr.copy(sl)
 if not mgr.booleanOperation(a,box(125,0,-22,131,12,-12.5),bt.IntersectionBooleanType):raise RuntimeError('Pilot cap section failed')
 if a.faces.count:add(a)
 camera((11,-10,5),(12.7,-.6,-1.7));capture('blind-pilot-cap-section.png');clear()
 stage('capturing new right-section base mounts')
 add(sr);add(br,dz=-12)
 camera((40,-25,-30),(27,-4.6,-.5));capture('right-shell-base-mounts.png');clear()
 stage('capturing DC input and open regulator carrier')
 hide();clear()
 for b in [sr,br]:
  a=mgr.copy(b)
  if not mgr.booleanOperation(a,box(201,0,-24.01,236,39,14),bt.IntersectionBooleanType):raise RuntimeError('Power detail crop failed')
  if a.faces.count:add(a)
 for o in main:
  if o.component.name.startswith(('DC power','Pololu')):
   for b in o.component.bRepBodies:add(b)
 camera((32,-20,17),(22,-2,-.6));capture('power-internal.png');clear()
 a=mgr.copy(sr)
 if not mgr.booleanOperation(a,box(199,0,-12,239,4,12),bt.IntersectionBooleanType):raise RuntimeError('Power rear crop failed')
 if a.faces.count:add(a)
 for b in find('DC power').bRepBodies:add(b)
 camera((17,15,10),(21,-.2,0));capture('power-rear.png');clear()
 stage('capturing raised clips and ventilation grilles')
 a=mgr.copy(br)
 if not mgr.booleanOperation(a,box(216,21,-24.01,236,40,-6),bt.IntersectionBooleanType):raise RuntimeError('Clip crop failed')
 if a.faces.count:add(a)
 camera((33,-20,17),(22.6,-3,-1.3));capture('clip-mount.png');clear()
 a=mgr.copy(br)
 if not mgr.booleanOperation(a,box(208,12,-24.01,269,59,-6),bt.IntersectionBooleanType):raise RuntimeError('Inlet crop failed')
 if a.faces.count:add(a)
 camera((35,-25,22),(24,-3,-1.5));capture('ventilation-base.png');clear()
 a=mgr.copy(sr)
 if not mgr.booleanOperation(a,box(217,0,-24.01,286,9,30.1),bt.IntersectionBooleanType):raise RuntimeError('Exhaust crop failed')
 if a.faces.count:add(a)
 camera((35,18,12),(25,-.3,.3));capture('ventilation-rear.png')
 camera((31,-14,10),(25,-.3,1.2));capture('rear-ribs-internal.png');clear()
 a=mgr.copy(sr)
 if not mgr.booleanOperation(a,box(241.5,0,13.8,258,3,15.2),bt.IntersectionBooleanType):raise RuntimeError('Membrane section crop failed')
 if a.faces.count:add(a)
 camera((31,-12,11),(25,-.15,1.45));capture('rear-vent-membrane-section.png');clear()
 for b in [sr,br]:
  a=mgr.copy(b)
  if not mgr.booleanOperation(a,box(255,0,-24.01,277,10,-15),bt.IntersectionBooleanType):raise RuntimeError('Rib seat crop failed')
  if a.faces.count:add(a)
 camera((31,-12,8),(26.7,-.4,-2));capture('rear-rib-base-seat.png');clear()
 stage('capturing modular assembly with the universal pair base')
 add(ps);add(pb,dz=-15);camera((25,-24,-20),(16,-4.6,-.5));capture('modular/pair-two-screw-mounts.png');clear()
 for b,dx,dz in [(cb,-75,22),(ls,-70,15),(pb,-70,-17),(ps,0,8),(pb,0,-17),(get(es,'SHELL'),0,0),(get(es,'BASE'),0,-17)]:add(b,dx=dx,dz=dz)
 camera((40,-30,-24),(19,-4.6,-.5));capture('modular/modular-exploded.png');clear()
 for b in [ls,pb,cb]:add(b)
 camera((8,-18,-18),(15.9,-4.6,-.5));capture('modular/cap-floor-underside.png');clear()
 for i,(name,b,sign) in enumerate([('pair-shell',ps,1),('pair-shell-at-cap',ls,1),('pair-base',pb,0),('left-cap',cb,-1)]):
  a=mgr.copy(b)
  if sign:
   m=adsk.core.Matrix3D.create();m.setToRotation(sign*math.pi/2,adsk.core.Vector3D.create(0,1,0),adsk.core.Point3D.create(0,0,0));mgr.transform(a,m)
  q=a.boundingBox;m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(-q.minPoint.x+i*10,-q.minPoint.y,-q.minPoint.z);mgr.transform(a,m);add(a,name)
 camera((40,-30,30),(18,5,2));capture('modular/new-parts-print-orientations.png');clear()
 ao.isLightBulbOn=True
 for o in root.allOccurrences:
  if o.fullPathName.startswith(ao.name+'+'):o.isLightBulbOn=not o.component.name.startswith('REF')
 camera((43,-47,27),(19.6,-19.6,.5),native_visible(True));capture('modular/modular-assembled.png')
 stage('recording source geometry and render provenance')
 layout=[]
 for o in main:
  layout.append({'component':o.component.name,'transform':list(o.transform2.asArray()),'bodies':[{'name':b.name,'volume_mm3':b.volume*1000,'min_world_mm':[v*10 for v in b.boundingBox.minPoint.asArray()],'max_world_mm':[v*10 for v in b.boundingBox.maxPoint.asArray()]} for b in o.component.bRepBodies]})
 fingerprint=hashlib.sha256(json.dumps(layout,sort_keys=True).encode()).hexdigest()
 write('current-layout.json',{'revision':revision,'coordinate_system':'Fusion world in mm: X right, negative Y towards front, Z up','main_outline_mm':[350,92,54],'main':layout,'geometry_fingerprint_sha256':fingerprint})
 write('render-manifest.json',{'revision':revision,'captured_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_document':app.activeDocument.name,'source_geometry_sha256':fingerprint,'images':[{ 'path':n,'sha256':hashlib.sha256(open(out+n,'rb').read()).hexdigest()} for n in images],'optional_LEDs':'Shown fitted in main views; mounting membranes remain present in the printable shell.'})
 work.deleteMe()
 for o,v in visibility:o.isLightBulbOn=v
 ao.isLightBulbOn=False
 for o in main:o.isLightBulbOn=not o.component.name.startswith('REF')
 camera((40,-32,24),(17.5,-4.6,0),native_visible())
 if not app.activeDocument.save('Refreshed audited wall reinforcements, 2mm screw closures, modular cap and restored left floor; preserved exterior, hardware, clearances and membranes.'):
  raise RuntimeError('Save failed')
 stage('complete')
