"""Install the exact Pololu S13V10F5 and an open, edge-supporting base carrier.

This independent stage does not cut the DC socket opening: socket dimensions
and supply polarity are requested separately.
"""
import adsk.core,adsk.fusion,json,math


def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 if root.attributes.itemByName('MIDI_POWER','converter_carrier'):raise RuntimeError('Converter already installed')
 ao=next(o for o in root.occurrences if o.component.name.startswith('ALT Chainable'));alt=ao.component
 main=[o for o in root.occurrences if o!=ao and not o.component.name.startswith(('TEMP','reg26b'))]
 bc=next(o.component for o in main if o.component.name.startswith('02 '));uc=next(o.component for o in main if o.component.name.startswith('01 '))
 old=next(b for b in bc.bRepBodies if 'RIGHT' in b.name)
 elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'))
 old_alt=next(b for b in elec.bRepBodies if 'BASE' in b.name)
 source=next(o for o in root.occurrences if o.component.name=='reg26b01_0J12728')
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def stage(s):
  with open('/tmp/converter-carrier-progress.json','w') as f:json.dump({'stage':s},f)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def op(a,b,k):
  if not mgr.booleanOperation(a,b,k):raise RuntimeError('BRep Boolean failed')
  return a
 def union(a,b):return op(a,b,bt.UnionBooleanType)
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def move(a,dx=0,dz=0):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,0,dz/10);mgr.transform(a,m);return a
 def gap(a,b):
  q,r=a.boundingBox,b.boundingBox
  return math.sqrt(sum(max(getattr(q.minPoint,k)-getattr(r.maxPoint,k),getattr(r.minPoint,k)-getattr(q.maxPoint,k),0)**2 for k in 'xyz'))*10
 def hit(a,b):
  q,r=a.boundingBox,b.boundingBox
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(inter(mgr.copy(a),mgr.copy(b)))
 stage('placing exact converter and open carrier')
 board=mgr.copy(source.component.bRepBodies.item(0))
 rot=adsk.core.Matrix3D.create();rot.setToRotation(-math.pi/2,adsk.core.Vector3D.create(0,0,1),adsk.core.Point3D.create(0,0,0));mgr.transform(board,rot)
 tr=adsk.core.Matrix3D.create();tr.translation=adsk.core.Vector3D.create(22,-2.6,-1.7);mgr.transform(board,tr)
 # Side/end guides clear the nominal PCB by 0.4mm. The floor remains
 # open under the components, with three ledges on unpopulated edges.
 blocks=[(218,24,-22,234.065,25.6,-16),(218,35.29,-22,234.065,36.89,-16),
         (218,25.6,-22,219.6,35.29,-16),(232.465,25.6,-22,234.065,35.29,-16),
         (220.2,25.2,-22,221.7,26.8,-17),(220.2,34.09,-22,221.7,35.69,-17),
         (231.265,29.9,-22,233.0,31.0,-17)]
 base=mgr.copy(old)
 for values in blocks:base=union(base,box(*values))
 if not base.isSolid or base.lumps.count!=1:raise RuntimeError('Carrier/base disconnected')
 added=cut(mgr.copy(base),mgr.copy(old));contacts=hit(added,board)
 hits=[];near=[]
 for o in main:
  if o.component in [bc] or o.component.name.startswith('REF'):continue
  for b in o.component.bRepBodies:
   for label,a in [('carrier',added),('converter',board)]:
    v=hit(a,b)
    if v>.001:hits.append([label,o.component.name,b.name,v])
    g=gap(a,b)
    if g<3 and o.component!=uc:near.append([label,o.component.name,b.name,g])
 wires=next(o.component for o in main if o.component.name.startswith('REF LED'))
 for b in wires.bRepBodies:
  for label,a in [('carrier',added),('converter',board)]:
   v=hit(a,b)
   if v>.001:hits.append([label,'LED wiring',b.name,v])
 if contacts>.001:hits.append(['carrier to actual double-sided components',contacts])
 paths=[]
 for z in range(-20,1):
  for u in uc.bRepBodies:
   v=hit(move(mgr.copy(base),dz=z),u)
   if v>.001:paths.append(['base insertion',z,u.name,v])
 # Board is lowered into its open carrier before the wire strain relief and
 # adhesive at the bare edge pads are applied.
 for i in range(41):
  z=i*.25;v=hit(move(mgr.copy(board),dz=z),added)
  if v>.001:paths.append(['converter vertical insertion',z,v])
 report={'revision':'aux_power_converter_carrier','converter':'Pololu S13V10F5 #4083; Kamami 1178565','manufacturer_STEP':'datasheets/pololu-4083.step',
  'PCB_layout_XY_mm':[[220,26],[232.065,34.89]],'PCB_bottom_Z_mm':-17,'populated_Z_mm':[-18.349875,-14.184],
  'inside_floor_Z_mm':-22,'under_component_floor_clearance_mm':3.650125,'carrier_outer_XY_mm':[[218,24],[234.065,36.89]],
  'PCB_edge_guide_clearance_mm':.4,'PCB_edge_seat_overlap_mm':.8,'carrier':'Open component cavity, four outer guides and three bare-edge ledges; retain with small neutral-cure silicone dots on bare PCB edges, not on components.',
  'PCB_mount_holes':False,'new_mounting_screws':0,'base_insertion_samples':21,'converter_insertion_samples':41,
  'body_collisions':hits,'assembly_collisions':paths,'near_body_AABB_lower_bounds_mm':near,'converter_component_carrier_intersection_mm3':contacts,
  'socket_status':'Rear-panel socket opening pending body/flange and thread dimensions; converter placement is independent of the proposed X210 socket center.',
  'socket_candidate_reservation':{'center_X_mm':210,'center_Z_mm':0,'thread_diameter_mm':8,'overall_length_mm':20,'not_yet_cut':True},
  'backup':'archive/pre-aux-power.zip','limits':'Board boundary tolerance is ±0.3mm; physical fit and adhesive/thermal performance require validation.'}
 with open(out+'converter-carrier-candidate.json','w') as f:json.dump(report,f,indent=2)
 if hits or paths or near:raise RuntimeError('Converter carrier check failed; inspect candidate report')
 for c,b in [(bc,old),(elec,old_alt)]:
  appearance=b.appearance;name=b.name;b.deleteMe();n=c.bRepBodies.add(mgr.copy(base));n.name=name+' - open Pololu carrier';n.appearance=appearance
 for parent,name in [(root,'Pololu S13V10F5 - 5V converter - manufacturer STEP'),(elec,'ALT reference - Pololu S13V10F5 - 5V converter')]:
  o=parent.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name;o.component.isOriginFolderLightBulbOn=False
  b=o.component.bRepBodies.add(mgr.copy(board));b.name='Exact Pololu 4083 double-sided assembly'
 source.deleteMe()
 root.attributes.add('MIDI_POWER','converter_carrier',json.dumps(report))
 with open(out+'converter-carrier.json','w') as f:json.dump(report,f,indent=2)
 if not app.activeDocument.save('Added exact Pololu S13V10F5 regulator and open base carrier to both main and modular electronics sections; DC jack opening pending socket dimensions.'):
  raise RuntimeError('Save failed')
 stage('complete')
