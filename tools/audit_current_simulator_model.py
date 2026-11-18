from pathlib import Path
import sys,json,base64,gzip,re,ast,math
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/cadlibs'))
import trimesh
from OCP.STEPControl import STEPControl_Reader
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common,BRepAlgoAPI_Cut
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Trsf,gp_Ax2,gp_Pnt,gp_Dir
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
O=R/'simulator';S=R/'mechanics'
source=json.loads((S/'assembly_data.json').read_text(encoding='utf-8'));forks=json.loads((O/'Fork_Adaptation_Meshes.json').read_text(encoding='utf-8'));horn=json.loads((O/'Servo_Horn_Mesh.json').read_text(encoding='utf-8'))
raw=[forks[0] if p['name']=='Fork_pair' else horn if p['name']=='SG90_original_horn' else p for p in source['items'] if p['name'] not in ('User_Motor_0','User_Motor.001_0','Crank_R18','Crank_horn_M1_4x6_7','Crank_horn_M1_4x6_13')]+forks[1:]
link=json.loads((O/'Servo_Link_Meshes.json').read_text(encoding='utf-8'));replacement={'Drive_pin_nut_M3':link[0],'Drive_pin_sleeve_4x3_2x11':link[1]};raw=[replacement.get(p['name'],p) for p in raw]
page=(O/'Open_Simulation_3D.html').read_text(encoding='utf-8');packed=re.search(r"createRadial3D\(canvas,board,'([^']+)'",page).group(1);embedded=json.loads(gzip.decompress(base64.b64decode(packed)))['items'];byname={p['name']:p for p in raw};assert len(raw)==len(embedded)==len(byname)
for p in embedded:
 expected=np.frombuffer(base64.b64decode(byname[p['name']]['vertices']),dtype='<f4').reshape(-1,3);actual=np.frombuffer(base64.b64decode(p['vertices']),dtype='<i2').reshape(-1,3)
 assert set(map(tuple,np.round(expected.astype(np.float64)*20).astype(np.int64)))==set(map(tuple,actual)),p['name']
assert 'SG90_original_horn' not in {p['name'] for p in embedded};assert 'SG90_integrated_crank_R18' in byname;assert 'Fork_pair' not in byname
def rawmesh(p):return trimesh.Trimesh(np.frombuffer(base64.b64decode(p['vertices']),dtype='<f4').reshape(-1,3),np.frombuffer(base64.b64decode(p['indices']),dtype='<u4').reshape(-1,3),process=False)
mapping={'Mast':'02_Mast','Carriage':'03_Carriage','SG90_mount_plate':'04_SG90_Bolted_Bracket','Sensor_bar':'06_LDR_Trial_Bar','Electronics_tray':'09_Upper_Tray','Cargo_feeler':'11_Cargo_Feeler','Caster_spacer':'12_Caster_Spacer','Electronics_carrier':'15_Electronics_Carrier','UNO_edge_clip':'19_UNO_Edge_Clip',**{f'Carrier_riser_{i}':'18_Carrier_Riser' for i in range(4)}}
matches=[]
for name,stem in mapping.items():
 a=rawmesh(byname[name]);b=trimesh.load(S/'Print_Ready'/(stem+'.stl'),force='mesh')
 if name=='Crank_R18':
  phase=math.radians(70);rotation=np.array([[math.cos(phase),-math.sin(phase),0],[0,0,1],[-math.sin(phase),-math.cos(phase),0]]);a.vertices=a.vertices@rotation
 dv=abs(abs(a.volume)-abs(b.volume))/max(abs(b.volume),1);dd=max(abs(np.sort(a.extents)-np.sort(b.extents)));assert dv<.001 and dd<.02,(name,dv,dd);matches.append(dict(name=name,stl=stem+'.stl',relative_volume_error=float(dv),max_dimension_error_mm=float(dd)))
for name,filename in [('Fork_spine_removable','01_Removable_Fork_Spine'),('Fork_arm_Left_low','02_Fork_Arm_Left'),('Fork_arm_Right_low','02_Fork_Arm_Right'),('Fork_arm_Left_high','02_Fork_Arm_Left'),('Fork_arm_Right_high','02_Fork_Arm_Right'),('Cargo_button_spacer_Left','03_Cargo_Button_Spacer'),('Cargo_button_spacer_Right','03_Cargo_Button_Spacer'),('SG90_integrated_crank_R18','SG90_Integrated_R18_21T_Fit2')]:
 a=rawmesh(byname[name]);b=trimesh.load(O/('Servo_Horn' if name=='SG90_integrated_crank_R18' else 'Fork_Adapters')/(filename+('' if name=='SG90_integrated_crank_R18' else '_Print_Orientation')+'.stl'),force='mesh')
 if name=='SG90_integrated_crank_R18':
  phase=math.radians(70);rotation=np.array([[math.cos(phase),-math.sin(phase),0],[0,0,1],[-math.sin(phase),-math.cos(phase),0]]);a.vertices=a.vertices@rotation
 dv=abs(abs(a.volume)-abs(b.volume))/max(abs(b.volume),1);dd=max(abs(np.sort(a.extents)-np.sort(b.extents)));assert dv<.001 and dd<.02,(name,dv,dd);matches.append(dict(name=name,stl=filename+'.stl',relative_volume_error=float(dv),max_dimension_error_mm=float(dd)))
