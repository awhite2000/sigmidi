"""Add two M2x6 mounts near the split in both reused right enclosure sections."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 if root.attributes.itemByName('MIDI_FDM','extra_right_base_screws'):raise RuntimeError('Extra screws already installed')
 assert root.attributes.itemByName('MIDI_FDM','rear_vent_membranes')
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 uc=next(c for c in main if c.name.startswith('01 '));bc=next(c for c in main if c.name.startswith('02 '));fast=next(c for c in main if c.name.startswith('Base fasteners'))
 oldshell=next(b for b in uc.bRepBodies if 'RIGHT' in b.name);oldbase=next(b for b in bc.bRepBodies if 'RIGHT' in b.name);left=next(b for b in uc.bRepBodies if 'LEFT' in b.name)
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));ashell=next(b for b in elec.bRepBodies if 'SHELL' in b.name);abase=next(b for b in elec.bRepBodies if 'BASE' in b.name)
 afast=next(o.component for o in elec.occurrences if o.component.name.startswith('Existing right base'))
 assert fast.bRepBodies.count==6 and afast.bRepBodies.count==2
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes;cache={}
 def stage(s):
  with open('/tmp/extra-right-screws-progress.json','w') as f:json.dump({'stage':s},f)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def cyl(x,y,z0,z1,r0,r1=None):return mgr.createCylinderOrCone(p(x,y,z0),r0/10,p(x,y,z1),(r0 if r1 is None else r1)/10)
 def bounds(a):
  key=id(a)
  if key not in cache:cache[key]=(a,a.boundingBox)
  return cache[key][1]
 def known(a,b):cache[id(a)]=(a,b.boundingBox);return a
 def op(a,b,k):
  if not mgr.booleanOperation(a,b,k):raise RuntimeError('Boolean failed')
  return a
 def union(a,b):return op(a,b,bt.UnionBooleanType)
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def shift(a,dx=0,dy=0,dz=0):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,-dy/10,dz/10);mgr.transform(a,m);return a
 def hit(a,b):
  q,r=bounds(a),bounds(b)
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(inter(mgr.copy(a),mgr.copy(b)))
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 def point_segment(q,a,b):
  dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/(dx*dx+dy*dy)))
  return math.hypot(q[0]-a[0]-t*dx,q[1]-a[1]-t*dy)
 def seg_distance(a,b,c,e):
  if all(min(max(a[i],b[i]),max(c[i],e[i]))>=max(min(a[i],b[i]),min(c[i],e[i]))-1e-10 for i in [0,1]) and cross(a,b,c)*cross(a,b,e)<=1e-10 and cross(c,e,a)*cross(c,e,b)<=1e-10:return 0
  return min(point_segment(a,c,e),point_segment(b,c,e),point_segment(c,a,b),point_segment(e,a,b))
 def in_poly(q,poly):
  signs=[cross(a,b,q) for a,b in zip(poly,poly[1:]+poly[:1])]
  return min(signs)>=-1e-9 or max(signs)<=1e-9
 def mount_distance(x,y,poly,b):
  q=bounds(b);x0,x1=q.minPoint.x*10,q.maxPoint.x*10;y0,y1=-q.maxPoint.y*10,-q.minPoint.y*10
  rect=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
  circle=max(0,math.hypot(max(x0-x,x-x1,0),max(y0-y,y-y1,0))-4.5)
  tri=0 if any(in_poly(q,poly) for q in rect) or any(x0<=q[0]<=x1 and y0<=q[1]<=y1 for q in poly) else min(seg_distance(a,b,c,e) for a,b in zip(poly,poly[1:]+poly[:1]) for c,e in zip(rect,rect[1:]+rect[:1]))
  dz=max(-22-q.maxPoint.z*10,q.minPoint.z*10+15,0)
  return math.hypot(min(circle,tri),dz)
 def expanded(poly,delta):
  area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]));lines=[]
  for a,b in zip(poly,poly[1:]+poly[:1]):
   dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy);nx,ny=(dy/length,-dx/length) if area>0 else (-dy/length,dx/length)
   lines.append(((a[0]+delta*nx,a[1]+delta*ny),(dx,dy)))
  result=[]
  for (a,v),(b,w) in zip(lines[-1:]+lines[:-1],lines):
   den=v[0]*w[1]-v[1]*w[0];t=((b[0]-a[0])*w[1]-(b[1]-a[1])*w[0])/den;result.append((a[0]+t*v[0],a[1]+t*v[1]))
  return result
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component;tc.name='TEMP right seam screw mounts'
 def prism(poly,z0,z1):
  sk=tc.sketches.add(tc.xYConstructionPlane)
  for a,b in zip(poly,poly[1:]+poly[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(p(*a,0)),sk.modelToSketchSpace(p(*b,0)))
  tc.features.extrudeFeatures.addSimple(sk.profiles.item(0),adsk.core.ValueInput.createByReal((z1-z0)/10),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
  a=mgr.copy(tc.bRepBodies.item(tc.bRepBodies.count-1));q=bounds(a);a=shift(a,dz=z0-q.minPoint.z*10);cache.pop(id(a),None)
  tc.bRepBodies.item(tc.bRepBodies.count-1).deleteMe();sk.deleteMe();return a
 stage('building two seam-adjacent bosses and matching countersunk bores')
 centers=[(201,6),(201,86)];shell=mgr.copy(oldshell);base=mgr.copy(oldbase);mounts=[];polys=[];pilots=[];new_screws=[]
 source=fast.bRepBodies.item(0);q=bounds(source);sx=(q.minPoint.x+q.maxPoint.x)*5;sy=-(q.minPoint.y+q.maxPoint.y)*5
 assert abs(sx-6)<1e-5 and abs(sy-6)<1e-5
 metal=source.appearance
 for x,y in centers:
  wall,inside=(1.8,10.5) if y<46 else (90.2,81.5)
  poly=[(x+9,wall),(x,wall),(x,inside)];polys.append(poly)
  a=union(cyl(x,y,-22,-15,4.5),prism(poly,-22,-15));known(a,box(x-4.5,min(wall,inside,y-4.5),-22,x+9,max(wall,inside,y+4.5),-15));mounts.append(a)
  shell=union(shell,mgr.copy(a))
  pilot=cyl(x,y,-22.1,-15.5,.95);pilots.append(pilot);shell=cut(shell,mgr.copy(pilot))
  # Relieve only raised locating ribs, retaining the complete 2mm floor.
  relief=union(cyl(x,y,-22,-14.9,4.8),prism(expanded(poly,.3),-22,-14.9));base=cut(base,relief)
  base=cut(base,cyl(x,y,-24.1,-21.9,1.3));base=cut(base,cyl(x,y,-24,-23.1,2.2,1.3))
  screw=shift(mgr.copy(source),dx=x-sx,dy=y-sy);new_screws.append(screw)
 assert shell.isSolid and base.isSolid and shell.lumps.count==base.lumps.count==1
 added=known(cut(mgr.copy(shell),mgr.copy(oldshell)),box(196.5,1.5,-22,210,90.5,-15))
 shell_loss=vol(cut(mgr.copy(oldshell),mgr.copy(shell)));assert shell_loss<.001,shell_loss
 assert vol(cut(mgr.copy(base),mgr.copy(oldbase)))<.001
 seam_loss=hit(cut(mgr.copy(oldbase),mgr.copy(base)),box(193.89,0,-24.01,195.91,92,-19.8));assert seam_loss<.001
 assert bounds(left).maxPoint.x*10<196.5
 stage('checking component, LED lead and wiring clearance')
 hits=[];near=[];wires=[];minimum=1e9;closest=[]
 for c in main:
  if c in [uc,bc]:continue
  for b in c.bRepBodies:
   for i,((x,y),a,poly) in enumerate(zip(centers,mounts,polys)):
    amount=hit(a,b)
    if c.name.startswith('REF'):
     if amount>.001:wires.append([i,c.name,b.name,amount])
     continue
    if amount>.001:hits.append([i,c.name,b.name,amount])
    low=mount_distance(x,y,poly,b);minimum=min(minimum,low)
    if low<5:closest.append([i,c.name,b.name,low])
    if low<3-1e-5:near.append([i,c.name,b.name,low])
 assert not hits and not near and not wires,[hits,near,wires]
 # The pilots are blind, and the cosmetic M2x6 models fit their coaxial bores.
 pilot_checks=[];screw_hits=[]
 for i,((x,y),pilot,screw) in enumerate(zip(centers,pilots,new_screws)):
  empty=hit(pilot,shell);cap=hit(cyl(x,y,-15.49,-15,.95),shell)
  assert empty<.001 and cap>1, [empty,cap]
  assert hit(cyl(x,y,-24,-22,1.3),base)<.001
  pilot_checks.append({'center_XY_mm':[x,y],'empty_pilot_intersection_mm3':empty,'blind_cap_probe_mm3':cap})
  for label,b in [('upper shell',shell),('base',base)]:
   amount=hit(screw,b)
   if amount>.001:screw_hits.append([i,label,amount])
 assert not screw_hits,screw_hits
 # Compare the new shell/base directly, allowing intentional zero-gap seating.
 assert hit(added,base)<.001
 stage('checking base removal with the added mounts')
 assembly=[];steps=[0,-.01,-.25,-.5,-1,-2,-5,-10,-20];bq=bounds(base)
 for dz in steps:
  moving=shift(mgr.copy(base),dz=dz);qb=adsk.core.BoundingBox3D.create(adsk.core.Point3D.create(bq.minPoint.x,bq.minPoint.y,bq.minPoint.z+dz/10),adsk.core.Point3D.create(bq.maxPoint.x,bq.maxPoint.y,bq.maxPoint.z+dz/10));cache[id(moving)]=(moving,qb)
  amount=hit(added,moving)
  if amount>.001:assembly.append([dz,amount])
 assert not assembly,assembly
 report={'revision':'extra_right_base_screws','new_centers_XY_mm':centers,'distance_right_of_split_mm':7.1,'right_section_base_screw_count':4,'main_total_base_screws':8,'modular_8_switch_total_base_screws':8,'screw_type':'M2x6 countersunk, same as existing base screws','boss_outer_diameter_mm':9,'boss_Z_mm':[-22,-15],'pilot_diameter_mm':1.9,'pilot_depth_mm':6.5,'pilot_blind_cap_mm':.5,'base_clearance_diameter_mm':2.6,'countersink_diameter_mm':4.4,'countersink_depth_mm':.9,'countersink_included_angle_degrees':90,'leading_print_web_run_mm':9,'leading_print_web_rise_mm':8.7,'leading_print_web_angle_degrees':math.degrees(math.atan2(8.7,9)),'locating_rib_relief_radial_clearance_mm':.3,'physical_collisions':hits,'clearances_below_3mm':near,'minimum_mount_to_hardware_clearance_lower_bound_mm':minimum,'nearest_hardware_below_5mm':closest,'wire_collisions':wires,'pilot_checks':pilot_checks,'new_screw_intersections':screw_hits,'assembly_collisions':assembly,'base_removal_samples_Z_mm':steps,'upper_original_material_removed_mm3':shell_loss,'upper_added_material_mm3':vol(added),'base_glue_lip_material_removed_mm3':seam_loss,'joint_assembly_argument':'All added shell material is at X>=196.5mm, beyond the left shell maximum X193.65; the vertical seam approach is unchanged. No original upper material or base glue lip is removed.','component_positions_and_existing_mounts_unchanged':True,'rear_and_floor_vent_geometry_unchanged':True,'main_and_modular_updated':True,'backup':'archive/pre-extra-right-base-screws.zip','limits':'Nominal CAD fit and slicing do not establish printed screw engagement strength or physical tolerances. Remove all base screws before withdrawing the floor.'}
 stage('committing main and modular mounts and the four screw references')
 work.deleteMe()
 for c,b,a in [(uc,oldshell,shell),(bc,oldbase,base),(elec,ashell,shell),(elec,abase,base)]:
  name=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(a));n.name=name+' - two extra M2x6 near split'
  if appearance:n.appearance=appearance
 for i,a in enumerate(new_screws):
  for c in [fast,afast]:
   n=c.bRepBodies.add(mgr.copy(a));n.name='M2x6 extra right base '+('rear' if i==0 else 'front')+' near split X201';n.appearance=metal
 fast.name='Base fasteners - eight M2x6 countersunk - cosmetic threads'
 assert fast.bRepBodies.count==8 and afast.bRepBodies.count==4
 with open(out+'extra-right-base-screws.json','w') as f:json.dump(report,f,indent=2)
 with open(out+'modular/modular-design.json') as f:mod=json.load(f)
 mod.update({'right_section_base_screw_count':4,'example_total_base_screws':8,'right_extra_screw_centers_XY_mm':centers,'right_mount_update':'../extra-right-base-screws.json'})
 with open(out+'modular/modular-design.json','w') as f:json.dump(mod,f,indent=2)
 for c in [root,alt]:c.attributes.add('MIDI_FDM','extra_right_base_screws',json.dumps(report))
 alt.attributes.add('MIDI_MODULAR','configuration',json.dumps(mod))
 if not app.activeDocument.save('Added two M2x6 countersunk base mounts near the split at X201 Y6/Y86 in main and modular right sections, with 1.9mm blind pilots and 0.8mm-nozzle base bores; right base now has four screws, main and modular example eight total.'):
  raise RuntimeError('Save failed')
 stage('complete')
