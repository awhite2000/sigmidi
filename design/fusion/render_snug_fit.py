"""Render exact STL sections of the current mating faces for print-fit review."""
from pathlib import Path
import numpy as np,struct,json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent

def read(name):
 data=(P/name).read_bytes();n=struct.unpack_from('<I',data,80)[0]
 dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')])
 return np.frombuffer(data,dtype=dtype,offset=84,count=n)['v'].astype(float)

def native(name):
 v=read(name)
 if name.endswith('shell-left.stl'):return np.stack([v[:,:,2],92-v[:,:,1],30-v[:,:,0]],axis=2)
 if name.endswith('shell-right.stl'):return np.stack([350-v[:,:,2],92-v[:,:,1],v[:,:,0]-22],axis=2)
 return np.stack([v[:,:,0],92-v[:,:,1],v[:,:,2]-24],axis=2)

def section(v,axis,value,out_axes):
 rows=[]
 for tri in v:
  if tri[:,axis].min()>value or tri[:,axis].max()<value:continue
  pts=[]
  for a,b in zip(tri,np.roll(tri,-1,axis=0)):
   if abs(b[axis]-a[axis])<1e-9:continue
   t=(value-a[axis])/(b[axis]-a[axis])
   if -1e-8<=t<=1+1e-8:
    q=(a+t*(b-a))[list(out_axes)]
    if not any(np.linalg.norm(q-r)<1e-5 for r in pts):pts.append(q)
  if len(pts)==2:rows.append(pts)
 return rows

font='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
f=ImageFont.truetype(font,24);small=ImageFont.truetype(font,21);h=ImageFont.truetype(bold,30)
im=Image.new('RGB',(1600,920),'#eff3f6');dr=ImageDraw.Draw(im)
dr.text((35,20),'0.6 mm PETG fit: sections of the actual print meshes',font=h,fill='#172d40')
blue='#136b9b';gold='#ad6816'
left=native('print/shell-left.stl');right=native('print/shell-right.stl');base=native('print/base-left.stl')

def panel(x,title,rect,layers,arrow,caption):
 w,height=745,700;frame=Image.new('RGB',(w,height),'white');d=ImageDraw.Draw(frame)
 x0,y0,x1,y1=rect;scale=min((w-70)/(x1-x0),(height-120)/(y1-y0))
 def pt(q):return (35+(q[0]-x0)*scale,height-65-(q[1]-y0)*scale)
 for gx in range(int(x0),int(x1)+1):d.line((pt((gx,y0)),pt((gx,y1))),fill='#e3e9ee',width=1)
 for gy in range(int(y0),int(y1)+1):d.line((pt((x0,gy)),pt((x1,gy))),fill='#e3e9ee',width=1)
 for segments,color in layers:
  for a,b in segments:d.line((pt(a),pt(b)),fill=color,width=4)
 a,b=map(pt,arrow);d.line((a,b),fill='#c43240',width=3)
 # Perpendicular end ticks make the designed air gap visible at this scale.
 for q in [a,b]:d.ellipse((q[0]-3,q[1]-3,q[0]+3,q[1]+3),fill='#c43240')
 mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
 d.line((mid,(mid[0]+80,mid[1]-80)),fill='#c43240',width=2)
 d.text((mid[0]+50,mid[1]-112),'0.20 mm',font=f,fill='#b02031')
 im.paste(frame,(x,155));dr.text((x,105),title,font=h,fill='#172d40');dr.rectangle((x,155,x+w,855),outline='#bdcbd6',width=2)
 dr.text((x,865),caption,font=small,fill='#425c70')

floor=np.sqrt(2)*.2;a=np.array([192.6,218.65-floor-192.6]);b=a+np.array([.2/np.sqrt(2)]*2)
panel(35,'Upper sliding hook',[188,20,199,31],[(section(left,1,15,[0,2]),blue),(section(right,1,15,[0,2]),gold)],(a,b),'Blue: left shell. Amber: right receiver. Section Y = 15 mm.')
panel(820,'Base locating rib',[0,-24.6,8,-15],[(section(left,0,60,[1,2]),gold),(section(base,0,60,[1,2]),blue)],([2,-20.8],[2.2,-20.8]),'Blue: removable base. Amber: shell. Section X = 60 mm.')
im.save(P/'snug-fit-sections.png')
report={'revision':'snug_06_tolerances','source':'Exact intersections of current high-resolution STL triangles, mapped back to native millimetres; no mesh alteration','image':'snug-fit-sections.png','image_sha256':hashlib.sha256((P/'snug-fit-sections.png').read_bytes()).hexdigest(),'STL_sha256':{n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['print/shell-left.stl','print/shell-right.stl','print/base-left.stl']},'nominal_clearances_mm':{'inclined_hook_normal':.2,'base_rib_to_wall':.2},'limitations':'Nominal geometry, not measurements of a physical print. The hook panel is cropped; edges outside the view continue into the main walls.'}
(P/'snug-fit-sections.json').write_text(json.dumps(report,indent=2))
print('Rendered current joint and guide mesh sections')
