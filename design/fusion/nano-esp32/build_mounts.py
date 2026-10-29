"""Create reversible Nano ESP32 mount inserts; never change an enclosure body.
Run with the project's Fusion MCP client. Lengths below are millimetres.
"""
import adsk.core, adsk.fusion, json, math
from pathlib import Path

OUT=Path('/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/nano-esp32')


def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert app.activeDocument.name.startswith('MIDI Foot Controller - VERIFIED')
 assert not root.attributes.itemByName('SIGMIDI','nano_esp32_mounts'),'Already installed'
 for old in list(root.occurrences):
  if old.component.name=='ALT Arduino Nano ESP32 mount kit - original base unchanged':
   assert old.component.occurrences.count==3
   old.deleteMe()
 source=next(o for o in root.occurrences if o.component.name=='REF Arduino Nano ESP32 manufacturer STEP')
 main=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Mirrored MAIN'))
 base=next(o.component for o in main.occurrences if 'Removable base' in o.component.name)
 oldboard=next(o.component for o in main.occurrences if 'DFRobot' in o.component.name)
 usb=next(b for b in oldboard.bRepBodies if 'USB_' in b.name)
 cx=(usb.boundingBox.minPoint.x+usb.boundingBox.maxPoint.x)*5
 usb_face=usb.boundingBox.maxPoint.y*10-.3
 old_usb_center=(usb.boundingBox.minPoint.z+usb.boundingBox.maxPoint.z)*5
 front=usb_face-1.1119551197170543
 board_face=old_usb_center+(-.45000071895100163+3.1699997310360017)/2
 holes_x=[cx-7.62,cx+7.62];holes_y=[front-1.27,front-41.91]
 old_x=[88.30579390305104,110.30622390305105];old_y=[-6.70103,-63.30265]
 floor=-22;seat=board_face;post_top=-13.1;pilot=1.55;clearance=2.0;pad_r=2.0
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def p(x,y,z):return adsk.core.Point3D.create(x/10,y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):
  return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def cyl(x,y,z0,z1,r):return mgr.createCylinderOrCone(p(x,y,z0),r/10,p(x,y,z1),r/10)
 def cone(x,y,z0,z1,r0,r1):return mgr.createCylinderOrCone(p(x,y,z0),r0/10,p(x,y,z1),r1/10)
 def boolean(a,b,kind):
  assert mgr.booleanOperation(a,b,kind),'BRep boolean failed';return a
 def union(a,b):return boolean(a,b,bt.UnionBooleanType)
 def cut(a,b):return boolean(a,b,bt.DifferenceBooleanType)
 def collision(a,b):
  aa,bb=a.boundingBox,b.boundingBox
  if any(min(getattr(aa.maxPoint,s),getattr(bb.maxPoint,s))-max(getattr(aa.minPoint,s),getattr(bb.minPoint,s))<=1e-7 for s in 'xyz'):return 0
  c=boolean(mgr.copy(a),mgr.copy(b),bt.IntersectionBooleanType)
  return c.volume*1000 if c.faces.count else 0
 def subtract_below_ramp(body):
  # Keep z >= y - 6.8: a 45 degree support under the cantilever.
  normal=adsk.core.Vector3D.create(0,1,-1);normal.normalize()
  center=p(0,3.4,-3.4);center.translateBy(adsk.core.Vector3D.create(normal.x*10,normal.y*10,normal.z*10))
  tool=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(center,normal,adsk.core.Vector3D.create(1,0,0),20,40,40))
  return cut(body,tool)
 def pilot_hole(body,x,y):
  body=cut(body,cyl(x,y,seat-3.6,seat+.05,pilot/2))
  return cut(body,cone(x,y,seat-.25,seat+.05,pilot/2,1.05))
 # USB-side insert: flat glue land on the unvented floor; stepped walls are untouched.
 front_insert=box(cx-7.3,-12.8,floor+.15,cx+7.3,-9.5,-19.45)
 for x in holes_x:
  arm=box(x-pad_r,-12.8,-19.6,x+pad_r,holes_y[0]+pad_r,seat)
  arm=subtract_below_ramp(arm)
  arm=union(arm,box(x-1.8,-12.8,-19.6,x+1.8,-10.8,-12.8))
  front_insert=union(front_insert,arm)
 for x in old_x:
  front_insert=cut(front_insert,cyl(x,old_y[0],-24,post_top+.3,2.8))
 for x in holes_x:front_insert=pilot_hole(front_insert,x,holes_y[0])
 # Far-end insert: U-shaped bridge on the two existing non-USB mounting poles.
 rear=box(old_x[0]-2.8,old_y[1]-2.8,post_top,old_x[1]+2.8,old_y[1]+2.8,post_top+2.2)
 for x in holes_x:
  rear=union(rear,box(x-pad_r,old_y[1],post_top,x+pad_r,holes_y[1]+pad_r,post_top+2.2))
  rear=union(rear,cyl(x,holes_y[1],post_top,seat,pad_r))
  rear=pilot_hole(rear,x,holes_y[1])
 for x in old_x:
  rear=cut(rear,cyl(x,old_y[1],post_top-.1,post_top+2.3,clearance/2))
 # Component-side-down boards have LEDs/capacitors close to the corner holes.
 # Relieve the upper 1.2 mm, retaining outward-facing semicircular bearing pads.
 # The lower pilot remains enclosed; there are no fragile slivers next to SMDs.
 def relieve_necks(body,y):
  body=cut(body,box(cx-20,-70,seat-1.2,cx+20,0,seat+.1))
  for x in holes_x:
   neck=cyl(x,y,seat-1.3,seat,pad_r)
   neck=cut(neck,box(x if x<cx else x-5,y-3,seat-1.4,x+5 if x<cx else x,y+3,seat+.1))
   body=union(body,neck)
   body=pilot_hole(body,x,y)
  return body
 front_insert=relieve_necks(front_insert,holes_y[0])
 front_insert=cut(front_insert,box(cx-20,-4.95,-25,cx+20,0,seat+.1))
 rear=relieve_necks(rear,holes_y[1])
 assert front_insert.isSolid and front_insert.lumps.count==1
 assert rear.isSolid and rear.lumps.count==1
 # Correct manufacturer PCB reference: its STEP represents a box without holes.
 # Use the four mounting bores in the official dimension drawing (R0.83).
 matrix=adsk.core.Matrix3D.create()
 assert matrix.setToAlignCoordinateSystems(p(0,0,0),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),adsk.core.Vector3D.create(0,0,1),p(cx+8.89,front,board_face),adsk.core.Vector3D.create(0,-1,0),adsk.core.Vector3D.create(-1,0,0),adsk.core.Vector3D.create(0,0,-1))
 board_bodies=[];excluded=[]
 for occ in source.component.allOccurrences:
  if '+JP1:' in '+'+occ.fullPathName or '+JP2:' in '+'+occ.fullPathName:
   excluded.append(occ.fullPathName);continue
  for b in occ.bRepBodies:
   if not b.faces.count:continue
   a=mgr.copy(b);assert mgr.transform(a,matrix)
   name=occ.fullPathName+' / '+b.name
   if '+Board:1+' in '+'+occ.fullPathName:
    for x in holes_x:
     for y in holes_y:a=cut(a,cyl(x,y,seat-.1,seat+2,.83))
    name='Nano ESP32 PCB - 43.18x17.78 - four diameter 1.66 mounting bores'
   board_bodies.append((name,a,b))
 assert any(name.startswith('Nano ESP32 PCB') for name,_,_ in board_bodies)
 # Exact insert-to-enclosure checks, and conservative electronic envelopes.
 collisions=[]
 for label,a in [('USB glue insert',front_insert),('Existing-pole insert',rear)]:
  for cocc in main.occurrences:
   c=cocc.component
   if 'DFRobot' in c.name or c.name.startswith('REF'):continue
   for b in c.bRepBodies:
    if b.name.startswith('DFR1075 M1.6'):continue
    v=collision(a,b)
    if v>.001:collisions.append([label,c.name,b.name,v])
  for name,b,_ in board_bodies:
   if name.startswith('Nano ESP32 PCB'):continue
   q=b.boundingBox
   lo=[getattr(q.minPoint,s)*10 for s in 'xyz'];hi=[getattr(q.maxPoint,s)*10 for s in 'xyz']
   # STEP also contains zero-thickness copper/reference faces.
   for axis in range(3):
    if hi[axis]-lo[axis]<.01:lo[axis]-=.005;hi[axis]+=.005
   envelope=box(*lo,*hi)
   v=collision(a,envelope)
   if v>.001:collisions.append([label,'Nano electronic envelope',name,v])
 # Capture unchanged body revisions before adding only separate components.
 preserved={b.entityToken:b.revisionId for o in root.allOccurrences for b in o.component.bRepBodies if o.component!=source.component}
 kit=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());kit.component.name='ALT Arduino Nano ESP32 mount kit - original base unchanged'
 def addpart(name,shape):
  o=kit.component.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name
  b=o.component.bRepBodies.add(mgr.copy(shape));b.name=name;return o.component,b
 usbpart,fb=addpart('Nano USB-side glue insert - 45 degree supports - M1.6x5',front_insert)
 rearpart,rb=addpart('Nano opposite-end bridge - existing M1.6 poles - M1.6x5 PCB mounts',rear)
 bo=kit.component.occurrences.addNewComponent(adsk.core.Matrix3D.create());bo.component.name='Arduino Nano ESP32 - components down - no headers - USB rear'
 for name,a,original in board_bodies:
  b=bo.component.bRepBodies.add(a);b.name=name
 kit.isLightBulbOn=False;source.isLightBulbOn=False
 report={'status':'Nominal geometry verified; physical fit testing required','board':'Arduino Nano ESP32 ABX00083 without headers','board_dimensions_mm':[43.18,17.78,1.6060039],'hole_pitch_mm':[40.64,15.24],'board_hole_diameter_mm':1.66,'component_face_down':True,'board_component_face_Z_mm':board_face,'USB_face_Y_mm':usb_face,'USB_recess_increase_mm':.3,'board_holes_XY_mm':[[x,y] for y in holes_y for x in holes_x],'glue_insert_land_mm':[14.6,3.3],'glue_gap_mm':.15,'PCB_screws':'Four M1.6x5 pan head','PCB_pilot_diameter_mm':pilot,'PCB_pilot_depth_mm':3.6,'bridge_fasteners':'Two M1.6x6 pan head into existing far-end posts','bridge_clearance_holes_mm':clearance,'bridge_thickness_mm':2.2,'existing_post_centers_XY_mm':[[x,old_y[1]] for x in old_x],'physical_or_envelope_collisions':collisions,'excluded_manufacturer_header_occurrences':excluded,'inserts_single_solids':True,'unchanged_original_bodies':all(b.revisionId==preserved[b.entityToken] for o in root.allOccurrences for b in o.component.bRepBodies if b.entityToken in preserved),'source_STEP':'datasheets/NANO_ESP32.step','source_drawing':'datasheets/ABX00083-datasheet.pdf page 17'}
 with open(OUT/'mount-fit.json','w') as f:json.dump(report,f,indent=2)
 for name,b in [('usb-side-glue-insert',fb),('existing-pole-insert',rb)]:
  a=mgr.copy(b);q=a.boundingBox;m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(-q.minPoint.x,-q.minPoint.y,-q.minPoint.z);assert mgr.transform(a,m)
  temp=kit.component.bRepBodies.add(a);opt=d.exportManager.createSTLExportOptions(temp,str(OUT/(name+'.stl')));opt.isBinaryFormat=True;opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh;assert d.exportManager.execute(opt);temp.deleteMe()
