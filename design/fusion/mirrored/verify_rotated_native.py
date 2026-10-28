"""Check the rotated variants and all preserved original geometry after their exports."""
import adsk.core,adsk.fusion,json,math,datetime,os,hashlib


REUSE_PASSED_SOURCE_CHECK = False

def run(_context):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/mirrored/'
 report=json.loads(root.attributes.itemByName('MIDI_MIRROR','logical_left_electronics').value)
 main=next(o.component for o in root.occurrences if o.component.name==report['new_main_component']);mod=next(o.component for o in root.occurrences if o.component.name==report['new_modular_component']);lib=next(o.component for o in root.occurrences if o.component.name==report['new_library_component'])
 def stage(s):
  with open('/tmp/logical-mirror-final-progress.json','w') as f:json.dump({'stage':s},f)
 def bounds(b):
  q=b.boundingBox;return [q.minPoint.x*10,q.minPoint.y*10,q.minPoint.z*10,q.maxPoint.x*10,q.maxPoint.y*10,q.maxPoint.z*10]
 def check_source(row,occ):
  assert row['component']==occ.component.name and row['occurrence']==occ.name
  assert max(abs(a-b) for a,b in zip(row['transform'],occ.transform2.asArray()))<1e-9
  bodies=list(occ.component.bRepBodies);assert len(bodies)==len(row['bodies'])
  for saved,b in zip(row['bodies'],bodies):
   assert saved['name']==b.name and saved['faces']==b.faces.count
   assert abs(saved['volume_cm3']-b.volume)<1e-8
   assert max(abs(a-b) for a,b in zip(saved['bounds_mm'],bounds(b)))<1e-6
  children=list(occ.component.occurrences);assert len(children)==len(row['children'])
  for saved,child in zip(row['children'],children):check_source(saved,child)
 stage('checking preservation of every original native body and occurrence')
 with open(out+'original-native-signatures.json') as f:originals=json.load(f)
 cached=None
 if os.path.exists(out+'native-source-preservation.json'):
  with open(out+'native-source-preservation.json') as f:cached=json.load(f)
 if REUSE_PASSED_SOURCE_CHECK and cached and cached['original_preservation_check_passed'] and cached['baseline_sha256']==hashlib.sha256(open(out+'original-native-signatures.json','rb').read()).hexdigest():
  for saved in originals:
   occ=next(o for o in root.occurrences if o.component.name==saved['component']);assert max(abs(a-b) for a,b in zip(saved['transform'],occ.transform2.asArray()))<1e-9
 else:
  for saved in originals:check_source(saved,next(o for o in root.occurrences if o.component.name==saved['component']))
 def box(lo,hi):
  return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((lo[0]+hi[0])/20,(lo[1]+hi[1])/20,(lo[2]+hi[2])/20),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(hi[0]-lo[0])/10,(hi[1]-lo[1])/10,(hi[2]-lo[2])/10))
 uc=next(o.component for o in main.occurrences if o.component.name.startswith('Mirrored 01 '))
 shells=list(uc.bRepBodies)
 pair=next(o.component for o in mod.occurrences if o.component.name.startswith('Repeatable pair'));last=next(o.component for o in mod.occurrences if o.component.name.startswith('Rightmost pair'))
 pair_shell=next(b for b in pair.bRepBodies if 'SHELL' in b.name);last_shell=next(b for b in last.bRepBodies if 'SHELL' in b.name)
 variants={o.component.name.split(' (')[0]:o.component.bRepBodies.item(0) for o in lib.occurrences}
 mapping={'pair-shell C3':pair_shell,'pair-shell-at-cap D4':last_shell,'pair-shell D4':variants['pair-shell-D'],'pair-shell-at-cap C3':variants['pair-shell-at-right-cap-C'],'pair-shell-at-cap E5':variants['pair-shell-at-right-cap-E']}
 backing=[]
 stage('verifying solid 2.2mm backing beneath each readable label')
 for row in report['readable_labels']:
  q=row['bounds_mm'];roof=q[5]
  source=next(b for b in shells if b.boundingBox.minPoint.x*10-.001<row['LED_XY_mm'][0]<b.boundingBox.maxPoint.x*10+.001) if row['part'].startswith('main') else mapping[row['part']]
  probe=box([q[0]+.00001,q[1]+.00001,roof-3+.00001],[q[3]-.00001,q[4]-.00001,roof-.8-.00001])
  expected=probe.volume*1000;assert mgr.booleanOperation(probe,mgr.copy(source),bt.DifferenceBooleanType)
  missing=probe.volume*1000 if probe.faces.count else 0
  assert missing<.003,(row['part'],row['label'],missing)
  backing.append({'part':row['part'],'label':row['label'],'solid_backing_mm':2.2,'probe_volume_mm3':expected,'missing_mm3':missing})
 cad=[]
 for folder,name in [('main','midi-foot-mirrored-main'),('modular','midi-foot-mirrored-modular'),('modular','pair-shell-D'),('modular','pair-shell-at-right-cap-C'),('modular','pair-shell-at-right-cap-E')]:
  with open(out+folder+'/'+name+'.step') as f:solids=f.read().count('MANIFOLD_SOLID_BREP(')
  assert solids>200 if name.startswith('midi-') else solids==1
  cad.append({'file':folder+'/'+name,'STEP_solids':solids})
 rotation=json.loads(root.attributes.itemByName('MIDI_MIRROR','display_180_ribbon_left').value)
 assert rotation['ribbon_side']=='left' and not rotation['physical_collisions']
 lcd=next(o.component for o in main.occurrences if o.component.name.startswith('Mirrored LCD '))
 encoder=next(o.component for o in main.occurrences if o.component.name.startswith('Mirrored Encoder'))
 fpc=next(b for b in lcd.bRepBodies if 'PCBA:1 Body2' in b.name)
 pcb=next(b for b in lcd.bRepBodies if 'PCBA:1 Body1' in b.name)
 glass=next(b for b in lcd.bRepBodies if '240X280-LCD' in b.name)
 assert bounds(fpc)[3]<42.59781
 assert abs(bounds(glass)[5])<1e-6
 encoder_right=max(bounds(b)[3] for b in encoder.bRepBodies)
 rotation['PCB_to_encoder_lateral_clearance_mm']=bounds(pcb)[0]-encoder_right
 rotation['FPC_to_encoder_lateral_clearance_mm']=bounds(fpc)[0]-encoder_right
 assert rotation['PCB_to_encoder_lateral_clearance_mm']>=3

 report['display_rotation']=rotation
 for row in report['placements']:
  if row['component'].startswith('LCD '):
   row['strategy']='rigid translation followed by 180deg about PCB mounting centre';row['ribbon_side']='left'
 report['LCD_window_glass_shift_X_mm_from_initial_mirrored_variant']=-.5
 root.attributes.add('MIDI_MIRROR','logical_left_electronics',json.dumps(report))
 for comp in [main,mod]:comp.attributes.add('MIDI_MIRROR','logical_left_electronics',json.dumps(report))
 assert not [o for o in root.occurrences if o.component.name.startswith('TEMP')]
 assert app.activeDocument.save('Verified independent mirrored alternatives, readable labels with solid backing and visible complete CAD exports; original assemblies preserved')
 result={'document':app.activeDocument.name,'saved':app.activeDocument.isSaved,'original_assemblies_and_library_preserved':True,'original_top_level_components_verified':len(originals),'readable_label_backing_checks':backing,'CAD':cad,'temporary_components':[],'display_rotation':rotation,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 with open(out+'final-native-verification.json','w') as f:json.dump(result,f,indent=2)
 with open(out+'export-verification.json','w') as f:json.dump({'document':app.activeDocument.name,'saved':app.activeDocument.isSaved,'parts':13,'renders':len(json.load(open(out+'render-manifest.json'))['images']),'CAD':cad,'temporary_components':[]},f,indent=2)
 stage('complete');print(json.dumps({'preserved':len(originals),'labels_checked':len(backing),'CAD':cad,'saved':True}))
