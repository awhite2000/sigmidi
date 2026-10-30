"""Fit Nano components-up and integrate its four posts into all electronics bases.

Run through scripts/fusion_mcp_client.py. Millimetres; assembly-local coordinates.
Native upper-shell revision IDs are checked before and after the operation.
API: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_TemporaryBRepManager.htm
"""
import adsk.core, adsk.fusion, json, math, hashlib
from pathlib import Path

OUT=Path('/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/nano-esp32')
APPLY=True


def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
 assert not r.attributes.itemByName('SIGMIDI','nano_direct_posts'),'Direct mounts already fitted'
 kit=next(o.component for o in r.occurrences if o.component.name.startswith('ALT Arduino Nano ESP32 mount kit'))
 pcb=next(o.component for o in kit.occurrences if o.component.name.startswith('Arduino Nano ESP32'))
 oldspec=json.loads((OUT/'mount-fit.json').read_text())
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def stage(s):Path('/tmp/sigmidi-direct-mount-progress.json').write_text(json.dumps({'stage':s}))
 def p(x,y,z):return adsk.core.Point3D.create(x/10,y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):
  return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def cyl(x,y,z0,z1,rad,r1=None):return mgr.createCylinderOrCone(p(x,y,z0),rad/10,p(x,y,z1),(rad if r1 is None else r1)/10)
 def boolean(a,b,kind):assert mgr.booleanOperation(a,b,kind),'Temporary boolean failed';return a
 def union(a,b):return boolean(a,b,bt.UnionBooleanType)
 def cut(a,b):return boolean(a,b,bt.DifferenceBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count and a.isSolid else 0
 cache={}
 def bounds(a):
  key=id(a)
  if key not in cache:
   q=a.boundingBox;cache[key]=(a,([getattr(q.minPoint,s)*10 for s in 'xyz'],[getattr(q.maxPoint,s)*10 for s in 'xyz']))
  return cache[key][1]
 def hit(a,b):
  aa,bb=bounds(a),bounds(b)
  if any(min(aa[1][i],bb[1][i])-max(aa[0][i],bb[0][i])<1e-6 for i in range(3)):return 0
  return vol(boolean(mgr.copy(a),mgr.copy(b),bt.IntersectionBooleanType))
 def shift(a,dx=0,dz=0):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,0,dz/10);assert mgr.transform(a,m);return a
 def get(c,token):return next(b for b in c.bRepBodies if token in b.name)
 def find(c,prefix):return next(o.component for o in c.occurrences if o.component.name.startswith(prefix))
 leftmain=find(r,'ALT Mirrored MAIN');leftmod=find(find(r,'ALT Mirrored MODULAR'),'Existing LEFT')
 rightmod=find(find(r,'ALT Chainable'),'Existing RIGHT')
 bases=[('Left main',find(leftmain,'Mirrored 02 '), 'LEFT',0,leftmain,False),
        ('Left modular',leftmod,'BASE',0,leftmod,False),
        ('Right main',find(r,'02 '),'RIGHT',350-2*sum(x for x,y in oldspec['board_holes_XY_mm'][:2])/2,r,True),
        ('Right modular',rightmod,'BASE',350-2*sum(x for x,y in oldspec['board_holes_XY_mm'][:2])/2,rightmod,False)]
 # The continuous USB pocket and all upper shells must stay byte-for-byte native revisions.
 preserved={}
 for o in r.allOccurrences:
  for b in o.component.bRepBodies:
   if ('SHELL' in b.name.upper() or 'cap' in o.component.name.lower()) and b.isSolid:
    preserved[b.entityToken]=b.revisionId
 stage('rotating exact manufacturer board around the USB connector centre')
 usb=next(b for b in pcb.bRepBodies if 'CX90B' in b.name)
 ub=bounds(usb);cx=sum(x for x,y in oldspec['board_holes_XY_mm'][:2])/2;usbz=(ub[0][2]+ub[1][2])/2
 flip=adsk.core.Matrix3D.create();assert flip.setToRotation(math.pi,adsk.core.Vector3D.create(0,1,0),p(cx,0,usbz))
 translation=flip.translation;translation.y-=.15;flip.translation=translation
 board=[]
 for b in pcb.bRepBodies:
  a=mgr.copy(b);assert mgr.transform(a,flip);board.append((b,a))
 plate=next(a for b,a in board if b.name.startswith('Nano ESP32 PCB'))
 pb=bounds(plate);seat=pb[0][2];component_face=pb[1][2]
 assert abs(pb[0][0]-90.42163840008723)<.001
 holes=[[x,y-1.5] for x,y in oldspec['board_holes_XY_mm']];pilot=1.55;depth=4.3
 def slot(x0,x1,y0,y1,z0,z1):
  width,height=x1-x0,y1-y0
  if width>=height:
   rad=height/2;cy=(y0+y1)/2
   a=box(x0+rad,y0,z0,x1-rad,y1,z1)
   for x in [x0+rad,x1-rad]:a=union(a,cyl(x,cy,z0,z1,rad))
  else:
   rad=width/2;cx=(x0+x1)/2
   a=box(x0,y0+rad,z0,x1,y1-rad,z1)
   for y in [y0+rad,y1-rad]:a=union(a,cyl(cx,y,z0,z1,rad))
  return a
 specs=json.loads((OUT.parent/'base-vent-reinforcement.json').read_text())['floor_slots_XY_mm']
 # Floor openings retain their exact capsule outlines. Chamfered channels under
 # the front two posts bridge the 2.4mm openings with 45-degree printable roofs.
 def vent_tools_for(right):
  tools=[]
  for name,x0,x1,y0,y1 in specs:
   if not right:x0,x1=350-x1,350-x0
   y0,y1=-y1,-y0
   v=slot(x0,x1,y0,y1,-24.1,-20.9)
   if name=='DFR1075' and abs((y0+y1)/2+47.2)<.1:
    rad=(y1-y0)/2;diamond=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,-20.9),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,2**-.5,2**-.5),(x1-x0)/10,rad*math.sqrt(2)/10,rad*math.sqrt(2)/10))
    v=union(v,diamond)
   tools.append(v)
  return tools
 def post(x,y,tools):
  a=cyl(x,y,-22.1,-21.1,4,3)
  a=union(a,cyl(x,y,-21.2,seat,3))
  if y>-10:a=cut(a,box(x-5,-4.95,-24,x+5,0,seat+.1))
  for tool in tools:
   if hit(a,tool)>.0001:a=cut(a,mgr.copy(tool))
  a=cut(a,cyl(x,y,seat-depth,seat+.1,pilot/2))
  a=cut(a,cyl(x,y,seat-.3,seat+.1,pilot/2,1.05))
  assert a.isSolid and a.lumps.count==1
  return a
 vent_sets={False:vent_tools_for(False),True:vent_tools_for(True)}
 post_sets={}
 for right in [False,True]:
  dx=bases[2][3] if right else 0
  post_sets[right]=[post(x+dx,y,vent_sets[right]) for x,y in holes]
 screws=[]
 for i,(x,y) in enumerate(holes):
  a=cyl(x,y,component_face-5,component_face,.8)
  a=union(a,cyl(x,y,component_face,component_face+1.2,1.5));screws.append(a)
 def collect(c,rootmain=False):
  found=[]
  for o in c.occurrences:
   n=o.component.name
   if rootmain and n.startswith(('ALT','REF','TEMP')):continue
   if 'DFRobot' in n or any(t in n for t in ('REF','Nano','Arduino')):continue
   for b in o.component.bRepBodies:
    if not b.name.startswith('DFR1075 M1.6') and b.isSolid:found.append((n,b))
   # Modular nested electronics references have identity child transforms.
   found.extend(collect(o.component))
  return found
 stage('building all four base candidates and checking exact interference')
 records=[];candidates=[];all_hits=[]
 for label,c,token,dx,assembly,rootmain in bases:
  stage('building '+label+' integral base posts')
  original=get(c,token);base=mgr.copy(original)
  # Remove only the four original MCU columns above the unchanged floor.
  right=dx!=0
  oldxs=[350-x if right else x for x in [88.30579390305104,110.30622390305105]]
  for x in oldxs:
   for y in [-6.70103,-63.30265]:
    base=cut(base,cyl(x,y,-22,0,2.8))
  for a in post_sets[right]:base=union(base,mgr.copy(a))
  assert base.isSolid and base.lumps.count==1,(label,base.lumps.count)
  delta=cut(mgr.copy(base),mgr.copy(original));removed=cut(mgr.copy(original),mgr.copy(base))
  # Outside four old/new mount neighborhoods, the original base is untouched.
  allowed=None
  for x in oldxs:
   for y in [-6.70103,-63.30265]:
    a=cyl(x,y,-22.01,0,2.81);allowed=union(allowed,a) if allowed else a
  for x,y in holes:
   a=cyl(x+dx,y,-22.11,seat+.01,4.01);allowed=union(allowed,a)
  unintended_removed=vol(cut(mgr.copy(removed),mgr.copy(allowed)))
  unintended_added=vol(cut(mgr.copy(delta),mgr.copy(allowed)))
  assert unintended_removed<.001 and unintended_added<.001
  floor_change=vol(boolean(mgr.copy(delta),box(-1,-93,-24.01,351,1,-22.1001),bt.IntersectionBooleanType))
  # Crop complex shell bodies to the mounting neighborhood once, so hundreds
  # of tiny board components are not repeatedly intersected with full shells.
  region=box(86.5+dx,-52,-22.2,112+dx,-3.9,-5)
  targets=[]
  for n,b in collect(assembly,rootmain):
   if b.entityToken==original.entityToken or hit(region,b)<.00001:continue
   cropped=boolean(mgr.copy(b),mgr.copy(region),bt.IntersectionBooleanType)
   if cropped.faces.count:targets.append((n,cropped))
  # No base material may protrude above the PCB seating plane within the
  # board/USB footprint. This checks the whole board envelope in one operation.
  clearance_box=box(pb[0][0]+dx-.01,pb[0][1]-.01,seat+.0001,pb[1][0]+dx+.01,-4.06,-5)
  base_intrusion=boolean(mgr.copy(base),clearance_box,bt.IntersectionBooleanType)
  assert vol(base_intrusion)<.001,(label,'base above PCB seat',vol(base_intrusion))
  stage('checking '+label+' board, screw and shell interference')
  hits=[]
  # Board and screw envelopes versus every fitted part, excluding intentional
  # screw-to-pilot engagement. New base is checked against the entire board.
  for b,a in board:
   if not a.isSolid:continue
   candidate=shift(mgr.copy(a),dx)
   for n,t in targets:
    amount=hit(candidate,t)
    if amount>.001:hits.append(['Nano / '+b.name,n+' / '+t.name,amount])
  for i,a in enumerate(screws):
   candidate=shift(mgr.copy(a),dx)
   for n,t in targets:
    amount=hit(candidate,t)
    if amount>.001:hits.append(['Nano screw '+str(i+1),n+' / '+t.name,amount])
  for n,t in targets:
   amount=hit(delta,t)
   if amount>.001:hits.append(['new post material',n+' / '+t.name,amount])
  blocked=[]
  for tool in vent_sets[right]:
   q=bounds(tool)
   probe=slot(q[0][0],q[1][0],q[0][1],q[1][1],-24.01,-21.001)
   amount=hit(base,probe)
   if amount>.001:blocked.append(amount)
  assert not blocked,(label,blocked)
  all_hits+=hits
  records.append({'variant':label,'translation_X_mm':dx,'single_connected_base':True,'physical_collisions':hits,'blocked_floor_slots':blocked,'unintended_removed_mm3':unintended_removed,'unintended_added_mm3':unintended_added,'base_volume_mm3':vol(base),'removed_old_posts_mm3':vol(removed),'integral_posts_added_mm3':vol(delta),'floor_exterior_added_mm3':floor_change})
  candidates.append((c,original,base))
  Path('/tmp/sigmidi-direct-mount-check.json').write_text(json.dumps({'status':'checking','seat_Z_mm':seat,'component_face_Z_mm':component_face,'checks':records},indent=2))
 assert not all_hits,all_hits
 newusb=next(a for b,a in board if 'CX90B' in b.name)
 assert max(abs(bounds(newusb)[i][k]-ub[i][k]) for i in [0,1] for k in [0,2])<.001
 assert abs(bounds(newusb)[1][1]-(ub[1][1]-1.5))<.001
 report={'revision':'nano_direct_base_components_up','board':'Arduino Nano ESP32 ABX00083 without headers','component_face_down':False,'headers_fitted':False,'board_dimensions_mm':oldspec['board_dimensions_mm'],'hole_pitch_mm':[40.64,15.24],'board_hole_diameter_mm':1.66,'board_holes_XY_mm':holes,'PCB_bottom_Z_mm':seat,'board_component_face_Z_mm':component_face,'USB_face_Y_mm':ub[1][1]-1.5,'USB_center_Z_mm':usbz,'USB_alignment_XZ_unchanged':True,'USB_recess_increase_mm':1.5,'USB_pocket_geometry_unchanged':True,'post_minimum_radial_wall_mm':(6-pilot)/2,'post_outer_diameter_mm':6,'post_root_diameter_mm':8,'post_root_chamfer_degrees':45,'rear_post_flat_Y_mm':-4.95,'vent_channel_roof_chamfer_degrees':45,'PCB_screws':'Four M1.6x5 pan head','PCB_pilot_diameter_mm':pilot,'PCB_pilot_depth_mm':depth,'minimum_blind_web_above_vent_mm':seat-depth+19.7,'nominal_screw_engagement_mm':5-oldspec['board_dimensions_mm'][2],'separate_inserts':0,'bridge_fasteners':0,'physical_or_envelope_collisions':all_hits,'checks':records,'all_variants_collision_free':not all_hits,'upper_shells_modified':False,'floor_vent_count_preserved':13,'physical_fit_qualified':False,'source_STEP':'datasheets/NANO_ESP32.step','source_drawing':'datasheets/ABX00083-datasheet.pdf page 17'}
 Path('/tmp/sigmidi-direct-mount-check.json').write_text(json.dumps(report,indent=2))
 if not APPLY:return
 stage('saving recovery archive before replacing mounts')
 backup='/tmp/sigmidi-before-direct-nano-posts.f3d'
 assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(backup))
 stage('installing integral posts and component-side-up board in all assemblies')
 for c,old,new in candidates:
  name=old.name;appearance=old.appearance;old.deleteMe()
  b=c.bRepBodies.add(new);b.name=name+' - Nano direct posts - components up';b.appearance=appearance
 # Shared board component updates every assembly instance at its existing pose.
 for old,new in board:
  name=old.name;appearance=old.appearance;old.deleteMe()
  b=pcb.bRepBodies.add(new);b.name=name;b.appearance=appearance
 pcb.name='Arduino Nano ESP32 - components UP - no headers - USB rear'
 for o in list(kit.occurrences):
  if 'glue insert' in o.component.name or 'opposite-end bridge' in o.component.name:o.deleteMe()
 hw=next(o.component for o in kit.occurrences if o.component.name.startswith('Nano mounting screws'))
 for b in list(hw.bRepBodies):b.deleteMe()
 for i,a in enumerate(screws):
  b=hw.bRepBodies.add(a);b.name='Nano PCB M1.6x5 '+str(i+1);b.appearance=d.appearances.itemByName('Steel - Satin')
 hw.name='Nano mounting screws - four M1.6x5 - reference'
 kit.name='ALT Arduino Nano ESP32 - direct base posts - components up'
 assert kit.occurrences.count==2
 # Follow each enclosing assembly's presentation pose once. Fusion's native
 # shared occurrences can retain offsets; the root-context transform is authoritative.
 for occurrence in list(r.allOccurrences):
  if occurrence.component!=kit or occurrence.assemblyContext is None:continue
  matrix=occurrence.assemblyContext.transform2.copy();translation=matrix.translation
  if 'Existing RIGHT' in occurrence.fullPathName:translation.x+=bases[2][3]/10
  matrix.translation=translation;occurrence.transform2=matrix

 unchanged=all(b.revisionId==preserved[b.entityToken] for o in r.allOccurrences for b in o.component.bRepBodies if b.entityToken in preserved)
 assert unchanged,'An upper shell or cap changed'
 report['upper_shell_revision_IDs_verified_unchanged']=unchanged
 report['assembly_instance_placement_verified']=True
 placement=[]
 for occurrence in r.allOccurrences:
  if occurrence.component!=kit or occurrence.assemblyContext is None:continue
  parent=occurrence.assemblyContext.transform2.translation;world=occurrence.transform2.translation
  expected_x=bases[2][3] if 'Existing RIGHT' in occurrence.fullPathName else 0
  assert abs((world.x-parent.x)*10-expected_x)<1e-5 and abs(world.y-parent.y)<1e-7
  placement.append({'path':occurrence.fullPathName,'aligned_to_own_assembly':True})
 (OUT/'instance-placement.json').write_text(json.dumps({'world_pose_checks':placement,'upper_shell_revisions_unchanged':unchanged},indent=2)+'\n')
 report['instance_placement_report']='instance-placement.json'
 report['upper_shell_and_cap_bodies_verified']=len(preserved)
 for f in ['mount-fit.json','assembly-clearance.json']:(OUT/f).write_text(json.dumps(report,indent=2)+'\n')
 (OUT/'installation.json').write_text(json.dumps({'revision':report['revision'],'component_face_down':False,'separate_inserts':0,'original_upper_shell_revisions_unchanged':True,'base_shells_modified':True,'USB_cutout_modified':False,'instances':[{'variant':a[0],'translation_X_mm':a[3]} for a in bases]},indent=2)+'\n')
 r.attributes.add('SIGMIDI','nano_direct_posts',json.dumps(report))
 r.attributes.add('SIGMIDI','nano_esp32_mounts',json.dumps(report))
 assert app.activeDocument.save('Nano ESP32 directly on four reinforced integral base posts, components up; upper shells unchanged')
 stage('complete')
