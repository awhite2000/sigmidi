"""Restore 2mm rounded wall above obsolete corner screw-mount reliefs."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert not root.attributes.itemByName('MIDI_FDM','upper_corner_walls'),'Already repaired'
 assert root.attributes.itemByName('MIDI_FDM','wide_pololu_clips')
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes;cache={}
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 uc=next(c for c in main if c.name.startswith('01 '));bc=next(c for c in main if c.name.startswith('02 '))
 sl=next(b for b in uc.bRepBodies if 'LEFT' in b.name);sr=next(b for b in uc.bRepBodies if 'RIGHT' in b.name)
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 ec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));ar=next(b for b in ec.bRepBodies if 'SHELL' in b.name)
 cc=next(o.component for o in alt.occurrences if o.component.name.startswith('Closed left cap'));cb=cc.bRepBodies.item(0)
 def stage(s):
  with open('/tmp/upper-corner-walls-progress.json','w') as f:json.dump({'stage':s},f)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def cyl(x,y,z0,z1,r):return mgr.createCylinderOrCone(p(x,y,z0),r/10,p(x,y,z1),r/10)
 def op(a,b,k):
  assert mgr.booleanOperation(a,b,k),'Boolean failed';return a
 def diff(a,b):return op(mgr.copy(a),mgr.copy(b),bt.DifferenceBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def bounds(a):
  key=id(a)
  if key not in cache:cache[key]=(a,a.boundingBox)
  return cache[key][1]
 def bbox(a):
  q=bounds(a);return [q.minPoint.x*10,-q.maxPoint.y*10,q.minPoint.z*10,q.maxPoint.x*10,-q.minPoint.y*10,q.maxPoint.z*10]
 def hit(a,b):
  q,r=bounds(a),bounds(b)
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(op(mgr.copy(a),mgr.copy(b),bt.IntersectionBooleanType))
 def shift(a,dz):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,0,dz/10);assert mgr.transform(a,m);return a
 def skin(x,sign,inner=4):
  a=diff(cyl(x,6,-15,-9.2,6),cyl(x,6,-15.1,-9.1,inner))
  return op(a,box(x if sign>0 else x-6,0,-15,x+6 if sign>0 else x,6,-9.2),bt.IntersectionBooleanType)
 stage('restoring continuous concentric R6/R4 walls in three rear corners')
 candidates=[];rows=[]
 for label,c,b,x,sign in [('main back-left',uc,sl,6,-1),('main back-right',uc,sr,344,1),('modular cap back-left',cc,cb,126.15,-1)]:
  patch=skin(x,sign);new=op(mgr.copy(b),mgr.copy(patch),bt.UnionBooleanType);added=diff(new,b)
  assert new.isSolid and new.lumps.count==1 and vol(added)>.01
  assert vol(diff(b,new))<.001 and vol(diff(patch,new))<.001
  assert max(abs(a-z) for a,z in zip(bbox(b),bbox(new)))<1e-6
  # Added material stays inside the exterior skin, at least 0.05mm off it.
  assert hit(added,skin(x,sign,5.95))<.001
  candidates.append((c,b,new,added));rows.append({'part':label,'center_XY_mm':[x,6],'outer_radius_mm':6,'inner_radius_mm':4,'minimum_radial_wall_mm':2,'repaired_Z_mm':[-15,-9.2],'added_material_mm3':vol(added),'added_bounds_XYZ_mm':bbox(added),'missing_reference_wall_after_mm3':vol(diff(patch,new)),'original_material_removed_mm3':vol(diff(b,new))})
 assert vol(diff(sr,ar))<.001 and vol(diff(ar,sr))<.001
 stage('checking hardware, wiring, screw pilots and base withdrawal')
 hits=[];wires=[];paths=[];pilot_checks=[]
 for row,(c,old,new,added) in zip(rows,candidates):
  if c==uc:
   for other in main:
    if other==uc:continue
    for b in other.bRepBodies:
     v=hit(added,b)
     if v>.001:(wires if other.name.startswith('REF') else hits).append([row['part'],other.name,b.name,v])
   for step in range(41):
    for b in bc.bRepBodies:
     v=hit(added,shift(mgr.copy(b),-step*.5))
     if v>.001:paths.append([row['part'],-step*.5,b.name,v])
   x=row['center_XY_mm'][0]
   pilot=cyl(x,6,-22,-15.5,.95);assert hit(new,pilot)<.001
   pilot_checks.append({'part':row['part'],'pilot_diameter_mm':1.9,'pilot_empty_mm3':hit(new,pilot),'blind_cap_mm':.5})
  else:
   # The cap and its adjacent pair have the same -65mm local placement;
   # compare in their source coordinates, including the drop-down approach.
   left=next(o.component for o in alt.occurrences if o.component.name.startswith('Leftmost pair'))
   for step in range(9):
    for b in left.bRepBodies:
     v=hit(shift(mgr.copy(added),step*.25),b)
     if v>.001:paths.append([row['part'],'cap approach',step*.25,b.name,v])
 assert not any([hits,wires,paths]),[hits,wires,paths]
 # The front corners use stretched R6/R4 arcs and a 2.19275mm flat joining
 # strip. They do not have the obsolete rear-boss rectangular pockets.
 report={'revision':'upper_corner_walls','cause':'Obsolete rectangular reliefs above rear screw bosses intersected the rounded side wall. At the back-right corner a 4x4mm inner corner inside R6 leaves 6-sqrt(4^2+4^2)=0.343mm, too narrow for the 0.8mm nozzle.','previous_back_right_theoretical_minimum_mm':6-math.sqrt(32),'previous_back_right_sampled_mm':.325,'previous_secondary_relief_theoretical_minimum_mm':6-math.sqrt(3.1**2+4**2),'nominal_repaired_wall_mm':2,'repair':'Fill only missing material in concentric R6/R4 rear quarter-rings from Z-15 to Z-9.2, matching the adjacent 2mm wall.','parts':rows,'all_changed_parts_single_connected_solids':True,'exterior_shape_and_bounds_unchanged':True,'screw_bosses_pilots_base_seating_and_shell_joints_unchanged':True,'front_corner_arc_wall_mm':2,'front_corner_flat_join_wall_mm':math.sqrt(32)-math.sqrt(12),'modular_right_matches_main':True,'repeated_pair_shells_do_not_have_outer_corner_reliefs':True,'body_collisions':hits,'wire_collisions':wires,'assembly_collisions':paths,'base_removal_samples':41,'pilot_checks':pilot_checks,'all_component_positions_and_base_parts_unchanged':True,'backup':'archive/pre-upper-corner-walls.zip','limits':'Thickness and toolpath checks address the geometric hole; actual print bonding and extrusion still depend on printer calibration.'}
 stage('committing main, reused modular right shell and one-piece end cap')
 for c,b,new,added in candidates+[(ec,ar,candidates[1][2],candidates[1][3])]:
  name=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(new));n.name=name+' - continuous 2mm rear corner wall'
  if appearance:n.appearance=appearance
 with open(out+'upper-corner-walls.json','w') as f:json.dump(report,f,indent=2)
 for c in [root,alt]:c.attributes.add('MIDI_FDM','upper_corner_walls',json.dumps(report))
 assert app.activeDocument.save('Restored continuous 2mm rear corner skins above screw bosses in main left/right, reused modular electronics shell and end cap; removed obsolete thin-wall relief effect while retaining exterior and all screws, vents, base fit and component positions.')
 stage('complete')
