"""Restore stock rear skin over an obsolete TRS-port relief sliver."""
import adsk.core,adsk.fusion,json

def run(_context):
 app=adsk.core.Application.get();root=adsk.fusion.Design.cast(app.activeProduct).rootComponent
 assert root.attributes.itemByName('MIDI_FDM','enclosure_wall_reinforcement')
 assert not root.attributes.itemByName('MIDI_FDM','old_TRS_relief_closed')
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 uc=next(c for c in main if c.name.startswith('01 '));old=next(b for b in uc.bRepBodies if 'RIGHT' in b.name)
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'));ec=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'));ab=next(b for b in ec.bRepBodies if 'SHELL' in b.name)
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def cyl(r):return mgr.createCylinderOrCone(p(344,6,-6.5),r/10,p(344,6,6.5),r/10)
 def op(a,b,k):
  assert mgr.booleanOperation(a,b,k);return a
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def hit(a,b):
  q,r=a.boundingBox,b.boundingBox
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-7 for k in 'xyz'):return 0
  return vol(op(mgr.copy(a),mgr.copy(b),bt.IntersectionBooleanType))
 ring=op(cyl(6),cyl(4),bt.DifferenceBooleanType);ring=op(ring,box(344,0,-6.5,350,6,6.5),bt.IntersectionBooleanType)
 patch=op(ring,box(339.5,0,-6.5,344,2,6.5),bt.UnionBooleanType)
 new=op(mgr.copy(old),mgr.copy(patch),bt.UnionBooleanType);added=op(mgr.copy(new),mgr.copy(old),bt.DifferenceBooleanType)
 assert .01<vol(added)<100 and new.isSolid and new.lumps.count==1
 assert vol(op(mgr.copy(old),mgr.copy(new),bt.DifferenceBooleanType))<.001
 assert vol(op(mgr.copy(patch),mgr.copy(new),bt.DifferenceBooleanType))<.001
 hits=[];wires=[]
 for c in main:
  if c==uc:continue
  for b in c.bRepBodies:
   v=hit(added,b)
   if v>.001:(wires if c.name.startswith('REF') else hits).append([c.name,b.name,v])
 assert not hits and not wires,[hits,wires]
 for c,b in [(uc,old),(ec,ab)]:
  name=b.name;appearance=b.appearance;b.deleteMe();n=c.bRepBodies.add(mgr.copy(new));n.name=name+' - obsolete TRS relief closed';n.appearance=appearance
 with open(out+'enclosure-wall-reinforcement.json') as f:report=json.load(f)
 report['obsolete_TRS_relief']={'location_XY_mm':[343.8,0,344.6,2.06],'Z_mm':[-6.5,6.5],'previous_sampled_minimum_mm':.0043,'restored_wall_mm':2,'added_material_mm3':vol(added),'current_TRS_ports_and_chamfers_unchanged':True,'body_collisions':hits,'wire_collisions':wires,'restored_nominal_profile_missing_mm3':0}
 with open(out+'enclosure-wall-reinforcement.json','w') as f:json.dump(report,f,indent=2)
 for c in [root,alt]:c.attributes.add('MIDI_FDM','enclosure_wall_reinforcement',json.dumps(report));c.attributes.add('MIDI_FDM','old_TRS_relief_closed',json.dumps(report['obsolete_TRS_relief']))
 assert app.activeDocument.save('Closed obsolete outboard TRS-port relief at X343.8..344.6 using nominal 2mm rear R6/R4 wall profile; current ports and all component positions unchanged; main and modular electronics shells matched.')
