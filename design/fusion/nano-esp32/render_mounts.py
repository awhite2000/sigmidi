"""Export current components-up Nano assemblies, changed bases and native views.

Upper print files are preserved byte-for-byte. Native assembly exports contain
only current physical hardware; hidden source references are not manufacturing
parts. The complete source archive retains the editable component hierarchy.
"""
import adsk.core,adsk.fusion,json,math,hashlib,datetime,shutil
from pathlib import Path

OUT=Path('/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/nano-esp32')


def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent;P=OUT.parent
 assert r.attributes.itemByName('SIGMIDI','nano_direct_posts')
 spec=json.loads((OUT/'mount-fit.json').read_text());assert not spec['component_face_down']
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def find(c,prefix):return next(o.component for o in c.occurrences if o.component.name.startswith(prefix))
 def get(c,token):return next(b for b in c.bRepBodies if token in b.name)
 kit=find(r,'ALT Arduino Nano ESP32 - direct')
 lm=find(r,'ALT Mirrored MAIN');lmod=find(r,'ALT Mirrored MODULAR');rm=find(r,'ALT Chainable')
 lbase=get(find(lm,'Mirrored 02 '),'LEFT');rbase=get(find(r,'02 '),'RIGHT')
 protected={str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in [P/'print',P/'modular',P/'mirrored/main',P/'mirrored/modular'] for p in folder.iterdir() if p.suffix in ['.stl','.3mf'] and 'shell' in p.name or p.name in ['left-cap.stl','left-cap.3mf','right-cap.stl','right-cap.3mf']}
 vis=[(o,o.isLightBulbOn) for o in r.occurrences];original=app.activeViewport.camera
 work=r.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component
 tc.name='TEMP Nano direct-mount exports';tc.isOriginFolderLightBulbOn=False
 images=[];archives=[]
 def stage(s):Path('/tmp/sigmidi-nano-export-progress.json').write_text(json.dumps({'stage':s}))
 def p(x,y,z):return adsk.core.Point3D.create(x/10,y/10,z/10)
 def clear():
  for b in list(tc.bRepBodies):b.deleteMe()
 def hide():
  for o in r.occurrences:o.isLightBulbOn=o==work
 def add(source,shape=None,dz=0):
  a=mgr.copy(shape if shape is not None else source)
  if dz:
   m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,0,dz/10);assert mgr.transform(a,m)
  b=tc.bRepBodies.add(a);b.name=source.name;b.isLightBulbOn=True
  if source.appearance:b.appearance=source.appearance
  return b
 def mul(a,b):return [sum(a[i*4+k]*b[k*4+j] for k in range(4)) for i in range(4) for j in range(4)]
 def walk(c,matrix=None,path=''):
  matrix=matrix or adsk.core.Matrix3D.create();path=path+'/'+c.name
  if any(tag in c.name for tag in ['DFRobot','REF ']):return
  for b in c.bRepBodies:
   if b.name.startswith('DFR1075 M1.6') or not b.isSolid:continue
   a=mgr.copy(b);assert mgr.transform(a,matrix);yield path,b,a
  for o in c.occurrences:
   m=adsk.core.Matrix3D.create();assert m.setWithArray(mul(list(matrix.asArray()),list(o.transform2.asArray())))
   yield from walk(o.component,m,path)
 def assembly(root_occ=None):
  # Fusion's shared instances can carry root-context placement overrides.
  # Use their world transforms, then remove this assembly's presentation shift.
  origin=root_occ.transform2.translation if root_occ else adsk.core.Vector3D.create(0,0,0)
  prefix=root_occ.fullPathName if root_occ else None
  for o in r.allOccurrences:
   path=o.fullPathName
   if prefix and not (path==prefix or path.startswith(prefix+'+')):continue
   if not prefix:
    top=path.split('+')[0]
    root_o=next((v for v in r.occurrences if v.fullPathName==top),None)
    if not root_o or root_o==work:continue
    if root_o.component.name.startswith(('ALT','REF','TEMP')):
     if root_o.component!=kit or root_o.transform2.translation.x<1:continue
   if any(tag in path for tag in ['DFRobot','REF ']):continue
   matrix=o.transform2.copy();t=matrix.translation
   t.x-=origin.x;t.y-=origin.y;t.z-=origin.z;matrix.translation=t
   for b in o.component.bRepBodies:
    if b.name.startswith('DFR1075 M1.6') or not b.isSolid:continue
    a=mgr.copy(b);assert mgr.transform(a,matrix)
    yield path,b,a
 def board_bounds(items,title):
  boards=[a for path,b,a in items if b.name.startswith('Nano ESP32 PCB')]
  assert len(boards)==1,(title,len(boards))
  q=boards[0].boundingBox;lo=[v*10 for v in q.minPoint.asArray()];hi=[v*10 for v in q.maxPoint.asArray()]
  dx=0 if title.startswith('Left') else spec['checks'][2]['translation_X_mm']
  expected_lo=[90.42163840008723+dx,-49.86824885058946,-13.336008235603408]
  expected_hi=[108.20163840008724+dx,-6.688248850589463,-11.730004335603407]
  assert all(abs(a-b)<.01 for a,b in zip(lo+hi,expected_lo+expected_hi)),(title,lo,hi)
  return {'assembly':title,'PCB_min_mm':lo,'PCB_max_mm':hi,'aligned_to_mount_posts':True}
 def camera(eye,target,width=None):
  direction=adsk.core.Vector3D.create(*[target[i]-eye[i] for i in range(3)]);direction.normalize()
  upseed=adsk.core.Vector3D.create(0,1 if direction.z<0 else -1,0) if abs(direction.z)>.999 else adsk.core.Vector3D.create(0,0,1)
  right=direction.crossProduct(upseed);right.normalize();up=right.crossProduct(direction);up.normalize()
  points=[]
  for b in tc.bRepBodies:
   q=b.boundingBox
   for x in [q.minPoint.x,q.maxPoint.x]:
    for y in [q.minPoint.y,q.maxPoint.y]:
     for z in [q.minPoint.z,q.maxPoint.z]:points.append(adsk.core.Vector3D.create(x,y,z))
  ranges=[]
  for axis in [right,up,direction]:
   dots=[v.dotProduct(axis) for v in points];ranges.append((min(dots),max(dots)))
  mid=[(a+b)/2 for a,b in ranges]
  center=adsk.core.Point3D.create(*[getattr(right,k)*mid[0]+getattr(up,k)*mid[1]+getattr(direction,k)*mid[2] for k in 'xyz'])
  cam=adsk.core.Camera.create();cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
  cam.target=center;cam.eye=adsk.core.Point3D.create(center.x-direction.x*100,center.y-direction.y*100,center.z-direction.z*100);cam.upVector=up
  aspect=min(1800/1100,app.activeViewport.width/app.activeViewport.height)
  h=max(ranges[1][1]-ranges[1][0],(ranges[0][1]-ranges[0][0])/aspect)*1.12
  if width:h=max(h,width/10/aspect)
  cam.setExtents(h*aspect,h);cam.isFitView=False;cam.isSmoothTransition=False;app.activeViewport.camera=cam;adsk.doEvents();app.activeViewport.refresh()
 def capture(path):
  assert app.activeViewport.saveAsImageFile(str(path),1800,1100);images.append(path)
 def stl(body,path):
  a=mgr.copy(body);q=a.boundingBox;m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(-q.minPoint.x,-q.minPoint.y,-q.minPoint.z);assert mgr.transform(a,m)
  b=add(body,a);o=d.exportManager.createSTLExportOptions(b,str(path));o.isBinaryFormat=True;o.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh;assert d.exportManager.execute(o);b.deleteMe()
 def archive(name):
  f3d=P/(name+'.f3d');step=P/(name+'.step')
  assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(f3d),tc))
  assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(str(step),tc))
  expected=tc.bRepBodies.count;raw=step.read_text();solids=raw.count('MANIFOLD_SOLID_BREP(')+raw.count('BREP_WITH_VOIDS(')
  assert solids==expected,(name,solids,expected)
  archives.append({'file':name,'native_solids':expected,'STEP_solids':solids,'complete':True,'physical_hardware_only':True})
 try:
  hide();stage('exporting the two changed electronics-base meshes')
  stl(lbase,P/'mirrored/main/base-left.stl');stl(rbase,P/'print/base-right.stl')
  shutil.copyfile(P/'mirrored/main/base-left.stl',P/'mirrored/modular/electronics-base-left.stl')
  shutil.copyfile(P/'print/base-right.stl',P/'modular/electronics-base.stl')
  datasets=[('Left main',list(assembly(next(o for o in r.occurrences if o.component==lm))),'mirrored/main/midi-foot-mirrored-main','mirrored/main'),
            ('Left modular',list(assembly(next(o for o in r.occurrences if o.component==lmod))),'mirrored/modular/midi-foot-mirrored-modular','mirrored/modular'),
            ('Right main',list(assembly()),'midi-foot-chassis',''),
            ('Right modular',list(assembly(next(o for o in r.occurrences if o.component==rm))),'modular/midi-foot-modular','modular')]
  board_checks=[board_bounds(items,title) for title,items,name,folder in datasets]
  layout=[]
  for title,items,name,folder in datasets:
   clear();stage('exporting '+title+' CAD and rendering current hardware')
   for path,source,a in items:add(source,a)
   archive(name)
   left=title.startswith('Left');target=(17.5,-4.6,0);eye=(-25,-30,28) if left else (58,-30,28)
   camera(eye,target);capture(P/folder/('modular-assembled.png' if title=='Right modular' else 'assembled.png'))
   camera((17.5,-4.6,45),target);capture(P/folder/('panel-top.png' if title=='Right main' else 'top.png'))
   camera((-20,24,22) if left else (58,24,22),target);capture(P/folder/'rear.png')
   clear()
   for path,source,a in items:
    if 'SHELL' not in source.name.upper() and 'cap' not in path.lower():add(source,a)
   camera(eye,target);capture(P/folder/('internal.png' if title!='Right modular' else 'modular-internal.png'))
   clear()
   for path,source,a in items:
    if source.name.upper().startswith('BASE') or 'ALT Arduino Nano' in path or 'Pololu S13V10F5' in path:add(source,a)
   camera(eye,target);capture(P/folder/('base-supports.png' if title=='Right main' else 'base-mounts.png'))
   clear()
   for path,source,a in items:
    dz=-18 if source.name.upper().startswith('BASE') or 'ALT Arduino Nano' in path or 'Pololu S13V10F5' in path else 0
    add(source,a,dz)
   camera(eye,target);capture(P/folder/('modular-exploded.png' if title=='Right modular' else 'exploded.png'))
   clear()
   if left:
    for path,source,a in items:
     q=a.boundingBox;layout.append({'assembly':'main' if title=='Left main' else 'modular','component_path':path,'body':source.name,'min_mm':[v*10 for v in q.minPoint.asArray()],'max_mm':[v*10 for v in q.maxPoint.asArray()],'volume_mm3':a.volume*1000,'physical':True})
  (P/'mirrored/layout.json').write_text(json.dumps({'coordinate_system':'Local assembly mm, X right, negative Y front, Z up; presentation shifts excluded','revision':spec['revision'],'bodies':layout},indent=2)+'\n')
  stage('rendering the components-up Nano and integral post detail')
  crop=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p(99.3,-34,-14.5),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),4.4,7,3))
  cropped=mgr.copy(lbase);assert mgr.booleanOperation(cropped,crop,bt.IntersectionBooleanType)
  add(lbase,cropped)
  for path,source,a in walk(kit):add(source,a)
  archive('nano-esp32/nano-esp32-direct-mount')
  camera((152,38,55),(99,-34,-10),87);capture(OUT/'installed.png');clear()
  add(lbase,cropped)
  for path,source,a in walk(kit):add(source,a,23 if 'screws' in path else 13)
  camera((152,38,68),(99,-34,-6),94);capture(OUT/'exploded.png');clear()
  add(lbase);camera((-25,-30,28),(8,-4.6,-1));capture(OUT/'print-orientation.png');clear()
  # Expose the printable post channels in an isolated native detail.
  add(lbase,cropped);camera((147,16,20),(99,-34,-16),87);capture(OUT/'posts.png');clear()
 finally:
  clear();work.deleteMe()
  for o,v in vis:
   if o.isValid:o.isLightBulbOn=v
  for o in r.occurrences:o.isLightBulbOn=o.component==lm
  app.activeViewport.camera=original;adsk.doEvents()
 assert all(hashlib.sha256((P/name).read_bytes()).hexdigest()==digest for name,digest in protected.items())
 report={'assembly_board_bounds_checks':board_checks,'revision':spec['revision'],'CAD':archives,'images':[{'path':str(p.relative_to(P)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in images],'upper_print_files_preserved':protected,'upper_shell_print_files_byte_identical':True,'native_upper_shells_unchanged':True,'printed_parts_added':0,'printed_inserts_removed':2,'captured_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 (OUT/'exports.json').write_text(json.dumps(report,indent=2)+'\n')
 for folder in [P/'mirrored',P]:
  old=folder/'render-manifest.json'
  previous=json.loads(old.read_text()) if old.exists() else {'images':[]}
  entries={v['path']:v for v in previous['images']}
  for item in report['images']:
   full=P/item['path']
   if full.is_relative_to(folder):entries[str(full.relative_to(folder))]={'path':str(full.relative_to(folder)),'sha256':item['sha256']}
  previous.update(revision=spec['revision'],captured_UTC=report['captured_UTC'],images=list(entries.values()));old.write_text(json.dumps(previous,indent=2)+'\n')
 for path in [P/'cad-export.json',P/'mirrored/emboss-complete-cad.json']:
  path.write_text(json.dumps({'revision':spec['revision'],'CAD':archives,'physical_hardware_only':True,'native_source':'../sigmidi-foot-controller-0.1.f3d' if path.parent.name=='mirrored' else 'sigmidi-foot-controller-0.1.f3d'},indent=2)+'\n')
 assert app.activeDocument.save('Exported components-up direct Nano bases and all four current assemblies; upper shells unchanged')
 stage('complete')
