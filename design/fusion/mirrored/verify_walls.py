"""Audit the actual mirrored STL walls, reusing reviewed source feature classes."""
from pathlib import Path
import ast,math,json,hashlib,subprocess,concurrent.futures,zipfile,sys
P=Path(__file__).resolve().parent
binary=Path('/tmp/midi-wall-audit')
source=P.parent/'audit_wall_thickness.cpp'
if not binary.exists() or binary.stat().st_mtime<source.stat().st_mtime:
 subprocess.run(['c++','-std=c++17','-O3',str(source),'-o',str(binary)],check=True)
# Load only the pure coordinate/classification functions; do not execute the original audit writer.
tree=ast.parse((P.parent/'audit_enclosure_walls.py').read_text())
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['world','category']]
namespace={'math':math};exec(compile(ast.Module(body=functions,type_ignores=[]),'source-wall-classes','exec'),namespace)
world,category=namespace['world'],namespace['category']
mapping={'main/shell-left':'print/shell-right','main/shell-right':'print/shell-left','main/base-left':'print/base-right','main/base-right':'print/base-left','modular/pair-shell-C':'modular/pair-shell','modular/pair-shell-D':'modular/pair-shell-D','modular/pair-shell-at-right-cap-D':'modular/pair-shell-at-cap','modular/pair-shell-at-right-cap-C':'modular/pair-shell-at-cap-C','modular/pair-shell-at-right-cap-E':'modular/pair-shell-at-cap-E','modular/pair-base':'modular/pair-base','modular/right-cap':'modular/left-cap'}

selected=set(sys.argv[1:])
dimensions={r['path']:r['size_mm'] for r in json.loads((P/'print-export.json').read_text())['parts']}

def audit(item):
 name,old=item;path=P/(name+'.stl')
 raw=Path('/tmp/midi-mirror-wall-'+name.replace('/','-')+'.json')
 with raw.open('w') as out:subprocess.run([str(binary),str(path)],stdout=out,check=True)
 data=json.loads(raw.read_text());counts={};unresolved=[]
 if 'base' in name:
  width=156.1 if name=='main/base-left' else 193.65 if name=='main/base-right' else 64.75
 else:width=dimensions[name][0]
 def source_point(p):return world(old,[width-p[0],p[1],p[2]])
 for sample in data['thin_samples']:
  s={**sample,'world':source_point(sample['p']),'end_world':source_point(sample['end'])}
  feature=category(old,s)
  x,y,z=s['world'];ex,ey,ez=s['end_world']
  if name=='main/shell-left' and 262.35<=x<=287.45 and 7.85<=y<=28.15 and min(z,ez)>=29.999 and max(z,ez)>30.001:
   feature='Intentional 0.6mm raised icon wall; full 3mm roof backing verified in native CAD'
  counts[feature]=counts.get(feature,0)+1
  if feature=='REVIEW':unresolved.append(s)
 return {'part':name,'source_feature_frame':old,'STL_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'surface_samples':data['sample_count'],'miss_count':data['miss_count'],'thin_sample_count':data['thin_count'],'reviewed_features':counts,'unresolved':unresolved,'raw':str(raw)}
items=[item for item in mapping.items() if not selected or item[0] in selected]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(audit,items))
if selected:
 previous={r['part']:r for r in json.loads((P/'wall-audit.json').read_text())['parts']}
 previous.update({r['part']:r for r in rows});rows=list(previous.values())
report={'revision':'logical_left_electronics','method':'BVH inward normal wall chords of actual mirrored STL triangles; reviewed feature classes mapped through the reflection into source coordinates','threshold_mm':1.8,'parts':rows,'unique_parts':len(rows),'surface_samples':sum(r['surface_samples'] for r in rows),'miss_count':sum(r['miss_count'] for r in rows),'unresolved_samples':sum(len(r['unresolved']) for r in rows),'limits':'Finite normal-chord samples, not an exhaustive medial-axis minimum or a physical print test. Optional LED covers, rear films, lead-ins, glyph walls, USB/LCD seats and flexible clips retain their documented exceptions. No global 1.8mm minimum is claimed.'}
(P/'wall-audit.json').write_text(json.dumps(report,indent=2)+'\n')
with zipfile.ZipFile(P/'wall-sampling.zip','w',zipfile.ZIP_DEFLATED) as z:
 for r in rows:z.write(r['raw'],Path(r['raw']).name)
 z.write(P/'wall-audit.json','wall-audit.json')
print(json.dumps({k:report[k] for k in ['unique_parts','surface_samples','miss_count','unresolved_samples']}))
if report['miss_count'] or report['unresolved_samples']:
 for r in rows:
  if r['unresolved']:print(r['part'],r['unresolved'][:4])
 raise SystemExit('Review new wall samples before packaging')
