"""Render oriented STL solids with actual support extrusion paths from checked G-code."""
from pathlib import Path
import re, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from audit_print_mesh import read_stl
OUT=Path(__file__).resolve().parent/'print'
SCALE=2;W,H=1600,1320
im=Image.new('RGB',(W*SCALE,H*SCALE),'#edf1f5');draw=ImageDraw.Draw(im)
font='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def f(n,b=False):return ImageFont.truetype(bold if b else font,n*SCALE)
def txt(x,y,t,n=18,color='#172d3e',b=False):draw.text((x*SCALE,y*SCALE),t,font=f(n,b),fill=color)
def support_segments(name):
 path=Path('/tmp/sigmidi-direct-nano-right.gcode') if name=='base-right' else Path('/tmp/midi-'+name+'.gcode')
 text=path.read_text()
 assert '; nozzle_diameter = 0.6' in text
 if name.startswith('shell'):assert '; support_material_threshold = 40' in text
 xyz=np.zeros(3);kind='';segments=[];relE=True;lastE=0
 for line in text.splitlines():
  if line.startswith(';TYPE:'):kind=line[6:];continue
  code=line.split(';')[0].strip()
  if code=='M83':relE=True
  if code=='M82':relE=False
  if code.startswith('G92 '):
   m=re.search(r'\bE(-?[\d.]+)',code)
   if m:lastE=float(m.group(1))
  if not code.startswith(('G0 ','G1 ')):continue
  vals={k:float(v) for k,v in re.findall(r'([XYZE])(-?\d*\.?\d+)',code)}
  new=xyz.copy()
  for i,k in enumerate('XYZ'):
   if k in vals:new[i]=vals[k]
  extrude=vals.get('E',0) if relE else vals.get('E',lastE)-lastE
  if 'E' in vals:lastE=vals['E']
  if kind.startswith('Support material') and extrude>0 and np.linalg.norm(new[:2]-xyz[:2])>.001:segments.append((xyz.copy(),new.copy()))
  xyz=new
 return np.array(segments) if segments else np.empty((0,2,3))

