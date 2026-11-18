from pathlib import Path
import sys,os,json,math,ast,io,struct,base64,shutil,csv
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/cadlibs'))
from OCP.STEPControl import STEPControl_Reader,STEPControl_AsIs
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder,BRepPrimAPI_MakePrism,BRepPrimAPI_MakeSphere,BRepPrimAPI_MakeCone
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform,BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse,BRepAlgoAPI_Cut,BRepAlgoAPI_Common
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Builder,BRep_Tool
from OCP.BRepTools import BRepTools
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.gp import gp_Pnt,gp_Vec,gp_Trsf,gp_Ax2,gp_Dir
from OCP.TopoDS import TopoDS,TopoDS_Shape,TopoDS_Compound
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE,TopAbs_REVERSED,TopAbs_SOLID
from OCP.TopLoc import TopLoc_Location
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.XCAFDoc import XCAFDoc_DocumentTool,XCAFDoc_ColorGen
from OCP.Quantity import Quantity_Color,Quantity_TOC_RGB
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import trimesh

OUT=ROOT/'mechanics';DL=OUT/'Downloaded_Models';OUT.mkdir(exist_ok=True)
original_downloads=ROOT/'outputs/AmurCargo_Virtual/Downloaded_Models'
if original_downloads.exists():shutil.copytree(original_downloads,DL,dirs_exist_ok=True)
assert DL.exists(),'Restore Downloaded_Models from the deliverable archive'
PARTS=OUT/'Print_Parts';PARTS.mkdir(exist_ok=True)
REFERENCES=OUT/'Purchased_Part_References';REFERENCES.mkdir(exist_ok=True)
THREADED_REFERENCE={'10_Sensor_Standoff','13_UNO_Standoff','14_Driver_Standoff','16_Upper_Tray_Post'}
components={};items=[];shapes={}
def bounds(shape):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(shape,b,False,False)
 lo=b.CornerMin();hi=b.CornerMax();return np.array([[lo.X(),lo.Y(),lo.Z()],[hi.X(),hi.Y(),hi.Z()]])
def translation(x=0,y=0,z=0):
 m=np.eye(4);m[:3,3]=[x,y,z];return m
def rotation(axis,angle):
 a=math.radians(angle);c=math.cos(a);s=math.sin(a);m=np.eye(4)
 if axis=='x':m[:3,:3]=[[1,0,0],[0,c,-s],[0,s,c]]
 if axis=='y':m[:3,:3]=[[c,0,s],[0,1,0],[-s,0,c]]
 if axis=='z':m[:3,:3]=[[c,-s,0],[s,c,0],[0,0,1]]
 return m
def transform(shape,m):
 t=gp_Trsf();t.SetValues(*[float(v) for v in m[:3,:].flatten()]);return BRepBuilderAPI_Transform(shape,t,True).Shape()
def compound(ss):
 c=TopoDS_Compound();b=BRep_Builder();b.MakeCompound(c)
 for s in ss:b.Add(c,s)
 return c
def step(name):
 if name not in shapes:
  r=STEPControl_Reader();status=r.ReadFile(str(DL/name));r.TransferRoots();s=r.OneShape()
  if s.IsNull():raise RuntimeError(name+' empty')
  shapes[name]=s
 return shapes[name]
def box(x,y,z,X,Y,Z):return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),X-x,Y-y,Z-z).Shape()
def cyl(r,h,x=0,y=0,z=0,d=(0,0,1)):
 return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(*d)),r,h).Shape()
def hex_prism(flat,h,x=0,y=0,z=0,axis='z'):
 poly=BRepBuilderAPI_MakePolygon()
 for i in range(6):
  a=i*math.pi/3;u=flat/math.sqrt(3)*math.cos(a);v=flat/math.sqrt(3)*math.sin(a)
  poly.Add(gp_Pnt(x+u,y+v,z) if axis=='z' else gp_Pnt(x+u,y,z+v))
 poly.Close();return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(poly.Wire()).Face(),gp_Vec(0,0,h) if axis=='z' else gp_Vec(0,h,0)).Shape()

def fuse(ss):
 s=ss[0]
 for other in ss[1:]:s=BRepAlgoAPI_Fuse(s,other).Shape()
 return s
def csg(solids,cuts):
 s=fuse([box(*b) for b in solids])
 for b in cuts:s=BRepAlgoAPI_Cut(s,box(*b)).Shape()
 return s
def aligned(shape,target,rot=None):
 rot=np.eye(4) if rot is None else rot
 rotated=transform(shape,rot);bb=bounds(rotated)
 # target X/Y is box centre; target Z is its lower bound.
 return translation(target[0]-(bb[0,0]+bb[1,0])/2,target[1]-(bb[0,1]+bb[1,1])/2,target[2]-bb[0,2])@rot
def tessellate(shape):
 BRepMesh_IncrementalMesh(shape,.28,False,.32,True).Perform()
 vertices=[];triangles=[];e=TopExp_Explorer(shape,TopAbs_FACE)
 while e.More():
  f=TopoDS.Face(e.Current());loc=TopLoc_Location();tri=BRep_Tool.Triangulation_s(f,loc)
  if tri is not None:
   start=len(vertices)
   for i in range(1,tri.NbNodes()+1):
    p=tri.Node(i).Transformed(loc.Transformation());vertices.append((p.X(),p.Y(),p.Z()))
   reverse=f.Orientation()==TopAbs_REVERSED
   for i in range(1,tri.NbTriangles()+1):
    t=tri.Triangle(i);a,b,c=t.Value(1)-1,t.Value(2)-1,t.Value(3)-1
    triangles.append((start+a,start+c,start+b) if reverse else (start+a,start+b,start+c))
  e.Next()
 return np.array(vertices,dtype=np.float32),np.array(triangles,dtype=np.uint32)
