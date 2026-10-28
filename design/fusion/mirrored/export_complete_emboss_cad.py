"""Export complete assembly geometry independently of source folder visibility."""
import adsk.core,adsk.fusion,json,datetime,zipfile,os

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 mgr=adsk.fusion.TemporaryBRepManager.get()
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/mirrored/'
 report=json.loads(root.attributes.itemByName('MIDI_MIRROR','logical_left_electronics').value)
 names=[('main',report['new_main_component'],'midi-foot-mirrored-main'),('modular',report['new_modular_component'],'midi-foot-mirrored-modular')]
 visibility=[(o,o.isLightBulbOn) for o in root.occurrences];records=[];work=None
 def stage(s):
  with open('/tmp/sigmidi-complete-cad-progress.json','w') as f:json.dump({'stage':s},f)
 def mul(a,b):return [sum(a[i*4+k]*b[k*4+j] for k in range(4)) for i in range(4) for j in range(4)]
 def walk(comp,matrix=None,path=''):
  matrix=matrix or adsk.core.Matrix3D.create();path=path+'/'+comp.name
  for b in comp.bRepBodies:
   a=mgr.copy(b);assert mgr.transform(a,matrix);yield path,b,a
  for o in comp.occurrences:
   m=adsk.core.Matrix3D.create();assert m.setWithArray(mul(list(matrix.asArray()),list(o.transform2.asArray())))
   yield from walk(o.component,m,path)
 try:
  for folder,name,filename in names:
   comp=next(o.component for o in root.occurrences if o.component.name==name)
   stage('copying complete '+folder+' assembly into export component')
   work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());temp=work.component
   temp.name='TEMP SIGMIDI complete '+folder+' assembly';temp.isOriginFolderLightBulbOn=False
   for o in root.occurrences:o.isLightBulbOn=o==work
   bodies=[]
   for path,source,shape in walk(comp):
    b=temp.bRepBodies.add(shape);b.name=path.split('/')[-1]+' / '+source.name;b.isLightBulbOn=True
    if source.appearance:b.appearance=source.appearance
    bodies.append(b)
   expected=sum(b.isSolid for b in bodies)
   stage('exporting complete '+folder+' assembly: '+str(expected)+' solids')
   native=out+folder+'/'+filename+'.f3d';step=out+folder+'/'+filename+'.step'
   current=False
   if folder=='main' and os.path.exists(step) and os.path.exists(native):
    data=open(step).read();current=data.count('MANIFOLD_SOLID_BREP(')+data.count('BREP_WITH_VOIDS(')==expected
   if not current:
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(native,temp))
    assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(step,temp))
   with zipfile.ZipFile(native) as z:assert z.testzip() is None
   with open(step) as f:data=f.read()
   solids=data.count('MANIFOLD_SOLID_BREP(');voids=data.count('BREP_WITH_VOIDS(')
   assert solids+voids==expected,(folder,solids,voids,expected)
   records.append({'file':folder+'/'+filename,'STEP_solids':solids,'STEP_BREP_WITH_VOIDS':voids,'native_bodies':len(bodies),'native_solids':expected,'complete':True,'hierarchy':'flattened named bodies in assembly coordinates; editable source hierarchy retained in current Fusion document'})
   work.deleteMe();work=None
 finally:
  if work:work.deleteMe()
  for o,v in visibility:o.isLightBulbOn=v
 assert app.activeDocument.save('SIGMIDI icon: complete assembly exports independent of hidden source component folders')
 with open(out+'emboss-complete-cad.json','w') as f:json.dump({'CAD':records,'document':app.activeDocument.name,'saved':app.activeDocument.isSaved,'geometry_unchanged_during_export':True,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()},f,indent=2)
 stage('complete')
