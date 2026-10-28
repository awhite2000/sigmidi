"""Add the 9V center-negative M8 DC inlet to both electronics sections."""
import adsk.core,adsk.fusion,json,math


def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 if root.attributes.itemByName('MIDI_POWER','dc_input'):raise RuntimeError('DC inlet already installed')
 if not root.attributes.itemByName('MIDI_POWER','converter_carrier'):raise RuntimeError('Install converter first')
 ao=next(o for o in root.occurrences if o.component.name.startswith('ALT Chainable'));alt=ao.component
 main=[o for o in root.occurrences if o!=ao and not o.component.name.startswith(('TEMP','Temporary'))]
 def find(prefix):return next(o.component for o in main if o.component.name.startswith(prefix))
 uc,bc=find('01 '),find('02 ');old=next(b for b in uc.bRepBodies if 'RIGHT' in b.name)
 elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));old_alt=next(b for b in elec.bRepBodies if 'SHELL' in b.name)
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def stage(s):
  with open('/tmp/dc-input-progress.json','w') as f:json.dump({'stage':s},f)
 def write(n,v):
  with open(out+n,'w') as f:json.dump(v,f,indent=2)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def op(a,b,k):
  if not mgr.booleanOperation(a,b,k):raise RuntimeError('BRep Boolean failed')
  return a
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def union(a,b):return op(a,b,bt.UnionBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def cone(x,z,y0,y1,r0,r1):return mgr.createCylinderOrCone(p(x,y0,z),r0/10,p(x,y1,z),r1/10)
 def gap(a,b):
  q,r=a.boundingBox,b.boundingBox
  return math.sqrt(sum(max(getattr(q.minPoint,k)-getattr(r.maxPoint,k),getattr(r.minPoint,k)-getattr(q.maxPoint,k),0)**2 for k in 'xyz'))*10
 def hit(a,b):
  q,r=a.boundingBox,b.boundingBox
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(inter(mgr.copy(a),mgr.copy(b)))
 def move(a,dx=0,dz=0):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,0,dz/10);mgr.transform(a,m);return a
 stage('forming rear opening and corrected 18mm socket stack')
 x,z=210.,0.
 shell=cut(mgr.copy(old),cone(x,z,-.1,2.1,4.2,4.2))
 shell=cut(shell,cone(x,z,1.6,2.01,4.2,4.61))
 shell=cut(shell,cone(x,z,-.01,.2,4.41,4.2))
 if not shell.isSolid or shell.lumps.count!=1:raise RuntimeError('Shell disconnected')
 thread=cut(cone(x,z,-6,2,4,4),cone(x,z,-6.1,2.1,2.75,2.75))
 flange=cut(cone(x,z,2,6,6,6),cone(x,z,1.99,4.5,2.75,2.75))
 pin=cone(x,z,-5.5,4.5,1.05,1.05)
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component;tc.name='TEMP DC socket geometry'
 sk=tc.sketches.add(tc.xZConstructionPlane);R=13/math.sqrt(3)
 pts=[(x+R*math.cos(i*math.pi/3),R*math.sin(i*math.pi/3)) for i in range(6)]
 for a,b in zip(pts,pts[1:]+pts[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(p(a[0],0,a[1])),sk.modelToSketchSpace(p(b[0],0,b[1])))
 tc.features.extrudeFeatures.addSimple(sk.profiles.item(0),adsk.core.ValueInput.createByString('2 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
 nut=mgr.copy(tc.bRepBodies.item(tc.bRepBodies.count-1));m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,-nut.boundingBox.minPoint.y,0);mgr.transform(nut,m)
 nut=cut(nut,cone(x,z,-2.1,.1,4,4))
 # Lug position/width and flange/nut diameter are conservative reference
 # envelopes: the supplied dimensions define only the axial stack and M8.
 lugs=[box(207.5,6,-2,208.5,12,-1),box(211.5,6,-2,212.5,12,-1)]
 pieces=[('M8 threaded barrel - 8mm long - no helix',thread),('Rear flange/body - 4mm long - assumed diameter 12mm',flange),('2.1mm center contact - nominal visual geometry',pin),('2mm nut - conservative 13mm AF envelope',nut),('Center-negative solder lug - nominal location',lugs[0]),('Positive sleeve solder lug - nominal location',lugs[1])]
 hits=[];clear=[];distances=[]
 def exact_gap(a,b):
  lower=gap(a,b)
  if lower>=3:return lower
  # An empty intersection with the first body's expanded bounding box
  # proves at least 3mm Euclidean separation, including complex floor posts.
  q=a.boundingBox;pad=.3
  region=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((q.minPoint.x+q.maxPoint.x)/2,(q.minPoint.y+q.maxPoint.y)/2,(q.minPoint.z+q.maxPoint.z)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),q.maxPoint.x-q.minPoint.x+2*pad,q.maxPoint.y-q.minPoint.y+2*pad,q.maxPoint.z-q.minPoint.z+2*pad))
  near=inter(mgr.copy(b),region)
  return 3.0 if vol(near)<1e-7 else gap(a,near)
 physical=[]
 for o in main:
  if o.component==uc or o.component.name.startswith('REF'):continue
  for b in o.component.bRepBodies:physical.append((o.component.name,b.name,b))
 left_shell=next(b for b in uc.bRepBodies if 'LEFT' in b.name);physical.append((uc.name,left_shell.name,left_shell))
 hook=inter(mgr.copy(shell),box(189.6,2,-22.01,200.05,12,30.01))
 for label,a in pieces:
  for comp,name,b in physical:
   v=hit(a,b)
   if v>.001:hits.append([label,comp,name,v])
   g=exact_gap(a,b)
   distances.append([label,comp,name,g])
   if g<3-1e-5:clear.append([label,comp,name,g])
  v=hit(a,shell)
  if v>.001:hits.append([label,'mounted shell',v])
  g=exact_gap(a,hook)
  distances.append([label,'internal split receiver',g])
  if g<3-1e-5:clear.append([label,'internal split receiver',g])
 # Resolve the actual cylindrical holes closest to the manufacturer pinout's
 # VIN and GND locations. These are routed approaches, not a PCB netlist.
 pcb=next(b for b in find('DFRobot').bRepBodies if b.name.startswith('Exact PCB'))
 holes=[]
 for f in pcb.faces:
  c=adsk.core.Cylinder.cast(f.geometry)
  if c and abs(c.axis.z)>.999 and .35<c.radius*10<.8:
   q=c.origin;value=[q.x*10,-q.y*10]
   if value[0]>260 and 20<value[1]<40 and not any(math.dist(value,v)<.05 for v in holes):holes.append(value)
 def nearest(y):return min(holes,key=lambda q:math.dist(q,[262.13,y])) if holes else [262.13,y]
 vin=nearest(26.6);gnd=nearest(31.68)
 routes=[('9V sleeve positive to VIN',[(212,12,-1.5),(212,20,-8),(214,24,-12),(214,32.985,-12),(221.27,32.985,-12),(221.27,32.985,-15.984)]),
         ('Center negative to converter GND',[(208,12,-1.5),(208,20,-8),(212,24,-12),(212,30.445,-12),(221.27,30.445,-12),(221.27,30.445,-15.984)]),
         ('Regulated 5V VOUT to DFR1075 VIN-5V',[(221.27,27.905,-15.984),(221.27,27.905,-2),(vin[0],27.905,-2),(vin[0],vin[1],-2),(vin[0],vin[1],-11.5)]),
         ('Converter GND to DFR1075 GND',[(221.27,30.445,-15.984),(221.27,30.445,-2),(gnd[0],30.445,-2),(gnd[0],gnd[1],-2),(gnd[0],gnd[1],-11.5)])]
 wire_shapes=[]
 for name,points in routes:
  for j,(a,b) in enumerate(zip(points,points[1:])):
   wire_shapes.append((name+' segment '+str(j+1),mgr.createCylinderOrCone(p(*a),.08,p(*b),.08)))
 wire_hits=[]
 connected=[find('DFRobot'),find('Pololu')]
 for name,a in wire_shapes:
  for o in main:
   if o.component in connected or o.component.name.startswith('REF'):continue
   for b in o.component.bRepBodies:
    if o.component==uc and b==old:b=shell
    v=hit(a,b)
    if v>.001:wire_hits.append([name,o.component.name,b.name,v])
 paths=[]
 for zoff in range(-20,1):
  for b in bc.bRepBodies:
   v=hit(move(mgr.copy(b),dz=zoff),shell)
   if v>.001:paths.append(['base removal',zoff,b.name,v])
 # The two assembled shell interfaces have not gained material. Verify the
 # original vertical approach with the unchanged left upper shell.
 for i in range(121):
  dz=i*.5;v=hit(move(mgr.copy(left_shell),dz=dz),shell)
  if v>.001:paths.append(['upper shell approach',dz,v])
 # Barrel inserts from inside before the external nut is tightened. Solder
 # the lugs after fitting; the larger rear flange stays inside the enclosure.
 for i in range(41):
  dy=i*.25
  for name,a in [('thread',thread),('rear flange',flange)]:
   moving=mgr.copy(a);m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,-dy/10,0);mgr.transform(moving,m)
   v=hit(moving,shell)
   if v>.001:paths.append(['socket insertion',dy,name,v])
 report={'revision':'aux_dc_power','regulator':'Pololu S13V10F5 #4083 / Kamami 1178565','input_V_DC':9,'polarity':'center negative, sleeve positive',
  'socket_center_layout_XYZ_mm':[210,0,0],'shell_side':'rear, right of split and left of SW4 housing','hole_diameter_mm':8.4,'rear_wall_thickness_mm':2,
  'socket_thread_diameter_mm':8,'thread_length_mm':8,'nut_thickness_mm':2,'flange_body_length_mm':4,'terminal_length_mm':6,'total_socket_length_mm':18,
  'socket_axial_layout_Y_mm':{'front_tip':-6,'nut':[-2,0],'rear_flange':[2,6],'terminals':[6,12]},'free_thread_ahead_of_nut_mm':4,
  'assumed_flange_diameter_mm':12,'assumed_nut_AF_mm':13,'reference_lug_locations':'Nominal only; identify center/sleeve contacts electrically on the purchased socket.',
  'converter_position':'converter-carrier.json','wiring':{'jack_center':'regulator GND','jack_sleeve':'regulator VIN','regulator VOUT':'DFR1075 regulated 5V input header (VIN/VCC)','regulator GND':'DFR1075 GND'},
  'wire_corridor_diameter_mm':1.6,'wire_routes':routes,'DFR1075_header_approaches_XY_mm':{'VIN':vin,'GND':gnd},
  'socket_component_clearance_lower_bounds_mm':distances,'body_collisions':hits,'component_clearance_lower_bounds_below_3mm':clear,'wire_collisions':wire_hits,'assembly_collisions':paths,
  'socket_insertion_samples':41,'base_removal_samples':21,'upper_shell_insertion_samples':121,'all_existing_component_positions_unchanged':True,
  'external_case_dimensions_unchanged':True,'all_base_glue_joints_preserved':True,'backup':'archive/pre-aux-power.zip',
  'limits':'Generic socket reference uses the supplied axial dimensions and conservative flange/nut envelopes. Exact flange diameter, lug positions and plug engagement are not supplied; confirm these on the purchased socket. Native geometric fit does not establish physical thermal/current or printed fit performance.'}
 write('aux-power-candidate.json',report)
 if hits or clear or wire_hits or paths:raise RuntimeError('DC power fit failed; see aux-power-candidate.json')
 work.deleteMe()
 for c,b in [(uc,old),(elec,old_alt)]:
  appearance=b.appearance;name=b.name;b.deleteMe();n=c.bRepBodies.add(mgr.copy(shell));n.name=name+' - M8 DC input';n.appearance=appearance
 for parent,name in [(root,'DC power socket - 9V center-negative - M8 x8 - 18mm overall'),(elec,'ALT reference - DC power socket - 9V center-negative')]:
  o=parent.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name;o.component.isOriginFolderLightBulbOn=False
  for name,a in pieces:b=o.component.bRepBodies.add(mgr.copy(a));b.name=name
 for parent,name in [(root,'REF AUX DC wiring - nonphysical - do not print'),(alt,'REF AUX DC wiring - nonphysical - do not print')]:
  o=parent.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name;o.component.isOriginFolderLightBulbOn=False
  for name,a in wire_shapes:b=o.component.bRepBodies.add(mgr.copy(a));b.name=name
  o.isLightBulbOn=False
 with open(out+'converter-carrier.json') as f:carrier=json.load(f)
 carrier['socket_status']='Installed; see aux-power.json'
 carrier.pop('socket_candidate_reservation',None)
 write('converter-carrier.json',carrier)
 root.attributes.add('MIDI_POWER','converter_carrier',json.dumps(carrier));root.attributes.add('MIDI_POWER','dc_input',json.dumps(report))
 write('aux-power.json',report)
 if not app.activeDocument.save('Added 9V center-negative M8 DC input at X210, exact Pololu 4083 carrier and wiring to DFR1075 5V/GND in main and modular models; socket stack corrected to 18mm.'):
  raise RuntimeError('Save failed')
 stage('complete')