def component(key,title,source,status,qty=1):
 components[key]=dict(key=key,title=title,source=source,status=status,quantity=qty)
def add(key,name,shape,color,placement=None,motion=None,alpha=1):
 placement=np.eye(4) if placement is None else placement
 module_keys={'lift','moving','servo','crank','lever','cargo'}
 if key in module_keys or name.startswith('Mast_adapter_') or (motion=='lift' and key in {'buttons','fasteners'}):
  placement=translation(0,-6,0)@placement
 if key in {'servo','crank'} or name in {'Carriage','SG90_mount_plate'} or name.startswith('Fork_screw_'):
  placement=translation(0,0,24)@placement
 if key in {'battery','holders'}:placement=translation(0,0,-1.05)@placement
 if key in {'battery','holders','arduino','driver','pcb_supports'}:placement=translation(0,0,12)@placement
 if key=='tray':placement=translation(0,0,13.95)@placement
 if key=='breadboard':placement=translation(0,0,14.45)@placement
 if key=='resistors':placement=translation(0,0,12.15)@placement
 if name=='Start_button':placement=translation(0,0,12.45)@placement
 world=transform(shape,placement);v,f=tessellate(shape);v=(v@placement[:3,:3].T+placement[:3,3]).astype(np.float32)
 items.append(dict(component=key,name=name,shape=world,color=color,vertices=v,faces=f,motion=motion,alpha=alpha,rigid_matrix=placement.tolist(),source_dimensions=(bounds(shape)[1]-bounds(shape)[0]).tolist()))
 print('Placed',name,len(f),'triangles',flush=True)

# Recover author-designed solids and subtractive details from the existing source.
src=(ROOT/'tools/build_kit_parts.py').read_text(encoding='utf-8').split('# Preview')[0]
tree=ast.parse(src);replacement=ast.parse('def build(name,solids,cuts=()):\n model_specs[name]=(list(solids),list(cuts))\n return []').body[0]
tree.body=[replacement if isinstance(n,ast.FunctionDef) and n.name=='build' else n for n in tree.body]
ns={'__file__':str(ROOT/'tools/build_kit_parts.py'),'model_specs':{}};exec(compile(ast.fix_missing_locations(tree),'specs','exec'),ns)
specs=ns['model_specs']
# Correct the prior mast base: long front flange obstructed the low fork backplate.
solid,cut=specs['02_Mast'];solid[0]=(-50,-17,0,50,17,5);solid[1]=(-50,0,5,50,5,125)
# FDM running fit: 0.5 mm per lateral face, 0.6 mm under retaining lips.
for i in range(2,len(solid)):
 b=list(solid[i]);cx=-27 if (b[0]+b[3])/2<0 else 27
 for j in (0,3):
  rel=round(b[j]-cx,5)
  if abs(abs(rel)-4.3)<1e-5:b[j]=cx+math.copysign(4.5,rel)
  if abs(abs(rel)-7.3)<1e-5:b[j]=cx+math.copysign(7.5,rel)
 for j in (1,4):
  if b[j]==13.5:b[j]=13.6
  elif b[j]==16.5:b[j]=16.6
 solid[i]=tuple(b)
# Discard obsolete rectangular base slots; the four measured mounting holes are drilled below.
cut=[b for b in cut if b[1]<20 and b[2]>=0]
cut=[(-24,-1,18,4,6,85) if b==(-24,-1,25,4,6,85) else b for b in cut]
# No unused mounting slots in the revised base.
specs['02_Mast']=(solid,cut)
solid,cut=specs['01_Fork_Pair_Gap18'];solid[0]=(-35,0,0,35,4,94)
# Original four square M3 holes are replaced by cylindrical clearance holes below.
cut=[]
cut.append((-4.4,-1,12,4.4,5,20))
specs['01_Fork_Pair_Gap18']=(solid,cut)

fork_solids,fork_cuts=specs['01_Fork_Pair_Gap18']
fork_solids=[(b[0],b[1],b[2],b[3],49,b[5]) if i in (1,2) else b for i,b in enumerate(fork_solids)]
fork_solids.extend([(-9,46,4,-3,49,6),(3,46,4,9,49,6)])
fork_solids.extend([(-33,4,0,-29,10,94),(29,4,0,33,10,94)])
specs['01_Fork_Pair_Gap18']=(fork_solids,fork_cuts)
solid,cut=specs['03_Carriage'];solid=[(b[0],5.6,b[2],b[3],b[4],b[5]) if b[1]==7 else b for b in solid];cut=[b for b in cut if b[3]-b[0]>4];cut=[(-12,17,17.8,12,25,22.2) if b==(-12,17,18,12,25,22) else b for b in cut]
cut.append((-16,17,33,-8,25,41));specs['03_Carriage']=(solid,cut)
specs['06_LDR_Trial_Bar']=([(-40,-7,0,40,13,2.4)],[(x-3,-3,-1,x+3,3,5) for x in (-16,0,16)]+[(x-2,5.7,-1,x+2,9.9,5) for x in (-16,0,16)])
designed={name:csg(*data) for name,data in specs.items()}
# Round M3 clearance holes; front-entry hex pockets capture ordinary M3 nuts.
for xx in (-25,25):
 for zz in (70,84):designed['01_Fork_Pair_Gap18']=BRepAlgoAPI_Cut(designed['01_Fork_Pair_Gap18'],cyl(1.7,6,xx,-1,zz,d=(0,1,0))).Shape()
 for zz in (16,30):
  designed['03_Carriage']=BRepAlgoAPI_Cut(designed['03_Carriage'],cyl(1.7,8,xx,17,zz,d=(0,1,0))).Shape()
  designed['03_Carriage']=BRepAlgoAPI_Cut(designed['03_Carriage'],hex_prism(5.8,2.65,xx,21.4,zz,axis='y')).Shape()
