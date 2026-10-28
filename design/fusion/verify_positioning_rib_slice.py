"""Verify 1.8mm locating ribs and joined gaps in actual 0.6mm PETG toolpaths."""
from pathlib import Path
import json,hashlib,re,math
P=Path(__file__).resolve().parent

def scan(path):
 pos=[0.,0.,0.];kind='';segments={z:[] for z in [2.4,3.,3.6,4.2]}
 for line in path.read_text().splitlines():
  if line.startswith(';TYPE:'):kind=line[6:]
  code=line.split(';')[0].strip()
  if not code.startswith(('G0 ','G1 ')):continue
  q={k:float(v) for k,v in re.findall(r'\b([XYZE])(-?[\d.]+)',code)}
  end=[q.get(k,pos[i]) for i,k in enumerate('XYZ')];z=round(end[2],3)
  if z in segments and q.get('E',0)>0 and not kind.startswith('Support') and math.hypot(end[0]-pos[0],end[1]-pos[1])>.01 and abs(end[2]-pos[2])<1e-5:segments[z].append((pos[:],end[:]))
  pos=end
 return segments

def tracks(seg,x,y0,y1):
 values=[]
 for a,b in seg:
  if abs(b[0]-a[0])<1e-7:continue
  t=(x-a[0])/(b[0]-a[0])
  if -.00001<=t<=1.00001:
   y=a[1]+t*(b[1]-a[1])
   if y0-.06<=y<=y1+.06:values.append(y)
 distinct=[]
 for v in sorted(values):
  if not distinct or v-distinct[-1]>.12:distinct.append(v)
 return len(distinct)

checks=[];sources=[]
for name,offset,probes in [('print/base-left',28.175,[('front',60),('front',150),('rear',62.5)]),('print/base-right',-146.95,[('front',220),('front',245),('front',275),('front',288.5),('front',305),('rear',294)]),('modular/pair-base',-36.275,[('front',145),('front',170),('rear',145)])]:
 gcode=Path('/tmp/midi-'+('modular-' if name.startswith('modular/') else '')+name.split('/')[-1]+'.gcode');seg=scan(gcode)
 for side,x in probes:
  lo,hi=(61.2,63.0) if side=='front' else (147.0,148.8)
  for z in seg:
   count=tracks(seg[z],x+offset,lo,hi);assert count>=2,(name,side,x,z,count)
   checks.append({'part':name,'side':side,'native_X_mm':x,'print_Z_mm':z,'extrusion_tracks':count})
 stl=P/(name+'.stl');sources.append({'path':name+'.stl','sha256':hashlib.sha256(stl.read_bytes()).hexdigest(),'gcode_sha256':hashlib.sha256(gcode.read_bytes()).hexdigest()})
result={'revision':'display_m2x5','printer':'Prusa MK3S+','material':'PETG','nozzle_mm':.6,'rib_thickness_mm':1.8,'layers_below_top_lead_in_mm':[2.4,3.,3.6,4.2],'all_probes_have_two_or_more_tracks':True,'base_supports_required':False,'checks':checks,'STL_checks':sources,'limits':'Finite toolpath probes; actual fit and layer adhesion depend on print calibration.'}
(P/'positioning-rib-slice.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'checks':len(checks),'passed':True}))
