"""Compare installed main and modular right parts without editing the model."""
import adsk.core,adsk.fusion,json

def run(_context: str):
 app=adsk.core.Application.get();root=adsk.fusion.Design.cast(app.activeProduct).rootComponent
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 electronics=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'))
 def find(prefix):return next(c for c in main if c.name.startswith(prefix))
 def body(c,label):return next(b for b in c.bRepBodies if label in b.name)
 pairs=[('upper shell',body(find('01 '),'RIGHT'),body(electronics,'SHELL')),('base',body(find('02 '),'RIGHT'),body(electronics,'BASE'))]
 pair=next(o.component for o in alt.occurrences if o.component.name.startswith('Repeatable pair'));left=next(o.component for o in alt.occurrences if o.component.name.startswith('Leftmost pair'))
 pairs.append(('universal pair base',body(pair,'BASE'),body(left,'BASE')))
 rows=[]
 for name,a,b in pairs:
  difference=[]
  for x,y in [(a,b),(b,a)]:
   v=mgr.copy(x)
   if not mgr.booleanOperation(v,mgr.copy(y),bt.DifferenceBooleanType):raise RuntimeError('Comparison failed')
   difference.append(v.volume*1000 if v.faces.count else 0)
  rows.append({'part':name,'main_volume_mm3':a.volume*1000,'modular_volume_mm3':b.volume*1000,'main_solid':a.isSolid,'main_lumps':a.lumps.count,'modular_solid':b.isSolid,'modular_lumps':b.lumps.count,'bidirectional_difference_mm3':difference})
  assert a.isSolid and b.isSolid and a.lumps.count==b.lumps.count==1 and max(difference)<.001
 # Confirm the retained modular rib profile clears both matching upper variants.
 pair_paths=[]
 for dz in [0,-.01,-.25,-.5,-1,-2,-3,-5,-10,-20]:
  moving=mgr.copy(body(pair,'BASE'));matrix=adsk.core.Matrix3D.create();matrix.translation=adsk.core.Vector3D.create(0,0,dz/10);mgr.transform(moving,matrix)
  for c in [pair,left]:
   a=mgr.copy(moving);assert mgr.booleanOperation(a,mgr.copy(body(c,'SHELL')),bt.IntersectionBooleanType)
   amount=a.volume*1000 if a.faces.count else 0
   if amount>.001:pair_paths.append([dz,c.name,amount])
 assert not pair_paths,pair_paths
 locator_clear=[];minimum=1e9
 with open('/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/ventilated-clip.json') as f:cooling=json.load(f)
 for v in cooling['lateral_locator_boxes_mm']:
  x0,y0,z0,x1,y1,z1=v
  qmin=[x0/10,-y1/10,z0/10];qmax=[x1/10,-y0/10,z1/10]
  for c in main:
   if c.name.startswith(('02 ','Pololu','REF')):continue
   for b in c.bRepBodies:
    q=b.boundingBox
    lower=sum(max(qmin[i]-getattr(q.maxPoint,k),getattr(q.minPoint,k)-qmax[i],0)**2 for i,k in enumerate('xyz'))**.5*10
    if lower<3:
     center=adsk.core.Point3D.create(*[(a+b)/2 for a,b in zip(qmin,qmax)])
     expanded=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(center,adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),qmax[0]-qmin[0]+.6,qmax[1]-qmin[1]+.6,qmax[2]-qmin[2]+.6))
     a=mgr.copy(b)
     assert mgr.booleanOperation(a,expanded,bt.IntersectionBooleanType)
     if not a.faces.count or a.volume*1000<1e-7:lower=3.
     else:locator_clear.append([c.name,b.name,lower])
    minimum=min(minimum,lower)
 assert not locator_clear,locator_clear
 report={'locator_minimum_other_component_clearance_lower_bound_mm':minimum,'locator_clearances_below_3mm':locator_clear,'revision':'display_m2x5' if root.attributes.itemByName('MIDI_FDM','display_m2x5') else 'snug_06_tolerances' if root.attributes.itemByName('MIDI_FDM','snug_06_tolerances') else 'refined_positioning_ribs' if root.attributes.itemByName('MIDI_FDM','refined_positioning_ribs') else 'enclosure_wall_reinforcement' if root.attributes.itemByName('MIDI_FDM','enclosure_wall_reinforcement') else 'upper_corner_walls' if root.attributes.itemByName('MIDI_FDM','upper_corner_walls') else 'wide_pololu_clips' if root.attributes.itemByName('MIDI_FDM','wide_pololu_clips') else 'base_corner_repair' if root.attributes.itemByName('MIDI_FDM','base_corner_repair') else 'recessed_switch_labels' if root.attributes.itemByName('MIDI_FDM','recessed_switch_labels') else 'extra_right_base_screws' if root.attributes.itemByName('MIDI_FDM','extra_right_base_screws') else 'rear_vent_membranes' if root.attributes.itemByName('MIDI_FDM','rear_vent_membranes') else 'straight_rear_rib' if root.attributes.itemByName('MIDI_POWER','straight_rear_rib') else 'full_height_rear_rib' if root.attributes.itemByName('MIDI_POWER','full_height_rear_rib') else 'reinforced_floor_grilles' if root.attributes.itemByName('MIDI_POWER','reinforced_floor_grilles') else 'rear_column_rib' if root.attributes.itemByName('MIDI_POWER','rear_column_rib') else 'raised_rear_grilles' if root.attributes.itemByName('MIDI_POWER','raised_rear_grilles') else 'expanded_cooling_grilles' if root.attributes.itemByName('MIDI_POWER','expanded_grilles') else 'ventilated_petg_clip' if root.attributes.itemByName('MIDI_POWER','ventilated_clip') else 'aux_dc_power','main_and_modular_electronics_print_parts_identical':True,'universal_pair_bases_identical':True,'pair_base_removal_collisions':pair_paths,'parts':rows,'document':app.activeDocument.name}
 with open('/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/power-geometry-verification.json','w') as f:json.dump(report,f,indent=2)