for xx in (-23.8757,24.10195):designed['06_LDR_Trial_Bar']=BRepAlgoAPI_Cut(designed['06_LDR_Trial_Bar'],cyl(1.7,5,xx,0,-1)).Shape()
holder_plate=box(-30,0,0,30,4,50)
holder_plate=BRepAlgoAPI_Cut(holder_plate,box(-6.7,-1,7.2,6.7,5,31)).Shape()
for xx in (-26,22):
 for zz in (4,46):holder_plate=BRepAlgoAPI_Cut(holder_plate,cyl(1.7,6,xx,-1,zz,d=(0,1,0))).Shape()
for zz in (5.75,32.95):
 holder_plate=BRepAlgoAPI_Fuse(holder_plate,cyl(1.75,.5,0,-.5,zz,d=(0,1,0))).Shape()
 holder_plate=BRepAlgoAPI_Cut(holder_plate,cyl(1.2,6,0,-1,zz,d=(0,1,0))).Shape()
designed.pop('04_SG90_Trial_Plate');designed['04_SG90_Bolted_Bracket']=holder_plate
for xx in (-38,10):
 for zz in (35.05,77.05):designed['02_Mast']=BRepAlgoAPI_Cut(designed['02_Mast'],cyl(1.7,7,xx,-1,zz,d=(0,1,0))).Shape()
MAST_HOLES=[(-24.63435,79.8527),(24.8604,79.8527),(-23.8757,95.35735),(24.10195,95.35735)]
for xx,yy in MAST_HOLES:
 designed['02_Mast']=BRepAlgoAPI_Cut(designed['02_Mast'],cyl(1.7,7,xx,yy-94,-1)).Shape()
 if yy>90:designed['02_Mast']=BRepAlgoAPI_Cut(designed['02_Mast'],box(xx-4,yy-94-4,5,xx+4,yy-94+4,16)).Shape()
for xx in (-50,45):
 poly=BRepBuilderAPI_MakePolygon()
 for pt in [(xx,-17,5),(xx,0,5),(xx,0,55)]:poly.Add(gp_Pnt(*pt))
 poly.Close();rib=BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(poly.Wire()).Face(),gp_Vec(5,0,0)).Shape()
 designed['02_Mast']=BRepAlgoAPI_Fuse(designed['02_Mast'],rib).Shape()
# The button PCB is mounted behind the fork spine on two integral bosses.
for xx in (-6,6):
 designed['01_Fork_Pair_Gap18']=BRepAlgoAPI_Fuse(designed['01_Fork_Pair_Gap18'],cyl(3.5,1.4,xx,-1.4,23,d=(0,1,0))).Shape()
 designed['01_Fork_Pair_Gap18']=BRepAlgoAPI_Cut(designed['01_Fork_Pair_Gap18'],cyl(1.7,6,xx,-2,23,d=(0,1,0))).Shape()
for xx in (-5,5):designed['01_Fork_Pair_Gap18']=BRepAlgoAPI_Cut(designed['01_Fork_Pair_Gap18'],cyl(1.7,6,xx,-1,30.25,d=(0,1,0))).Shape()
designed['01_Fork_Pair_Gap18']=BRepAlgoAPI_Cut(designed['01_Fork_Pair_Gap18'],box(-16,-1,87,-8,5,95)).Shape()
designed['01_Fork_Pair_Gap18']=BRepAlgoAPI_Cut(designed['01_Fork_Pair_Gap18'],box(-16,-1,70,16,5,78)).Shape()

arm_solids,arm_cuts=specs['05_Crank_R18_Trial']
arm=fuse([cyl(5,4),box(0,-4,0,24,4,4)])
for xx,rr in ((0,2.1),(7,.8),(13,.8),(18,1.7)):arm=BRepAlgoAPI_Cut(arm,cyl(rr,6,xx,0,-1)).Shape()
arm=BRepAlgoAPI_Cut(arm,hex_prism(5.8,2.95,18,0,1.1)).Shape()
designed['05_Crank_R18_Trial']=arm


