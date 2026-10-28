"""Independent logical left/right alternatives; never edit either original assembly."""
import adsk.core,adsk.fusion,json,math,os,hashlib

COMMIT = True
REUSE_PASSED_PREFLIGHT = False


def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 out='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/mirrored/'
 mgr=adsk.fusion.TemporaryBRepManager.get();bt=adsk.fusion.BooleanTypes
 assert app.activeDocument.name.startswith('MIDI Foot Controller - VERIFIED')
 assert root.attributes.itemByName('MIDI_FDM','display_m2x5')
 assert not root.attributes.itemByName('MIDI_MIRROR','logical_left_electronics'),'Already created'
 source_roots=list(root.occurrences)
 main=[o for o in source_roots if not o.component.name.startswith(('ALT','TEMP','Temporary'))]
 ao=next(o for o in source_roots if o.component.name.startswith('ALT Chainable'));alt=ao.component
 library=next(o.component for o in source_roots if o.component.name.startswith('ALT Engraved pair'))
 created=[]
 def stage(s):
  with open('/tmp/logical-mirror-progress.json','w') as f:json.dump({'stage':s},f)
 def write(n,v):
  with open(out+n,'w') as f:json.dump(v,f,indent=2)
 def p(x,y,z):return adsk.core.Point3D.create(x/10,-y/10,z/10)
 def box(x0,y0,z0,x1,y1,z1):return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(p((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
 def op(a,b,kind):
  assert mgr.booleanOperation(a,b,kind),'BRep Boolean failed';return a
 def cut(a,b):return op(a,b,bt.DifferenceBooleanType)
 def inter(a,b):return op(a,b,bt.IntersectionBooleanType)
 def union(a,b):return op(a,b,bt.UnionBooleanType)
 def vol(a):return a.volume*1000 if a.faces.count else 0
 def bounds(a):
  q=a.boundingBox;return [q.minPoint.x*10,q.minPoint.y*10,q.minPoint.z*10,q.maxPoint.x*10,q.maxPoint.y*10,q.maxPoint.z*10]
 bbox_cache={}
 def cached_bounds(a):
  key=id(a)
  if key not in bbox_cache:bbox_cache[key]=(a,bounds(a))
  return bbox_cache[key][1]
 def hit(a,b):
  q,r=cached_bounds(a),cached_bounds(b)
  if any(min(q[i+3],r[i+3])-max(q[i],r[i])<.000001 for i in range(3)):return 0
  return vol(inter(mgr.copy(a),mgr.copy(b)))
 def move(a,dx=0,dy=0,dz=0):
  m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,-dy/10,dz/10);assert mgr.transform(a,m);return a
 def mirror(a):
  m=adsk.core.Matrix3D.create();m.setCell(0,0,-1);m.setCell(0,3,35);assert mgr.transform(a,m);return a
 def signatures():
  def row(o):
   c=o.component
   return {'component':c.name,'token':c.entityToken,'occurrence':o.name,'transform':list(o.transform2.asArray()),'bodies':[{'name':b.name,'token':b.entityToken,'volume_cm3':b.volume,'bounds_mm':bounds(b),'faces':b.faces.count} for b in c.bRepBodies],'children':[row(q) for q in c.occurrences]}
  return [row(o) for o in source_roots]
 before=signatures()
 previous_signatures=None
 if os.path.exists(out+'original-native-signatures.json'):
  with open(out+'original-native-signatures.json') as f:previous_signatures=json.load(f)
 write('original-native-signatures.json',before)
 stage('preserving full native source assembly')
 backup=out+'../archive/pre-logical-mirror-native.f3d'
 if not os.path.exists(backup):assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(backup))
 def find(prefix):return next(o.component for o in main if o.component.name.startswith(prefix))
 uc,bc=find('01 '),find('02 ')
 sl=next(b for b in uc.bRepBodies if 'LEFT' in b.name);sr=next(b for b in uc.bRepBodies if 'RIGHT' in b.name)
 bl=next(b for b in bc.bRepBodies if 'LEFT' in b.name);br=next(b for b in bc.bRepBodies if 'RIGHT' in b.name)
 with open(out+'../recessed-switch-labels.json') as f:labels=json.load(f)
 # Recover the exact existing glyph cavities, retaining the original font outlines.
 stage('recovering readable Arial Bold glyphs from original pockets')
 glyphs={};label_tools={}
 for row in labels['placements']:
  if not row['part'].startswith('main'):continue
  ch=row['label'];x,y=row['LED_center_XY_mm'];z=row['roof_Z_mm'];lo,hi=row['glyph_bounds_layout_mm']
  source=sl if x<194 else sr
  mask=box(lo[0]-.00001,lo[1]-.00001,z-.8,hi[0]+.00001,hi[1]+.00001,z)
  tool=cut(mask,mgr.copy(source));assert abs(vol(tool)-row['removed_volume_mm3'])<.001
  assert tool.isSolid and tool.lumps.count==1
  glyphs[ch]=(tool,row);label_tools[ch]=tool
 assert len(glyphs)==10
 pocket_checks=[]
 def shell_candidate(source,part):
  rows=[r for r in labels['placements'] if r['part']==part];assert rows,(source.name,part)
  blank=mgr.copy(source);expected=0
  for r in rows:
   lo,hi=r['glyph_bounds_layout_mm'];z=r['roof_Z_mm']
   blank=union(blank,box(lo[0]-.00001,lo[1]-.00001,z-.80001,hi[0]+.00001,hi[1]+.00001,z));expected+=r['removed_volume_mm3']
  assert abs(vol(blank)-vol(source)-expected)<.003,(part,'pocket restoration')
  result=mirror(blank)
  for r in rows:
   tool,origin=glyphs[r['label']];a=mgr.copy(tool);q=bounds(a);width=q[3]-q[0]
   oldx,oldy=r['LED_center_XY_mm'];newx=350-oldx;z=r['roof_Z_mm']
   # Preserve the reflected label bounding box, but keep the letter itself readable.
   a=move(a,dx=newx-6-width-q[0],dy=oldy-origin['LED_center_XY_mm'][1],dz=z-origin['roof_Z_mm'])
   assert abs(hit(result,a)-vol(a))<.003,(part,r['label'],'label not within roof')
   result=cut(result,a)
   pocket_checks.append({'part':part,'label':r['label'],'LED_XY_mm':[newx,oldy],'bounds_mm':bounds(a),'height_mm':8,'depth_mm':.8,'text_reflected':False})
  assert result.isSolid and result.lumps.count==1
  return result
 upper_right=shell_candidate(sl,'main left')
 upper_left=shell_candidate(sr,'main/right electronics')
 # Copy the asymmetric display opening in the same rigid pose as the actual LCD.
 stage('adapting asymmetric LCD opening and TRS saddle to real components')
 lcd_dx=350-2*307.40219
 lcd_mask=box(286.30219,45,-5.3,328.50219,79.2,.4)
 lcd_region=inter(mgr.copy(sr),mgr.copy(lcd_mask))
 upper_left=cut(upper_left,mirror(mgr.copy(lcd_mask)))
 upper_left=union(upper_left,move(lcd_region,dx=lcd_dx))
 # Original board hole pattern is symmetric about this measured mounting datum.
 hw=find('PCB screws');mcu_screws=[b for b in hw.bRepBodies if b.name.startswith('DFR1075')]
 mcu_anchor=sum((bounds(b)[0]+bounds(b)[3])/2 for b in mcu_screws)/4
 mcu_dx=350-2*mcu_anchor
 # Retain the printed pocket/chamfer handedness, widening only the tiny front aperture
 # difference needed for the real connector's translated datum (about 0.012mm).
 stage('extracting the USB partition opening')
 usb_mask=box(243.69,2.99,-14.03,257.71,4.67,-5.97)
 usb_void=cut(usb_mask,mgr.copy(sr))
 # A small extra clearance avoids nearly coincident Boolean edges and never narrows the port.
 usb_void=move(usb_void,dx=-250.7,dy=-3.83,dz=10)
 scale=adsk.core.Matrix3D.create();scale.setCell(0,0,1.02);scale.setCell(1,1,1.02);scale.setCell(2,2,1.02);assert mgr.transform(usb_void,scale)
 usb_void=move(usb_void,dx=250.7+mcu_dx,dy=3.83,dz=-10)
 stage('fitting the USB partition opening')
 upper_left=cut(upper_left,usb_void)
 base_right=mirror(mgr.copy(bl));base_left=mirror(mgr.copy(br))
 # A real TRS block is translated, so its small asymmetric saddle follows it rigidly.
 stage('refitting the TRS saddle on a restored continuous floor')
 base_left=cut(base_left,box(18.4,24.9,-22.05,43.9,27.5,-7.9))
 base_left=union(base_left,box(18.4,24.9,-24,43.9,27.5,-22))
 base_left=union(base_left,box(18.225,25,-22,43.545,27.4,-8))
 printed={sl.entityToken:upper_right,sr.entityToken:upper_left,bl.entityToken:base_right,br.entityToken:base_left}
 for a in printed.values():assert a.isSolid and a.lumps.count==1
 placements=[];hardware_cache={};main_rows=[];master={}
 def canonical(name):return name.removeprefix('ALT reference - ')
 stage('creating rigid hardware copies at mirrored positions')
 for o in main:
  c=o.component;name=c.name;strategy='geometric reflection';anchor=None;cy=None
  if name.startswith('DFRobot'):anchor=mcu_anchor;strategy='rigid translation'
  elif name.startswith('LCD'):anchor=307.40219;strategy='rigid translation'
  elif name.startswith('Double TRS'):anchor=319.;strategy='rigid translation'
  elif name.startswith('Pololu'):anchor=226.0325;strategy='rigid translation'
  elif name.startswith('Encoder'):anchor=337.5;strategy='rigid translation'
  elif name.startswith('DC power'):anchor=210.;strategy='rigid translation'
  elif name.startswith('SW'):
   cap=next(b for b in c.bRepBodies if 'actuator cap' in b.name);q=bounds(cap);anchor=(q[0]+q[3])/2;cy=(q[1]+q[4])/2
   strategy='rigid 180deg about shaft' if int(name[2:4])<=5 else 'rigid translation'
  elif name.startswith('LED'):
   index=int(name[3:5]);anchor=(47.4 if index<=5 else 14.9)+65*((index-1)%5);cy=-(26.2 if index<=5 else 81.7);strategy='rigid 180deg about shaft'
  rows=[]
  for b in c.bRepBodies:
   if b.entityToken in printed:a=printed[b.entityToken]
   elif strategy=='geometric reflection':a=mirror(mgr.copy(b))
   else:
    a=mgr.copy(b)
    if strategy.startswith('rigid 180'):
     m=adsk.core.Matrix3D.create();m.setToRotation(math.pi,adsk.core.Vector3D.create(0,0,1),adsk.core.Point3D.create(anchor/10,cy/10,0));assert mgr.transform(a,m)
    a=move(a,dx=350-2*anchor)
   rows.append((b,a));main_rows.append((name,b,a))
  hardware_cache[c.entityToken]=rows;master[name]=c
  if anchor is not None:placements.append({'component':name,'strategy':strategy,'old_anchor_X_mm':anchor,'new_anchor_X_mm':350-anchor,'manufacturer_geometry_preserved':True})
 # Regenerate power wiring corridors to the true translated pads, not their reflected locations.
 pol_dx=350-2*226.0325;px=221.27+pol_dx;mx=262.11420453389894+mcu_dx
 routes=[['9V sleeve positive to VIN',[[142,12,-1.5],[142,20,-2],[114,20,-2],[114,32.985,-2],[px,32.985,-2],[px,32.985,-9.984]]],
         ['Center negative to converter GND',[[138,12,-1.5],[138,18,-4],[116,18,-4],[116,30.445,-4],[px,30.445,-4],[px,30.445,-9.984]]],
         ['Regulated 5V VOUT to DFR1075 VIN-5V',[[px,27.905,-9.984],[px,27.905,-2],[mx,27.905,-2],[mx,26.78537742,-2],[mx,26.78537742,-11.5]]],
         ['Converter GND to DFR1075 GND',[[px,30.445,-9.984],[px,30.445,-2],[mx,30.445,-2],[mx,31.86537742,-2],[mx,31.86537742,-11.5]]]]
 power_wires=[]
 for name,points in routes:
  for i,(a,b) in enumerate(zip(points,points[1:])):
   power_wires.append((name+' segment '+str(i+1),mgr.createCylinderOrCone(p(*a),.08,p(*b),.08)))
 stage('checking physical fit and optional LED knockouts')
 cached_preflight=None
 if REUSE_PASSED_PREFLIGHT and before==previous_signatures and os.path.exists(out+'preflight.json'):
  with open(out+'preflight.json') as f:prior=json.load(f)
  if not any(prior[k] for k in ['physical_collisions','power_wire_collisions','base_withdrawal_collisions']) and prior['placements']==placements and prior['power_wire_routes']==routes and prior['readable_labels']==pocket_checks:
   cached_preflight=prior
 if cached_preflight:
  collisions=[];wirehits=[];withdrawals=[];intentional=cached_preflight['intentional_optional_LED_knockout_contacts']
  stage('reusing passed preflight for unchanged source geometry and transformations')
 else:
  collisions=[];intentional=[];wirehits=[]
  for cn,b,a in main_rows:
   if not cn.startswith(('01 ','02 ')):continue
   for hn,h,ha in main_rows:
    if hn.startswith(('01 ','02 ','REF')):continue
    amount=hit(a,ha)
    if amount>.001:
     previous=hit(b,h)
     row={'printed_part':b.name,'hardware':hn,'body':h.name,'overlap_mm3':amount,'original_overlap_mm3':previous}
     if hn.startswith('LED') and abs(amount-previous)<.003:intentional.append(row)
     else:collisions.append(row)
  stage('checking rerouted power-wire clearance')
  for name,a in power_wires:
   for cn,b,other in main_rows:
    if cn.startswith(('REF','DFRobot','Pololu')):continue
    if name.startswith(('9V','Center')) and cn.startswith('DC power'):continue
    amount=hit(a,other)
    if amount>.001:wirehits.append([name,cn,b.name,amount])
  withdrawals=[]
  stage('checking base withdrawal paths')
  for dz in [0,-.01,-.25,-.5,-1,-2,-3,-5,-10,-20]:
   for base in [base_left,base_right]:
    moving=move(mgr.copy(base),dz=dz)
    for shell in [upper_left,upper_right]:
     amount=hit(moving,shell)
     if amount>.001:withdrawals.append([dz,amount])
 report={'revision':'logical_left_electronics','source_document':app.activeDocument.name,'main_outline_mm':[350,92,54],'modular_example_outline_mm':[294.85,92,54],'reflection_plane_X_mm':175,'switch_pitch_mm':65,'upper_row_elevation_mm':30,'row_pitch_mm':53,'display_screws':'M2x5 countersunk','base_screws':'M2x6 countersunk','normal_joint_gap_mm':.2,'base_locator_gap_mm':.2,'placements':placements,'readable_labels':pocket_checks,'LCD_opening_rigid_translation_X_mm':lcd_dx,'LCD_glass_not_geometrically_reflected':True,'TRS_saddle_rigid_translation_X_mm':-288,'MCU_translation_X_mm':mcu_dx,'power_wire_routes':routes,'physical_collisions':collisions,'intentional_optional_LED_knockout_contacts':intentional,'power_wire_collisions':wirehits,'base_withdrawal_collisions':withdrawals,'original_native_assemblies_unchanged':signatures()==before}
 write('preflight.json',report)
 assert not collisions and not wirehits and not withdrawals,(collisions,wirehits,withdrawals)
 assert report['original_native_assemblies_unchanged']
 if not COMMIT:print(json.dumps({'preflight':True,'contacts':len(intentional)}));return
 try:
  stage('creating independent main variant')
  def new(parent,name,m=None):
   o=parent.occurrences.addNewComponent(m or adsk.core.Matrix3D.create());o.component.name=name;o.isLightBulbOn=False;o.component.isOriginFolderLightBulbOn=False;return o
  def presentation(y):
   m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,-y/10,0);return m
  nm=new(root,'ALT Mirrored MAIN - left electronics - 10 switches',presentation(300));created.append(nm)
  def side_name(name):return name.replace('LEFT','{SIDE}').replace('RIGHT','LEFT').replace('{SIDE}','RIGHT').replace('left','{side}').replace('right','left').replace('{side}','right')
  def add(c,source,shape,name=None):
   n=c.bRepBodies.add(mgr.copy(shape));n.name=name or (side_name(source.name)+' - logical mirror')
   if source.appearance:n.appearance=source.appearance
   return n
  def copy_attrs(src,dst):
   for a in src.attributes:dst.attributes.add(a.groupName,a.name,a.value)
  def duplicate(c,parent,name=None):
   o=new(parent,name or ('Mirrored '+side_name(c.name)));dst=o.component
   if c.name.startswith('REF AUX DC'):
    appearance=c.bRepBodies.item(0).appearance
    for name,a in power_wires:
     n=dst.bRepBodies.add(mgr.copy(a));n.name=name
     if appearance:n.appearance=appearance
   else:
    for old,a in hardware_cache[c.entityToken]:add(dst,old,a)
   dst.attributes.add('MIDI_MIRROR','source_component',c.name)
   o.isLightBulbOn=not c.name.startswith('REF');return o
  main_children={}
  for o in main:main_children[o.component.name]=duplicate(o.component,nm.component)
  for c in [nm.component]:c.attributes.add('MIDI_MIRROR','logical_left_electronics',json.dumps(report))
  # Mirror occurrence placements (all currently translation-only), never the real hardware shapes.
  def conjugate(matrix):
   v=list(matrix.asArray());f=[-1,0,0,35,0,1,0,0,0,0,1,0,0,0,0,1]
   def mul(a,b):return [sum(a[i*4+k]*b[k*4+j] for k in range(4)) for i in range(4) for j in range(4)]
   m=adsk.core.Matrix3D.create();assert m.setWithArray(mul(mul(f,v),f));return m
  def match_master(name):
   clean=canonical(name)
   prefixes=['SW'+clean[2:4] if clean.startswith('SW') else clean[:5]]
   for prefix in ['DFRobot','LCD ','Double TRS','Pololu','Encoder','PCB screws','DC power','REF AUX DC','REF LED']:
    if clean.startswith(prefix):return find(prefix)
   if clean.startswith(('SW','LED')):
    return find(clean[:4] if clean.startswith('SW') else clean[:5])
   return None
  stage('creating separate right-extending modular variant')
  na=new(root,'ALT Mirrored MODULAR - right extensions - 8 switches',presentation(450));created.append(na)
  modular_parts=[];source_hardware_discrepancies=[]
  def copy_node(src,parent,matrix):
   name=src.name
   if name.startswith('Existing RIGHT'):destname='Existing LEFT electronics - 4 switches - real PCB poses'
   elif name.startswith('Leftmost pair'):destname='Rightmost pair - D4 - two M2x6 mounts'
   elif name.startswith('Closed left cap'):destname='Closed right cap - one piece - 8.5mm'
   elif name.startswith('Repeatable pair'):destname='Repeatable pair - C3 - extends right - 65mm pitch'
   else:destname='Mirrored '+side_name(name)
   o=new(parent,destname,conjugate(matrix));dst=o.component
   physical_master=match_master(name)
   if physical_master and src.bRepBodies.count:
    expected=list(physical_master.bRepBodies);actual=list(src.bRepBodies)
    assert len(expected)==len(actual),(name,len(expected),len(actual))
    for a,b in zip(actual,expected):
     if abs(a.volume-b.volume)>=1e-7 or max(abs(x-y) for x,y in zip(bounds(a),bounds(b)))>=.00001:
      source_hardware_discrepancies.append({'component':name,'old_body':a.name,'old_volume_mm3':vol(a),'new_reference':physical_master.name,'new_body':b.name,'new_volume_mm3':vol(b),'resolution':'Use the correct, validated main hardware in the new variant; preserve the original modular body unchanged'})
    # Use the already checked rigid geometry, including revised power-wire routes.
    if physical_master.name.startswith('REF AUX DC'):
     for wn,a in power_wires:add(dst,actual[0],a,wn)
    else:
     for old,shape in hardware_cache[physical_master.entityToken]:add(dst,old,shape)
   else:
    for b in src.bRepBodies:
     if 'SHELL' in b.name and name.startswith('Existing RIGHT'):shape=upper_left
     elif 'BASE' in b.name and name.startswith('Existing RIGHT'):shape=base_left
     elif 'SHELL' in b.name and name.startswith('Repeatable pair'):shape=shell_candidate(b,'pair-shell C3')
     elif 'SHELL' in b.name and name.startswith('Leftmost pair'):shape=shell_candidate(b,'pair-shell-at-cap D4')
     else:shape=mirror(mgr.copy(b))
     n=add(dst,b,shape)
     if name.startswith(('Existing','Repeatable','Leftmost','Closed')):
      modular_parts.append({'component':dst.name,'body':n.name,'volume_mm3':vol(shape),'solid':shape.isSolid,'lumps':shape.lumps.count})
   copy_attrs(src,dst)
   for child in src.occurrences:copy_node(child.component,dst,child.transform2)
   o.isLightBulbOn=not name.startswith('REF');return o
  for o in alt.occurrences:copy_node(o.component,na.component,o.transform2)
  na.component.attributes.add('MIDI_MIRROR','logical_left_electronics',json.dumps(report))
  stage('creating right-end modular label library')
  nl=new(root,'ALT Mirrored modular upper print library - NOT assembly');created.append(nl)
  variant_names=[]
  for o in library.occurrences:
   name=o.component.name;src=o.component.bRepBodies.item(0)
   labelpart={'pair-shell-D':'pair-shell D4','pair-shell-at-cap-C':'pair-shell-at-cap C3','pair-shell-at-cap-E':'pair-shell-at-cap E5'}[name]
   shape=shell_candidate(src,labelpart)
   part=new(nl.component,name.replace('at-cap','at-right-cap'));add(part.component,src,shape);part.isLightBulbOn=True;variant_names.append(part.component.name)
  assert signatures()==before,'An original assembly was modified'
  report.update({'new_main_component':nm.component.name,'new_modular_component':na.component.name,'new_library_component':nl.component.name,'modular_parts':modular_parts,'source_hardware_discrepancies':source_hardware_discrepancies,'modular_label_variants':variant_names,'original_native_assemblies_unchanged':True,'independent_BRep_copies':True,'main_switch_labels_left_to_right':{'upper':list('ABCDE'),'lower':list('12345')},'modular_8_switch_labels_left_to_right':{'upper':list('ABCD'),'lower':list('1234')}})
  write('variant-creation.json',report)
  root.attributes.add('MIDI_MIRROR','logical_left_electronics',json.dumps(report))
  for o in root.occurrences:o.isLightBulbOn=o==nm
  app.activeViewport.fit();adsk.doEvents()
  assert app.activeDocument.save('Preserve original main and modular assemblies; add independent logically mirrored left-electronics variants with readable labels and actual PCB poses')
  stage('complete')
  print(json.dumps({'main':nm.component.name,'modular':na.component.name,'source_preserved':True,'physical_collisions':len(collisions),'wire_collisions':len(wirehits),'base_withdrawal_collisions':len(withdrawals)}))
 except Exception:
  marker=root.attributes.itemByName('MIDI_MIRROR','logical_left_electronics')
  if marker:marker.deleteMe()
  for o in reversed(created):
   if o.isValid:o.deleteMe()
  raise
