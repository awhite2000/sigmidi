"""Plot an exact STL section through a revised display mounting tower."""
from pathlib import Path
import numpy as np,struct,json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent
path=P/'print/base-right.stl';data=path.read_bytes();n=struct.unpack_from('<I',data,80)[0]
dt=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]);v=np.frombuffer(data,dtype=dt,offset=84,count=n)['v'].astype(float)
v=np.stack([193.9+v[:,:,0],92-v[:,:,1],v[:,:,2]-24],axis=2)
x=291.50219;y=49.83437+.0001;segments=[]
for tri in v:
 if tri[:,1].min()>y or tri[:,1].max()<y:continue
 pts=[]
 for a,b in zip(tri,np.roll(tri,-1,axis=0)):
  if abs(b[1]-a[1])<1e-9:continue
  t=(y-a[1])/(b[1]-a[1])
  if -1e-8<=t<=1+1e-8:
   q=(a+t*(b-a))[[0,2]];q[0]-=x
   if not any(np.linalg.norm(q-r)<1e-5 for r in pts):pts.append(q)
 if len(pts)==2:segments.append(pts)
im=Image.new('RGB',(1250,1020),'#f2f5f8');d=ImageDraw.Draw(im)
font='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def txt(pos,s,size=23,b=False,color='#19354b'):d.text(pos,s,font=ImageFont.truetype(bold if b else font,size),fill=color)
S=31;ox=330;oy=125
# plot Z -1 .. -25; axis downwards
def pt(q):return (ox+S*q[0],oy+S*(-q[1]-1))
def line(a,b,color='#196b92',w=3):d.line((pt(a),pt(b)),fill=color,width=w)
def poly(coords,fill,outline):d.polygon([pt(q) for q in coords],fill=fill,outline=outline,width=2)
txt((35,22),'Display mounting: M2 × 5 mm',34,True)
txt((35,69),'Actual STL section through one hollow tower; dimensions in mm',22)
for z in range(-24,-1,2):
 line((-5.5,z),(5.5,z),'#d7e0e8',1);txt((100,pt((0,z))[1]-10),str(z),18)
# The polygon represents the nominal screw envelope, not a thread rendering.
poly([(-1.9,-9.51),(1.9,-9.51),(1,-8.61),(1,-4.51),(-1,-4.51),(-1,-8.61)],'#e5ae54','#966019')
# Factory stud seating surface and blind bore, schematic envelope.
poly([(-2.4,-5.9),(-1,-5.9),(-1,-2.9),(1,-2.9),(1,-5.9),(2.4,-5.9),(2.4,-1.8),(-2.4,-1.8)],'#bfccd7','#687d8e')
# exact mesh outlines, clipped to plotted region
for a,b in segments:
 if max(a[0],b[0])<-5.5 or min(a[0],b[0])>5.5:continue
 aa=a.copy();bb=b.copy()
 if abs(bb[0]-aa[0])>1e-9:
  lo=max(0,min((-5.5-aa[0])/(bb[0]-aa[0]),(5.5-aa[0])/(bb[0]-aa[0])))
  hi=min(1,max((-5.5-aa[0])/(bb[0]-aa[0]),(5.5-aa[0])/(bb[0]-aa[0])))
  if hi<lo:continue
  aa=a+lo*(b-a);bb=a+hi*(b-a)
 line(aa,bb)
def callout(z,text,yy):
 a=pt((2.3,z));d.line((a,(565,yy+14),(610,yy+14)),fill='#738a9d',width=2);txt((625,yy),text)
callout(-4.51,'Screw tip Z −4.51',170)
callout(-5.9,'Factory stud rests at Z −5.90',235)
callout(-9.51,'Head seat Z −9.51  (+1.00)',345)
callout(-16,'Tower wall ≥ 2.00',535)
callout(-24,'Outside floor Z −24.00',810)
txt((625,405),'5.00 screw length, including head',23,True)
txt((625,450),'1.39 nominal thread engagement',23)
txt((625,485),'1.61 clearance to blind-hole end',23)
txt((625,595),'Access Ø4.40   /   shaft bore Ø2.60',22)
txt((625,635),'Display glass remains flush at Z 0',22)
txt((625,685),'Blue: exact printed post section',21,color='#196b92')
txt((625,720),'Amber / grey: nominal screw / stud',21,color='#687d8e')
txt((35,920),'Main and modular electronics bases share the same revised mount.',24,True)
txt((35,960),'The encoder-adjacent tower retains its clearance flat. Base screws remain M2 × 6.',21)
im.save(P/'display-m2x5-section.png')
r={'revision':'display_m2x5','image':'display-m2x5-section.png','image_sha256':hashlib.sha256((P/'display-m2x5-section.png').read_bytes()).hexdigest(),'STL_sha256':hashlib.sha256(data).hexdigest(),'section_XY_mm':[x,y],'source':'Exact STL triangle intersections; nominal screw and factory stud envelope overlaid for explanation, no rendered thread detail.'}
(P/'display-m2x5-section.json').write_text(json.dumps(r,indent=2));print('Rendered M2x5 section')