native_data=json.loads((ROOT/'mechanics/user_base_payload.json').read_text(encoding='utf-8'))
CASTER_XY=np.array([-.1391,-.2471,0.])
component('user_chassis','Шасси из вашего архива','2wd_robot.blend / RobotChassis.001','Оригинальная сетка, масштаб 1:1; STEP — габаритная замена')
component('user_drive','Моторы с колёсами из вашего архива','2wd_robot.blend / Motor, Motor.001','Оригинальные размеры и взаимное расположение, масштаб 1:1',2)
component('user_caster','Опорный ролик из вашего архива','2wd_robot.blend / Caster','Без масштабирования; опущен на 5,313 мм до пола')
seen=set()
for p in native_data['items']:
 key='user_chassis' if p['source_object'].startswith('Robot') else 'user_caster' if p['source_object']=='Caster' else 'user_drive'
 v=np.frombuffer(base64.b64decode(p['vertices']),dtype='<f4').reshape(-1,3).copy()
 f=np.frombuffer(base64.b64decode(p['indices']),dtype='<u4').reshape(-1,3).copy()
 proxy=None
 if key=='user_caster':v+=CASTER_XY
 if p['source_object'] not in seen:
  row=next(x for x in native_data['objects'] if x['name']==p['source_object']);bb=np.array(row['bounds'])
  if key=='user_chassis':proxy=box(bb[0,0],bb[0,1],44.95,bb[1,0],bb[1,1],47.95)
  elif key=='user_drive':
   sg=1 if bb[:,0].mean()>0 else -1
   r=native_data['wheel_axis_z'];outer=bb[1,0] if sg>0 else bb[0,0]
   wheel=cyl(r,27,outer-27 if sg>0 else outer,35,r,d=(1,0,0))
   body=box(bb[0,0] if sg>0 else -53.7,-18.56,23.2,53.7 if sg>0 else bb[1,0],50,45.7)
   proxy=compound([wheel,body])
  else:proxy=box(*(bb[0]+CASTER_XY),*(bb[1]+CASTER_XY))
  seen.add(p['source_object'])
 items.append(dict(component=key,name=p['name'],shape=proxy,color=p['color'],vertices=v,faces=f,motion=None,alpha=1,cad_proxy=True,source_object=p['source_object']))
 print('Native user mesh',p['name'],len(f),'triangles',flush=True)
component('caster_spacer','Проставка опорного ролика','Авторская деталь по вашему шасси','Компенсация зазора ролика до пола, около 4,97 мм')
spacer=box(-18.8957,-95.6557,39.97555,19.1042,-63.6557,44.94)
for x in (-14.8958,15.1042):spacer=BRepAlgoAPI_Cut(spacer,box(x-2.2,-93.8,39,x+2.2,-65.5,46)).Shape()
add('caster_spacer','Caster_spacer',spacer,'#4c6775')
designed['12_Caster_Spacer']=transform(spacer,translation(18.7566,95.4086,-39.97555))

component('mounts','Крепление мачты к штатным отверстиям','Авторские монтажные детали','Четыре М3×12; основание мачты 100×34×5 мм лежит на шасси')
component('lift','Мачта с косынками и кронштейн SG90','Авторские модели проекта','Основание сверху шасси; направляющая сдвинута назад на 20 мм')
mast=designed['02_Mast'];add('lift','Mast',mast,'#2b7f9d',translation(0,100,47.95))
component('moving','Каретка и вилочный блок','Авторские модели проекта','Регулируемая компоновка, посадки не проверены')
add('moving','Carriage',designed['03_Carriage'],'#53b8c6',translation(0,100,32),motion='lift')
add('moving','Fork_pair',designed['01_Fork_Pair_Gap18'],'#e8b53f',translation(0,124,2),motion='lift')
component('servo','Сервопривод SG90','FreeCAD-library / Servo-sg90.step','Скачанная типовая модель SG90; усилие не проверено')
add('servo','SG90',step('SG90.step'),'#225bbb',translation(-12,77.1,85.6)@rotation('x',-90))
plate=designed['04_SG90_Bolted_Bracket'];add('lift','SG90_mount_plate',plate,'#48788d',translation(-12,96,55))
component('crank','Кривошип и штатная качалка','Авторский кривошип + FreeCAD SG90-1-arm-horn.step','Кинематическая примерка; крепёж уточнить')
crank_matrix=translation(-12,110,69)@rotation('x',-90)@rotation('z',70)
add('crank','Crank_R18',designed['05_Crank_R18_Trial'],'#f1cd60',crank_matrix,motion='crank')
horn=step('SG90_Horn.step');bb=bounds(horn);hub=[bb[0,0]+4,(bb[0,1]+bb[1,1])/2,bb[0,2]]
add('crank','SG90_original_horn',horn,'#e6e6de',translation(-12,105,69)@rotation('x',-90)@rotation('z',70)@translation(*[-v for v in hub]),motion='crank')
pin_nut=BRepAlgoAPI_Cut(hex_prism(5.5,2.4,18,0,1.1),cyl(1.5,5,18,0,0)).Shape()
add('crank','Drive_pin_nut_M3',pin_nut,'#b99d50',crank_matrix,motion='crank')
sleeve=BRepAlgoAPI_Cut(cyl(2,11,18,0,3.5),cyl(1.6,13,18,0,2.5)).Shape()
add('crank','Drive_pin_sleeve_4x3_2x11',sleeve,'#b8c3c9',crank_matrix,motion='crank')
wsh=BRepAlgoAPI_Cut(cyl(3,.5,18,0,14.5),cyl(1.6,2,18,0,14)).Shape()
add('crank','Drive_pin_retaining_washer',wsh,'#a5b4bf',crank_matrix,motion='crank')
sh=fuse([cyl(1.5,16,18,0,-1),cyl(2.75,3,18,0,15)])
add('crank','Drive_pin_M3x16',sh,'#9cabb5',crank_matrix,motion='crank')

