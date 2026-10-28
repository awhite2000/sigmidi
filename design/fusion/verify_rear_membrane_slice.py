"""Verify extrusion through every rear slot film in the end-down 0.6mm slice."""
from pathlib import Path
import json,re,math,hashlib,statistics,sys
P=Path(__file__).resolve().parent
spec=json.loads((P/'rear-vent-membranes.json').read_text())
layout=json.loads((P/'current-layout.json').read_text())
uc=next(c for c in layout['main'] if c['component'].startswith('01 '))
b=next(b for b in uc['bodies'] if 'RIGHT' in b['name'])
lo,hi=b['min_world_mm'],b['max_world_mm']
ox=125-(hi[2]-lo[2])/2-lo[2];oy=105-(hi[1]-lo[1])/2-lo[1]
slot_specs=[r['slot_XZ_mm'] for r in spec['slot_checks']]
def scan(path):
 text=path.read_text();pos=[0.,0.,0.];kind='';relative=True;last_e=0.;segments=[];layers=set()
 for line in text.splitlines():
  if line.startswith(';TYPE:'):kind=line[6:]
  code=line.split(';')[0].strip()
  if code=='M83':relative=True
  if code=='M82':relative=False
  q={k:float(v) for k,v in re.findall(r'\b([XYZE])(-?[\d.]+)',code)}
  if code.startswith('G92 '):
   last_e=q.get('E',last_e);continue
  if not code.startswith(('G0 ','G1 ')):continue
  end=[q.get(k,pos[i]) for i,k in enumerate('XYZ')]
  e=q.get('E',0) if relative else q.get('E',last_e)-last_e
  if 'E' in q:last_e=q['E']
  length=math.hypot(end[0]-pos[0],end[1]-pos[1])
  if e>0 and length>.01 and not kind.startswith('Support') and abs(end[2]-pos[2])<1e-5:
   z=round(end[2],3);layers.add(z);segments.append((pos[:],end[:],e,length,kind))
  pos=end
 output=[]
 for x0,x1,z0,z1 in slot_specs:
  height0,height1=hi[0]-x1+1.5,hi[0]-x0-1.5
  expected={z for z in layers if height0-1e-5<=z<=height1+1e-5};seen=set();widths=[]
  target_x=ox+(z0+z1)/2
  for a,b,e,length,kind in segments:
   z=round(b[2],3)
   if z not in expected or abs(b[0]-a[0])<1e-7:continue
   t=(target_x-a[0])/(b[0]-a[0])
   if not -1e-6<=t<=1+1e-6:continue
   y=a[1]+t*(b[1]-a[1])
   if oy-2-.015<=y<=oy-1.4+.015:
    seen.add(z)
    if 'Bridge' not in kind:widths.append(e*math.pi*(1.75/2)**2/(length*.3)+.3*(1-math.pi/4))
  output.append({'slot_XZ_mm':[x0,x1,z0,z1],'core_print_Z_mm':[height0,height1],'expected_layers':len(expected),'layers_with_membrane_extrusion':len(seen),'missing_layers':sorted(expected-seen),'estimated_commanded_bead_width_mm_median':round(statistics.median(widths),4) if widths else None})
 return output
baseline=Path('/tmp/pre-membrane-shell-right.gcode')
if sys.argv[1:]==['--baseline']:
 print(json.dumps([{k:r[k] for k in ['slot_XZ_mm','expected_layers','layers_with_membrane_extrusion']} for r in scan(baseline)]));raise SystemExit
current=Path('/tmp/midi-shell-right.gcode');rows=scan(current)
assert all(r['expected_layers']>=34 and not r['missing_layers'] for r in rows),rows
before=scan(baseline) if baseline.exists() else None
if before:assert all(r['layers_with_membrane_extrusion']==0 for r in before),before
report={'revision':'rear_vent_membranes','nozzle_mm':.6,'layer_mm':.3,'nominal_membrane_thickness_mm':.6,'source_orientation':'Right outer end on bed; native X reversed into print Z','all_12_membranes_have_continuous_toolpaths':True,'central_core_check':'Every 0.3mm print layer through each slot core, excluding 1.5mm tapered ends, has non-support extrusion across the slot center in the membrane Y band.','slots':rows,'baseline_without_membranes':[{k:r[k] for k in ['slot_XZ_mm','expected_layers','layers_with_membrane_extrusion']} for r in before] if before else None,'STL_sha256':hashlib.sha256((P/'print/shell-right.stl').read_bytes()).hexdigest(),'Gcode_sha256':hashlib.sha256(current.read_bytes()).hexdigest(),'limits':'Extrusion paths and estimated commanded width do not establish adhesion, cutting effort or physical print quality.'}
(P/'rear-vent-membrane-slice.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'membrane_count':len(rows),'all_12_membranes_have_continuous_toolpaths':True,'layers_checked':[r['expected_layers'] for r in rows],'estimated_bead_widths_mm':[r['estimated_commanded_bead_width_mm_median'] for r in rows]}))
