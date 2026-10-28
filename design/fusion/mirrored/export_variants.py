"""Export and render only the new mirrored variants, leaving old deliverables intact."""
import adsk.core,adsk.fusion,json,math,os,hashlib,datetime


def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/mirrored/'
 report=json.loads(root.attributes.itemByName('MIDI_MIRROR','logical_left_electronics').value)
 main=next(o.component for o in root.occurrences if o.component.name==report['new_main_component'])
 mod=next(o.component for o in root.occurrences if o.component.name==report['new_modular_component'])
 lib=next(o.component for o in root.occurrences if o.component.name==report['new_library_component'])
 for name in ['main','modular']:os.makedirs(out+name,exist_ok=True)
 def stage(s):
  with open('/tmp/logical-mirror-export-progress.json','w') as f:json.dump({'stage':s},f)
 def write(name,data):
  with open(out+name,'w') as f:json.dump(data,f,indent=2)
 def get(c,token):return next(b for b in c.bRepBodies if token in b.name)
 def find(c,prefix):return next(o.component for o in c.occurrences if o.component.name.startswith(prefix))
 uc=find(main,'Mirrored 01 ');bc=find(main,'Mirrored 02 ')
 sl,sr=get(uc,'LEFT'),get(uc,'RIGHT');bl,br=get(bc,'LEFT'),get(bc,'RIGHT')
 pair=find(mod,'Repeatable pair');endpair=find(mod,'Rightmost pair');cap=find(mod,'Closed right cap');electronics=find(mod,'Existing LEFT')
 ps,pb=get(pair,'SHELL'),get(pair,'BASE');es=get(endpair,'SHELL');cb=cap.bRepBodies.item(0)
 # These are separate native bodies but must remain exactly interchangeable.
 comparisons=[]
 for name,a,b in [('electronics shell',sl,get(electronics,'SHELL')),('electronics base',bl,get(electronics,'BASE')),('universal pair base',pb,get(endpair,'BASE'))]:
  dif=[]
  for first,second in [(a,b),(b,a)]:
   q=mgr.copy(first);assert mgr.booleanOperation(q,mgr.copy(second),bt.DifferenceBooleanType);dif.append(q.volume*1000 if q.faces.count else 0)
  assert max(dif)<.001,(name,dif);comparisons.append({'parts':name,'bidirectional_difference_mm3':dif})
 visibility=[(o,o.isLightBulbOn) for o in root.occurrences];original=app.activeViewport.camera
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());temp=work.component;temp.name='TEMP mirrored exports and views';work.isLightBulbOn=False;temp.isOriginFolderLightBulbOn=False
 images=[];parts=[]
 def clear():
  for b in list(temp.bRepBodies):b.deleteMe()
 def hide():
  for o in root.occurrences:o.isLightBulbOn=o==work
 def add(b,shape=None,dx=0,dy=0,dz=0):
  a=mgr.copy(shape or b);m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,-dy/10,dz/10);assert mgr.transform(a,m)
  n=temp.bRepBodies.add(a);n.name=b.name
  if b.appearance:n.appearance=b.appearance
  return n
 def mul(a,b):return [sum(a[i*4+k]*b[k*4+j] for k in range(4)) for i in range(4) for j in range(4)]
 def walk(comp,matrix=None,path=''):
  matrix=matrix or adsk.core.Matrix3D.create();path=path+'/'+comp.name
  for b in comp.bRepBodies:
   a=mgr.copy(b);assert mgr.transform(a,matrix);yield path,b,a
  for o in comp.occurrences:
   m=adsk.core.Matrix3D.create();assert m.setWithArray(mul(list(matrix.asArray()),list(o.transform2.asArray())))
   yield from walk(o.component,m,path)
 def physical(path):return '/Mirrored REF' not in path and '/REF ' not in path
 def camera(eye,target):
  direction=adsk.core.Vector3D.create(*[target[i]-eye[i] for i in range(3)]);direction.normalize()
  upseed=adsk.core.Vector3D.create(0,1 if direction.z<0 else -1,0) if abs(direction.z)>.999 else adsk.core.Vector3D.create(0,0,1)
  right=direction.crossProduct(upseed);right.normalize();up=right.crossProduct(direction);up.normalize()
  pts=[]
  for b in temp.bRepBodies:
   q=b.boundingBox
   for x in [q.minPoint.x,q.maxPoint.x]:
    for y in [q.minPoint.y,q.maxPoint.y]:
     for z in [q.minPoint.z,q.maxPoint.z]:pts.append(adsk.core.Vector3D.create(x,y,z))
  ranges=[]
  for axis in [right,up,direction]:
   dots=[v.dotProduct(axis) for v in pts];ranges.append((min(dots),max(dots)))
  mid=[(a+b)/2 for a,b in ranges]
  center=adsk.core.Point3D.create(*[getattr(right,k)*mid[0]+getattr(up,k)*mid[1]+getattr(direction,k)*mid[2] for k in 'xyz'])
  cam=adsk.core.Camera.create();cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType;cam.target=center;cam.eye=adsk.core.Point3D.create(center.x-direction.x*100,center.y-direction.y*100,center.z-direction.z*100);cam.upVector=up
  aspect=min(1800/1100,app.activeViewport.width/app.activeViewport.height);h=max(ranges[1][1]-ranges[1][0],(ranges[0][1]-ranges[0][0])/aspect)*1.12
  cam.setExtents(h*aspect,h);cam.isFitView=False;cam.isSmoothTransition=False;app.activeViewport.camera=cam;adsk.doEvents();app.activeViewport.refresh()
 def capture(name):
  assert app.activeViewport.saveAsImageFile(out+name,1800,1100);images.append(name)
 def export_stl(name,b,rotate=0):
  a=mgr.copy(b)
  if rotate:
   m=adsk.core.Matrix3D.create();m.setToRotation(rotate*math.pi/2,adsk.core.Vector3D.create(0,1,0),adsk.core.Point3D.create(0,0,0));assert mgr.transform(a,m)
  q=a.boundingBox;size=[(getattr(q.maxPoint,k)-getattr(q.minPoint,k))*10 for k in 'xyz'];m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(-q.minPoint.x,-q.minPoint.y,-q.minPoint.z);assert mgr.transform(a,m)
  n=temp.bRepBodies.add(a);opt=d.exportManager.createSTLExportOptions(n,out+name+'.stl');opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh;opt.isBinaryFormat=True;assert d.exportManager.execute(opt);n.deleteMe()
  parts.append({'path':name,'size_mm':size,'solid':a.isSolid,'lumps':a.lumps.count,'rotation_Y_degrees':rotate*90,'orientation':'outer end on bed, seam upward' if 'shell' in name or name.endswith('cap') else 'outside floor down, posts upward'})
 try:
  stage('exporting independent mirrored main CAD')
  for o in root.occurrences:o.isLightBulbOn=o.component==main
  assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(out+'main/midi-foot-mirrored-main.f3d',main))
  assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(out+'main/midi-foot-mirrored-main.step',main))
  stage('exporting independent mirrored modular CAD')
  for o in root.occurrences:o.isLightBulbOn=o.component==mod
  assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(out+'modular/midi-foot-mirrored-modular.f3d',mod))
  assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(out+'modular/midi-foot-mirrored-modular.step',mod))
  stage('exporting all mirrored print parts')
  hide()
  for name,b,rot in [('main/shell-left',sl,-1),('main/shell-right',sr,1),('main/base-left',bl,0),('main/base-right',br,0),('modular/pair-shell-C',ps,-1),('modular/pair-shell-at-right-cap-D',es,-1),('modular/pair-base',pb,0),('modular/right-cap',cb,1)]:export_stl(name,b,rot)
  for o in lib.occurrences:
   name=o.component.name;filename=name if name.startswith('pair-shell-at-') else 'pair-shell-D'
   b=o.component.bRepBodies.item(0);export_stl('modular/'+filename,b,-1)
   lib_occ=next(q for q in root.occurrences if q.component==lib);lib_occ.isLightBulbOn=True
   assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(out+'modular/'+filename+'.f3d',o.component))
   assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(out+'modular/'+filename+'.step',o.component))
  lib_occ.isLightBulbOn=False
  # Seam coupon region is exactly the reflection of the existing fitted coupon.
  def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20,-(y0+y1)/20,(z0+z1)/20),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
  for name,b,rot in [('left',sl,-1),('right',sr,1)]:
   a=mgr.copy(b);assert mgr.booleanOperation(a,box(146.35,20,20,166.35,26,30.01),bt.IntersectionBooleanType);assert a.lumps.count==1;export_stl('main/fit-coupon-'+name,a,rot)
  stage('capturing assembled and internal mirrored main model')
  main_shapes=list(walk(main));mod_shapes=list(walk(mod))
  for path,b,a in main_shapes:
   if physical(path):add(b,a)
  camera((-25,-30,28),(17.5,-4.6,0));capture('main/assembled.png')
  camera((17.5,-4.6,45),(17.5,-4.6,0));capture('main/top.png')
  camera((-20,24,22),(17.5,-4.6,0));capture('main/rear.png');clear()
  for path,b,a in main_shapes:
   if physical(path) and '/Mirrored 01 ' not in path:add(b,a)
  camera((-20,-32,28),(17.5,-4.6,-.5));capture('main/internal.png');clear()
  for path,b,a in main_shapes:
   if '/Mirrored LCD ' in path or '/Mirrored Encoder' in path:add(b,a)
  camera((4.25,-6.2,-25),(4.25,-6.2,-.5));capture('main/display-underside.png');clear()
  for b in [sl,sr]:add(b)
  for b in [bl,br]:add(b,dz=-18)
  camera((-20,-32,25),(17.5,-4.6,-1));capture('main/exploded.png');clear()
  for b in [bl,br]:add(b)
  camera((-15,-24,30),(17.5,-4.6,-1));capture('main/base-mounts.png');clear()
  stage('capturing right-extending modular variant')
  for path,b,a in mod_shapes:
   if physical(path):add(b,a)
  camera((-20,-30,25),(14.75,-4.6,0));capture('modular/assembled.png')
  camera((14.75,-4.6,45),(14.75,-4.6,0));capture('modular/top.png');clear()
  for path,b,a in mod_shapes:
   if not physical(path):continue
   movebase='BASE' in b.name
   add(b,a,dz=-18 if movebase else 0)
  camera((-20,-30,25),(14.75,-4.6,-1));capture('modular/exploded.png');clear()
  layout=[]
  for title,items in [('main',main_shapes),('modular',mod_shapes)]:
   for path,b,a in items:
    q=a.boundingBox;layout.append({'assembly':title,'component_path':path,'body':b.name,'min_mm':list(v*10 for v in q.minPoint.asArray()),'max_mm':list(v*10 for v in q.maxPoint.asArray()),'volume_mm3':a.volume*1000,'physical':physical(path)})
  write('layout.json',{'coordinate_system':'Local assembly mm, X right, negative Y front, Z up; presentation occurrence shifts excluded','bodies':layout})
  write('print-export.json',{'revision':'logical_left_electronics','parts':parts,'native_equivalence_checks':comparisons})
  write('render-manifest.json',{'revision':'logical_left_electronics','captured_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'images':[{'path':name,'sha256':hashlib.sha256(open(out+name,'rb').read()).hexdigest()} for name in images]})
  for folder,name in [('main','midi-foot-mirrored-main'),('modular','midi-foot-mirrored-modular')]:
   with open(out+folder+'/'+name+'.step') as f:count=f.read().count('MANIFOLD_SOLID_BREP(')
   assert count>200,(folder,count)
  stage('saving completed variants')
 finally:
  clear();work.deleteMe()
  for o,v in visibility:o.isLightBulbOn=v
  app.activeViewport.camera=original;adsk.doEvents()
 assert app.activeDocument.save('Independent mirrored main and modular CAD, print meshes and previews exported; original models and files preserved')
 write('export-verification.json',{'document':app.activeDocument.name,'saved':app.activeDocument.isSaved,'parts':len(parts),'renders':len(images),'native_equivalence_checks':comparisons,'temporary_components':[o.component.name for o in root.occurrences if o.component.name.startswith('TEMP')]})
 stage('complete');print(json.dumps({'parts':len(parts),'images':len(images),'saved':True}))
