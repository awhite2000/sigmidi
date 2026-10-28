"""Summarize the all-part BVH wall scan and review thin-feature exceptions."""
from pathlib import Path
from collections import defaultdict
import json,hashlib,math,zipfile,subprocess,concurrent.futures,sys
P=Path(__file__).resolve().parent
before=json.loads((P/'wall-thickness-before.json').read_text())

def world(name,p):
 x,y,z=p
 if 'base-left' in name:return [x,92-y,z-24]
 if 'base-right' in name:return [193.9+x,92-y,z-24]
 if 'pair-base' in name:return [128.9+x,92-y,z-24]
 if 'shell-left' in name:return [z,92-y,30-x]
 if 'shell-right' in name:return [350-z,92-y,x-22]
 if 'left-cap' in name:return [120.15+z,92-y,30-x]
 return [193.65-z,92-y,x-22]

def category(name,s):
 x,y,z=s['world'];ex,ey,ez=s['end_world']
 if s['weight']<1e-6:return 'Numerical surface sliver below 1e-6 mm2'
 if 'base' in name:
  ends=[0,193.65] if 'base-left' in name else [193.9,350] if 'base-right' in name else [128.9,193.65]
  if min(abs(x-v) for v in ends)<2.1 and z<=-19.9:return '45-degree glue land runout backed by 2mm floor'
  if z<=-21.9 and ez<=-21.9 and s['t']>=1.3:return 'Countersink edge in 2mm floor, retained screw opening'
  if abs(z+22)<.0011 and abs(ez+22)<.0011 and s['weight']<.001:return 'Sub-micron raised remnant backed by intact 2mm floor'
  if -22.001<=z<=-18.999 and (2.199<=y<=4.001 or 87.999<=y<=89.801 or x<=4.001 or x>=345.999):
   if z>=-19.501 or s['t']>=1.79:return '1.8mm locating rib or 0.5mm lead-in; actual toolpaths verified'
  if 'base-right' in name:
   if 217.9<=x<=234.2 and 22<=y<=38.2 and z>=-21.1:return 'Open Pololu fixture: specified spring/hook/edge-seat geometry'
   if 237<=x<=264.3 and 4<=y<=66 and -22.1<=z<=-13.09 and s['t']>=1.7:return '1.725mm MCU post wall, two-track slice required'
   if 196<=x<=211 and (y<12 or y>80) and z>=-22.1:return 'Boss clearance terminates locating rib; floor backing retained'
 else:
  ends=[193.65] if 'shell-left' in name else [193.9] if 'shell-right' in name else [128.65] if 'left-cap' in name else [128.9,193.65]
  if min(abs(x-v) for v in ends)<4.5:return 'Mating drop-down joint ramp/runout, protected assembly interface'
  for roof,cy,xs in [(30,26.2,[47.4+65*i for i in range(5)]),(0,81.7,[14.9+65*i for i in range(5)])]:
   if roof-.801<=z<=roof+.001 and roof-.801<=ez<=roof+.001:
    if any(math.hypot(x-cx,y-cy)<=2.71 for cx in xs):return 'Intentional 0.8mm optional LED breakaway cover'
    return 'Recessed glyph side/edge backed by exact-checked 2.2mm roof'
   if any(math.hypot(x-cx,y-cy)<5.8 for cx in xs) and roof-8.1<=z<=roof+.001:return 'Internal LED seat/taper at intact roof or cover'
  if -15.01<=z<=-14.49 and (y<2.1 or y>89.9) and s['weight']<.001:return 'Internal boss-to-wall fillet tangent, backed by stock 2mm wall'
  if 'shell-right' in name:
   if 2<=y<=3.011 and any(abs(math.hypot(x-cx,z)-5.9)<.5 for cx in [310.725,327.275]):return 'Intentional TRS bore mouth chamfer in reinforced 3mm wall'
   if y<=2.01 and 2<=z<=22.4 and any(a<=x<=b for a,b in [(220.5,234.9),(243,257.4),(266,280.4)]):return 'Intentional 0.6mm rear vent breakaway film/edge'
   if 239.9<=x<=261.5 and y<=4.651 and -16.71<=z<=-3.09:return 'USB pocket: open lead-in bevel or retained 1.6mm partition'
   if 284.9<=x<=329 and 45<=y<=79 and -5<=z<=.31:return 'LCD opening bevel or fixed 1.5mm seating ledge'
 return 'REVIEW'

parts=[];unresolved=[]
for old in before['parts']:
 name=old['part'];path=Path('/tmp/wall-after-'+name.replace('/','-')+'.json');j=json.loads(path.read_text());areas=defaultdict(float);counts=defaultdict(int);review=[]
 for s in j['thin_samples']:
  s['world']=world(name,s['p']);s['end_world']=world(name,s['end']);k=category(name,s);areas[k]+=s['weight'];counts[k]+=1
  if k=='REVIEW':review.append(s)
 if review:unresolved.append({'part':name,'samples':review})
 parts.append({'part':name,'STL_sha256':hashlib.sha256((P/(name+'.stl')).read_bytes()).hexdigest(),'sample_count':j['sample_count'],'miss_count':j['miss_count'],'surface_area_mm2':j['sampled_surface_area_mm2'],'thin_sample_count':j['thin_count'],'area_bins_lt_0_4_0_8_1_2_1_6_1_8_2_rest_mm2':j['area_bins_lt_0_4_0_8_1_2_1_6_1_8_2_rest_mm2'],'reviewed_thin_feature_categories':[{'feature':k,'samples':counts[k],'sampled_surface_area_mm2':v} for k,v in areas.items()],'unresolved_samples':len(review)})
result={'revision':'display_m2x5','method':before['method'],'threshold_mm':1.8,'unique_print_parts':len(parts),'total_samples':sum(r['sample_count'] for r in parts),'parts':parts,'unresolved_sample_count':sum(len(r['samples']) for r in unresolved),'unresolved':unresolved,'reinforcements':'enclosure-wall-reinforcement.json','actual_toolpath_checks':'enclosure-wall-slice.json','review_notes':'Thin is not automatically defective: opening chamfers, joint tapers, countersinks, text sidewalls and floor-backed runouts have vanishing edge thickness. Breakaway covers are intentionally thin. The fixed display/USB seats, MCU posts and flexible clips are retained only with actual extrusion checks. No claim of a global 1.8mm minimum is made.','limitations':'Finite interior-face sampling, inward normal chord thickness, and nominal CAD/toolpaths; not an exhaustive medial-axis minimum, physical print, thermal or fatigue test.'}
(P/'wall-thickness-audit.json').write_text(json.dumps(result,indent=2))
with zipfile.ZipFile(P/'archive/post-display-m2x5-wall-sampling.zip','w',zipfile.ZIP_DEFLATED) as z:
 for row in parts:
  name=row['part'];f=Path('/tmp/wall-after-'+name.replace('/','-')+'.json');z.write(f,f.name)
 z.write(P/'wall-thickness-audit.json','wall-thickness-audit.json')
print(json.dumps({'parts':len(parts),'samples':result['total_samples'],'unresolved_samples':result['unresolved_sample_count']}))
if unresolved:
 for r in unresolved:
  print(r['part'],len(r['samples']),[{k:v for k,v in s.items() if k in ['world','end_world','t','weight']} for s in r['samples'][:4]])
