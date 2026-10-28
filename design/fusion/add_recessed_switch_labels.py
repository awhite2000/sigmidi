"""Engrave stable A-E / 1-5 LED-adjacent labels; retain all hardware and seams."""
import adsk.core,adsk.fusion,json,math,os

def run(_context):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/'
 assert root.attributes.itemByName('MIDI_FDM','extra_right_base_screws')
 assert not root.attributes.itemByName('MIDI_FDM','recessed_switch_labels'),'Labels already installed'
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 main=[o.component for o in root.occurrences if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 uc=next(c for c in main if c.name.startswith('01 '))
 alt=next(o.component for o in root.occurrences if o.component.name.startswith('ALT Chainable'))
 pair=next(o.component for o in alt.occurrences if o.component.name.startswith('Repeatable pair'))
 left=next(o.component for o in alt.occurrences if o.component.name.startswith('Leftmost pair'))
 right=next(o.component for o in alt.occurrences if o.component.name.startswith('Existing RIGHT'))
 def get(c,s):return next(b for b in c.bRepBodies if s in b.name)
 sl,sr=get(uc,'LEFT'),get(uc,'RIGHT');ps,ls=get(pair,'SHELL'),get(left,'SHELL');ars=get(right,'SHELL')
 def stage(s):
  with open('/tmp/recessed-labels-progress.json','w') as f:json.dump({'stage':s},f)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def op(a,b,k):
  assert mgr.booleanOperation(a,b,k),'Boolean failed';return a
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def hit(a,b):
  q,r=a.boundingBox,b.boundingBox
  if any(min(getattr(q.maxPoint,k),getattr(r.maxPoint,k))-max(getattr(q.minPoint,k),getattr(r.minPoint,k))<1e-8 for k in 'xyz'):return 0
  a=op(mgr.copy(a),mgr.copy(b),bt.IntersectionBooleanType);return a.volume*1000 if a.faces.count else 0
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def shift(a,dx=0,dy=0,dz=0):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,-dy/10,dz/10);assert mgr.transform(a,m);return a
 def bounds(a):
  q=a.boundingBox;return [[q.minPoint.x*10,-q.maxPoint.y*10,q.minPoint.z*10],[q.maxPoint.x*10,-q.minPoint.y*10,q.maxPoint.z*10]]
 def signatures():
  return [(c.name,[(b.name,b.volume,list(b.boundingBox.minPoint.asArray()),list(b.boundingBox.maxPoint.asArray())) for b in c.bRepBodies]) for c in main if c!=uc]
 before=signatures();work=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=work.component;tc.name='TEMP switch label tools'
 cache={};glyphs=[];placements=[];checks=[]
 try:
  stage('creating measured Arial bold letter and numeral tools')
  for ch in 'ABCDE12345':
   sk=tc.sketches.add(tc.xYConstructionPlane)
   ti=sk.sketchTexts.createInput3("'"+ch+"'",adsk.core.ValueInput.createByReal(.8))
   ti.fontName='Arial';ti.textStyle=adsk.fusion.TextStyles.TextStyleBold
   assert ti.setAsMultiLine(adsk.core.Point3D.create(0,0,0),adsk.core.Point3D.create(2,2,0),adsk.core.HorizontalAlignments.LeftHorizontalAlignment,adsk.core.VerticalAlignments.BottomVerticalAlignment,0)
   text=sk.sketchTexts.add(ti);text.explode()
   profile=max(list(sk.profiles),key=lambda a:a.areaProperties().area)
   loops=profile.profileLoops.count
   tc.features.extrudeFeatures.addSimple(profile,adsk.core.ValueInput.createByReal(.08),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
   native=tc.bRepBodies.item(tc.bRepBodies.count-1);a=mgr.copy(native);q=a.boundingBox
   scale=.8/(q.maxPoint.y-q.minPoint.y);m=adsk.core.Matrix3D.create();m.setCell(0,0,scale);m.setCell(1,1,scale)
   assert mgr.transform(a,m);q=a.boundingBox
   # Each cached tool has its actual left at X0, centerline at Y0 and Z0..0.8.
   shift(a,dx=-q.minPoint.x*10,dy=(q.minPoint.y+q.maxPoint.y)*5,dz=-q.minPoint.z*10)
   bb=bounds(a);assert abs(bb[1][1]-bb[0][1]-8)<1e-5
   glyphs.append({'label':ch,'font_family':'Arial','bold':True,'outline_height_mm':bb[1][1]-bb[0][1],'outline_width_mm':bb[1][0]-bb[0][0],'profile_loops':loops})
   cache[ch]=a;native.deleteMe();sk.deleteMe()
  specs=[(ch,47.4+65*i,26.2,30) for i,ch in enumerate('EDCBA')]+[(ch,14.9+65*i,81.7,0) for i,ch in enumerate('54321')]
  def engrave(source,items,name):
   body=mgr.copy(source);removal=0;rows=[]
   for ch,x,y,z in items:
    tool=shift(mgr.copy(cache[ch]),dx=x+6,dy=y,dz=z-.8);bb=bounds(tool)
    # Exact bottom of each pocket; only remove the outer 0.8mm of the roof.
    intended=vol(tool);actual=hit(source,tool)
    assert abs(intended-actual)<.001,(name,ch,'not wholly in flat roof',intended,actual,bb)
    # The corresponding 2.2mm wall below must be intact, not a hole/counterbore.
    backing=mgr.copy(tool);m=adsk.core.Matrix3D.create();m.setCell(2,2,2.2/.8);assert mgr.transform(backing,m)
    q=backing.boundingBox;shift(backing,dz=z-3-q.minPoint.z*10)
    assert abs(vol(backing)-hit(source,backing))<.001,(name,ch,'insufficient backing')
    body=cut(body,tool);removal+=actual
    row={'part':name,'label':ch,'LED_center_XY_mm':[x,y],'glyph_left_X_mm':x+6,'glyph_bounds_layout_mm':bb,'roof_Z_mm':z,'pocket_bottom_Z_mm':z-.8,'removed_volume_mm3':actual,'minimum_remaining_roof_mm':2.2,'flange_clearance_X_mm':3.0}
    rows.append(row);placements.append(row)
   assert body.isSolid and body.lumps.count==1,name
   assert abs(vol(source)-vol(body)-removal)<.001,(name,'unexpected material removal')
   assert vol(cut(mgr.copy(body),mgr.copy(source)))<.001,(name,'material added')
   checks.append({'part':name,'solid':True,'lumps':1,'removed_volume_mm3':removal,'labels':[r['label'] for r in rows]})
   return body
  stage('checking all pockets and 2.2mm roof backing on temporary shell copies')
  litems=[a for a in specs if a[1]<194];ritems=[a for a in specs if a[1]>194]
  aleft=engrave(sl,litems,'main left');aright=engrave(sr,ritems,'main/right electronics')
  def pair_items(upper,lower):return [(upper,177.4,26.2,30),(lower,144.9,81.7,0)]
  apair=engrave(ps,pair_items('C','3'),'pair-shell C3')
  acap=engrave(ls,pair_items('D','4'),'pair-shell-at-cap D4')
  variants=[('pair-shell-D',engrave(ps,pair_items('D','4'),'pair-shell D4')),
            ('pair-shell-at-cap-C',engrave(ls,pair_items('C','3'),'pair-shell-at-cap C3')),
            ('pair-shell-at-cap-E',engrave(ls,pair_items('E','5'),'pair-shell-at-cap E5'))]
  # Slots and seam features are far from the glyphs; verify protected seam volumes.
  for name,old,new in [('left',sl,aleft),('right',sr,aright),('pair',ps,apair),('cap pair',ls,acap)]:
   removed=cut(mgr.copy(old),mgr.copy(new))
   if name=='left':seams=[(191.65,200.1)]
   elif name=='right':seams=[(193.89,200.1)]
   else:seams=[(124.64,130.91),(191.65,200.1)]
   for x0,x1 in seams:assert hit(removed,box(x0,-1,-25,x1,93,31))<.001,(name,'joint affected')
  assert signatures()==before,'Unrelated controls or floors changed'
  stage('committing upper shells and label-specific modular print variants')
  for comp,old,shape in [(uc,sl,aleft),(uc,sr,aright),(pair,ps,apair),(left,ls,acap),(right,ars,aright)]:
   appearance=old.appearance;name=old.name;old.deleteMe();b=comp.bRepBodies.add(shape);b.name=name+' - Arial bold 8mm inset 0.8mm';b.appearance=appearance
  library=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());library.component.name='ALT Engraved pair print variants - NOT assembly';library.isLightBulbOn=False
  library.component.isOriginFolderLightBulbOn=False
  variant_rows=[]
  for i,(name,shape) in enumerate(variants):
   occ=library.component.occurrences.addNewComponent(adsk.core.Matrix3D.create());occ.component.name=name
   b=occ.component.bRepBodies.add(shape);b.name=name+' - upper shell only - select for switch count';b.appearance=get(pair,'SHELL').appearance
   variant_rows.append({'file':name,'component':occ.component.name,'solid':b.isSolid,'lumps':b.lumps.count})
  assert signatures()==before
  report={'revision':'recessed_switch_labels','font_family':'Arial','text_style':'Bold','actual_outline_height_mm':8,'inset_depth_mm':.8,'minimum_remaining_top_mm':2.2,'label_side':'right of LED; left glyph edge 6mm right of LED center','minimum_LED_flange_clearance_X_mm':3,'main_labels_upper_left_to_right':list('EDCBA'),'main_labels_lower_left_to_right':list('54321'),'glyphs':glyphs,'placements':placements,'parts':checks,'additional_modular_variants':variant_rows,'all_changed_shells_single_connected_solids':True,'all_glyphs_wholly_in_flat_roof':True,'all_pockets_backed_by_2_2mm_roof':True,'main_and_modular_right_identical':True,'seam_and_joint_material_removed_mm3':0,'all_other_components_and_base_parts_unchanged':True,'component_positions_unchanged':True,'backup':'archive/pre-recessed-switch-labels.zip','limits':'Nominal CAD roof thickness and slicing do not establish printed load strength; the recessed text follows the existing printing orientations.'}
  with open(out+'recessed-switch-labels.json','w') as f:json.dump(report,f,indent=2)
  configpath=out+'modular/modular-design.json'
  with open(configpath) as f:mod=json.load(f)
  mod.update({'switch_labels':'Upper A-E, lower 1-5, starting from the right','engraving':'../recessed-switch-labels.json','pair_shell_labels':'C/3','cap_pair_labels_shown':'D/4','additional_upper_shell_variants':[r['file'] for r in variant_rows], 'upper_shell_selection':{'6':['pair-shell-at-cap-C'],'8':['pair-shell','pair-shell-at-cap'],'10':['pair-shell','pair-shell-D','pair-shell-at-cap-E']}})
  with open(configpath,'w') as f:json.dump(mod,f,indent=2)
  root.attributes.add('MIDI_FDM','recessed_switch_labels',json.dumps(report));alt.attributes.add('MIDI_MODULAR','configuration',json.dumps(mod))
  work.deleteMe()
  if not app.activeDocument.save('Recessed Arial Bold switch labels A-E and 1-5, actual 8mm outlines, 0.8mm deep beside LEDs; separate modular label variants.'):raise RuntimeError('Save failed')
  stage('complete')
 finally:
  if work.isValid:work.deleteMe()
