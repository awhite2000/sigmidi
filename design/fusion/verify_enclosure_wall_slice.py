"""Verify reinforced closures and functional thin walls in actual 0.6mm G-code."""
from pathlib import Path
import json,re,math,hashlib
P=Path(__file__).resolve().parent
report=json.loads((P/'enclosure-wall-reinforcement.json').read_text())

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def nearest(z):return round(round(z/.3)*.3,3)
def scan(path,layers):
 pos=[0.,0.,0.];kind='';relative=True;last_e=0.;segments={z:[] for z in layers}
 for line in path.read_text().splitlines():
  if line.startswith(';TYPE:'):kind=line[6:]
  code=line.split(';')[0].strip()
  if code=='M83':relative=True
  if code=='M82':relative=False
  q={k:float(v) for k,v in re.findall(r'\b([XYZE])(-?[\d.]+)',code)}
  if code.startswith('G92 '):last_e=q.get('E',last_e);continue
  if not code.startswith(('G0 ','G1 ')):continue
  end=[q.get(k,pos[i]) for i,k in enumerate('XYZ')]
  e=q.get('E',0) if relative else q.get('E',last_e)-last_e
  if 'E' in q:last_e=q['E']
  length=math.hypot(end[0]-pos[0],end[1]-pos[1]);z=round(end[2],3)
  if z in segments and e>0 and length>.01 and not kind.startswith('Support') and abs(end[2]-pos[2])<1e-5:
   width=e*math.pi*(1.75/2)**2/(length*.3)+.3*(1-math.pi/4)
   segments[z].append((pos[:],end[:],width))
  pos=end
 return segments

def tracks(seg,axis,target,low,high):
 other=1-axis;values=[]
 for a,b,width in seg:
  if abs(b[axis]-a[axis])<1e-7:continue
  t=(target-a[axis])/(b[axis]-a[axis])
  if not -1e-7<=t<=1+1e-7:continue
  v=a[other]+t*(b[other]-a[other])
  if low-.06<=v<=high+.06:values.append(v)
 unique=[]
 for x in sorted(values):
  if not unique or x-unique[-1]>.12:unique.append(x)
 return len(unique)
def coverage(seg,x,y):
 for a,b,width in seg:
  dx,dy=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
  if math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)<=width/2+.05:return True
 return False

checks=[];stls=[]
for row in report['parts'][:7]:
 name=row['part'];left=name=='main-left';right=name=='main-right';filename={'main-left':'shell-left','main-right':'shell-right'}.get(name,name)
 folder='print' if left or right else 'modular';gcode=Path('/tmp/midi-'+('' if folder=='print' else 'modular-')+filename+'.gcode')
 def height(x):return x if left else (350 if right else 193.65)-x
 def gx(z):return 129-z if left else 121+z
 layers={nearest(height(x)+.15) for x,y in row['pilot_centers_XY_mm']}
 # LED membranes are intentional; verify center coverage at three sections.
 leds=[(47.4+65*i,26.2,30) for i in range(5) if (47.4+65*i<194)==left]+[(14.9+65*i,81.7,0) for i in range(5) if (14.9+65*i<194)==left] if left or right else [(177.4,26.2,30),(144.9,81.7,0)]
 if not (left or right):leds=[(177.4,26.2,30),(144.9,81.7,0)]
 layers.update(nearest(height(x+off)+.15) for x,y,z in leds for off in [-1,0,1])
 if right:
  layers.update(nearest(350-x+.15) for x in [248.7,251.1,254.1,300,310])
 seg=scan(gcode,layers)
 for x,y in row['pilot_centers_XY_mm']:
  h=nearest(height(x)+.15);count=tracks(seg[h],1,151-y+.11,min(gx(-15.5),gx(-13.5)),max(gx(-15.5),gx(-13.5)))
  assert count>=2,(name,'blind cap',x,y,h,count)
  checks.append({'part':filename,'feature':'2mm blind pilot cap','center_XY_mm':[x,y],'print_layer_mm':h,'extrusion_tracks':count})
 for x,y,z in leds:
  for off in [-1,0,1]:
   h=nearest(height(x+off)+.15);ok=coverage(seg[h],gx(z-.4),151-y)
   assert ok,(name,'LED cover',x,y,off,h)
   checks.append({'part':filename,'feature':'intentional 0.8mm LED cover','center_XY_mm':[x,y],'offset_X_mm':off,'covered':ok})
 if right:
  for x in [248.7,251.1,254.1]:
   h=nearest(350-x+.15);count=tracks(seg[h],0,gx(-5.2),151-4.65,151-3.05);assert count>=2,('USB partition',x,h,count)
   checks.append({'part':filename,'feature':'retained 1.6mm USB partition','print_layer_mm':h,'extrusion_tracks':count})
  for x in [300,310]:
   h=nearest(350-x+.15)
   for y in [77.8,78.0]:
    count=tracks(seg[h],1,151-y,gx(-1.5),gx(0));assert count>=2,('LCD ledge',x,y,h,count)
    checks.append({'part':filename,'feature':'retained 1.5mm flush LCD seat','native_XY_mm':[x,y],'extrusion_tracks':count})
 stls.append({'path':folder+'/'+filename+'.stl','sha256':sha(P/folder/(filename+'.stl')),'gcode_sha256':sha(gcode)})
