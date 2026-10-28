"""Match the rotated LCD aperture without turning the adjacent slanted deck surface."""
import adsk.core,adsk.fusion,json

def run(_context):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/mirrored/'
 report=json.loads(root.attributes.itemByName('MIDI_MIRROR','logical_left_electronics').value)
 def find(c,p):return next(o.component for o in c.occurrences if o.component.name.startswith(p))
 def body(c,t):return next(b for b in c.bRepBodies if t in b.name)
 def op(a,b,t):assert mgr.booleanOperation(a,b,t);return a
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20,-(y0+y1)/20,(z0+z1)/20),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 main=next(o.component for o in root.occurrences if o.component.name==report['new_main_component']);mod=next(o.component for o in root.occurrences if o.component.name==report['new_modular_component'])
 upper=find(main,'Mirrored 01 ');electronics=find(mod,'Existing LEFT');source=find(root,'01 ')
 old=body(upper,'LEFT');other=body(electronics,'SHELL')
 mask=box(21.49781,45,-5.3,63.69781,79.2,.4)
 # The original aperture is symmetric front-to-rear: reflection in X places it
 # exactly under the actual glass turned 180 degrees. Unlike rotating the whole
 # crop, this retains the slanted transition on its original rear side.
 mirror=adsk.core.Matrix3D.create();mirror.setCell(0,0,-1);mirror.setCell(0,3,35)
 shape=mgr.copy(body(source,'RIGHT'));assert mgr.transform(shape,mirror)
 patch=op(shape,mgr.copy(mask),bt.IntersectionBooleanType)
 new=op(op(mgr.copy(old),mgr.copy(mask),bt.DifferenceBooleanType),patch,bt.UnionBooleanType)
 assert new.isSolid and new.lumps.count==1
 dif=[]
 for a,b in [(new,old),(old,new)]:dif.append(vol(op(op(mgr.copy(a),mgr.copy(b),bt.DifferenceBooleanType),mgr.copy(mask),bt.DifferenceBooleanType)))
 assert max(dif)<.001
 lcd=find(main,'Mirrored LCD ');contacts=[]
 for b in lcd.bRepBodies:
  q=op(mgr.copy(new),mgr.copy(b),bt.IntersectionBooleanType);v=vol(q)
  if v>.003:contacts.append([b.name,v])
 assert not contacts,contacts
 for comp,b in [(upper,old),(electronics,other)]:
  n=comp.bRepBodies.add(mgr.copy(new));n.name=b.name;n.appearance=b.appearance;b.deleteMe()
 with open(out+'display-rotation.json') as f:data=json.load(f)
 data['window_method']='Original aperture reflected left-to-right, matching the rigidly rotated glass while preserving the adjacent slanted deck'
 data['window_repair_outside_region_difference_mm3']=dif
 root.attributes.add('MIDI_MIRROR','display_180_ribbon_left',json.dumps(data))
 for c in [main,mod]:c.attributes.add('MIDI_MIRROR','display_180_ribbon_left',json.dumps(data))
 assert app.activeDocument.save('Rotated LCD opening corrected: preserve stepped deck and remove thin ridge; both mirrored variants only')
 data['document']=app.activeDocument.name
 with open(out+'display-rotation.json','w') as f:json.dump(data,f,indent=2)
 print(json.dumps({'saved':True,'LCD_contacts':contacts,'outside_region_difference_mm3':dif}))
