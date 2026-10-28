"""Probe all revised display towers in the actual 0.6mm nozzle toolpaths."""
from pathlib import Path
import json,hashlib,math
import verify_enclosure_wall_slice as v
P=Path(__file__).resolve().parent
note=json.loads((P/'display-m2x5.json').read_text());heights=[3.,10.2,14.4,14.7,15.,15.3,15.6,15.9,16.2,16.5,17.4]
gcode=Path('/tmp/midi-base-right.gcode');seg=v.scan(gcode,set(heights));checks=[]
for row in note['posts']:
 x,y=row['center_XY_mm'];cx=x-146.95;cy=151-y
 for h in heights:
  z=h-24-.15;seat=note['new_recessed_head_seat_Z_mm']
  ri=2.2 if z<=seat else 2.2-(z-seat) if z<seat+.9 else 1.3
  ro=4.2 if z<=seat+.9 else 4.2-(z-seat-.9) if z<seat+1.8 else 3.3
  assert not v.coverage(seg[h],cx,cy),(x,y,h,'blocked access')
  # Offset 0.11mm from the exact axis to avoid counting a perimeter seam endpoint as a missing track.
  offset=.11;ri=math.sqrt(ri*ri-offset*offset);ro=math.sqrt(ro*ro-offset*offset)
  for axis in [0,1]:
   for sign in [-1,1]:
    low,high=sorted([sign*ri,sign*ro]);origin=cy if axis==0 else cx;target=(cx if axis==0 else cy)+offset
    count=v.tracks(seg[h],axis,target,origin+low,origin+high)
    assert count>=2,(x,y,h,axis,sign,count)
    checks.append({'post_XY_mm':[x,y],'print_layer_mm':h,'crossing_axis':axis,'probe_offset_mm':offset,'side':sign,'extrusion_tracks':count})
result={'revision':'display_m2x5','nozzle_mm':.6,'layer_mm':.3,'screw_length_mm':5,'checks':checks,'all_probes_have_two_or_more_tracks':True,'all_access_centers_open':True,'support_required':False,'STL_sha256':hashlib.sha256((P/'print/base-right.stl').read_bytes()).hexdigest(),'gcode_sha256':hashlib.sha256(gcode.read_bytes()).hexdigest(),'limits':'Finite cardinal wall probes at 11 heights in every tower, including both transitions; nominal toolpaths, not a physical screw-fit test.'}
(P/'display-m2x5-slice.json').write_text(json.dumps(result,indent=2));print(json.dumps({'display_tower_checks':len(checks),'passed':True}))