# Exact UNO geometry recovered from its downloaded FreeCAD document; placements are baked in BREPs.
component('arduino','Arduino UNO R3','FreeCAD-library / Arduino UNO.FCStd','Типовая UNO R3; не точная модель выданного CH340G')
z=ZipFile(DL/'UNO_R3.FCStd');xml=ET.fromstring(z.read('Document.xml'));skipped=[]
for ob in xml.find('ObjectData'):
 props={p.attrib['name']:p for p in ob.find('Properties')}
 if 'Shape' not in props:continue
 sh=TopoDS_Shape();filename=props['Shape'].find('Part').attrib['file'];BRepTools.Read_s(sh,io.BytesIO(z.read(filename)),BRep_Builder())
 if sh.IsNull():skipped.append(ob.attrib['name']);continue
 name=ob.attrib['name'];color='#18788f' if 'pcb' in name else '#adb5bb' if 'metal' in name else '#222a30'
 if 'Led' in name:color='#94c848'
 add('arduino',name,sh,color,translation(-50.67,3.71,59.65))
 if 'missblack' in name or 'missmetal' in name:items[-1]['boolean_unreliable']=True

component('driver','Драйвер L298N — условный','FreeCAD-library / L298N.step','Типовая замена: реальный драйвер ещё не назван')
driver=step('L298N.step');dm=aligned(driver,(30,35,57));e=TopExp_Explorer(driver,TopAbs_SOLID);idx=0
while e.More():
 sh=TopoDS.Solid(e.Current());bb=bounds(sh);sz=bb[1]-bb[0]
 color='#ba3a3c' if sz[2]<2 and sz[0]>25 else '#252a2d' if bb[1,2]>15 else '#258c69' if sz[0]>8 and sz[2]>5 else '#a3a9ad'
 add('driver','L298N_'+str(idx),sh,color,dm);idx+=1;e.Next()

component('battery','Четыре аккумулятора 18650','Авторский габарит 18×65 мм','Номинальный 18650; защищённый 69-мм образец оставлен в исходниках',4)
component('pcb_supports','Изолирующие стойки плат','Авторские стойки по отверстиям скачанных плат','По четыре опоры на плату; высоты UNO 11,70 мм, L298N 10,45 мм; закреплены на несущей площадке',8)
uno_post=BRepAlgoAPI_Cut(cyl(2.5,11.7),cyl(1.6,13,0,0,-.5)).Shape()
driver_post=BRepAlgoAPI_Cut(cyl(2.5,10.45),cyl(1.65,12,0,0,-.5)).Shape()
designed['13_UNO_Standoff']=uno_post;designed['14_Driver_Standoff']=driver_post
for j,(xx,yy) in enumerate(((2.54,13.97),(17.78,66.04),(45.72,66.04),(50.8,13.97))):
 add('pcb_supports','UNO_standoff_'+str(j),uno_post,'#727f8b',translation(xx-50.67,yy+3.71,47.95))
for j,(xx,yy) in enumerate(((3,3),(3,40),(40,3),(40,40))):
 add('pcb_supports','Driver_standoff_'+str(j),driver_post,'#727f8b',translation(xx+8.5,yy+13.5,47.95))
component('holders','Держатель четырёх элементов','KiCad / Keystone 1042 ×4','Четыре одиночных держателя как габаритная замена общего блока',4)
for i,x in enumerate((-34.5,-11.5,11.5,34.5)):
 sh=step('18650_Holder_Keystone.step');add('holders','Cell_holder_'+str(i),sh,'#2b3036',aligned(sh,(x,-47,49),rotation('z',90)))
 sh=step('18650_Cell.step');bb=bounds(sh);m=translation(x,-47,60.5)@rotation('x',90)@translation(*[-v for v in (bb[0]+bb[1])/2])
 # Nominal 18 x 65 mm cell, not the downloaded protected 69 mm variant.
 cell=compound([cyl(9,64.5,0,0,0),cyl(3,.5,0,0,64.5)])
 cb=bounds(cell);m=translation(x,-47,61.83)@rotation('x',90)@translation(*[-v for v in (cb[0]+cb[1])/2])
 add('battery','18650_'+str(i),cell,'#b95995',m)

component('tray','Верхняя монтажная площадка','Авторская модель','Дополнительная печатная деталь; можно скрыть в просмотрщике')
tray=box(-65,-97,102,65,77,105)
for x in (-60,60):
 for y in (-75,75):tray=BRepAlgoAPI_Cut(tray,cyl(1.7,5,x,y,101)).Shape()
add('tray','Electronics_tray',tray,'#bacbd2',alpha=.25)
designed['09_Upper_Tray']=transform(tray,translation(65,97,-102))
component('breadboard','Макетная плата MB-102','Авторская габаритная модель; Adafruit 400-point STEP скачан как образец','Принят габарит 165×55 мм, размер выданной платы не подтверждён')
board=box(-27.5,-92.5,105,27.5,72.5,114.7)
board=BRepAlgoAPI_Cut(board,box(-1.7,-91,112,1.7,71,116)).Shape()
add('breadboard','MB102_envelope',board,'#e9e7dc')
# Cosmetic strips on the envelope; do not claim a detailed electrical socket model.
for x,col in ((-24,'#be4b4b'),(24,'#4789bd')):add('breadboard','Breadboard_rail_'+str(x),box(x-.35,-90,114.7,x+.35,70,114.85),col)

