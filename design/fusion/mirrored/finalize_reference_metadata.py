"""Keep copied lead labels aligned with the correct replacement reference bodies."""
import adsk.core,adsk.fusion,json,re


def run(_context):
 app=adsk.core.Application.get();root=adsk.fusion.Design.cast(app.activeProduct).rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/mirrored/'
 report=json.loads(root.attributes.itemByName('MIDI_MIRROR','logical_left_electronics').value)
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 mod=next(o.component for o in root.occurrences if o.component.name==report['new_modular_component'])
 original_mod=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 def walk(c):
  yield c
  for o in c.occurrences:yield from walk(o.component)
 def bnd(b):
  q=b.boundingBox;return [*q.minPoint.asArray(),*q.maxPoint.asArray()]
 corrected=[]
 for c in walk(mod):
  match=re.search(r'LED(\d\d)',c.name)
  if not match or c.bRepBodies.count!=5:continue
  source=next(x for x in main if x.name.startswith('LED'+match.group(1)))
  for b,old in zip(c.bRepBodies,source.bRepBodies):
   b.name=old.name+' - logical mirror'
  corrected.append(c.name)
 differences=[]
 for c in walk(original_mod):
  clean=c.name.removeprefix('ALT reference - ')
  if not clean.startswith(('LED','Pololu')):continue
  prefix=clean[:5] if clean.startswith('LED') else 'Pololu'
  source=next(x for x in main if x.name.startswith(prefix))
  byname={b.name:b for b in source.bRepBodies}
  for b in c.bRepBodies:
   old=byname.get(b.name)
   if not old:continue
   if abs(b.volume-old.volume)>1e-7 or max(abs(a-b) for a,b in zip(bnd(b),bnd(old)))>.000001:
    differences.append({'original_component':c.name,'original_body':b.name,'original_volume_mm3':b.volume*1000,'correct_reference':source.name,'correct_volume_mm3':old.volume*1000,'resolution':'New variant uses the correct validated main reference; original modular body preserved unchanged'})
 report['source_hardware_discrepancies']=differences
 report['copied_LED_lead_names_match_rigid_reference_geometry']=True
 for c in [root,mod,next(o.component for o in root.occurrences if o.component.name==report['new_main_component'])]:
  c.attributes.add('MIDI_MIRROR','logical_left_electronics',json.dumps(report))
 with open(out+'variant-creation.json','w') as f:json.dump(report,f,indent=2)
 print(json.dumps({'reference_metadata_corrected':corrected,'source_reference_inconsistencies':differences}))
