import bpy,json,base64,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
raw=[]
for obj in bpy.context.scene.objects:
 if obj.type!='MESH':continue
 mesh=obj.data;v=np.empty((len(mesh.vertices),3),dtype=np.float32);mesh.vertices.foreach_get('co',v.ravel())
 m=np.array(obj.matrix_world,dtype=float);v=v@m[:3,:3].T+m[:3,3]
 mesh.calc_loop_triangles();f=np.empty((len(mesh.loop_triangles),3),dtype=np.int32);mesh.loop_triangles.foreach_get('vertices',f.ravel())
 if np.linalg.det(m[:3,:3])<0:f=f[:,[0,2,1]]
 raw.append((obj.name,v,f))
allv=np.concatenate([v for n,v,f in raw]);ground=allv[:,2].min();cx=(allv[:,0].min()+allv[:,0].max())/2
motor=[x for x in raw if x[0].startswith('Motor')];cy=[];cz=[]
for n,v,f in motor:
 zmax=v[:,2].max();zmin=v[:,2].min();cy.append(float(np.median(v[v[:,2]>zmax-.02,1])));cz.append((zmax+zmin)/2)
axis_y=float(np.mean(cy));offset=np.array([cx,35+axis_y,-ground])
caster_shift=0
rotation=np.diag([-1.,-1.,1.]);payload=[];report=[]
for name,v,f in raw:
 w=v@rotation.T+offset;face_centers=v[f].mean(1)
 if name=='Caster':
  caster_shift=-float(w[:,2].min());w[:,2]+=caster_shift
 if name.startswith('Motor'):
  left=float(v[:,0].mean())<0;threshold=-55 if left else 51
  outside=face_centers[:,0]<threshold if left else face_centers[:,0]>threshold
  rad=np.sqrt((face_centers[:,1]-axis_y)**2+(face_centers[:,2]-float(np.mean(cz)))**2)
  assignments=np.where(outside,np.where(rad>20,0,1),np.where(face_centers[:,1]>-10,2,1))
  colors=['#242b30','#e3b83e','#a8b0b7']
 else:assignments=np.zeros(len(f),dtype=np.int32);colors=['#d5ab5a' if name.startswith('Robot') else '#9da8b0']
 for label in sorted(set(assignments)):
  ff=f[assignments==label];used,inv=np.unique(ff,return_inverse=True);verts=w[used].astype('<f4');faces=inv.reshape(-1,3).astype('<u4')
  payload.append(dict(name='User_'+name+'_'+str(label),source_object=name,color=colors[label],vertices=base64.b64encode(verts.tobytes()).decode(),indices=base64.b64encode(faces.tobytes()).decode()))
 report.append(dict(name=name,bounds=[w.min(0).tolist(),w.max(0).tolist()],dimensions=(w.max(0)-w.min(0)).tolist(),triangles=len(f)))
 if name.startswith('Robot') or name=='Caster':
  front=w[(w[:,1]>95)&(w[:,2]<35)]
  print('FRAME FRONT LOW',front.min(0) if len(front) else None,front.max(0) if len(front) else None,flush=True)
  normals=np.cross(w[f[:,1]]-w[f[:,0]],w[f[:,2]]-w[f[:,0]]);areas=np.linalg.norm(normals,axis=1)/2
  horizontal=np.abs(normals[:,2])>1.98*areas
  zs=np.round(w[f].mean(1)[:,2],2);levels={}
  for zz,aa in zip(zs[horizontal],areas[horizontal]):levels[float(zz)]=levels.get(float(zz),0)+float(aa)
  print(name,'PLATE LEVELS',sorted(levels.items(),key=lambda x:x[1],reverse=True)[:8],flush=True)
world=allv@rotation.T+offset
result=dict(source_units='scene METRIC, scale_length=0.001: coordinates are millimetres',rigid_rotation_degrees=180,translation=offset.tolist(),caster_vertical_correction_mm=caster_shift,wheel_axis_y=35,wheel_axis_z=float(np.mean(cz)-ground),raw_wheel_axis_y=axis_y,raw_ground=ground,raw_center_x=cx,bounds=[world.min(0).tolist(),world.max(0).tolist()],dimensions=(world.max(0)-world.min(0)).tolist(),objects=report,items=payload)
(ROOT/'mechanics/user_base_payload.json').write_text(json.dumps(result,separators=(',',':')),encoding='utf-8')
(ROOT/'tools/user_base_summary.json').write_text(json.dumps({k:v for k,v in result.items() if k!='items'},ensure_ascii=False,indent=2),encoding='utf-8')
print('USER BASE SUMMARY', {k:v for k,v in result.items() if k not in ['objects','items']},flush=True)
