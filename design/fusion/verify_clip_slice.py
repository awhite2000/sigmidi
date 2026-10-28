"""Check that both thin retaining leaves survive the 0.6mm nozzle slice."""
from pathlib import Path
import json,re,hashlib
P=Path(__file__).resolve().parent
gcode=Path('/tmp/midi-base-right.gcode');text=gcode.read_text()
# Native X193.9..350 / world Y-92..0 is normalized for STL, then centered
# at 125,105 by slice_print_parts.py. The new leaf tops are at print Z16.216.
cooling=json.loads((P/'ventilated-clip.json').read_text())
width=cooling['spring_leaf_width_mm'];cx=79.25
regions={'rear_leaf':[cx-width/2,cx+width/2,125.8,127.4],'front_leaf':[cx-width/2,cx+width/2,113.71,115.31]}
counts={n:0 for n in regions};layers={n:set() for n in regions}
xs={n:{} for n in regions}
x=y=z=0.;kind=''
for line in text.splitlines():
    if line.startswith(';TYPE:'):kind=line[6:]
    if not line.startswith('G1 '):continue
    q={k:float(v) for k,v in re.findall(r'\b([XYZE])(-?[\d.]+)',line)}
    x=q.get('X',x);y=q.get('Y',y);z=q.get('Z',z)
    if q.get('E',0)<=0 or not ('X' in q or 'Y' in q) or kind.startswith('Support') or not 13<=z<=16.6:continue
    for n,(x0,x1,y0,y1) in regions.items():
        if x0-.15<=x<=x1+.15 and y0-.15<=y<=y1+.15:
            counts[n]+=1;layers[n].add(z);xs[n].setdefault(z,[]).append(x)
assert all(counts[n]>0 and len(layers[n])>=6 for n in regions),(counts,layers)
spans={n:{str(z):round(max(v)-min(v),4) for z,v in rows.items()} for n,rows in xs.items()}
assert all(min(rows.values())>=width-1.4 for rows in spans.values()),spans
report={'expected_leaf_width_mm':width,'extrusion_endpoint_X_spans_mm_by_layer':spans,'revision':json.loads((P/'ventilated-clip.json').read_text())['revision'],'nozzle_mm':.6,'base_support_extrusion_mm':next(r['support_extrusion_filament_mm'] for r in json.loads((P/'print/slice-verification.json').read_text())['parts'] if r['part']=='base-right'),'clip_extrusion_endpoints_above_Z13':counts,'clip_layers_above_Z13':{n:sorted(v) for n,v in layers.items()},'STL_sha256':hashlib.sha256((P/'print/base-right.stl').read_bytes()).hexdigest(),'Gcode_sha256':hashlib.sha256(gcode.read_bytes()).hexdigest(),'limits':'Toolpath presence does not establish snap force, fatigue or high-temperature retention.'}
assert report['base_support_extrusion_mm']==0
(P/'clip-slice-detail.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
