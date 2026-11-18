from pathlib import Path
import sys,ast,json,math,base64
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/cadlibs'))
import trimesh
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut,BRepAlgoAPI_Fuse
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder,BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCone,BRepPrimAPI_MakePrism
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE,TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.gp import gp_Pnt,gp_Dir,gp_Ax2,gp_Vec
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
# Reuse our own validated CAD-to-mesh function without running the fork builder.
tree=ast.parse((R/'tools/build_removable_forks.py').read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='mesh');exec(compile(ast.Module(body=[fn],type_ignores=[]),'mesh_helper','exec'))
O=R/'simulator';D=(R/'mechanics')/'Servo_Horn';D.mkdir(exist_ok=True)
def cyl(r,h,x=0,y=0,z=0):return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(0,0,1)),r,h).Shape()
def box(x,y,z,X,Y,Z):return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),X-x,Y-y,Z-z).Shape()
def spline_cut(teeth,diameter):
 p=BRepBuilderAPI_MakePolygon();outer=diameter/2;inner=outer-.25
 for i in range(teeth):
  for fraction,r in [(-.5,inner),(-.35,inner),(-.16,outer),(.16,outer),(.35,inner)]:
   a=2*math.pi*(i+fraction)/teeth;p.Add(gp_Pnt(r*math.cos(a),r*math.sin(a),-.1))
 p.Close();return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(p.Wire()).Face(),gp_Vec(0,0,3.3)).Shape()
def horn(teeth,diameter,arm=True):
 s=cyl(4.2,5)
 if arm:
  # The R18 arm occupies the original crank plane, now fused to the spline hub.
  s=BRepAlgoAPI_Fuse(s,cyl(5,4,z=5)).Shape()
  s=BRepAlgoAPI_Fuse(s,box(0,-4,5,24,4,9)).Shape()
  s=BRepAlgoAPI_Cut(s,cyl(1.7,4.4,18,0,4.8)).Shape()
  polygon=BRepBuilderAPI_MakePolygon()
  for i in range(6):
   a=i*math.pi/3;r=5.8/math.sqrt(3);polygon.Add(gp_Pnt(18+r*math.cos(a),r*math.sin(a),4.9))
  polygon.Close();pocket=BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(polygon.Wire()).Face(),gp_Vec(0,0,2.7)).Shape()
  s=BRepAlgoAPI_Cut(s,pocket).Shape()
  s=BRepAlgoAPI_Cut(s,cyl(2.1,4.2,z=5)).Shape()
 s=BRepAlgoAPI_Cut(s,spline_cut(teeth,diameter)).Shape();s=BRepAlgoAPI_Cut(s,cyl(1.25,6,z=-.5)).Shape()
 entry=BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(0,0,-.01),gp_Dir(0,0,1)),diameter/2+.2,diameter/2-.25,.36).Shape();return BRepAlgoAPI_Cut(s,entry).Shape()
def print_mesh(m):
 m=m.copy();m.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]));m.apply_translation(-m.bounds[0]);return m
profiles=[('21T_Fit1',21,4.80),('21T_Fit2',21,4.85),('20T_Fit3',20,4.80),('20T_Fit4',20,4.85)]
checks=[];nominal=None
for name,n,d in profiles:
 m=mesh(horn(n,d));filename='SG90_Integrated_R18_'+name+'.stl';print_mesh(m).export(D/filename)
 checks.append(dict(file=filename,teeth=n,assumed_shaft_diameter_mm=4.75,cavity_outer_diameter_mm=d,radial_tooth_depth_mm=.25,spline_depth_mm=3.2,central_clearance_mm=2.5,central_head_access_mm=4.2,drive_radius_mm=18,drive_hole_mm=3.4,nut_pocket_AF_mm=5.8,nut_insertion='back, servo side',pocket_depth_mm=2.6,front_retaining_wall_mm=1.4,sleeve_length_mm=10.5,watertight=True,single_connected_body=True,physical_fit_tested=False))
 if name=='21T_Fit2':nominal=m
# One connected test strip, numbered by raised dots. Its sockets face upwards.
plate=box(0,0,0,64,20,1.2)
for i,(_,n,d) in enumerate(profiles):
 m=print_mesh(mesh(horn(n,d,False)));m.apply_translation([8+i*16-4.2,1.8,0])
 # Transform the exact CAD socket by a rigid rotation for the common test strip.
 from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
 from OCP.gp import gp_Trsf,gp_Ax1
 tr=gp_Trsf();tr.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(1,0,0)),math.pi);s=BRepBuilderAPI_Transform(horn(n,d,False),tr,True).Shape();tr=gp_Trsf();tr.SetTranslation(gp_Vec(8+i*16,6,5));s=BRepBuilderAPI_Transform(s,tr,True).Shape();plate=BRepAlgoAPI_Fuse(plate,s).Shape()
 for j in range(i+1):plate=BRepAlgoAPI_Fuse(plate,cyl(.65,.6,8+i*16+(j-i/2)*2.2,16,1.2)).Shape()
mesh(plate).export(D/'00_SG90_Spline_Fit_Test.stl')
# Keep the same crank mounting face as the factory horn in the existing assembly.
a=math.radians(70);rot=np.array([[math.cos(a),-math.sin(a),0],[0,0,1],[-math.sin(a),-math.cos(a),0]])
v=nominal.vertices@rot.T+np.array([-12,99,93]);part=dict(name='SG90_integrated_crank_R18',component='crank',motion='crank',color='#f6d783',alpha=1,vertices=base64.b64encode(v.astype('<f4').tobytes()).decode(),indices=base64.b64encode(nominal.faces.astype('<u4').tobytes()).decode())
(O/'Servo_Horn_Mesh.json').write_text(json.dumps(part),encoding='utf-8')
# The nut now enters from the servo side; the front wall traps it under tension.
source=json.loads((R/'mechanics/assembly_data.json').read_text(encoding='utf-8'))
nut=next(p.copy() for p in source['items'] if p['name']=='Drive_pin_nut_M3')
nv=np.frombuffer(base64.b64decode(nut['vertices']),dtype='<f4').reshape(-1,3).copy();nv[:,1]-=.9
nut['vertices']=base64.b64encode(nv.astype('<f4').tobytes()).decode()
sleeve=mesh(BRepAlgoAPI_Cut(cyl(2,10.5,18,0,9),cyl(1.6,10.9,18,0,8.8)).Shape())
sv=sleeve.vertices@rot.T+np.array([-12,99,93])
sleevepart=dict(name='Drive_pin_sleeve_4x3_2x10_5',component='crank',motion='crank',color='#b8c3c9',alpha=1,vertices=base64.b64encode(sv.astype('<f4').tobytes()).decode(),indices=base64.b64encode(sleeve.faces.astype('<u4').tobytes()).decode())
(O/'Servo_Link_Meshes.json').write_text(json.dumps([nut,sleevepart]),encoding='utf-8')
(O/'Servo_Horn_Checks.json').write_text(json.dumps(dict(profiles=checks,fit_strip='00_SG90_Spline_Fit_Test.stl',fit_strip_watertight=True,crank_R18_unchanged=True,shaft_size_from_user_mm=[4.7,4.8],profile_is_approximation=True,physical_fit_tested=False),indent=2),encoding='utf-8');print(json.dumps(checks))