component('sensors','Линия: 3 фоторезистора и 3 LED','FreeCAD-library / Photoresistor.step, led-3mm-short.step','Скачанные модели; оптика и контраст не проверены',3)
component('sensor_mount','Планка и резьбовые стойки датчиков','Авторская модель','Под шасси; две стойки М3×35 на передних винтах основания мачты')
add('sensor_mount','Sensor_bar',designed['06_LDR_Trial_Bar'],'#354453',translation(0,95.35735,5.94))
post=BRepAlgoAPI_Cut(cyl(3,35),cyl(1.6,37,0,0,-1)).Shape();designed['10_Sensor_Standoff']=post
for i,x in enumerate((-23.8757,24.10195)):add('sensor_mount','Sensor_standoff_'+str(i),post,'#8999a4',translation(x,95.35735,9.94))
for i,x in enumerate((-16,0,16)):
 add('sensors','LDR_'+str(i),step('Photoresistor.step'),'#cb9b4f',translation(x,95.35735,4.94)@rotation('x',180))
 add('sensors','LED_'+str(i),step('LED_3mm.step'),'#b43e35',translation(x,103.15735,7.24)@rotation('x',180))
component('resistors','Три резистора 220 Ом и три 10 кОм','FreeCAD-library / axial resistor models','Механическая модель корпуса; номиналы 10 кОм в геометрии условны',6)
for i in range(3):
 add('resistors','R220_'+str(i),step('Resistor_220.step'),'#b39770',translation(-15,-45+i*12,119))
 add('resistors','R10k_'+str(i),step('Resistor_220.step'),'#b39770',translation(15,-45+i*12,119))

component('buttons','Кнопки пуска и обнаружения','FreeCAD-library / pushbutton-mini.step','Типовые кнопки; рычаг обнаружения авторский',2)
add('buttons','Start_button',step('Tactile_Button.step'),'#42474c',translation(12,35,119))
add('buttons','Cargo_button',step('Tactile_Button.step'),'#42474c',translation(0,126,18)@rotation('x',-90),motion='lift')
component('lever','Рычаг обнаружения перемычки','Авторская габаритная модель','Упругость и контакт проверить на грузе')
lever=fuse([box(-9,128,28.5,9,129.2,37),box(-9,128,35,9,132.2,37),box(-1.1,131,18,1.1,132.2,35),box(-1.1,132.2,17,1.1,146.8,19)])
for xx in (-5,5):lever=BRepAlgoAPI_Cut(lever,cyl(1.7,6,xx,127,32.25,d=(0,1,0))).Shape()
add('lever','Cargo_feeler',lever,'#bec4c8',motion='lift')
designed['11_Cargo_Feeler']=transform(lever,translation(7,-128,-17))

component('cargo','Гантель для примерки','Авторская модель по трём фотографиям пользователя','Внешний габарит 70×40×40 мм; оценка по фото: пластины 15 мм, перемычка Ø16 мм')
cargo=fuse([box(-35,135,0,-20,175,40),box(20,135,0,35,175,40),cyl(8,40,-20,155,20,d=(1,0,0)),cyl(9,1,-20,155,20,d=(1,0,0)),cyl(9,1,19,155,20,d=(1,0,0))])
add('cargo','Dumbbell_example',cargo,'#c63e38',motion='cargo')

component('fasteners','Крепёж M3','FreeCAD-library / ISO4762 M3×12, укороченная геометрия M3×10','На вилах M3×10, на площадке M3×12; резьба условная')
short_screw=BRepAlgoAPI_Cut(step('Screw_M3x12.step'),box(-10,-10,-13,10,10,-10)).Shape()
for x in (-25,25):
 for z0 in (48,62):add('fasteners','Fork_screw_'+str(x)+'_'+str(z0),short_screw,'#9ca7ad',translation(x,128,z0)@rotation('x',-90),motion='lift')
# Ordinary hex M3 nuts sit in accessible front pockets; no brass inserts are needed.
for xx in (-25,25):
 for zz in (16,30):
  fork_nut=BRepAlgoAPI_Cut(hex_prism(5.5,2.4,xx,21.4,zz,axis='y'),cyl(1.5,4,xx,21,zz,d=(0,1,0))).Shape()
  add('moving','Fork_nut_M3_'+str(xx)+'_'+str(zz),fork_nut,'#a5b2bb',translation(0,100,56),motion='lift')
exec(compile((ROOT/'tools/rigid_mounts.py').read_text(encoding='utf-8'),'rigid_mounts.py','exec'),globals())
# STEP exports with names and colour, preserving separate components.
def pose_shape(item,lifted=False,angle=None):
 sh=item['shape'];motion=item['motion']
 if sh is None:return None
 theta=angle if angle is not None else (140 if lifted else 20)
 h=18*(math.cos(math.radians(20))-math.cos(math.radians(theta)))
 if motion=='lift':sh=transform(sh,translation(0,0,h))
 if motion=='cargo':sh=transform(sh,translation(0,0,max(0,h-6)))
 if motion=='crank':sh=transform(sh,translation(-12,101,93)@rotation('y',20-theta)@translation(12,-101,-93))
 return sh
