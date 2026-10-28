"""Topology and orientation audit of exported binary STL; no mesh repair."""
import json, struct
from pathlib import Path
import numpy as np

def read_stl(path):
 data=Path(path).read_bytes(); n=struct.unpack_from('<I',data,80)[0]
 dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
 assert len(data)==84+50*n
 return np.frombuffer(data, dtype=dtype, offset=84,count=n)['v'].astype(float)

def audit(path):
 v=read_stl(path); cross=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]); norm=np.linalg.norm(cross,axis=1); normals=cross/np.maximum(norm[:,None],1e-30)
 verts,idx=np.unique(np.round(v.reshape(-1,3),5),axis=0,return_inverse=True); faces=idx.reshape(-1,3)
 edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]); ordered=np.sort(edges,axis=1)
 _, inv, counts=np.unique(ordered,axis=0,return_inverse=True,return_counts=True)
 signs=np.where(edges[:,0]<edges[:,1],1,-1); balance=np.bincount(inv,weights=signs)
 out={'file':str(path),'triangles':len(v),'bounds_mm':[v.min(axis=(0,1)).tolist(),v.max(axis=(0,1)).tolist()], 'boundary_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum()),'inconsistent_winding_edges':int((balance!=0).sum()),'degenerate_triangles':int((norm<1e-10).sum()),'volume_mm3':float(np.einsum('ij,ij->i',v[:,0],np.cross(v[:,1],v[:,2])).sum()/6),'overhang_surface_mm2':{}}
 for name,up in [('upright',(0,0,1)),('roof_down',(0,0,-1)),('left_end_down',(1,0,0)),('rear_down',(0,-1,0))]:
  up=np.array(up);height=v@up; floor=height.min();mask=(normals@up < -2**-.5)&(height.max(axis=1)>floor+.05)
  out['overhang_surface_mm2'][name]=round(float((norm[mask]/2).sum()),2)
 out['overhang_metric_limit']='Geometric downward area beyond 45 degrees, excluding bed-contact triangles; not slicer support volume, bridge assessment or a print guarantee.'
 return out
if __name__=='__main__':
 import sys
 results=[audit(p) for p in sys.argv[1:]]
 print(json.dumps(results,indent=2))
