"""Remove superseded post root remnants while preserving integral Nano supports."""
import adsk.core,adsk.fusion,json
from pathlib import Path
P=Path('/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/nano-esp32')
def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent;m=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 def find(c,s):return next(o.component for o in c.occurrences if o.component.name.startswith(s))
 def pt(x,y,z):return adsk.core.Point3D.create(x/10,y/10,z/10)
 def cyl(x,y,z0,z1,a,b=None):return m.createCylinderOrCone(pt(x,y,z0),a/10,pt(x,y,z1),(a if b is None else b)/10)
 def box(x0,y0,z0,x1,y1,z1):return m.createBox(adsk.core.OrientedBoundingBox3D.create(pt((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def diff(a,b):assert m.booleanOperation(a,b,bt.DifferenceBooleanType);return a
 spec=json.loads((P/'mount-fit.json').read_text());holes=spec['board_holes_XY_mm'];dx=spec['checks'][2]['translation_X_mm']
 protected={b.entityToken:b.revisionId for o in r.allOccurrences for b in o.component.bRepBodies if 'SHELL' in b.name.upper() or 'cap' in o.component.name.lower()}
 bases=[('Left main',find(find(r,'ALT Mirrored MAIN'),'Mirrored 02 '),'LEFT',False),('Left modular',find(find(r,'ALT Mirrored MODULAR'),'Existing LEFT'),'BASE',False),('Right main',find(r,'02 '),'RIGHT',True),('Right modular',find(find(r,'ALT Chainable'),'Existing RIGHT'),'BASE',True)]
 assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions('/tmp/sigmidi-before-root-cleanup-pass.f3d'))
 prior=json.loads((P/'root-cleanup-verification.json').read_text()) if (P/'root-cleanup-verification.json').exists() else {'assemblies':[]}
 records=[]
 for label,c,token,right in bases:
  old=next(b for b in c.bRepBodies if token in b.name);a=m.copy(old);before=a.volume*1000;tools=[]
  for source_x in [88.30579390305104,110.30622390305105]:
   for y in [-6.70103,-63.30265]:
    x=350-source_x if right else source_x
    t=cyl(x,y,-22,-20.29999,4.50001,2.79999)
    # Protect the new four post envelopes, including their tapered roots.
    for hx,hy in holes:
     hx+=dx if right else 0
     n=cyl(hx,hy,-22.1,-21.1,4,3);assert m.booleanOperation(n,cyl(hx,hy,-21.2,spec['PCB_bottom_Z_mm'],3),bt.UnionBooleanType)
     if hy>-10:n=diff(n,box(hx-5,-4.95,-24,hx+5,0,0))
     t=diff(t,n)
    # Preserve the rear locating rib strips at each side of the PCB.
    for lo,hi in [(80,85.30011390305106),(113.200113903051,119)]:
     if right:lo,hi=350-hi,350-lo
     t=diff(t,box(lo,-4.15,-22.1,hi,0,0))
    tools.append(t);a=diff(a,m.copy(t))
  assert a.isSolid and a.lumps.count==1
  removed=before-a.volume*1000;assert removed>-.001,(label,removed)
  # Every cleanup tool must be empty after subtraction.
  for t in tools:
   probe=m.copy(a);assert m.booleanOperation(probe,t,bt.IntersectionBooleanType)
   assert not probe.faces.count or probe.volume*1000<.001
  name=old.name;appearance=old.appearance;old.deleteMe();b=c.bRepBodies.add(a);b.name=name;b.appearance=appearance
  records.append({'assembly':label,'removed_mm3':removed+next((v['removed_mm3'] for v in prior['assemblies'] if v['assembly']==label),0),'base_volume_mm3':a.volume*1000,'single_solid':True,'root_regions_clear':True})
 assert all(b.revisionId==protected[b.entityToken] for o in r.allOccurrences for b in o.component.bRepBodies if b.entityToken in protected)
 report={'assemblies':records,'upper_geometry_unchanged':True,'floor_cut_limit_Z_mm':-22,'new_post_envelopes_and_rear_ribs_preserved':True}
 (P/'root-cleanup-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 for row in spec['checks']:row['base_volume_mm3']=next(v['base_volume_mm3'] for v in records if v['assembly']==row['variant'])
 spec['root_geometry_verification']='root-cleanup-verification.json'
 for name in ['mount-fit.json','assembly-clearance.json']:(P/name).write_text(json.dumps(spec,indent=2)+'\n')
 r.attributes.add('SIGMIDI','nano_direct_posts',json.dumps(spec));assert app.activeDocument.save('Clean integral base mounting geometry')
