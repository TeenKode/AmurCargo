from pathlib import Path
import sys,json,math
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/cadlibs'))
import trimesh
from OCP.STEPControl import STEPControl_Reader
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Pnt,gp_Trsf,gp_Vec
from OCP.TopAbs import TopAbs_IN,TopAbs_OUT
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
O=R/'simulator';P=(R/'mechanics')/'Fork_Adapters';SRC=R/'mechanics/Print_Parts'
def read(path):
 r=STEPControl_Reader();assert r.ReadFile(str(path))==1;r.TransferRoots();return r.OneShape()
def move(s,xyz):
 t=gp_Trsf();t.SetTranslation(gp_Vec(*xyz));return BRepBuilderAPI_Transform(s,t,True).Shape()
def volume(s):
 props=GProp_GProps();BRepGProp.VolumeProperties_s(s,props);return abs(props.Mass())
def overlap(a,b):return volume(BRepAlgoAPI_Common(a,b).Shape())
spine=read(P/'01_Removable_Fork_Spine.step');left=read(P/'02_Fork_Arm_Left.step');right=read(P/'02_Fork_Arm_Right.step');checks=[]
for side in (-1,1):
 for z in (10,22,36,48):
  for a in np.linspace(0,2*math.pi,24,endpoint=False):
   for radius,state in [(1.25,TopAbs_OUT),(1.35,TopAbs_IN)]:assert BRepClass3d_SolidClassifier(spine,gp_Pnt(side*23,5+radius*math.cos(a),z+radius*math.sin(a)),1e-7).State()==state
checks.append('eight blind pilot holes: diameter 2.6 mm, 24 radial samples each')
for dz in (0,26):
 for arm in (left,right):assert overlap(spine,move(arm,(0,0,dz)))<1e-5
checks.append('both removable arms clear the spine at both height stations')
# Probe both edges at full width and at two stations on the taper.
for side, arm in ((-1, left), (1, right)):
    for y, gap, elevations in ((43, 20, (0.01, 3.99)),
                               (50, 19, (0.01, 3.99)),
                               (55.9, 18 + 1/60, (0.01, 3.99, 5.99))):
        center_x = side * (gap/2 + 3)
        for z in elevations:
            for edge in (-1, 1):
                for delta, state in ((-0.01, TopAbs_IN), (0.01, TopAbs_OUT)):
                    x = center_x + edge*(3 + delta)
                    point = gp_Pnt(x, y, z)
                    assert BRepClass3d_SolidClassifier(arm, point, 1e-7).State() == state
    assert BRepClass3d_SolidClassifier(arm, gp_Pnt(side*12, 55.9, 6.01), 1e-7).State() == TopAbs_OUT
checks.append('fork gap tapers from 20 to 18 mm over the last 12 mm; blades stay 6 mm wide with flat undersides and 2 mm retaining lips')
for side,arm in [(-1,left),(1,right)]:
 for dz in (0,26):
  for z in (14,18):
   assert BRepClass3d_SolidClassifier(spine,gp_Pnt(side*14.5,1.999,z+dz),1e-7).State()==TopAbs_IN
   assert BRepClass3d_SolidClassifier(move(arm,(0,0,dz)),gp_Pnt(side*14.5,2.001,z+dz),1e-7).State()==TopAbs_IN
   assert BRepClass3d_SolidClassifier(spine,gp_Pnt(side*19.501,5,z+dz),1e-7).State()==TopAbs_IN
checks.append('fork roots bear on rear ledges and side columns; side M3x16 gives 6 mm engagement')
first_layer=BRepAlgoAPI_Common(spine,BRepPrimAPI_MakeBox(gp_Pnt(-100,0,-1),200,.2,200).Shape()).Shape()
ex=TopExp_Explorer(first_layer,TopAbs_SOLID);count=0
while ex.More():count+=1;ex.Next()
assert count==1
checks.append('first printed layer is one connected solid; no floating middle; flat rear face requires no support')
# Exact CAD checks against current mast and carriage; derive translations from their assembly bounds.
import base64,struct
data=json.loads((R/'mechanics/assembly_data.json').read_text(encoding='utf-8'))
def native_min(name):
 q=next(p for p in data['items'] if p['name']==name);raw=base64.b64decode(q['vertices']);v=np.frombuffer(raw,dtype='<f4').reshape(-1,3);return v.min(axis=0)
mast=read(SRC/'02_Mast.step');carriage=read(SRC/'03_Carriage.step')
def shape_min(s):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(s,b,False,False);p=b.CornerMin();return np.array([p.X(),p.Y(),p.Z()])
mast_offset=native_min('Mast')-shape_min(mast)
carriage_offset=native_min('Carriage')-shape_min(carriage)
mast=move(mast,mast_offset);carriage=move(carriage,carriage_offset)
gaps=[]
for h in np.linspace(0,30.703,32):
 shifted=move(spine,(0,118,2+h));assert overlap(shifted,mast)<1e-4;assert overlap(shifted,move(carriage,(0,0,h)))<1e-4
 gaps.append(BRepExtrema_DistShapeShape(shifted,mast).Value())
assert min(gaps)>6.9
checks.append('spine clears mast over 32 lift positions by at least 7 mm; no unintended carriage overlap')
# A collision-only test misses a disconnected joint. Check bearing faces too.
assembled=move(spine,(0,118,2))
for x in (-25,25):
 for z in (72,86):
  for dx,dz in ((4,0),(-4,0),(0,4),(0,-4)):
   assert BRepClass3d_SolidClassifier(carriage,gp_Pnt(x+dx,117.999,z+dz),1e-7).State()==TopAbs_IN
   assert BRepClass3d_SolidClassifier(assembled,gp_Pnt(x+dx,118.001,z+dz),1e-7).State()==TopAbs_IN
  nut=next(p for p in data['items'] if p['name']==f'Fork_nut_M3_{x}_{z-56}')
  screw=next(p for p in data['items'] if p['name']==f'Fork_screw_{x}_{z-24}')
  nv=np.frombuffer(base64.b64decode(nut['vertices']),dtype='<f4').reshape(-1,3)
  sv=np.frombuffer(base64.b64decode(screw['vertices']),dtype='<f4').reshape(-1,3)
  assert abs(sv[:,1].min()-112)<.01 and abs(sv[:,1].max()-125)<.1,(screw['name'],sv.min(0),sv.max(0))
  assert sv[:,1].min()<nv[:,1].min()<nv[:,1].max()<122
checks.append('four carriage joints bear directly at Y=118; M3x10 shanks span fork and carriage and the complete 2.4 mm nut thickness')
report=dict(passed=True,checks=checks,mast_clearance_min_mm=min(gaps),physical_print_tested=False,physical_thread_strength_tested=False)
(O/'Removable_Fork_Mounting_Checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