def export_step(path,lifted=False,light=False):
 doc=TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
 st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main());ct=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
 rootLabel=st.NewShape();st.SetShape(rootLabel,compound([]));TDataStd_Name.Set_s(rootLabel,TCollection_ExtendedString('Pogruzchik_Virtual_Prototype'))
 for key,comp in components.items():
  label=st.NewShape();st.SetShape(label,compound([]));TDataStd_Name.Set_s(label,TCollection_ExtendedString(comp['title']))
  for item in [x for x in items if x['component']==key]:
   geometry=pose_shape(item,lifted)
   if geometry is None:continue
   if light and key=='arduino':
    pieces=[];ee=TopExp_Explorer(geometry,TopAbs_SOLID)
    while ee.More():
     bb=bounds(ee.Current());pieces.append(box(*bb[0],*bb[1]));ee.Next()
    if pieces:geometry=compound(pieces)
   part=st.AddShape(geometry,False);TDataStd_Name.Set_s(part,TCollection_ExtendedString(item['name']))
   col=item['color'].lstrip('#');rgb=[int(col[i:i+2],16)/255 for i in (0,2,4)]
   ct.SetColor(part,Quantity_Color(*rgb,Quantity_TOC_RGB),XCAFDoc_ColorGen)
   st.AddComponent(label,part,TopLoc_Location())
  st.AddComponent(rootLabel,label,TopLoc_Location())
 st.UpdateAssemblies();w=STEPCAFControl_Writer();w.SetColorMode(True);w.SetNameMode(True);w.Transfer(doc,STEPControl_AsIs);w.Write(str(path))
 print('STEP exported',path.name,flush=True)

export_step(OUT/'Forklift_Assembly_Reference.step',light=True)
# Export revised author-designed fabrication geometry in CAD and mesh formats.
for obsolete in ('04_SG90_Trial_Plate','07_Mast_Adapter_Left','08_Mast_Adapter_Right','17_Breadboard_Clamp'):
 for suffix in ('.stl','.step'):
  old=PARTS/(obsolete+suffix)
  if old.exists():old.unlink()
for name,shape in designed.items():
 v,f=tessellate(shape);mesh=trimesh.Trimesh(vertices=v,faces=f,process=True);mesh.export((REFERENCES if name in THREADED_REFERENCE else PARTS)/(name.replace('Gap18','TipStops')+'.stl'))
 writer=STEPCAFControl_Writer() if False else None
from OCP.STEPControl import STEPControl_Writer
for name,shape in designed.items():
 w=STEPControl_Writer();w.Transfer(shape,STEPControl_AsIs);w.Write(str((REFERENCES if name in THREADED_REFERENCE else PARTS)/(name.replace('Gap18','TipStops')+'.step')))

scene=trimesh.Scene();payload=[]
for it in items:
 rgba=[int(it['color'][j:j+2],16) for j in (1,3,5)]+[int(it['alpha']*255)]
 mesh=trimesh.Trimesh(vertices=it['vertices'],faces=it['faces'],process=False)
 mesh.visual=trimesh.visual.ColorVisuals(mesh=mesh,vertex_colors=np.tile(rgba,(len(it['vertices']),1)))
 scene.add_geometry(mesh,geom_name=it['name'],node_name=it['name'])
 payload.append(dict(name=it['name'],component=it['component'],color=it['color'],alpha=it['alpha'],motion=it['motion'],vertices=base64.b64encode(it['vertices'].astype('<f4').tobytes()).decode(),indices=base64.b64encode(it['faces'].astype('<u4').tobytes()).decode()))
