"""Install the verified Nano kit in all four native assemblies; retain base solids."""
import adsk.core,adsk.fusion,json
from pathlib import Path
OUT=Path('/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/nano-esp32')

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
 spec=json.loads((OUT/'mount-fit.json').read_text())
 check=json.loads((OUT/'assembly-clearance.json').read_text());assert check['all_variants_collision_free']
 assert not r.attributes.itemByName('SIGMIDI','nano_esp32_mounts'),'Kit already installed'
 kit_occ=next(o for o in r.occurrences if o.component.name=='ALT Arduino Nano ESP32 mount kit - original base unchanged');kit=kit_occ.component
 main=next(o.component for o in r.occurrences if o.component.name.startswith('ALT Mirrored MAIN'))
 lm=next(o.component for o in r.occurrences if o.component.name.startswith('ALT Mirrored MODULAR'))
 leftmod=next(o.component for o in lm.occurrences if o.component.name.startswith('Existing LEFT'))
 rm=next(o.component for o in r.occurrences if o.component.name.startswith('ALT Chainable'))
 rightmod=next(o.component for o in rm.occurrences if o.component.name.startswith('Existing RIGHT'))
 # Track the enclosure bodies themselves, independent of visual hardware changes.
 preserved={b.entityToken:b.revisionId for o in r.allOccurrences for b in o.component.bRepBodies if any(t in o.component.name for t in ('Chassis','Removable base','Existing LEFT','Existing RIGHT','Repeatable pair','Leftmost pair','Closed left cap'))}
 colors={'usb':'Opaque(255,207,128)','bridge':'Modular left cap teal','pcb':'Opaque(0,85,0)','metal':'Steel - Satin','chip':'Opaque(51,51,51)'}
 for o in kit.occurrences:
  for b in o.component.bRepBodies:
   col='usb' if 'glue insert' in o.component.name else 'bridge' if 'opposite-end' in o.component.name else 'pcb' if b.name.startswith('Nano ESP32 PCB') else 'metal' if any(t in b.name for t in ('CX90B','USB','SHIELD')) else 'chip'
   b.appearance=d.appearances.itemByName(colors[col])
 # Model screw envelopes. Threads are represented by nominal cylinders.
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 hw=kit.occurrences.addNewComponent(adsk.core.Matrix3D.create());hw.component.name='Nano mounting screws - four M1.6x5 and two M1.6x6 - reference'
 def screw(x,y,z,length,label):
  def cyl(z0,z1,rad):return mgr.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),rad/10,adsk.core.Point3D.create(x/10,y/10,z1/10),rad/10)
  a=cyl(z-length,z,.8);assert mgr.booleanOperation(a,cyl(z,z+1.2,1.5),bt.UnionBooleanType)
  b=hw.component.bRepBodies.add(a);b.name=label;b.appearance=d.appearances.itemByName(colors['metal'])
 for i,(x,y) in enumerate(spec['board_holes_XY_mm']):screw(x,y,spec['board_component_face_Z_mm']+spec['board_dimensions_mm'][2],5,'Nano PCB M1.6x5 '+str(i+1))
 for i,(x,y) in enumerate(spec['existing_post_centers_XY_mm']):screw(x,y,-10.9,6,'Nano bridge M1.6x6 '+str(i+1))
 cx=sum(x for x,y in spec['board_holes_XY_mm'][:2])/2;dx=350-2*cx
 installed=[]
 for label,c,shift in [('Left main',main,0),('Left modular',leftmod,0),('Right main',r,dx),('Right modular',rightmod,dx)]:
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(shift/10,0,0)
  occ=c.occurrences.addExistingComponent(kit,m);occ.attributes.add('SIGMIDI','nano_variant',label);occ.isLightBulbOn=True
  for old in c.occurrences:
   if 'DFRobot' in old.component.name:old.isLightBulbOn=False
   if 'PCB screws' in old.component.name:
    for b in old.component.bRepBodies:
     if b.name.startswith('DFR1075 M1.6'):b.isLightBulbOn=False
  installed.append({'variant':label,'translation_X_mm':shift,'existing_board_hidden':True})
 # The raw STEP import is superseded by the fitted, bore-corrected reference.
 source=next(o for o in r.occurrences if o.component.name=='REF Arduino Nano ESP32 manufacturer STEP');source.deleteMe()
 kit_occ.isLightBulbOn=False
 unchanged=all(b.revisionId==preserved[b.entityToken] for o in r.allOccurrences for b in o.component.bRepBodies if b.entityToken in preserved)
 assert unchanged,'An original enclosure body changed'
 data={'board':'Arduino Nano ESP32 ABX00083','instances':installed,'original_enclosure_body_revisions_unchanged':unchanged,'enclosure_geometry_modified':False,'existing_USB_cutout_modified':False,'component_face_down':True,'headers_fitted':False,'fit_check':'assembly-clearance.json','firmware_migration':'Separate electrical and firmware migration required; current C6 firmware cannot run on Nano ESP32'}
 r.attributes.add('SIGMIDI','nano_esp32_mounts',json.dumps(data))
 with open(OUT/'installation.json','w') as f:json.dump(data,f,indent=2)
 kit_occ.isLightBulbOn=True
 assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(OUT/'nano-esp32-mount-kit.f3d'),kit))
 kit_occ.isLightBulbOn=False
 # Export STEP through the visible staging bodies in render_mounts.py.
 assert app.activeDocument.save('Arduino Nano ESP32 mount inserts; existing enclosure base geometry preserved')
