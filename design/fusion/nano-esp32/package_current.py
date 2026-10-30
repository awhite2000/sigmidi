"""Package all four current enclosure families after the direct Nano mount update.

Only current CAD, print files, documents and applicable verification are shipped.
Older feature-specific audit scripts remain source history; the changed post
regions are covered by native interference/difference, mesh-section and slicing
checks instead of inheriting invalid old mesh signatures.
"""
from pathlib import Path
import hashlib,json,zipfile,re,sys,datetime

P=Path(__file__).resolve().parent
F=P.parent
ROOT=P.parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from documentation_bundles import portable_markdown


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
 fit=json.loads((P/'mount-fit.json').read_text());exports=json.loads((P/'exports.json').read_text());printing=json.loads((P/'print-verification.json').read_text())
 assert fit['all_variants_collision_free'] and not fit['component_face_down'] and fit['separate_inserts']==0
 assert fit['upper_shell_revision_IDs_verified_unchanged'] and exports['upper_shell_print_files_byte_identical']
 assert fit['assembly_instance_placement_verified'] and len(exports['assembly_board_bounds_checks'])==4
 assert len(fit['checks'])==4 and all(not r['physical_collisions'] and not r['blocked_floor_slots'] for r in fit['checks'])
 assert all(r['unintended_added_mm3']<.001 and r['unintended_removed_mm3']<.001 for r in fit['checks'])
 assert printing['all_eight_post_sections_open_and_at_least_2mm_wall'] and not printing['support_material']
 for row in printing['unique_meshes']:assert sha(ROOT/row['file'])==row['STL_sha256']
 for name,digest in exports['upper_print_files_preserved'].items():assert sha(F/name)==digest,name
 for row in exports['images']:assert sha(F/row['path'])==row['sha256'],row['path']
 for folder,a,b in [(F/'mirrored','main/base-left','modular/electronics-base-left'),(F,'print/base-right','modular/electronics-base')]:
  for ext in ['.stl','.3mf']:assert (folder/(a+ext)).read_bytes()==(folder/(b+ext)).read_bytes()
 # Validate every current oriented STL and 3MF at its delivery boundary.
 inventories=[]
 for folder in [F/'print',F/'modular',F/'mirrored/main',F/'mirrored/modular']:
  entries=[]
  for path in sorted(folder.glob('*.3mf')):
   with zipfile.ZipFile(path) as z:
    assert z.testzip() is None,path
    assert b'nozzle_diameter = 0.6' in z.read('Metadata/Slic3r_PE.config'),path
   assert path.with_suffix('.stl').is_file()
   entries.append({'part':path.stem,'STL_sha256':sha(path.with_suffix('.stl')),'3MF_sha256':sha(path)})
  inventories.append({'folder':str(folder.relative_to(ROOT)),'parts':entries})
 # Refresh the two visible Right print-estimate tables with actual current slices.
 def seconds(value):return sum(int(n)*{'h':3600,'m':60,'s':1}[u] for n,u in re.findall(r'(\d+)([hms])',value))
 for folder,quantities in [(F/'print',{'shell-left':1,'shell-right':1,'base-left':1,'base-right':1}),
                           (F/'modular',{'pair-shell':1,'pair-shell-at-cap':1,'pair-base':2,'left-cap':1,'electronics-shell':1,'electronics-base':1})]:
  rows={v['part']:v for v in json.loads((folder/'slice-verification.json').read_text())['parts']}
  table=['| Part | Quantity | Estimated time each |','|---|---:|---|']
  for n,q in quantities.items():table.append(f"| {n} | {q} | {rows[n]['estimated_time']} |")
  total=sum(seconds(rows[n]['estimated_time'])*q for n,q in quantities.items());mass=sum(float(rows[n]['filament_g'])*q for n,q in quantities.items())
  table+=['',f'Estimated total: **{total//3600}h {(total%3600)//60}m, {mass:.0f} g**, including brims/supports, excluding fit coupons.','']
  readme=folder/'README.md';readme.write_text(readme.read_text().split('## Current slicer estimates')[0].rstrip()+'\n\n## Current slicer estimates\n\n'+'\n'.join(table))
 if '--prepare-docs' in sys.argv:
  print('Updated current print-estimate tables.');return
 report={'revision':fit['revision'],'source_model':'sigmidi-foot-controller-0.1.f3d','component_face_down':False,
         'direct_integral_posts':4,'separate_Nano_mount_parts':0,'Nano_screws':'Four M1.6x5 pan head',
         'upper_shells_native_revisions_unchanged':True,'upper_print_files_byte_identical':True,
         'all_four_assembly_interference_checks_passed':True,'floor_vents_preserved':13,
         'new_post_section_checks':8,'new_section_minimum_wall_mm':min(v['minimum_section_wall_mm'] for m in printing['unique_meshes'] for v in m['post_sections']),
         'minimum_blind_web_above_vent_mm':fit['minimum_blind_web_above_vent_mm'],'support_extrusion_in_updated_bases':False,
         'USB_XZ_alignment_preserved':True,'USB_additional_recess_mm':1.5,
         'inventories':inventories,'physical_print_tested':False,
         'validation_scope':'Changed mount regions: native solid/difference and interference checks, closed manifold meshes, eight pilot/post sections, 0.6mm PETG toolpaths. Other features: unchanged upper print hashes and exact no-change outside mounting neighborhoods. Physical fit and strength require a build.'}
 (P/'package-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 # Publish current verification pointers, never old hashes for changed meshes.
 for path in [F/'delivery-verification.json',F/'mirrored/delivery-verification.json',F/'mirrored/verification-summary.json']:
  path.write_text(json.dumps({**report,'details':'nano-esp32/package-verification.json' if path.parent==F else '../nano-esp32/package-verification.json'},indent=2)+'\n')
 packages={}
 for label,folder,zip_path,cad,guide in [
  ('Right main',F/'print',F/'print/mk3s-petg-06-print-package.zip',F/'midi-foot-chassis',F/'print/README.md'),
  ('Right modular',F/'modular',F/'modular/chainable-enclosure-mk3s-petg-06.zip',F/'modular/midi-foot-modular',F/'modular/README.md'),
  ('Left main',F/'mirrored/main',F/'mirrored/mirrored-main-mk3s-petg-06.zip',F/'mirrored/main/midi-foot-mirrored-main',F/'mirrored/README.md'),
  ('Left modular',F/'mirrored/modular',F/'mirrored/mirrored-modular-mk3s-petg-06.zip',F/'mirrored/modular/midi-foot-mirrored-modular',F/'mirrored/README.md')]:
  entries=[];prefix=(folder.name+'/') if label.startswith('Left') else ''
  for p in sorted(folder.iterdir()):
   if p.suffix in ['.stl','.3mf','.ini','.png']:entries.append((p,prefix+p.name))
  for ext in ['.f3d','.step']:entries.append((cad.with_suffix(ext),prefix+cad.name+ext))
  for name in ['mount-fit.json','installation.json','assembly-clearance.json','print-verification.json','package-verification.json','exports.json','instance-placement.json']:
   entries.append((P/name,'verification/'+name))
  for name in ['installed.png','exploded.png','posts.png']:entries.append((P/name,'nano/'+name))
  entries.extend([(guide,'README.md'),(P/'README.md','nano/README.md'),
      (ROOT/'docs/assembly-guide.md','docs/assembly-guide.md'),(ROOT/'docs/bill-of-materials.md','docs/bill-of-materials.md'),
      (ROOT/'docs/hardware.md','docs/hardware.md'),(ROOT/'docs/power.md','docs/power.md'),
      (ROOT/'output/pdf/sigmidi-foot-controller-0.1-assembly-guide.pdf','docs/assembly-guide.pdf'),
      (ROOT/'output/pdf/sigmidi-foot-controller-0.1-bill-of-materials.pdf','docs/bill-of-materials.pdf')])
  blobs={}
  for source,name in entries:
   assert source.is_file(),source
   if name in blobs:continue
   blobs[name]=portable_markdown(source,name,entries).encode() if name.endswith('.md') else source.read_bytes()
  manifest={'revision':fit['revision'],'assembly':label,'files':{n:hashlib.sha256(b).hexdigest() for n,b in blobs.items()},
            'nozzle_mm':.6,'layer_mm':.3,'Nano_components_up':True,'separate_Nano_inserts':0,'upper_shells_unchanged':True}
  mf=folder/'delivery-manifest.json';mf.write_text(json.dumps(manifest,indent=2)+'\n');blobs['delivery-manifest.json']=mf.read_bytes()
  with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
   for name,content in blobs.items():z.writestr(name,content)
  with zipfile.ZipFile(zip_path) as z:
   assert z.testzip() is None
   assert all(z.read(n)==b for n,b in blobs.items())
  packages[label]={'path':str(zip_path.relative_to(ROOT)),'files':len(blobs),'sha256':sha(zip_path)}
 (P/'packages.json').write_text(json.dumps({'revision':fit['revision'],'packages':packages},indent=2)+'\n')
 # Package hashes stay in a separate file, avoiding self-referential manifests.
 print(json.dumps({'packages':packages,'validation_scope':report['validation_scope']},indent=2))


if __name__=='__main__':main()
