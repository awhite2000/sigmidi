"""Fill the inherited inset-floor sliver at the rounded front-right corner."""
import adsk.core,adsk.fusion,json

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert not root.attributes.itemByName('MIDI_FDM','base_corner_repair'),'Already repaired'
 assert root.attributes.itemByName('MIDI_FDM','recessed_switch_labels')
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 bc=next(c for c in main if c.name.startswith('02 '));old=next(b for b in bc.bRepBodies if 'RIGHT' in b.name)
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 ec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));ab=next(b for b in ec.bRepBodies if 'BASE' in b.name)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def op(a,b,k):
  assert mgr.booleanOperation(a,b,k),'Boolean failed';return a
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def sub(a,b):return op(mgr.copy(a),mgr.copy(b),bt.DifferenceBooleanType)
 def bounds(a):
  q=a.boundingBox;return [q.minPoint.x*10,-q.maxPoint.y*10,q.minPoint.z*10,q.maxPoint.x*10,-q.minPoint.y*10,q.maxPoint.z*10]
 # Restore only a local piece of the original R6 outer floor outline.
 # The actual front-right M2 mount is at X326,Y85.6, outside this patch.
 patch=op(box(335,77,-24,344,92,-22),box(335,77,-24,350,86,-22),bt.UnionBooleanType)
 patch=op(patch,mgr.createCylinderOrCone(p(344,86,-24),.6,p(344,86,-22),.6),bt.UnionBooleanType)
 added=sub(patch,old);assert 10<vol(added)<20 and added.lumps.count==1
 new=op(mgr.copy(old),mgr.copy(patch),bt.UnionBooleanType)
 assert new.isSolid and new.lumps.count==1
 assert vol(sub(old,new))<.001 and vol(sub(patch,new))<.001
 assert max(abs(a-b) for a,b in zip(bounds(old),bounds(new)))<1e-6
 for a,b in [(old,ab),(ab,old)]:assert vol(sub(a,b))<.001,'Modular source differs'
 # Check all newly restored material against the upper shell, hardware and
 # reference wiring, in its seated position and along floor withdrawal.
 candidates=[]
 q=added.boundingBox
 for c in main:
  if c==bc:continue
  for b in c.bRepBodies:
   r=b.boundingBox
   if r.maxPoint.x<q.minPoint.x or r.minPoint.x>q.maxPoint.x or r.maxPoint.y<q.minPoint.y or r.minPoint.y>q.maxPoint.y:continue
   candidates.append((c.name,b,b.boundingBox))
 collisions=[];samples=[0,-.01,-.25,-.5,-1,-2,-5,-10,-20]
 for dz in samples:
  moving=mgr.copy(added);m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,0,dz/10);mgr.transform(moving,m)
  for name,b,r in candidates:
   if r.maxPoint.z<q.minPoint.z+dz/10 or r.minPoint.z>q.maxPoint.z+dz/10:continue
   hit=vol(op(mgr.copy(moving),mgr.copy(b),bt.IntersectionBooleanType))
   if hit>.001:collisions.append([dz,name,b.name,hit])
 assert not collisions,collisions
 # The patch is remote from the split, all vents and every installed screw.
 fast=next(c for c in main if c.name.startswith('Base fasteners'))
 screws=[]
 for b in fast.bRepBodies:
  r=b.boundingBox;x=(r.minPoint.x+r.maxPoint.x)*5;y=-(r.minPoint.y+r.maxPoint.y)*5;screws.append([x,y])
  assert vol(op(mgr.copy(patch),mgr.copy(b),bt.IntersectionBooleanType))<.001
 report={'revision':'base_corner_repair','location':'front-right rounded corner of main and reused modular electronics base','restored_material_bounds_XYZ_mm':bounds(added),'added_material_mm3':vol(added),'floor_thickness_mm':2,'floor_Z_mm':[-24,-22],'outer_corner_radius_mm':6,'local_patch_XY_mm':[335,77,350,92],'remaining_unintended_gap_mm3':vol(sub(patch,new)),'original_material_removed_mm3':vol(sub(old,new)),'single_connected_solid':new.isSolid and new.lumps.count==1,'outer_bounds_unchanged':True,'all_screw_centers_XY_mm':screws,'screw_bores_countersinks_vents_mounts_and_joints_unchanged':True,'upper_shell_and_all_other_base_parts_unchanged':True,'component_positions_unchanged':True,'main_and_modular_updated':True,'assembly_collisions':collisions,'base_removal_samples_Z_mm':samples,'backup':'archive/pre-base-corner-repair.zip'}
 for c,b in [(bc,old),(ec,ab)]:
  name=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(new));n.name=name+' - continuous front-right floor'
  if appearance:n.appearance=appearance
 for c in [root,alt]:c.attributes.add('MIDI_FDM','base_corner_repair',json.dumps(report))
 with open(out+'base-corner-repair.json','w') as f:json.dump(report,f,indent=2)
 assert app.activeDocument.save('Filled inherited front-right floor sliver in main and modular right base; preserved R6 outline, full 2mm floor, all screws, vents, supports and shell seating.')
