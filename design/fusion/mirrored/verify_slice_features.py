"""Probe retained USB walls, readable label backing and M2x5 display towers."""
from pathlib import Path
import json,re,math,hashlib
P=Path(__file__).resolve().parent

def scan(path,layers):
 pos=[0.,0.,0.];kind='';segments={h:[] for h in layers}
 for line in path.read_text().splitlines():
  if line.startswith(';TYPE:'):kind=line[6:]
  code=line.split(';')[0].strip()
  if not code.startswith(('G0 ','G1 ')):continue
  q={k:float(v) for k,v in re.findall(r'\b([XYZE])(-?[\d.]+)',code)}
  end=[q.get(k,pos[i]) for i,k in enumerate('XYZ')];h=round(end[2],3)
  if h in segments and q.get('E',0)>0 and not kind.startswith('Support') and math.hypot(end[0]-pos[0],end[1]-pos[1])>.01 and abs(end[2]-pos[2])<1e-5:segments[h].append((pos[:],end[:]))
  pos=end
 return segments

def tracks(segments,axis,target,low,high):
 values=[]
 for a,b in segments:
  if abs(b[axis]-a[axis])<1e-7:continue
  t=(target-a[axis])/(b[axis]-a[axis])
  if -.00001<=t<=1.00001:
   v=a[1-axis]+t*(b[1-axis]-a[1-axis])
   if low-.06<=v<=high+.06:values.append(v)
 distinct=[]
 for v in sorted(values):
  if not distinct or v-distinct[-1]>.12:distinct.append(v)
 return len(distinct)

def nearest(z):return round(round(z/.3)*.3,3)
emboss=json.loads((P/'embossed-icon-25mm.json').read_text()) if (P/'embossed-icon-25mm.json').exists() else {}
left_print_x_shift=emboss.get('raised_height_mm',0)/2
checks=[];sources={}
# Four screw access tubes, including both conical transitions and the encoder-side flat.
name='main/base-left';gcode=Path('/tmp/midi-mirrored-main-base-left.gcode');heights=[3.,10.2,14.4,14.7,15.,15.3,15.6,15.9,16.2,16.5,17.4];seg=scan(gcode,set(heights))
for x,y in [(26.69781,49.83437),(58.49781,49.83437),(26.69781,74.13437),(58.49781,74.13437)]:
 cx=x+46.95;cy=151-y
 for h in heights:
  z=h-24-.15;seat=-9.51
  ri=2.2 if z<=seat else 2.2-(z-seat) if z<seat+.9 else 1.3
  ro=4.2 if z<=seat+.9 else 4.2-(z-seat-.9) if z<seat+1.8 else 3.3
  off=.11;ri=math.sqrt(ri*ri-off*off);ro=math.sqrt(ro*ro-off*off)
  for axis in [0,1]:
   for sign in [-1,1]:
    lo,hi=sorted([sign*ri,sign*ro]);origin=cy if axis==0 else cx;target=(cx if axis==0 else cy)+off
    count=tracks(seg[h],axis,target,origin+lo,origin+hi)
    assert count>=2,(name,x,y,h,axis,sign,count)
    checks.append({'part':name,'feature':'M2x5 hollow tower wall','native_XY_mm':[x,y],'print_layer_mm':h,'axis':axis,'side':sign,'extrusion_tracks':count})
sources[name]=gcode
# The retained internal USB partition above and below its enlarged aperture.
name='main/shell-left';gcode=Path('/tmp/midi-mirrored-main-shell-left.gcode');layers={nearest(x+.15) for x in [101.3,98.9,95.9]};seg=scan(gcode,layers)
for x in [101.3,98.9,95.9]:
 h=nearest(x+.15)
 for z in [-5.2,-14.7]:
  count=tracks(seg[h],0,129+left_print_x_shift-z,151-4.65,151-3.05);assert count>=2,('USB wall',x,z,h,count)
  checks.append({'part':name,'feature':'retained 1.6mm USB pocket partition','native_XZ_mm':[x,z],'extrusion_tracks':count})
sources[name]=gcode
# Sample the 2.2mm roof backing beneath every new main-panel label.
creation=json.loads((P/'variant-creation.json').read_text())
for name,left in [('main/shell-left',True),('main/shell-right',False)]:
 gcode=Path('/tmp/midi-mirrored-'+name.replace('/','-')+'.gcode')
 rows=[r for r in creation['readable_labels'] if r['part'].startswith('main') and ((r['LED_XY_mm'][0]<156)==left)]
 def height(x):return x if left else 350-x
 layers={nearest(height((r['bounds_mm'][0]+r['bounds_mm'][3])/2)+.15) for r in rows};seg=scan(gcode,layers)
 for r in rows:
  x=(r['bounds_mm'][0]+r['bounds_mm'][3])/2;y=r['LED_XY_mm'][1];roof=r['bounds_mm'][5];h=nearest(height(x)+.15)
  gx=lambda z:129+left_print_x_shift-z if left else 121+z
  lo,hi=sorted([gx(roof-3),gx(roof-.8)])
  count=tracks(seg[h],1,151-y+.11,lo,hi)
  assert count>=2,(name,r['label'],x,y,h,count)
  checks.append({'part':name,'feature':'nominal 2.2mm label backing, multiple extrusion paths','label':r['label'],'print_layer_mm':h,'extrusion_tracks':count})
 sources[name]=gcode
report={'revision':'logical_left_electronics','nozzle_mm':.6,'layer_mm':.3,'all_checks_passed':True,'checks':checks,'STL_checks':[{'path':n+'.stl','sha256':hashlib.sha256((P/(n+'.stl')).read_bytes()).hexdigest(),'gcode_sha256':hashlib.sha256(g.read_bytes()).hexdigest()} for n,g in sources.items()],'limits':'Finite extrusion probes at critical sections, not a physical print or fit test.'}
(P/'slice-feature-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('Critical mirrored feature checks passed:',len(checks))
