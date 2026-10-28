"""Recess the four display screw seats for M2x5, without moving the display."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 assert app.activeDocument.name.startswith('MIDI Foot Controller - VERIFIED')
 assert not root.attributes.itemByName('MIDI_FDM','display_m2x5'),'Already applied'
 oldnote=json.loads(root.attributes.itemByName('MIDI_FDM','LCD_M2x6').value)
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def cone(x,y,z0,z1,r0,r1):return mgr.createCylinderOrCone(p(x,y,z0),r0/10,p(x,y,z1),r1/10)
 def cyl(x,y,z0,z1,r):return cone(x,y,z0,z1,r,r)
 def op(a,b,k):
  assert mgr.booleanOperation(a,b,k),'BRep operation failed'
  return a
 def union(a,b):return op(a,b,bt.UnionBooleanType)
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def collision(a,b):
  aa=a.boundingBox;bb=b.boundingBox
  if any(min(getattr(aa.maxPoint,s),getattr(bb.maxPoint,s))-max(getattr(aa.minPoint,s),getattr(bb.minPoint,s))<1e-7 for s in 'xyz'):return 0
  a=inter(mgr.copy(a),mgr.copy(b));return a.volume*1000 if a.faces.count else 0
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 base=next(c for c in main if c.name.startswith('02 '));hardware=next(c for c in main if c.name.startswith('PCB screws'))
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 ec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'))
 ehw=next(o.component for o in ec.occurrences if 'PCB screws' in o.component.name)
 old=next(b for b in base.bRepBodies if 'RIGHT' in b.name);modbase=next(b for b in ec.bRepBodies if 'BASE' in b.name)
 a=mgr.copy(old);mask=None
 dx,dy=330-323.30219,72-74.13437;dist=math.hypot(dx,dy);nx,ny=dx/dist,dy/dist
 def halfspace(x,y,offset):
  mid=(offset-20)/2
  return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p(x+nx*mid,y+ny*mid,-12),adsk.core.Vector3D.create(nx,-ny,0),adsk.core.Vector3D.create(-ny,-nx,0),(offset+20)/10,4,4))
 seat=-9.51;top=-5.9;posts=[]
 for row in oldnote['posts']:
  x,y=row['center_XY_mm'];m=cyl(x,y,-24.1,top+.1,4.21);mask=m if mask is None else union(mask,m)
  a=cut(a,cyl(x,y,-22,top+.1,4.21));a=union(a,cyl(x,y,-24,-22,2.25))
  outside=union(cyl(x,y,-22,seat+.9,4.2),cone(x,y,seat+.9,seat+1.8,4.2,3.3))
  outside=union(outside,cyl(x,y,seat+1.8,top,3.3))
  inside=union(cyl(x,y,-24.1,seat,2.2),cone(x,y,seat,seat+.9,2.2,1.3))
  inside=union(inside,cyl(x,y,seat+.9,top+.1,1.3))
  if row['encoder_clearance_flat']:
   outside=inter(outside,halfspace(x,y,4.02));inside=inter(inside,halfspace(x,y,2.02))
  a=union(a,outside);a=cut(a,inside);posts.append(row)
 assert a.isSolid and a.lumps.count==1
 # Exact comparison outside the four post envelopes.
 oldrest=cut(mgr.copy(old),mgr.copy(mask));newrest=cut(mgr.copy(a),mgr.copy(mask))
 diffs=[cut(mgr.copy(oldrest),mgr.copy(newrest)).volume*1000,cut(mgr.copy(newrest),mgr.copy(oldrest)).volume*1000]
 assert max(diffs)<.001,diffs
 moved=[];screwchecks=[]
 for c in (hardware,ehw):
  screws=[b for b in c.bRepBodies if b.name.startswith('LCD24382')];assert len(screws)==4
  for b in screws:
   bb=b.boundingBox;x=(bb.minPoint.x+bb.maxPoint.x)*5;y=-(bb.minPoint.y+bb.maxPoint.y)*5
   assert abs((bb.maxPoint.z-bb.minPoint.z)*10-6)<.001
   screw=inter(mgr.copy(b),cyl(x,y,-11,-5.51,2.5))
   m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,0,.1);assert mgr.transform(screw,m)
   assert screw.isSolid and screw.lumps.count==1
   bb=screw.boundingBox;assert abs(bb.minPoint.z*10-seat)<1e-5 and abs(bb.maxPoint.z*10+4.51)<1e-5
   moved.append((c,b,screw));screwchecks.append({'component':c.name,'center_XY_mm':[x,y],'min_Z_mm':bb.minPoint.z*10,'max_Z_mm':bb.maxPoint.z*10,'length_mm':(bb.maxPoint.z-bb.minPoint.z)*10})
 replaced={old.entityToken:a};replaced.update({b.entityToken:t for c,b,t in moved if c==hardware})
 hits=[];wirehits=[]
 for c in main:
  for b in c.bRepBodies:
   if b==old:continue
   target=replaced.get(b.entityToken,b);v=collision(a,target)
   if v>.001:(wirehits if c.name.startswith('REF LED') else hits).append(['base',c.name,b.name,v])
 for c,b,sc in moved:
  if c!=hardware:continue
  for other in main:
   if other==hardware:continue
   for ob in other.bRepBodies:
    v=collision(sc,replaced.get(ob.entityToken,ob))
    if v>.001:hits.append([b.name,other.name,ob.name,v])
 assert not hits and not wirehits,(hits,wirehits)
 def replace(c,old,new,name):
  appearance=old.appearance;b=c.bRepBodies.add(mgr.copy(new));b.name=name
  if appearance:b.appearance=appearance
  old.deleteMe();return b
 for c,b in [(base,old),(ec,modbase)]:replace(c,b,a,b.name+' - LCD M2x5 recessed seats')
 for c,b,sc in moved:replace(c,b,sc,b.name.replace('M2x6','M2x5').replace(' - same fastener as base',''))
 hardware.name='PCB screws - LCD recessed M2x5 - MCU M1.6'
 ehw.name='ALT reference - PCB screws - LCD recessed M2x5 - MCU M1.6'
 note={'revision':'display_m2x5','screw':'Four M2x5 countersunk display screws; base-shell screws remain M2x6','screw_length_mm':5,'screw_head_diameter_mm':3.8,'previous_recessed_head_seat_Z_mm':-10.51,'new_recessed_head_seat_Z_mm':seat,'seat_upward_adjustment_mm':1,'access_recess_depth_from_outside_floor_mm':24+seat,'internal_transition_Z_mm':[seat,seat+.9],'external_transition_Z_mm':[seat+.9,seat+1.8],'tower_height_mm':16.1,'minimum_normal_wall_mm':2,'parallel_cone_normal_wall_mm':2.9/math.sqrt(2),'nominal_access_diameter_mm':4.4,'shaft_clearance_diameter_mm':2.6,'one_access_profile_minimum_width_mm':4.22,'minimum_screw_head_to_flat_clearance_mm':.12,'outer_flat_to_encoder_gap_mm':dist-4.02,'nominal_stud_engagement_mm':1.39,'nominal_tip_to_blind_end_mm':1.61,'screw_tip_Z_mm':-4.51,'display_glass_Z_mm':0,'posts':posts,'physical_collisions':hits,'wire_corridor_collisions':wirehits,'main_and_modular_updated':True,'all_changed_parts_single_connected_solids':True,'outside_display_post_envelopes_bidirectional_difference_mm3':diffs,'screws':screwchecks}
 root.attributes.add('MIDI_FDM','display_m2x5',json.dumps(note))
 with open(out+'display-m2x5.json','w') as f:json.dump(note,f,indent=2)
 app.activeDocument.save('Display hollow posts recessed for M2x5 countersunk screws, main and modular')
 print(json.dumps(note))
