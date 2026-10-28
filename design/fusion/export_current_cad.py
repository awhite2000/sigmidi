"""Export main only, with independent visible copies instead of hidden instances."""
import adsk.core,adsk.fusion,json,os

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 mgr=adsk.fusion.TemporaryBRepManager.get();out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 originals=[o for o in root.occurrences if not o.component.name.startswith(('ALT ','TEMP ','Temporary '))]
 vis=[(o,o.isLightBulbOn) for o in root.occurrences]
 work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());comp=work.component;comp.name='MIDI Foot Controller - main enclosure';work.isLightBulbOn=False
 def stage(s):
  with open('/tmp/current-cad-progress.json','w') as f:json.dump({'stage':s},f)
 stage('copying independent main components')
 count=0;physical=0
 for o in originals:
  child=comp.occurrences.addNewComponent(adsk.core.Matrix3D.create());child.component.name=o.component.name
  show=not o.component.name.startswith(('LED','REF'))
  for b in o.component.bRepBodies:
   a=mgr.copy(b);mgr.transform(a,o.transform2)
   n=child.component.bRepBodies.add(a);n.name=b.name;n.appearance=b.appearance;n.isLightBulbOn=True;count+=1
   if show:physical+=1
  child.component.isOriginFolderLightBulbOn=False;child.isLightBulbOn=show
 comp.isOriginFolderLightBulbOn=False
 for a in root.attributes:
  if a.groupName in ('MIDI_FDM','MIDI_POWER'):comp.attributes.add(a.groupName,a.name,a.value)
 for o,_ in vis:o.isLightBulbOn=False
 work.isLightBulbOn=True
 adsk.doEvents()
 stage('exporting main F3D')
 if not d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(out+'midi-foot-chassis.f3d',comp)):raise RuntimeError('Main F3D failed')
 stage('exporting main STEP')
 if not d.exportManager.execute(d.exportManager.createSTEPExportOptions(out+'midi-foot-chassis.step',comp)):raise RuntimeError('Main STEP failed')
 with open(out+'midi-foot-chassis.step') as f:step=f.read()
 solids=step.count('MANIFOLD_SOLID_BREP(')
 if solids<4:raise RuntimeError('STEP does not contain the printed solids: '+str(solids))
 work.deleteMe()
 for o,v in vis:o.isLightBulbOn=v
 report={'main_components':len(originals),'copied_bodies':count,'visible_physical_bodies':physical,'STEP_manifold_solids':solids,'main_only':True,'independent_copies':True,'revision':'display_m2x5' if root.attributes.itemByName('MIDI_FDM','display_m2x5') else 'snug_06_tolerances' if root.attributes.itemByName('MIDI_FDM','snug_06_tolerances') else 'refined_positioning_ribs' if root.attributes.itemByName('MIDI_FDM','refined_positioning_ribs') else 'enclosure_wall_reinforcement' if root.attributes.itemByName('MIDI_FDM','enclosure_wall_reinforcement') else 'upper_corner_walls' if root.attributes.itemByName('MIDI_FDM','upper_corner_walls') else 'wide_pololu_clips' if root.attributes.itemByName('MIDI_FDM','wide_pololu_clips') else 'base_corner_repair' if root.attributes.itemByName('MIDI_FDM','base_corner_repair') else 'recessed_switch_labels' if root.attributes.itemByName('MIDI_FDM','recessed_switch_labels') else 'extra_right_base_screws' if root.attributes.itemByName('MIDI_FDM','extra_right_base_screws') else 'rear_vent_membranes' if root.attributes.itemByName('MIDI_FDM','rear_vent_membranes') else 'straight_rear_rib' if root.attributes.itemByName('MIDI_POWER','straight_rear_rib') else 'full_height_rear_rib' if root.attributes.itemByName('MIDI_POWER','full_height_rear_rib') else 'reinforced_floor_grilles' if root.attributes.itemByName('MIDI_POWER','reinforced_floor_grilles') else 'rear_column_rib' if root.attributes.itemByName('MIDI_POWER','rear_column_rib') else 'raised_rear_grilles' if root.attributes.itemByName('MIDI_POWER','raised_rear_grilles') else 'expanded_cooling_grilles' if root.attributes.itemByName('MIDI_POWER','expanded_grilles') else 'ventilated_petg_clip' if root.attributes.itemByName('MIDI_POWER','ventilated_clip') else ('aux_dc_power' if root.attributes.itemByName('MIDI_POWER','dc_input') else 'straight_base_glue_lips')}
 with open(out+'cad-export.json','w') as f:json.dump(report,f,indent=2)
 stage('copying independent modular components and hardware')
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 def clone(src,parent,matrix,name=None):
  occ=parent.occurrences.addNewComponent(matrix);dst=occ.component;dst.name=name or src.name;dst.isOriginFolderLightBulbOn=False;occ.isLightBulbOn=False
  for body in src.bRepBodies:
   n=dst.bRepBodies.add(mgr.copy(body));n.name=body.name;n.appearance=body.appearance;n.isLightBulbOn=True
  for child in src.occurrences:
   o=clone(child.component,dst,child.transform2);o.isLightBulbOn=not child.component.name.startswith('REF')
  for attr in src.attributes:dst.attributes.add(attr.groupName,attr.name,attr.value)
  return occ
 modwork=clone(alt,root,adsk.core.Matrix3D.create(),'TEMP independent modular CAD export')
 try:
  modwork.isLightBulbOn=True
  stage('exporting independent modular F3D/STEP')
  assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(out+'modular/midi-foot-modular.f3d',modwork.component))
  assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(out+'modular/midi-foot-modular.step',modwork.component))
  with open(out+'modular/midi-foot-modular.step') as f:mod_step=f.read()
  report['modular_STEP_manifold_solids']=mod_step.count('MANIFOLD_SOLID_BREP(')
  report['modular_independent_component_copies']=True
  assert report['modular_STEP_manifold_solids']>200,'Incomplete modular STEP'
 finally:modwork.deleteMe()
 stage('exporting label-specific modular shell CAD sources')
 library=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Engraved pair'))
 variant_files=[]
 for o in library.occurrences:
  name=o.component.name;part=clone(o.component,root,adsk.core.Matrix3D.create(),'TEMP '+name)
  try:
   part.isLightBulbOn=True
   assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(out+'modular/'+name+'.f3d',part.component))
   assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(out+'modular/'+name+'.step',part.component))
   with open(out+'modular/'+name+'.step') as f:assert f.read().count('MANIFOLD_SOLID_BREP(')==1
   variant_files.append(name)
  finally:part.deleteMe()
 report['engraved_modular_variant_CAD']=variant_files
 with open(out+'cad-export.json','w') as f:json.dump(report,f,indent=2)
 stage('complete')
