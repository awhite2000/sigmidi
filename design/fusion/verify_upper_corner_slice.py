"""Compare actual non-support toolpaths through repaired corner-wall probes."""
from pathlib import Path
import json,re,math,hashlib,statistics
P=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def scan(path):
 pos=[0.,0.,0.];kind='';relative=True;last_e=0.;segments=[]
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
  length=math.hypot(end[0]-pos[0],end[1]-pos[1])
  if e>0 and length>.01 and not kind.startswith('Support') and abs(end[2]-pos[2])<1e-5 and 2<=end[2]<=6:
   width=e*math.pi*(1.75/2)**2/(length*.3)+.3*(1-math.pi/4)
   segments.append((pos[:],end[:],kind,width))
  pos=end
 return segments

def probes(segments,side):
 heights=[round(i*.3,1) for i in (range(8,21) if side=='right' else range(11,21))]
 offset={'right':121.,'left':129.,'cap':128.}[side]
 rows=[]
 for height in heights:
  dx=6-(height-.15)
  y0=6-math.sqrt(36-dx*dx);y1=6-math.sqrt(16-dx*dx)
  for world_z in [-14.,-10.]:
   target=offset+world_z if side=='right' else offset-world_z
   tracks=[];widths=[]
   for a,b,kind,width in segments:
    if abs(b[2]-height)>.001 or abs(b[0]-a[0])<1e-7:continue
    t=(target-a[0])/(b[0]-a[0])
    if not -1e-7<=t<=1+1e-7:continue
    y=151-(a[1]+t*(b[1]-a[1]))
    if y0-.15<=y<=y1+.15:tracks.append(y);widths.append(width)
   unique=[]
   for y in sorted(tracks):
    if not unique or y-unique[-1]>.1:unique.append(y)
   rows.append({'print_layer_Z_mm':height,'native_Z_mm':world_z,'wall_Y_interval_mm':[round(y0,5),round(y1,5)],'distinct_track_count':len(unique),'track_centers_Y_mm':[round(y,5) for y in unique],'median_commanded_bead_width_mm':round(statistics.median(widths),4) if widths else None})
 return rows

parts=[];sources={}
for name,side,gcode,baseline,stl in [
 ('shell-right','right','/tmp/midi-shell-right.gcode','/tmp/pre-upper-corner-shell-right.gcode','print/shell-right.stl'),
 ('shell-left','left','/tmp/midi-shell-left.gcode','/tmp/pre-upper-corner-shell-left.gcode','print/shell-left.stl'),
 ('left-cap','cap','/tmp/midi-modular-left-cap.gcode','/tmp/pre-upper-corner-left-cap.gcode','modular/left-cap.stl')]:
 seg=scan(Path(gcode));after=probes(seg,side);before=probes(scan(Path(baseline)),side) if Path(baseline).exists() else None
 assert all(r['distinct_track_count']>=2 for r in after),(name,after)
 parts.append({'part':name,'minimum_distinct_tracks_before':min(r['distinct_track_count'] for r in before) if before else None,'minimum_distinct_tracks_after':min(r['distinct_track_count'] for r in after),'probes':after,'before':before,'before_zero_track_probes':sum(r['distinct_track_count']==0 for r in before) if before else None,'STL_path':stl,'STL_sha256':sha(P/stl),'Gcode_sha256':sha(Path(gcode))})
 if side=='right':sources={'before':scan(Path(baseline)),'after':seg}
report={'revision':'upper_corner_walls','nozzle_mm':.6,'layer_mm':.3,'all_repaired_probes_have_at_least_two_tracks':True,'probe_scope':'Two native heights (-14 and -10mm), every 0.3mm end-down print layer through the repaired radial wall core, with the CAD cross-section evaluated at the 0.15mm layer midpoint below print Z. Counts are distinct non-support extrusion centerline crossings inside the exact R6/R4 wall interval.','parts':parts,'limits':'Commanded toolpaths verify that the slicer retains wall material; they do not prove physical extrusion, bonding or calibrated dimensions.'}
(P/'upper-corner-slice.json').write_text(json.dumps(report,indent=2))
print(json.dumps([{k:p[k] for k in ['part','minimum_distinct_tracks_after','before_zero_track_probes']} for p in parts]))

# Compare the same real toolpaths in the layer where the old corner skin
# drops below one nozzle width. This is a path preview, not a photo render.
from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGB',(1600,830),'#eef2f5');dr=ImageDraw.Draw(im)
font_path='/System/Library/Fonts/Supplemental/Arial.ttf'
font=ImageFont.truetype(font_path,23);bold=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',28);small=ImageFont.truetype(font_path,18)
dr.text((36,22),'Back-right corner: actual toolpaths, original / current profiles',font=bold,fill='#122738')
dr.text((36,62),'Same print layer: 2.4 mm from the right end. Supports excluded. Lines show commanded bead width.',font=small,fill='#415768')
for label,x0 in [('before',35),('after',820)]:
 title='Before: 0.8 mm nozzle, obsolete 0.34 mm skin' if label=='before' else 'Current: 0.6 mm nozzle, continuous 2 mm wall'
 dr.text((x0,108),title,font=font,fill='#122738')
 panel=Image.new('RGB',(745,600),'white');d=ImageDraw.Draw(panel);scale=61.
 def point(z,y):return ((z+18.5)*scale+25,(7.5-y)*scale+35)
 for i in range(-18,-7):
  a=point(i,0);b=point(i,7);d.line((a,b),fill='#e2e8ec',width=1);d.text((a[0]-12,500),str(i),font=small,fill='#5b6e7d')
 for y in range(8):
  a=point(-18.5,y);b=point(-7.5,y);d.line((a,b),fill='#e2e8ec',width=1);d.text((5,a[1]-8),str(y),font=small,fill='#5b6e7d')
 for a,b,kind,width in sources[label]:
  if abs(b[2]-2.4)>.001:continue
  za,zb=a[0]-121,b[0]-121;ya,yb=151-a[1],151-b[1]
  if max(za,zb)<-18.5 or min(za,zb)>-7.5 or max(ya,yb)<-.3 or min(ya,yb)>7.5:continue
  d.line((point(za,ya),point(zb,yb)),fill='#155f86' if label=='before' else '#078e83',width=max(1,round(min(width,2)*scale)))
  d.line((point(za,ya),point(zb,yb)),fill='#113c52',width=1)
 # Native height of one verification probe, through the previous hole.
 for k in range(24):
  y=k*.3;d.line((point(-14,y),point(-14,min(y+.12,7.2))),fill='#e17328',width=2)
 d.text((250,535),'Native height Z (mm)',font=font,fill='#415768')
 im.paste(panel,(x0,154));dr.rectangle((x0,154,x0+745,754),outline='#becbd4',width=2)
dr.text((36,782),'Orange dashed line: Z -14 mm probe through the wall above the screw mount.',font=small,fill='#415768')
im.save(P/'upper-corner-toolpaths.png')

report['toolpath_comparison_image']='upper-corner-toolpaths.png'
report['toolpath_comparison_sha256']=sha(P/'upper-corner-toolpaths.png')
(P/'upper-corner-slice.json').write_text(json.dumps(report,indent=2))