(OUT/'assembly_data.json').write_text(json.dumps({'components':components,'items':payload},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
glb_scene=scene.copy();glb_scene.apply_scale(.001);glb_scene.units='m'
(OUT/'Forklift.glb').write_bytes(glb_scene.export(file_type='glb',include_normals=False))
scene.export(str(OUT/'Forklift.obj'),include_normals=False)
robot_vertices=np.concatenate([x['vertices'] for x in items if x['component']!='cargo'])
bb=[robot_vertices.min(0).tolist(),robot_vertices.max(0).tolist()]
full_lift=18*(math.cos(math.radians(20))-math.cos(math.radians(140)))
report={'units':'mm','robot_bounds':bb,'robot_dimensions':(robot_vertices.max(0)-robot_vertices.min(0)).tolist(),'components':len(components),'mesh_parts':len(items),'triangles':sum(len(x['faces']) for x in items),'uno_small_unreadable_parts':skipped,'geometric_lift_mm':full_lift,'example_cargo_slack_mm':6,'example_cargo_clearance_raised_mm':full_lift-6}

# Critical positive-volume intersections, excluding intentionally connected mounting hardware.
def intersection_volume(a,b):
 bb1=bounds(a);bb2=bounds(b)
 if np.any(np.minimum(bb1[1],bb2[1])-np.maximum(bb1[0],bb2[0])<=.001):return 0
 common=BRepAlgoAPI_Common(a,b).Shape();g=GProp_GProps();BRepGProp.VolumeProperties_s(common,g);return abs(g.Mass())
byname={x['name']:x for x in items};checks=[]
for a,b in [('Mast','Carriage'),('Mast','Fork_pair'),('Mast','SG90'),('Mast','Crank_R18'),('SG90_mount_plate','SG90'),('Carriage','Crank_R18'),('Fork_pair','Dumbbell_example'),('Fork_pair','Cargo_button'),('Fork_pair','Crank_R18'),('SG90_original_horn','Crank_R18'),('Fork_pair','Sensor_bar'),('Fork_pair','Cargo_feeler'),('Carriage','Drive_pin_sleeve_4x3_2x11'),('Fork_pair','Drive_pin_M3x16'),('Fork_pair','Drive_pin_retaining_washer')]:
 for angle in (20,40,60,90,120,140):
  vol=intersection_volume(pose_shape(byname[a],angle=angle),pose_shape(byname[b],angle=angle))
  checks.append(dict(a=a,b=b,angle_degrees=angle,intersection_mm3=vol))
report['critical_intersections']=checks

scale_rows=[]
for it in items:
 mat=np.array(it.get('rigid_matrix',np.eye(4)))
 factors=np.linalg.svd(mat[:3,:3],compute_uv=False)
 assert np.allclose(factors,[1,1,1],atol=1e-8),it['name']
 scale_rows.append(dict(name=it['name'],component=it['component'],scale=factors.tolist(),assembly_dimensions=(it['vertices'].max(0)-it['vertices'].min(0)).tolist(),source_dimensions=it.get('source_dimensions'),native_source=it.get('source_object')))
report['unit_scale_audit']=scale_rows
report['source_base_dimensions_mm']=native_data['dimensions']
report['caster_vertical_correction_mm']=native_data['caster_vertical_correction_mm']
cbb=bounds(byname['Dumbbell_example']['shape']);report['cargo_dimensions_xyz_mm']=(cbb[1]-cbb[0]).tolist()
assert np.allclose(cbb[1]-cbb[0],[70,40,40])
report['fork_tip_stop_height_mm']=2
# Check withdrawal/insertion with the cargo on the floor, and engagement of the lips.
fork=byname['Fork_pair']['shape'];load=byname['Dumbbell_example']['shape'];paths=[]
for dy in np.linspace(0,65,14):
 vol=intersection_volume(fork,transform(load,translation(0,float(dy),0)))
 paths.append(dict(cargo_forward_shift_mm=float(dy),intersection_mm3=vol))
 assert vol<.001,'Cargo cannot enter/leave under the fork stops'
report['cargo_insertion_and_withdrawal']=paths
raised_fork=pose_shape(byname['Fork_pair'],True);raised_load=pose_shape(byname['Dumbbell_example'],True)
stops=[]
for dy in (0,7,9,9.7,10,11,12):stops.append(dict(cargo_forward_shift_mm=dy,intersection_mm3=intersection_volume(raised_fork,transform(raised_load,translation(0,dy,0)))))
report['tip_stop_engagement']=stops
assert stops[2]['intersection_mm3']<.001 and stops[4]['intersection_mm3']>.001
report['photo_cargo_assumptions']={'outer_xyz_mm':[70,40,40],'end_plate_thickness_mm':15,'clear_gap_between_plates_mm':40,'shaft_diameter_mm':16,'shaft_axis_height_mm':20,'collar_diameter_mm':18,'collar_thickness_mm':1,'shaft_bottom_mm':12,'fork_tip_entry_clearance_mm':4,'stop_first_contact_forward_shift_mm':15-math.sqrt(28),'dimensions_status':'Outer dimensions from user; all internal dimensions estimated from photographs'}
(OUT/'Scale_Audit.json').write_text(json.dumps(scale_rows,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'Scale_Audit.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['Деталь','Группа','Масштаб X','Масштаб Y','Масштаб Z','Габарит X мм','Габарит Y мм','Габарит Z мм'])
 for r in scale_rows:writer.writerow([r['name'],r['component'],*r['scale'],*r['assembly_dimensions']])
# Broad-phase all-component position audit; imported user's base is verified as a mesh in Blender.
allowed={frozenset(x) for x in [('battery','holders'),('buttons','breadboard'),('resistors','breadboard'),('fasteners','mounts'),('fasteners','tray'),('fasteners','moving'),('fasteners','lift'),('crank','servo'),('buttons','lever'),('mechanical_fixings','servo'),('mechanical_fixings','pcb_supports'),('mechanical_fixings','sensor_mount'),('mechanical_fixings','moving'),('buttons','cargo_switch_mount')]}
overlaps=[];tested=0
valid=[x for x in items if x['shape'] is not None and not x.get('cad_proxy') and not x.get('boolean_unreliable')]
report['cad_mesh_only_parts']=[x['name'] for x in items if x.get('boolean_unreliable')]
audit_bounds={x['name']:bounds(x['shape']) for x in valid}
for i,a in enumerate(valid):
 for b in valid[i+1:]:
  if a['component']==b['component']:continue
  tested+=1
  ba=audit_bounds[a['name']];bb=audit_bounds[b['name']]
  if np.any(np.minimum(ba[1],bb[1])-np.maximum(ba[0],bb[0])<=.001):continue
  vol=intersection_volume(a['shape'],b['shape'])
  if vol>.001:overlaps.append(dict(a=a['name'],b=b['name'],component_a=a['component'],component_b=b['component'],volume_mm3=vol,expected_mating=frozenset((a['component'],b['component'])) in allowed))
report['position_audit']={'pairs_checked':tested,'overlaps':overlaps}
dynamic=[]
for angle in (40,60,90,120,140):
 posed={x['name']:pose_shape(x,angle=angle) for x in valid}
 boxes={name:bounds(sh) for name,sh in posed.items()}
 for i,a in enumerate(valid):
  for b in valid[i+1:]:
   if a['motion']==b['motion']:continue
   ba=boxes[a['name']];bb=boxes[b['name']]
   if np.any(np.minimum(ba[1],bb[1])-np.maximum(ba[0],bb[0])<=.001):continue
   if frozenset((a['component'],b['component'])) in allowed:continue
   vol=intersection_volume(posed[a['name']],posed[b['name']])
   if vol>.001:dynamic.append(dict(a=a['name'],b=b['name'],angle_degrees=angle,intersection_mm3=vol))
report['dynamic_unexpected_intersections']=dynamic
report['caster_xy_alignment_mm']=CASTER_XY[:2].tolist()

(OUT/'Assembly_Checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'component_manifest.json').write_text(json.dumps(components,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'Components.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['key','title','quantity','source','status']);w.writeheader();w.writerows(components.values())
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
