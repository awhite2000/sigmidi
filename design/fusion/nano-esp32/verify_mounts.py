"""Validate the Nano kit against all four enclosure configurations (Fusion API)."""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
OUT=Path('/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/nano-esp32')

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
 kit=next(o.component for o in r.occurrences if o.component.name=='ALT Arduino Nano ESP32 mount kit - original base unchanged')
 spec=json.loads((OUT/'mount-fit.json').read_text());assert not spec['physical_or_envelope_collisions']
 pcb=next(o.component for o in kit.occurrences if o.component.name.startswith('Arduino Nano ESP32'))
 parts=[o.component for o in kit.occurrences if o.component!=pcb and not o.component.name.startswith("Nano mounting screws")]
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def copy(b,dx=0):
  a=mgr.copy(b);m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,0,0);assert mgr.transform(a,m);return a
 def bounds(b):
  q=b.boundingBox
  return ([getattr(q.minPoint,s) for s in "xyz"],[getattr(q.maxPoint,s) for s in "xyz"])
 def collision(a,b,aa,bb):
  if any(min(aa[1][i],bb[1][i])-max(aa[0][i],bb[0][i])<1e-7 for i in range(3)):return 0
  c=mgr.copy(a);assert mgr.booleanOperation(c,mgr.copy(b),bt.IntersectionBooleanType)
  return c.volume*1000 if c.faces.count else 0
 def cylinder(x,y,z0,z1,rad):
  return mgr.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),rad/10,adsk.core.Point3D.create(x/10,y/10,z1/10),rad/10)
 def collect(c,mainroot=False):
  found=[(c.name,b) for b in c.bRepBodies]
  for o in c.occurrences:
   n=o.component.name
   if mainroot and n.startswith(('ALT','REF','TEMP')):continue
   if 'DFRobot' in n or any(tag in n for tag in ('REF','Nano','Arduino')):continue
   found.extend(collect(o.component))
  return [(n,b) for n,b in found if not b.name.startswith('DFR1075 M1.6')]
 mirrored=next(o.component for o in r.occurrences if o.component.name.startswith('ALT Mirrored MAIN'))
 modular=next(o.component for o in r.occurrences if o.component.name.startswith('ALT Chainable'))
 rightmod=next(o.component for o in modular.occurrences if o.component.name.startswith('Existing RIGHT'))
 lm=next(o.component for o in r.occurrences if o.component.name.startswith('ALT Mirrored MODULAR'))
 leftmod=next(o.component for o in lm.occurrences if o.component.name.startswith('Existing LEFT'))
 cx=sum(x for x,y in spec['board_holes_XY_mm'][:2])/2;dx=350-2*cx
 checks=[];seat=spec['board_component_face_Z_mm'];back=seat+1.6060039
 screws=[]
 for i,(x,y) in enumerate(spec['board_holes_XY_mm']):
  a=cylinder(x,y,back-5,back,.8);assert mgr.booleanOperation(a,cylinder(x,y,back,back+1.2,1.5),bt.UnionBooleanType);screws.append(('Nano M1.6x5 screw '+str(i+1),a))
 for label,c,shift,rootmain in [('Left main',mirrored,0,False),('Left modular',leftmod,0,False),('Right main',r,dx,True),('Right modular',rightmod,dx,False)]:
  targets=[(n,b,bounds(b)) for n,b in collect(c,rootmain)];hits=[]
  candidates=[(pc.name,b) for pc in parts for b in pc.bRepBodies]+[(pcb.name+' / '+b.name,b) for b in pcb.bRepBodies]+screws
  for name,b in candidates:
   shape=copy(b,shift); shape_bounds=bounds(shape)
   for target,other,other_bounds in targets:
    v=collision(shape,other,shape_bounds,other_bounds)
    if v>.001:hits.append([name,target,other.name,v])
  checks.append({'variant':label,'collisions':hits,'objects_checked':len(candidates),'target_bodies':len(targets)})
  with open(OUT/'assembly-clearance-progress.json','w') as f:json.dump({'checks':checks},f,indent=2)
 data={'checks':checks,'all_variants_collision_free':not any(c['collisions'] for c in checks),'source_geometry':'Official Nano STEP, corrected PCB bores, complete native enclosure BReps','threaded_engagements':'New screw-to-pilot intersections are intended; original MCU screws are omitted','physical_hardware_tested':False}
 with open(OUT/'assembly-clearance.json','w') as f:json.dump(data,f,indent=2)
 assert data['all_variants_collision_free'], 'Assembly collision found'
