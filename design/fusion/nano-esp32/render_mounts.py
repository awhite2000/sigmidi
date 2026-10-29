"""Export exact adapter CAD and capture installed, exploded and print views."""
import adsk.core,adsk.fusion,math,json
from pathlib import Path
OUT=Path('/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/nano-esp32')

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
 kit=next(o.component for o in r.occurrences if o.component.name=='ALT Arduino Nano ESP32 mount kit - original base unchanged')
 main=next(o.component for o in r.occurrences if o.component.name.startswith('ALT Mirrored MAIN'))
 base=next(o.component for o in main.occurrences if 'Removable base' in o.component.name)
 original=app.activeViewport.camera;vis=[(o,o.isLightBulbOn) for o in r.occurrences]
 for o,_ in vis:o.isLightBulbOn=False
 work=r.occurrences.addNewComponent(adsk.core.Matrix3D.create());temp=work.component;temp.name='TEMP Nano adapter export and views';temp.isOriginFolderLightBulbOn=False
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def p(x,y,z):return adsk.core.Point3D.create(x/10,y/10,z/10)
 def add(b,dz=0,shape=None):
  a=shape or mgr.copy(b)
  if dz:
   m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,0,dz/10);assert mgr.transform(a,m)
  n=temp.bRepBodies.add(a);n.name=b.name;n.appearance=b.appearance;return n
 def clear():
  for b in list(temp.bRepBodies):b.deleteMe()
 def frame(eye,target,width=65):
  cam=adsk.core.Camera.create();cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
  cam.eye=p(*eye);cam.target=p(*target);cam.upVector=adsk.core.Vector3D.create(0,0,1)
  cam.setExtents(width/10,width/10*1000/1500);cam.isSmoothTransition=False;cam.isFitView=False;app.activeViewport.camera=cam;adsk.doEvents();app.activeViewport.refresh()
 def capture(name):assert app.activeViewport.saveAsImageFile(str(OUT/(name+'.png')),1500,1000)
 # Flat, visible staging avoids exporting an empty STEP from a hidden kit occurrence.
 for o in kit.occurrences:
  for b in o.component.bRepBodies:add(b)
 assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(str(OUT/'nano-esp32-mount-kit.step'),temp))
 assert (OUT/'nano-esp32-mount-kit.step').stat().st_size>100000
 clear()
 box=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p(99,-35,-15),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),4.4,7,3))
 def floor():
  for b in base.bRepBodies:
   a=mgr.copy(b);assert mgr.booleanOperation(a,mgr.copy(box),bt.IntersectionBooleanType)
   if a.faces.count:add(b,shape=a)
 def kit_parts(explode=False):
  for o in kit.occurrences:
   dz=13 if explode and (o.component.name.startswith('Arduino') or o.component.name.startswith('Nano mounting screws')) else 4 if explode and 'opposite-end' in o.component.name else 0
   for b in o.component.bRepBodies:add(b,dz)
 floor();kit_parts();frame((150,38,48),(99,-35,-12),87);capture('installed');clear()
 floor();kit_parts(True);frame((150,38,65),(99,-35,-7),94);capture('exploded');clear()
 # The same mesh orientation as the delivered STL/3MF files: flat glue foot or plate down.
 for i,o in enumerate(o for o in kit.occurrences if 'glue insert' in o.component.name or 'opposite-end' in o.component.name):
  for b in o.component.bRepBodies:
   a=mgr.copy(b);q=a.boundingBox;m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(-q.minPoint.x+i*4,-q.minPoint.y,-q.minPoint.z);assert mgr.transform(a,m);add(b,shape=a)
 frame((95,-65,70),(35,10,3),85);capture('print-orientation');clear()
 work.deleteMe()
 for o,v in vis:o.isLightBulbOn=v
 # Leave the preferred main variant visible, fitted with Nano and the original base.
 for o in r.occurrences:
  if o.component.name.startswith('ALT Mirrored MAIN'):o.isLightBulbOn=True
 app.activeViewport.camera=original;adsk.doEvents()
 assert app.activeDocument.save('Saved Nano ESP32 adapter kit and verified unchanged enclosure geometry')
