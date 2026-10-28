"""Verify and package both independent alternatives without touching old deliveries."""
from pathlib import Path
import json,hashlib,zipfile,re,datetime,sys
P=Path(__file__).resolve().parent;ROOT=P.parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from documentation_bundles import portable_markdown
REVISION='sigmidi_embossed_icon_25mm' if (P/'embossed-icon-25mm.json').exists() else 'logical_left_electronics'
def read(name):return json.loads((P/name).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=read('original-file-signatures.json')
for name,value in old.items():assert sha(ROOT/name)==value,name
preservation={'files_verified':len(old),'all_original_files_byte_identical':True,'source_models_retained':True,'verified_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(P/'original-file-preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
creation=read('variant-creation.json');assert creation['original_native_assemblies_unchanged'] and creation['independent_BRep_copies']
assert not any(creation[k] for k in ['physical_collisions','power_wire_collisions','base_withdrawal_collisions'])
native=read('final-native-verification.json');assert native['saved'] and native['original_assemblies_and_library_preserved'] and not native['temporary_components']
assert len(native['readable_label_backing_checks'])==20 and max(r['missing_mm3'] for r in native['readable_label_backing_checks'])<.003
for row in native['CAD']:
 with zipfile.ZipFile(P/(row['file']+'.f3d')) as z:assert z.testzip() is None
 assert (P/(row['file']+'.step')).read_text().count('MANIFOLD_SOLID_BREP(')==row['STEP_solids']
exports=read('print-export.json');assert len(exports['parts'])==13
for row in exports['native_equivalence_checks']:assert max(row['bidirectional_difference_mm3'])<.001
meshes=read('mesh-audit.json');assert len(meshes)==13
for r in meshes:assert r['volume_mm3']>0 and all(r[k]==0 for k in ['boundary_edges','nonmanifold_edges','inconsistent_winding_edges','degenerate_triangles'])
walls=read('wall-audit.json');assert walls['unique_parts']==11 and walls['miss_count']==walls['unresolved_samples']==0
for r in walls['parts']:assert sha(P/(r['part']+'.stl'))==r['STL_sha256']
features=read('slice-feature-verification.json');assert features['all_checks_passed'] and len(features['checks'])==192
for r in features['STL_checks']:assert sha(P/r['path'])==r['sha256']
sl=read('slice-verification.json');assert sl['nozzle_mm']==.6 and sl['layer_mm']==.3 and len(sl['parts'])==17
for r in sl['parts']:
 assert r['slice_exit_code']==0 and sha(P/(r['part']+'.stl'))==r['STL_sha256']
 with zipfile.ZipFile(P/(r['part']+'.3mf')) as z:
  assert z.testzip() is None
  assert b'nozzle_diameter = 0.6' in z.read('Metadata/Slic3r_PE.config')
for a,b in {'electronics-shell-left':'shell-left','electronics-base-left':'base-left','fit-coupon-left':'fit-coupon-left','fit-coupon-right':'fit-coupon-right'}.items():
 for ext in ['stl','3mf']:assert (P/'modular'/f'{a}.{ext}').read_bytes()==(P/'main'/f'{b}.{ext}').read_bytes()
for r in read('render-manifest.json')['images']:assert sha(P/r['path'])==r['sha256']
# Summaries use slicer estimates including the supplied brims/supports.
slices={r['part']:r for r in sl['parts']}
def seconds(value):return sum(int(n)*{'h':3600,'m':60,'s':1}[u] for n,u in re.findall(r'(\d+)([hms])',value))
quantities={'main':{'main/shell-left':1,'main/shell-right':1,'main/base-left':1,'main/base-right':1},'modular_8_switches':{'modular/electronics-shell-left':1,'modular/electronics-base-left':1,'modular/pair-shell-C':1,'modular/pair-shell-at-right-cap-D':1,'modular/pair-base':2,'modular/right-cap':1}}
estimates={k:{'grams':round(sum(float(slices[n]['filament_g'])*q for n,q in v.items()),2),'seconds':sum(seconds(slices[n]['estimated_time'])*q for n,q in v.items())} for k,v in quantities.items()}
summary={'revision':REVISION,'native_document':native['document'],'original_native_components_preserved':native['original_top_level_components_verified'],'original_files_byte_identical':len(old),'unique_print_shapes':11,'print_meshes_with_coupons':13,'sliced_projects_with_aliases':17,'wall_samples':walls['surface_samples'],'unresolved_wall_samples':0,'critical_toolpath_checks':192,'solid_label_backing_checks':20,'nozzle_mm':.6,'layer_mm':.3,'CAD':native['CAD'],'estimates':estimates,'physical_print_tested':False}
(P/'verification-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
common=['display-rotation.json','verification-summary.json','README.md','variant-creation.json','final-native-verification.json','export-verification.json','original-file-preservation.json','original-file-signatures.json','print-export.json','mesh-audit.json','wall-audit.json','slice-feature-verification.json','slice-verification.json','render-manifest.json','layout.json']
if (P/'embossed-icon-25mm.json').exists():
 common+=['embossed-icon-25mm.json','emboss-export.json','emboss-print-verification.json','emboss-complete-cad.json']
packages={}
for folder in ['main','modular']:
 files=[P/n for n in common]+[f for f in (P/folder).iterdir() if f.is_file() and f.suffix in ['.f3d','.step','.stl','.3mf','.ini','.png']]
 paths={f.relative_to(P).as_posix():sha(f) for f in sorted(files)}
 portable_guide=portable_markdown(P/'README.md','README.md',[(f,f.relative_to(P).as_posix()) for f in files]).encode()
 paths['README.md']=hashlib.sha256(portable_guide).hexdigest()
 manifest={'revision':REVISION,'variant':folder,'files':paths,'nozzle_mm':.6,'layer_mm':.3,'original_files_byte_identical':True,'native_saved_document':native['document']}
 mf=P/folder/'delivery-manifest.json';mf.write_text(json.dumps(manifest,indent=2)+'\n');files.append(mf)
 filename='mirrored-'+folder+'-mk3s-petg-06.zip';target=P/filename
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  for f in files:
   if f==P/'README.md':z.writestr('README.md',portable_guide)
   else:z.write(f,f.relative_to(P).as_posix())
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
  for f,h in paths.items():assert hashlib.sha256(z.read(f)).hexdigest()==h
 packages[folder]={'path':filename,'files':len(files),'bytes':target.stat().st_size,'sha256':sha(target)}
report={'revision':REVISION,'original_native_assemblies_preserved':True,'original_files_byte_identical':len(old),'independent_main_and_modular_models':True,'unique_print_shapes':11,'print_meshes_with_coupons':13,'sliced_projects_with_aliases':17,'wall_samples':walls['surface_samples'],'unresolved_thin_wall_samples':0,'critical_toolpath_checks':192,'label_backing_checks':20,'label_backing_mm':2.2,'CAD':native['CAD'],'nozzle_mm':.6,'layer_mm':.3,'estimates':estimates,'packages':packages,'limits':'Nominal CAD, finite surface/toolpath checks and slicer estimates; no physical print/load test.'}
(P/'delivery-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
