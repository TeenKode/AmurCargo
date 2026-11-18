from pathlib import Path
import sys,io,contextlib,json,math,ast
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/cadlibs'))
import trimesh
from OCP.STEPControl import STEPControl_Reader
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common,BRepAlgoAPI_Cut,BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Pnt,gp_Ax2,gp_Dir,gp_Trsf
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
O=R/'simulator'
def read(p):
 r=STEPControl_Reader();assert r.ReadFile(str(p))==1;r.TransferRoots();return r.OneShape()
def tf(s,m):
 t=gp_Trsf();t.SetValues(*m[:3].ravel());return BRepBuilderAPI_Transform(s,t,True).Shape()
def T(x=0,y=0,z=0):m=np.eye(4);m[:3,3]=[x,y,z];return m
def RZ(a):m=np.eye(4);m[:2,:2]=[[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]];return m
def RY(a):m=np.eye(4);m[0,0]=m[2,2]=math.cos(a);m[0,2]=math.sin(a);m[2,0]=-math.sin(a);return m
def vol(s):p=GProp_GProps();BRepGProp.VolumeProperties_s(s,p);return abs(p.Mass())
def bounds(s):b=Bnd_Box();BRepBndLib.AddOptimal_s(s,b,False,False);p,q=b.CornerMin(),b.CornerMax();return np.array([[p.X(),p.Y(),p.Z()],[q.X(),q.Y(),q.Z()]])
def could_touch(a,b):return np.all(a[1]>=b[0]) and np.all(b[1]>=a[0])
def overlap(a,b):
 if not could_touch(bounds(a),bounds(b)):return 0
 return vol(BRepAlgoAPI_Common(a,b).Shape())
paths=list((R/'mechanics/Print_Ready').glob('*.stl'))
paths=[p for p in paths if p.name not in ('01_Fork_Pair_TipStops.stl','05_Crank_R18_Trial.stl')]
paths+=list((O/'Fork_Adapters').glob('*_Print_Orientation.stl'))+list((O/'Servo_Horn').glob('SG90_Integrated_R18_*.stl'))+[O/'Servo_Horn/00_SG90_Spline_Fit_Test.stl']
mesh_checks=[]
for p in paths:
 m=trimesh.load(p,force='mesh');assert m.is_watertight and m.is_winding_consistent and m.volume>0,p
 parents=list(range(len(m.vertices)))
 def find(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 for a,b in m.edges_unique:parents[find(int(a))]=find(int(b))
 assert len({find(i) for i in range(len(parents))})==1,p
 assert abs(m.bounds[0,2])<.001,p
 mesh_checks.append(dict(file=str(p.relative_to(R)),volume_mm3=float(m.volume),connected=True,on_print_bed=True))
# Re-evaluate all original structural joint contacts from their CAD definitions.
# Stop before assembly exports, so no older model replaces the current one.
source=(R/'tools/build_photo.py').read_text(encoding='utf-8').split('# STEP exports with names and colour')[0]
ns={'__file__':str(R/'tools/build_photo.py')}
with contextlib.redirect_stdout(io.StringIO()):exec(compile(source,'base_mechanics','exec'),ns)
contacts=ns['joint_rows'];assert all(c['gap_mm']<.011 for c in contacts)
spine=read(O/'Fork_Adapters/01_Removable_Fork_Spine.step');arms=[read(O/'Fork_Adapters'/('02_Fork_Arm_'+side+'.step')) for side in ('Left','Right')]
primary=['Mast','SG90','SG90_mount_plate','Sensor_bar','Electronics_carrier','Electronics_tray']
statics={p['name']:p['shape'] for p in ns['items'] if p['name'] in primary}
local_parts={p['name']:p['shape'] for p in ns['items'] if p['name'] in ['Carriage','Cargo_button','Cargo_switch_PCB','Cargo_feeler'] or p['name'].startswith(('Fork_screw_','Cargo_switch_M3','Cargo_switch_nut','Feeler_anchor_','Drive_pin_'))}
native_spine=tf(spine,T(0,118,2));local_fit=[]
for name,shape in local_parts.items():
 amount=overlap(native_spine,shape);assert amount<1e-4,('local fit',name,amount);local_fit.append(name)
# This guard must fail if the switch passage is accidentally filled again.
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_OUT
for x in (-4.4,0,4.4):
 for z in (12.1,16,19.9):assert BRepClass3d_SolidClassifier(spine,gp_Pnt(x,2,z),1e-7).State()==TopAbs_OUT
checks=0
for lift in np.linspace(0,30.703,32):
 for s in [spine,*arms]:
  moving=tf(s,T(0,118,2+lift))
  for name,static in statics.items():
   amount=overlap(moving,static);assert amount<1e-4,(lift,name,amount);checks+=1
# Cargo at the exact poses produced by the common C++ navigation core.
def box(a,b):return BRepPrimAPI_MakeBox(gp_Pnt(*a),*(np.array(b)-np.array(a))).Shape()
def cyl(r,length,x):return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,0,0),gp_Dir(1,0,0)),r,length).Shape()
cargo=box((-35,-20,-20),(-20,20,20))
for p in [box((20,-20,-20),(35,20,20)),cyl(8,40,-20),cyl(9,1,-20),cyl(9,1,19)]:cargo=BRepAlgoAPI_Fuse(cargo,p).Shape()
cargo_tests=0
for sample in json.loads((O/'Pickup_Geometry_Samples.json').read_text(encoding='utf-8')):
 vertical=sample['pose']=='vertical';dz=26 if vertical else 0;slack=23 if vertical else 6
 for lift in (0,6,15,23,30.703):
  c=tf(cargo,T(-sample['left'],35.1785+sample['forward'],(35 if vertical else 20)+max(0,lift-slack))@RZ(sample['angle'])@RY(math.pi/2 if vertical else 0))
  for name,s in [('spine',spine),('left',arms[0]),('right',arms[1])]:
   m=tf(s,T(0,118,2+lift+(dz if name!='spine' else 0)));amount=overlap(m,c)
   assert amount<.01,(sample,lift,name,amount);cargo_tests+=1
report=dict(passed=True,printed_meshes=mesh_checks,base_structural_contacts=len(contacts),local_switch_feeler_and_fastener_fit=local_fit,button_passage_verified=True,moving_static_checks=checks,cargo_collision_checks=cargo_tests,physical_load_strength_tested=False,source_meshes_of_bought_components_are_reference_models=True)
(O/'Full_Mechanical_Audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='printed_meshes'}))