# One-piece cap front wall is printed in seven full layers at this section.
layers={round(i*.3,1) for i in range(2,9)};seg=scan(Path('/tmp/midi-modular-left-cap.gcode'),layers)
for h in layers:
 ok=coverage(seg[h],143,66);assert ok,('cap front wall',h)
 checks.append({'part':'left-cap','feature':'reinforced front wall','print_layer_mm':h,'covered':True})
stls.append({'path':'modular/left-cap.stl','sha256':sha(P/'modular/left-cap.stl')})
# Restored outside floor surfaces, excluding the intentional internal infill.
layers={.3,.6,.9,1.5,1.8,2.1};seg=scan(Path('/tmp/midi-base-left.gcode'),layers)
for h in layers:
 ok=coverage(seg[h],31.175,66);assert ok,('left floor slit',h)
 checks.append({'part':'base-left','feature':'restored floor skin','print_layer_mm':h,'covered':True})
stls.append({'path':'print/base-left.stl','sha256':sha(P/'print/base-left.stl')})
# Existing post walls and flexible spring arms retain two variable-width paths.
seg=scan(Path('/tmp/midi-base-right.gcode'),{8.1})[8.1]
for x in [239.69377609695,261.69420609695]:
 for y in [6.70103,63.30265]:
  count=tracks(seg,1,151-y+.11,x+.775-146.95,x+2.5-146.95);assert count>=2,('MCU post',x,y,count)
  checks.append({'part':'base-right','feature':'retained 1.725mm MCU post wall','center_XY_mm':[x,y],'extrusion_tracks':count})
for lo,hi in [(23.6,25.2),(35.69,37.29)]:
 count=tracks(seg,0,79.25,151-hi,151-lo);assert count>=2,('spring',count)
 checks.append({'part':'base-right','feature':'retained 1.6mm spring arm','extrusion_tracks':count})
stls.append({'path':'print/base-right.stl','sha256':sha(P/'print/base-right.stl')})
result={'revision':'display_m2x5','printer':'Prusa MK3S+','nozzle_mm':.6,'material':'PETG','layer_mm':.3,'all_checks_passed':True,'checks':checks,'STL_checks':stls,'scope':'Actual non-support extrusion, two-track closure/wall probes; film and repaired plate point coverage checked against commanded bead width. The fixed 1.5mm flush-display seat, 1.6mm USB partition and spring arms, and 1.725mm MCU post walls retain at least two paths.','limits':'These nominal toolpaths do not prove physical calibration, adhesion, cooling or fatigue strength.'}
(P/'enclosure-wall-slice.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'all_checks_passed':True,'checks':len(checks),'unique_print_parts':len(stls)}))