def read(path):
 r=STEPControl_Reader();assert r.ReadFile(str(path))==1;r.TransferRoots();return r.OneShape()
def tf(shape,m):
 t=gp_Trsf();t.SetValues(*m[:3].reshape(-1));return BRepBuilderAPI_Transform(shape,t,True).Shape()
def T(x=0,y=0,z=0):m=np.eye(4);m[:3,3]=[x,y,z];return m
def RX(a):a=math.radians(a);m=np.eye(4);m[1:3,1:3]=[[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]];return m
def RY(a):a=math.radians(a);m=np.eye(4);m[0,0]=m[2,2]=math.cos(a);m[0,2]=math.sin(a);m[2,0]=-math.sin(a);return m
def RZ(a):a=math.radians(a);m=np.eye(4);m[:2,:2]=[[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]];return m
def volume(s):p=GProp_GProps();BRepGProp.VolumeProperties_s(s,p);return abs(p.Mass())
# Build the same horn CAD from our generator functions, without exporting files again.
tree=ast.parse((R/'tools/build_direct_servo_horn.py').read_text(encoding='utf-8'));end=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='profiles' for t in n.targets));ns={'__file__':str(R/'tools/build_direct_servo_horn.py')};exec(compile(ast.Module(body=tree.body[:end],type_ignores=[]),'horn_functions','exec'),ns)
direct=tf(ns['horn'](21,4.85),T(-12,99,93)@RX(-90)@RZ(70));servo=tf(read(S/'Downloaded_Models/SG90.step'),T(-12,71.1,109.6)@RX(-90))
# The schematic servo shaft is a smooth cylinder: overlap inside its spline zone is expected.
shaft_zone=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(-12,97.5,93),gp_Dir(0,1,0)),2.65,5.5).Shape()
def mounted(stem,name):
 shape=read(S/'Print_Parts'/(stem+'.step'));b=Bnd_Box();BRepBndLib.AddOptimal_s(shape,b,False,False);p=b.CornerMin();offset=rawmesh(byname[name]).bounds[0]-np.array([p.X(),p.Y(),p.Z()]);return tf(shape,T(*offset))
mast=mounted('02_Mast','Mast');carriage=mounted('03_Carriage','Carriage');spine=tf(read(O/'Fork_Adapters/01_Removable_Fork_Spine.step'),T(0,118,2))
sweep=[]
for angle in range(20,141,10):
 pose=T(-12,101,93)@RY(20-angle)@T(12,-101,-93);h=tf(direct,pose)
 body_overlap=volume(BRepAlgoAPI_Cut(BRepAlgoAPI_Common(h,servo).Shape(),shaft_zone).Shape());assert body_overlap<1e-4,(angle,body_overlap)
 lift=18*(math.cos(math.radians(20))-math.cos(math.radians(angle)));others={}
 for name,shape in [('mast',mast),('carriage',tf(carriage,T(0,0,lift))),('spine',tf(spine,T(0,0,lift)))]:
  amount=volume(BRepAlgoAPI_Common(h,shape).Shape());assert amount<1e-4,(angle,name,amount);others[name]=amount
 sweep.append(dict(angle=angle,integrated_horn_and_crank=True,horn_servo_body_overlap_mm3=body_overlap,other_intersections_mm3=others))
report=dict(passed=True,embedded_parts_checked=len(embedded),all_embedded_parts_match_current_sources=True,quantization_step_mm=.05,old_fork_and_factory_horn_absent=True,printed_part_matches=matches,horn_sweep=sweep,shaft_axis_coaxial=True,limitations=['Spline profile is provisional; physical fit must be tested','UNO and L298N are reference purchased-part geometries; selecting Nano changes flashing, not mounting geometry','Load capacity, friction and thread strength are not verified'])
(O/'Current_Model_Audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ('printed_part_matches','horn_sweep','limitations')}))
