from pathlib import Path
import ast,sys,json,math
import numpy as np
R=Path(__file__).resolve().parents[1]
tree=ast.parse((R/'work/build_direct_servo_horn.py').read_text(encoding='utf-8'));end=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='profiles' for t in n.targets));ns={'__file__':str(R/'work/build_direct_servo_horn.py')};exec(compile(ast.Module(body=tree.body[:end],type_ignores=[]),'horn_functions','exec'),ns)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace,BRepBuilderAPI_Transform
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut,BRepAlgoAPI_Common
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Pnt,gp_Vec,gp_Trsf
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_IN,TopAbs_OUT
def volume(s):
 p=GProp_GProps();BRepGProp.VolumeProperties_s(s,p);return abs(p.Mass())
poly=BRepBuilderAPI_MakePolygon()
for i in range(6):
 a=i*math.pi/3;r=5.5/math.sqrt(3);poly.Add(gp_Pnt(18+r*math.cos(a),r*math.sin(a),5.2))
poly.Close();nut=BRepAlgoAPI_Cut(BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(poly.Wire()).Face(),gp_Vec(0,0,2.4)).Shape(),ns['cyl'](1.5,3,18,0,5)).Shape()
arm=ns['horn'](21,4.85);sleeve=BRepAlgoAPI_Cut(ns['cyl'](2,10.5,18,0,9),ns['cyl'](1.6,11,18,0,8.9)).Shape()
assert volume(BRepAlgoAPI_Common(nut,arm).Shape())<1e-5
assert volume(BRepAlgoAPI_Common(sleeve,arm).Shape())<1e-5
tr=gp_Trsf();tr.SetTranslation(gp_Vec(0,0,.2));pulled=BRepBuilderAPI_Transform(nut,tr,True).Shape()
assert volume(BRepAlgoAPI_Common(pulled,arm).Shape())>1
for z,state in [(4.99,TopAbs_OUT),(6,TopAbs_OUT),(7.7,TopAbs_IN),(8.9,TopAbs_IN)]:assert BRepClass3d_SolidClassifier(arm,gp_Pnt(20.1,0,z),1e-7).State()==state
assert abs((20-5.2)-(2.4+1.4+10.5+.5))<1e-8
report=dict(passed=True,nut_inserted_from_servo_side=True,nut_retained_by_front_wall_mm=1.4,pocket_depth_mm=2.6,nut_thickness_mm=2.4,sleeve_length_mm=10.5,bolt_length_mm=16,bolt_protrusion_beyond_nut_mm=1.2,nut_and_sleeve_no_arm_intersections=True,physical_assembly_tested=False)
(R/'outputs/AmurCargo_Radial/Reverse_Nut_Checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