def panel(name,title,subtitle,dim,x,y,cam):
 global im,draw
 card=(x*SCALE,y*SCALE,(x+760)*SCALE,(y+560)*SCALE)
 draw.rounded_rectangle(card,18*SCALE,fill='white',outline='#d8e1e8',width=SCALE)
 txt(x+24,y+18,title,24,b=True);txt(x+24,y+53,subtitle,17)
 v=read_stl(OUT/(name+'.stl'));size=v.max(axis=(0,1))-v.min(axis=(0,1));sup=support_segments(name)
 if len(sup):sup-=np.array([125-size[0]/2,105-size[1]/2,0])
 camera=np.array(cam,dtype=float);camera/=np.linalg.norm(camera);right=np.cross(np.array([0.,0.,1.]),camera);right/=np.linalg.norm(right);up=np.cross(camera,right)
 basis=np.array([right,up,camera]).T
 bed=np.array([[-7,-7,0],[size[0]+7,-7,0],[size[0]+7,size[1]+7,0],[-7,size[1]+7,0]])
 pv=v@basis;pb=bed@basis
 allpts=np.concatenate([pv.reshape(-1,3),pb],axis=0);bounds=allpts[:,:2].min(axis=0),allpts[:,:2].max(axis=0)
 k=min(690/(bounds[1][0]-bounds[0][0]),410/(bounds[1][1]-bounds[0][1]))
 center=(bounds[0]+bounds[1])/2;screen=np.array([x+380,y+292])
 def project(a):return (np.stack([(a[...,0]-center[0])*k+screen[0],-(a[...,1]-center[1])*k+screen[1]],axis=-1)*SCALE)
 draw.polygon([tuple(a) for a in project(pb)],fill='#e5ebf0',outline='#a6b5c0',width=2*SCALE)
 for xx in np.arange(0,size[0]+1,20):
  pp=np.array([[xx,-7,0],[xx,size[1]+7,0]])@basis;draw.line([tuple(a) for a in project(pp)],fill='#ccd6de',width=SCALE)
 for yy in np.arange(0,size[1]+1,20):
  pp=np.array([[-7,yy,0],[size[0]+7,yy,0]])@basis;draw.line([tuple(a) for a in project(pp)],fill='#ccd6de',width=SCALE)
 normals=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-15)
 light=np.array(cam,dtype=float)+np.array([-.2,.1,1.2]);light/=np.linalg.norm(light)
 intensity=.52+.48*np.maximum(0,normals@light)
 colors=np.clip(intensity[:,None]*np.array([67,149,176]),0,255).astype(int)
 projected=project(pv);items=[(pv[i,:,2].mean(),0,i) for i in range(len(v))]
 if len(sup):
  ps=sup@basis;lines=project(ps);items.extend((ps[i,:,2].mean(),1,i) for i in range(len(sup)))
 # Per-pixel depth test preserves holes and prevents rear mesh faces showing through.
 pixels=np.array(im);depthbuffer=np.full((H*SCALE,W*SCALE),-np.inf,dtype=np.float32)
 def raster(q,z,color):
  x0=max(0,int(np.floor(q[:,0].min())));x1=min(W*SCALE-1,int(np.ceil(q[:,0].max())))
  y0=max(0,int(np.floor(q[:,1].min())));y1=min(H*SCALE-1,int(np.ceil(q[:,1].max())))
  if x1<x0 or y1<y0:return
  xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
  den=(q[1,1]-q[2,1])*(q[0,0]-q[2,0])+(q[2,0]-q[1,0])*(q[0,1]-q[2,1])
  if abs(den)<1e-10:return
  a=((q[1,1]-q[2,1])*(xx-q[2,0])+(q[2,0]-q[1,0])*(yy-q[2,1]))/den
  b=((q[2,1]-q[0,1])*(xx-q[2,0])+(q[0,0]-q[2,0])*(yy-q[2,1]))/den
  c=1-a-b;zz=a*z[0]+b*z[1]+c*z[2];buf=depthbuffer[y0:y1+1,x0:x1+1]
  keep=(a>=-1e-7)&(b>=-1e-7)&(c>=-1e-7)&(zz>buf)
  buf[keep]=zz[keep];pixels[y0:y1+1,x0:x1+1][keep]=color
 for i in range(len(v)):raster(projected[i],pv[i,:,2],colors[i])
 if len(sup):
  for q,z in zip(lines,ps[:,:,2]):
   direction=q[1]-q[0];length=np.linalg.norm(direction)
   if length<.01:continue
   normal=np.array([-direction[1],direction[0]])/length*max(.6,.7*k*SCALE/2)
   quad=np.array([q[0]+normal,q[0]-normal,q[1]-normal,q[1]+normal])
   raster(quad[[0,1,2]],np.array([z[0],z[0],z[1]]),[232,134,23])
   raster(quad[[0,2,3]],np.array([z[0],z[1],z[1]]),[232,134,23])
 im=Image.fromarray(pixels);draw=ImageDraw.Draw(im)
 txt(x+24,y+508,dim,17,b=True)
 txt(x+24,y+534,'Orange: slicer-generated supports' if len(sup) else 'No supports required in the checked profile',15,color='#a85a04' if len(sup) else '#26774a')
 return {'part':name,'support_extrusion_segments_shown':len(sup)}

txt(40,24,'Recommended print orientations',33,b=True)
txt(40,70,'Prusa MK3S+  •  PETG  •  0.6 mm nozzle  •  0.3 mm layers',20)
txt(40,104,'Blue: printed part     Orange: actual support toolpaths     Grey: build plate',18)
res=[]
exports={p['name']:p for p in json.loads((OUT/'print-export.json').read_text())['parts']}
for name,title,subtitle,x,y,cam in [
 ('shell-left','1  Left shell','Outer end on the bed; open seam faces upward',30,150,(1.5,-1.8,1.0)),
 ('shell-right','2  Right shell','Outer end on the bed; open seam faces upward',810,150,(-1.5,-1.8,1.0)),
 ('base-left','3  Left base','Outside floor on the bed; mounting posts upward',30,730,(1.1,-1.6,1.9)),
 ('base-right','4  Right base','Outside floor on the bed; mounting posts upward',810,730,(1.1,-1.6,1.9))]:
 dim=' × '.join(f'{v:.2f}'.rstrip('0').rstrip('.') for v in exports[name]['size_mm'])+' mm  •  6 mm brim'
 res.append(panel(name,title,subtitle,dim,x,y,cam))
im.resize((W*2,H*2),Image.Resampling.LANCZOS).save(OUT/'printing-orientations-supports.png')
(OUT/'printing-orientations-supports.json').write_text(json.dumps({'source':'Current oriented STL solids and PrusaSlicer support extrusion paths from /tmp/midi-PART.gcode','views':'Separate prints; independently scaled; brim omitted for clarity; occluded support paths are hidden by opaque part surfaces','parts':res,'STL_sha256':{n:hashlib.sha256((OUT/(n+'.stl')).read_bytes()).hexdigest() for n in exports},'Gcode_sha256':{n:hashlib.sha256((Path('/tmp/sigmidi-direct-nano-right.gcode') if n=='base-right' else Path('/tmp/midi-'+n+'.gcode')).read_bytes()).hexdigest() for n in exports}},indent=2))
print(json.dumps(res))
