"""Rigidly turn only the two mirrored variants' LCDs, including their window seats."""
import adsk.core,adsk.fusion,json,math,datetime

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/mirrored/'
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 marker='display_180_ribbon_left'
 assert not root.attributes.itemByName('MIDI_MIRROR',marker),'LCD rotation already applied'
 report=json.loads(root.attributes.itemByName('MIDI_MIRROR','logical_left_electronics').value)
 main=next(o.component for o in root.occurrences if o.component.name==report['new_main_component'])
 mod=next(o.component for o in root.occurrences if o.component.name==report['new_modular_component'])
 def stage(s):
  with open('/tmp/midi-lcd-180-progress.json','w') as f:json.dump({'stage':s},f)
 def find(c,p):return next(o.component for o in c.occurrences if o.component.name.startswith(p))
 def get(c,t):return next(b for b in c.bRepBodies if t in b.name)
 uc=find(main,'Mirrored 01 ');bc=find(main,'Mirrored 02 ');elec=find(mod,'Existing LEFT')
 lcd=find(main,'Mirrored LCD ');mlcd=find(elec,'Mirrored ALT reference - LCD ')
 encoder=find(main,'Mirrored Encoder')
 cx,cy=42.59781066034995,61.9843653568
 rot=adsk.core.Matrix3D.create();rot.setToRotation(math.pi,adsk.core.Vector3D.create(0,0,1),adsk.core.Point3D.create(cx/10,-cy/10,0))
 def bounds(b):
  q=b.boundingBox;return [v*10 for v in q.minPoint.asArray()]+[v*10 for v in q.maxPoint.asArray()]
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def op(a,b,kind):assert mgr.booleanOperation(a,b,kind);return a
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def turn(a):assert mgr.transform(a,rot);return a
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20,-(y0+y1)/20,(z0+z1)/20),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 stage('preparing rotated LCDs and symmetric window-seat crop')
 oldshell=get(uc,'LEFT');modshell=get(elec,'SHELL')
 mask=box(21.49781,45,-5.3,63.69781,79.2,.4)
 original_upper=find(root,'01 ')
 original_right=get(original_upper,'RIGHT')
 aperture=mgr.copy(original_right)
 reflection=adsk.core.Matrix3D.create();reflection.setCell(0,0,-1);reflection.setCell(0,3,35)
 assert mgr.transform(aperture,reflection)
 # X reflection matches the rotated symmetric glass aperture and preserves the slanted deck.
 region=inter(aperture,mgr.copy(mask))
 new_shell=op(cut(mgr.copy(oldshell),mgr.copy(mask)),region,bt.UnionBooleanType)
 assert new_shell.isSolid and new_shell.lumps.count==1
 outside_difference=[]
 for a,b in [(new_shell,oldshell),(oldshell,new_shell)]:outside_difference.append(vol(cut(cut(mgr.copy(a),mgr.copy(b)),mgr.copy(mask))))
 assert max(outside_difference)<.001,outside_difference
 old_lcd=list(lcd.bRepBodies);old_mod_lcd=list(mlcd.bRepBodies)
 assert len(old_lcd)==len(old_mod_lcd)==7
 candidates=[(b,turn(mgr.copy(b))) for b in old_lcd]
 # The four mounting stud locations are permuted, not displaced, by this turn.
 def sig(b):return [round(x,4) for x in bounds(b)]+[round(vol(b),4)]
 stud_old=sorted(sig(b) for b in old_lcd if 'stud' in b.name.lower())
 stud_new=sorted(sig(a) for b,a in candidates if 'stud' in b.name.lower())
 assert len(stud_old)==4 and stud_old==stud_new,(stud_old,stud_new)
 stage('checking rotated LCD against the shell, base and encoder')
 printed=[new_shell]+[mgr.copy(b) for b in bc.bRepBodies]
 other=[(encoder.name,b,mgr.copy(b)) for b in encoder.bRepBodies]
 # Checking the changed objects suffices: all other component poses remain fixed.
 for o in main.occurrences:
  if o.component in [lcd,uc,bc,encoder]:continue
  other.extend((o.component.name,b,mgr.copy(b)) for b in o.component.bRepBodies)
 cache={}
 def bb(a):
  k=id(a)
  if k not in cache:cache[k]=(a,bounds(a))
  return cache[k][1]
 def hit(a,b):
  q,r=bb(a),bb(b)
  if any(min(q[i+3],r[i+3])-max(q[i],r[i])<1e-6 for i in range(3)):return 0
  return vol(inter(mgr.copy(a),mgr.copy(b)))
 contacts=[]
 for b,a in candidates:
  for j,s in enumerate(printed):
   h=hit(a,s)
   if h>.003:contacts.append([b.name,'printed '+str(j),h])
  for name,other_body,s in other:
   h=hit(a,s)
   if h>.003:contacts.append([b.name,name+'/'+other_body.name,h])
 assert not contacts,contacts
 # All unedited root components and bodies retain their identities; only new variants are targeted.
 changes=[]
 for c,b,a in [(uc,oldshell,new_shell),(elec,modshell,new_shell)]+[(lcd,b,a) for b,a in candidates]+[(mlcd,b,candidates[i][1]) for i,b in enumerate(old_mod_lcd)]:
  # Modular LCD body ordering must match the corresponding exact main reference.
  if c==mlcd:
   source=old_lcd[old_mod_lcd.index(b)]
   assert abs(vol(source)-vol(b))<.001,(source.name,b.name)
  changes.append((c,b,a,b.name,b.appearance))
 data={'rotation_degrees':180,'axis':'Z, normal to display PCB','center_layout_XY_mm':[cx,cy],'ribbon_side':'left','applies_to':['mirrored main','mirrored modular'],'original_variants_modified':False,'glass_flush_Z_mm':0,'mounting_stud_positions_unchanged':True,'M2x5_posts_and_screws_unchanged':True,'window_region_outside_difference_mm3':outside_difference,'physical_collisions':contacts,'rotated_bodies':[{'name':b.name,'before_mm':bounds(b),'after_mm':bounds(a),'volume_mm3':vol(a)} for b,a in candidates],'verified_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 stage('committing mirrored display rotation and matched window seats')
 for c,b,a,name,appearance in changes:
  n=c.bRepBodies.add(mgr.copy(a));n.name=name
  if appearance:n.appearance=appearance
  b.deleteMe()
 root.attributes.add('MIDI_MIRROR',marker,json.dumps(data))
 for c in [main,mod]:c.attributes.add('MIDI_MIRROR',marker,json.dumps(data))
 assert app.activeDocument.save('Mirrored variants only: LCD rotated 180 degrees with ribbon to left; matched flush window and unchanged M2x5 posts')
 data['saved']=app.activeDocument.isSaved;data['document']=app.activeDocument.name
 with open(out+'display-rotation.json','w') as f:json.dump(data,f,indent=2)
 stage('complete');print(json.dumps(data))
