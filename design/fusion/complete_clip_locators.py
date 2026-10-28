"""Add positive lateral location to the three open PCB edge seats."""
import adsk.core,adsk.fusion,json,math

def run(_context: str):
 app=adsk.core.Application.get();root=adsk.fusion.Design.cast(app.activeProduct).rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 with open(out+'ventilated-clip.json') as f:report=json.load(f)
 if report.get('positive_lateral_locators'):raise RuntimeError('Locators already installed')
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','REF','TEMP','Temporary'))]
 bc=next(c for c in main if c.name.startswith('02 '));base=next(b for b in bc.bRepBodies if 'RIGHT' in b.name)
 uc=next(c for c in main if c.name.startswith('01 '));pc=next(c for c in main if c.name.startswith('Pololu'))
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 elec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'))
 ab=next(b for b in elec.bRepBodies if 'BASE' in b.name)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(v):
  x0,y0,z0,x1,y1,z1=v
  return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def hit(a,b):
  q,r=a.boundingBox,b.boundingBox
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  a=mgr.copy(a)
  if not mgr.booleanOperation(a,mgr.copy(b),bt.IntersectionBooleanType):raise RuntimeError('Intersection failed')
  return a.volume*1000 if a.faces.count else 0
 specs=[(218,24.4,-22,219.6,26.8,-9.484),(219.3,24.1,-22,221.7,25.7,-9.484),(218,34.09,-22,219.6,36.49,-9.484),(219.3,35.19,-22,221.7,36.79,-9.484),(232.465,29.25,-22,234.065,31.65,-9.484)]
 blocks=[box(v) for v in specs];hits=[];paths=[]
 for a in blocks:
  for c in main:
   if c==bc:continue
   for b in c.bRepBodies:
    v=hit(a,b)
    if v>.001:hits.append([c.name,b.name,v])
 for v in specs:
  sweep=box([v[0],v[1],v[2]-20,v[3],v[4],v[5]])
  for b in uc.bRepBodies:
   amount=hit(sweep,b)
   if amount>.001:paths.append([b.name,amount])
 if hits or paths:raise RuntimeError('Locator interference '+json.dumps([hits,paths]))
 final=mgr.copy(base)
 for a in blocks:
  if not mgr.booleanOperation(final,a,bt.UnionBooleanType):raise RuntimeError('Union failed')
 assert final.isSolid and final.lumps.count==1
 for c,b in [(bc,base),(elec,ab)]:
  name=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(final));n.name=name
  if appearance:n.appearance=appearance
 report.update({'positive_lateral_locators':True,'lateral_locator_boxes_mm':specs,'lateral_clearance_X_mm':.4,'lateral_clearance_Y_mm':.3,'locator_top_Z_mm':-9.484,'locator_body_collisions':hits,'locator_continuous_20mm_withdrawal_sweep_collisions':paths})
 with open(out+'ventilated-clip.json','w') as f:json.dump(report,f,indent=2)
 with open(out+'converter-carrier.json') as f:carrier=json.load(f)
 carrier.update({'carrier_outer_XY_mm':[[218,22.8],[234.065,38.09]],'positive_lateral_locators':True,'lateral_clearance_X_mm':.4,'lateral_clearance_Y_mm':.3})
 with open(out+'converter-carrier.json','w') as f:json.dump(carrier,f,indent=2)
 for c in [root,alt]:c.attributes.add('MIDI_POWER','ventilated_clip',json.dumps(report));c.attributes.add('MIDI_POWER','converter_carrier',json.dumps(carrier))
 if not app.activeDocument.save('Completed raised Pololu snap mount with open corner locators, 0.4mm X and 0.3mm Y lateral fit; main and modular bases matched.'):
  raise RuntimeError('Save failed')
