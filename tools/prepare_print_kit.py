from pathlib import Path
import sys, json, math, shutil, zipfile, base64, html
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/cadlibs'))
import trimesh
from PIL import Image,ImageDraw,ImageFont
from OCP.STEPControl import STEPControl_Reader,STEPControl_Writer,STEPControl_AsIs
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt,gp_Ax2,gp_Dir
from OCP.TopAbs import TopAbs_IN,TopAbs_OUT
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE,TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.TopLoc import TopLoc_Location

OUT=ROOT/'mechanics'; PARTS=OUT/'Print_Parts'
KIT=OUT/'Print_Ready';KIT.mkdir(exist_ok=True)
REF=OUT/'Purchased_Part_References';REF.mkdir(exist_ok=True)
for stem in ('10_Sensor_Standoff','13_UNO_Standoff','14_Driver_Standoff','16_Upper_Tray_Post'):
 for ext in ('.stl','.step'):
  p=PARTS/(stem+ext)
  if p.exists():shutil.move(str(p),str(REF/p.name))
(REF/'README_RU.txt').write_text('Это справочные габариты резьбовых стоек, а не готовые детали для FDM-печати. Нужны стойки с внутренней резьбой М3 с двух концов: 2×35 мм; 4×56 мм; 4×11,70 мм; 4×10,45 мм. Длины 56/11,70/10,45 нестандартные: обеспечить указанную высоту изготовлением или подбором стойки и проставок с пересчётом длины винтов. Гладкие отверстия в моделях лишь условно обозначают резьбу. Замена на печатные трубки без гаек и переделки крепежа не работает.\n',encoding='utf-8')

def read_step(path):
 r=STEPControl_Reader();assert r.ReadFile(str(path))==1;r.TransferRoots();return r.OneShape()
checks=[]
for p in sorted(PARTS.glob('*.step')):
 shape=read_step(p);assert BRepCheck_Analyzer(shape).IsValid(),p.name
 mesh=trimesh.load(p.with_suffix('.stl'),force='mesh')
 assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0,p.name
 edges=mesh.edges_unique
 parent=list(range(len(mesh.vertices)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for a,b in edges:
  a=find(int(a));b=find(int(b));parent[a]=b
 assert len({find(i) for i in range(len(parent))})==1,p.name+' detached body'
 checks.append(dict(file=p.name,valid_brep=True,watertight=True,single_connected_body=True,volume_mm3=float(mesh.volume)))

# Sample the cylindrical walls in exact CAD, not just the visual appearance of STL.
hole_checks=[]
def radial_check(stem,center,axis,radius,angles=24):
 shape=read_step(PARTS/(stem+'.step'));center=np.array(center,dtype=float)
 basis=[i for i in range(3) if i!=axis]
 for a in np.linspace(0,2*math.pi,angles,endpoint=False):
  direction=np.zeros(3);direction[basis]=[math.cos(a),math.sin(a)]
  for delta,wanted in ((-.05,TopAbs_OUT),(.05,TopAbs_IN)):
   pt=center+direction*(radius+delta)
   state=BRepClass3d_SolidClassifier(shape,gp_Pnt(*pt),1e-7).State()
   assert state==wanted,(stem,center.tolist(),radius,float(a),delta,str(state))
 hole_checks.append(dict(part=stem,center_mm=center.tolist(),axis='XYZ'[axis],diameter_mm=radius*2,angular_samples=angles))
for x in (-25,25):
 for z in (70,84):radial_check('01_Fork_Pair_TipStops',(x,2,z),1,1.7)
 for z in (16,30):radial_check('03_Carriage',(x,19,z),1,1.7)
for x in (-6,6):radial_check('01_Fork_Pair_TipStops',(x,2,23),1,1.7)
for x in (-5,5):radial_check('01_Fork_Pair_TipStops',(x,2,30.25),1,1.7)
radial_check('05_Crank_R18_Trial',(18,0,.5),2,1.7)
for z in (5.75,32.95):radial_check('04_SG90_Bolted_Bracket',(0,2,z),1,1.2)
for x,y in ((-24.63435,79.8527),(24.8604,79.8527),(-23.8757,95.35735),(24.10195,95.35735)):
 radial_check('02_Mast',(x,y-94,2.5),2,1.7)
hex_checks=[]
for stem,center,axis in [('03_Carriage',(x,22.5,z),1) for x in (-25,25) for z in (16,30)]+[('05_Crank_R18_Trial',(18,0,2.5),2)]:
 shape=read_step(PARTS/(stem+'.step'));center=np.array(center,dtype=float);basis=[i for i in range(3) if i!=axis]
 for angle in np.arange(6)*math.pi/3+math.pi/6:
  d=np.zeros(3);d[basis]=[math.cos(angle),math.sin(angle)]
  for radius,state in ((2.85,TopAbs_OUT),(2.95,TopAbs_IN)):
   assert BRepClass3d_SolidClassifier(shape,gp_Pnt(*(center+d*radius)),1e-7).State()==state
 hex_checks.append(dict(part=stem,center_mm=center.tolist(),across_flats_mm=5.8,faces_checked=6))

def rot(axis,degrees):
 return trimesh.transformations.rotation_matrix(math.radians(degrees),axis)
rows=[
 ('01_Fork_Pair_TipStops','Вилы с уступами',1,rot((1,0,0),90),'Спинкой вниз; две задние бобышки выступают на 1,4 мм.','Нужны под всей спинкой до высоты 1,4 мм; лапы направлены вверх. Снять поддержки вокруг бобышек.','PETG; 5–6 периметров; 50–60%','Лапы 4 мм, уступы 2 мм. Печатать с поддержкой спинки, иначе она начнётся в воздухе.'),
 ('02_Mast','Мачта',1,np.eye(4),'Широким основанием 100×34 мм на стол.','Локальные под крышей окна и нависающими площадками; не заполнять каналы неразборными поддержками.','PETG; 5 периметров; 40–50%','Основание и косынки 5 мм. Проверить чистоту направляющих.'),
 ('03_Carriage','Каретка',1,rot((1,0,0),-90),'Плоской передней стороной к столу; ползуны вверх.','Под нависающими полками Т-ползунов. Карманы гаек смотрят к столу: после печати очистить входы.','PETG; 5 периметров; 50%','Четыре гайки М3 закладываются в передние шестигранные карманы перед установкой вил.'),
 ('04_SG90_Bolted_Bracket','Кронштейн SG90',1,rot((1,0,0),-90),'Плоской стороной без бобышек на стол.','Не требуются для этой ориентации.','PETG; 5 периметров; 40–50%','М3 Ø3,4; отверстия ушек М2 Ø2,4. Перед сборкой примерить реальный SG90.'),
 ('05_Crank_R18_Trial','Кривошип',1,np.eye(4),'Плоской задней стороной на стол, карман гайки вверх.','Не требуются.','PETG; 5–6 периметров; 100%','Обычная гайка М3 под приводной палец. К штатной качалке — её мелкий крепёж, не М3 в вал.'),
 ('06_LDR_Trial_Bar','Планка датчиков',1,np.eye(4),'Большой плоской стороной на стол.','Не требуются.','PETG или PLA; 4 периметра; 100%','Толщина 2,4 мм. Прямоугольные окна под корпуса датчиков сохраняются.'),
 ('09_Upper_Tray','Верхняя площадка',1,np.eye(4),'Плашмя.','Не требуются.','PETG или PLA; 4 периметра; 25–35%','130×174×3 мм. Макетка приклеивается двусторонним скотчем.'),
 ('11_Cargo_Feeler','Щуп кнопки — пробная деталь',1,rot((0,1,0),-90),'Боковой гранью монтажного основания на стол.','Нужны под узким стержнем и наконечником. Отделять осторожно.','PETG; 3 периметра; 100%','Минимальная толщина 1,2 мм. Сначала печатать отдельно: упругость и усилие кнопки не рассчитаны.'),
 ('12_Caster_Spacer','Проставка ролика',1,np.eye(4),'Плашмя.','Не требуются.','PETG или PLA; 4 периметра; 50%','Толщина 4,964 мм. Два длинных прямоугольных паза оставлены для согласования креплений.'),
 ('15_Electronics_Carrier','Несущая площадка',1,np.eye(4),'Плоской нижней стороной на стол, бортики вверх.','Не требуются; потаи снизу могут потребовать зачистки.','PETG; 4 периметра; 30–40%','130×174 мм, пластина 4 мм. Узкие прямоугольные отверстия — под стяжки.'),
 ('18_Carrier_Riser','Проставка несущей площадки',4,np.eye(4),'Кольцевым торцом на стол.','Не требуются; для четырёх штук добавить brim.','PETG; 4 периметра; 100%','Ø7×8 мм, отверстие Ø3,4. Это дистанционная втулка под сквозной винт, резьба не нужна.'),
 ('19_UNO_Edge_Clip','Прижим Arduino',1,rot((1,0,0),90),'Боковой прямоугольной гранью на стол.','Не требуются в выбранной ориентации.','PETG; 4 периметра; 100%','Прижимная полка 1 мм: не перетягивать винт; проверить зазор до разъёмов.'),
]

def write_3mf(mesh,path):
 vertices=''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x,y,z in mesh.vertices)
 faces=''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in mesh.faces)
 model=f'<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="ru-RU" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources><object id="1" type="model"><mesh><vertices>{vertices}</vertices><triangles>{faces}</triangles></mesh></object></resources><build><item objectid="1"/></build></model>'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
  z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
  z.writestr('3D/3dmodel.model',model)
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  from xml.etree import ElementTree as ET
  doc=ET.fromstring(z.read('3D/3dmodel.model'));assert doc.attrib['unit']=='millimeter'
  n={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
  vv=np.array([[float(v.attrib[k]) for k in ('x','y','z')] for v in doc.findall('.//m:vertex',n)])
  assert np.allclose(np.array([vv.min(0),vv.max(0)]),mesh.bounds,atol=1e-5)
  assert len(doc.findall('.//m:triangle',n))==len(mesh.faces)

font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
def thumbnail(mesh):
 im=Image.new('RGB',(400,290),'#eef3f4');d=ImageDraw.Draw(im)
 m=mesh.copy();m.apply_transform(rot((0,0,1),-25));v=m.vertices
 points=np.column_stack((.9*v[:,0]-.45*v[:,1],.3*v[:,0]+.55*v[:,1]-v[:,2]))
 span=np.ptp(points,axis=0);scale=min(350/max(span[0],1),220/max(span[1],1));points=(points-points.min(0))*scale+[25,20]
 for f in sorted(m.faces,key=lambda f:float(np.mean(v[f]@np.array([.3,.8,.4])))):
  tri=v[f];n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n/=max(np.linalg.norm(n),1e-10)
  shade=int(160+65*abs(float(n@np.array([.4,-.3,.7]))))
  d.polygon([tuple(points[i]) for i in f],fill=(int(shade*.35),int(shade*.76),shade),outline=None)
 d.line((20,260,380,260),fill='#99afb4',width=2);d.text((22,266),'Z=0 — поверхность стола',font=font,fill='#3a5960')
 import io
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue(),im

manifest=[];cards=[];contact=Image.new('RGB',(1200,4*350),'white')
for i,(stem,title,qty,matrix,orientation,support,settings,note) in enumerate(rows):
 mesh=trimesh.load(PARTS/(stem+'.stl'),force='mesh');old_volume=mesh.volume;old_sorted=np.sort(mesh.extents)
 mesh.apply_transform(matrix);mesh.apply_translation(-mesh.bounds[0])
 assert abs(mesh.bounds[0,2])<1e-5 and np.allclose(np.sort(mesh.extents),old_sorted,atol=1e-4)
 assert abs(mesh.volume-old_volume)<max(1e-4,old_volume*1e-6)
 mesh.export(KIT/(stem+'.stl'));write_3mf(mesh,KIT/(stem+'.3mf'))
 png,im=thumbnail(mesh);contact.paste(im,((i%3)*400,(i//3)*350));ImageDraw.Draw(contact).text(((i%3)*400+15,(i//3)*350+296),f'{stem[:2]}. {title}',font=font,fill='#183540')
 manifest.append(dict(file=stem+'.stl',quantity=qty,title=title,dimensions_on_bed_mm=mesh.extents.tolist(),material='PETG',orientation=orientation,supports=support,settings=settings,note=note,transform_to_print_matrix=matrix.tolist(),min_z_mm=float(mesh.bounds[0,2])))
 cards.append(f'<article><img alt="{title}: ориентация на столе" src="data:image/png;base64,{base64.b64encode(png).decode()}"><div><h2>{stem[:2]}. {title} <small>×{qty}</small></h2><p><b>Ориентация:</b> {orientation}</p><p><b>Поддержки:</b> {support}</p><p><b>Начальные настройки:</b> {settings}</p><p>{note}</p><p class="size">На столе: '+ ' × '.join(f'{x:.2f}' for x in mesh.extents)+f' мм</p><a href="{stem}.3mf">3MF · миллиметры</a> <a href="{stem}.stl">STL · миллиметры</a></div></article>')
contact.save(KIT/'Print_Orientations.png')

# Compact fit coupon: M3 clearance, M2 clearance and hex pockets for ordinary M3 nuts.
coupon=BRepPrimAPI_MakeBox(gp_Pnt(0,0,0),72,24,5).Shape()
for i,r in enumerate((1.6,1.7,1.8,1.1,1.2)):
 cutter=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(7+i*13,7,-1),gp_Dir(0,0,1)),r,7).Shape();coupon=BRepAlgoAPI_Cut(coupon,cutter).Shape()
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.gp import gp_Vec
for i,flat in enumerate((5.6,5.8,6.0)):
 p=BRepBuilderAPI_MakePolygon();x=12+i*24
 for a in range(6):p.Add(gp_Pnt(x+flat/math.sqrt(3)*math.cos(a*math.pi/3),17+flat/math.sqrt(3)*math.sin(a*math.pi/3),2.4))
 p.Close();cut=BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(p.Wire()).Face(),gp_Vec(0,0,3)).Shape();coupon=BRepAlgoAPI_Cut(coupon,cut).Shape()
 coupon=BRepAlgoAPI_Cut(coupon,BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,17,-1),gp_Dir(0,0,1)),1.7,7).Shape()).Shape()
assert BRepCheck_Analyzer(coupon).IsValid()
w=STEPControl_Writer();w.Transfer(coupon,STEPControl_AsIs);w.Write(str(KIT/'00_Fit_Coupon.step'))
BRepMesh_IncrementalMesh(coupon,.08,False,.15,True).Perform();vs=[];fs=[];e=TopExp_Explorer(coupon,TopAbs_FACE)
while e.More():
 face=TopoDS.Face(e.Current());loc=TopLoc_Location();tri=BRep_Tool.Triangulation_s(face,loc);start=len(vs)
 for j in range(1,tri.NbNodes()+1):
  pt=tri.Node(j).Transformed(loc.Transformation());vs.append([pt.X(),pt.Y(),pt.Z()])
 for j in range(1,tri.NbTriangles()+1):
  a,b,c=tri.Triangle(j).Get();fs.append([start+a-1,start+c-1,start+b-1] if face.Orientation()==TopAbs_REVERSED else [start+a-1,start+b-1,start+c-1])
 e.Next()
cm=trimesh.Trimesh(vs,fs,process=True);assert cm.is_watertight and cm.volume>0
cm.export(KIT/'00_Fit_Coupon.stl');write_3mf(cm,KIT/'00_Fit_Coupon.3mf')

# Fit samples are cropped from the actual revised parts, so the sliding profiles match.
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.StlAPI import StlAPI_Writer
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Trsf
rail=read_step(PARTS/'02_Mast.step');slider=read_step(PARTS/'03_Carriage.step')
running_fit=[]
for angle in (20,40,60,90,120,140):
 height=18*(math.cos(math.radians(20))-math.cos(math.radians(angle)))
 tr=gp_Trsf();tr.SetTranslation(gp_Vec(0,0,8.05+height))
 posed=BRepBuilderAPI_Transform(slider,tr,True).Shape()
 gap=BRepExtrema_DistShapeShape(rail,posed).Value();assert abs(gap-.5)<1e-5,(angle,gap)
 running_fit.append(dict(angle_degrees=angle,minimum_gap_mm=gap))
for stem,shape,lo,hi,matrix in (
 ('00_Guide_Rail',rail,(17,-1,50),(37,18,70),np.eye(4)),
 ('00_Guide_Slider',slider,(17,5,0),(37,25,12),rot((1,0,0),-90))):
 cutter=BRepPrimAPI_MakeBox(gp_Pnt(*lo),hi[0]-lo[0],hi[1]-lo[1],hi[2]-lo[2]).Shape()
 sample=BRepAlgoAPI_Common(shape,cutter).Shape();assert BRepCheck_Analyzer(sample).IsValid()
 w=STEPControl_Writer();w.Transfer(sample,STEPControl_AsIs);w.Write(str(KIT/(stem+'.step')))
 BRepMesh_IncrementalMesh(sample,.08,False,.15,True).Perform()
 sv=[];sf=[];ex=TopExp_Explorer(sample,TopAbs_FACE)
 while ex.More():
  face=TopoDS.Face(ex.Current());loc=TopLoc_Location();tri=BRep_Tool.Triangulation_s(face,loc);start=len(sv)
  for j in range(1,tri.NbNodes()+1):
   pt=tri.Node(j).Transformed(loc.Transformation());sv.append([pt.X(),pt.Y(),pt.Z()])
  for j in range(1,tri.NbTriangles()+1):
   a,b,c=tri.Triangle(j).Get();sf.append([start+a-1,start+c-1,start+b-1] if face.Orientation()==TopAbs_REVERSED else [start+a-1,start+b-1,start+c-1])
  ex.Next()
 mesh=trimesh.Trimesh(sv,sf,process=True);assert mesh.is_watertight and mesh.volume>0
 mesh.apply_transform(matrix);mesh.apply_translation(-mesh.bounds[0]);mesh.export(KIT/(stem+'.stl'));write_3mf(mesh,KIT/(stem+'.3mf'))

intro='''<h1>ПОГРУЗЧИК · комплект для печати</h1><p class="lead">12 типов деталей, 15 экземпляров. Масштаб 1:1, миллиметры. Файлы уже повёрнуты для печати и поставлены на Z=0.</p>
<div class="notice"><b>Сначала пробник 00_Fit_Coupon.</b> Он проверяет посадки на вашем принтере: верхний ряд слева направо Ø3,2 / 3,4 / 3,6 / 2,2 / 2,4 мм; нижний — карманы под гайку М3 5,6 / 5,8 / 6,0 мм под ключ, глубина 2,6 мм. Отметки заданы этой схемой, текста на самом пробнике нет. В основных деталях М3 проходит через Ø3,4 мм, гайки входят в шестигранник 5,8 мм. Гайка должна входить рукой, без расклинивания пластика. Масштабировать всю деталь ради отверстий нельзя.</div>
<h2>Что исправлено</h2><p>Квадратные отверстия под четыре винта вил и каретки заменены круглыми Ø3,4 мм. Удалены лишние прямоугольные отверстия старого основания мачты. В каретке сделаны четыре шестигранных кармана под обычные гайки М3, в кривошипе — ещё один. Латунных вставок нет. Прямоугольные рабочие окна, паз пальца, окна датчиков, пазы стяжек и регулировочные пазы ролика сохранены.</p>
<p>Вилы крепятся четырьмя М3×10. Приводной палец — М3×16, гайка М3, трубка Ø4/Ø3,2×11 мм и шайба. Гайки сначала закладываются в карманы, затем устанавливаются вилы и втулка пальца. Гайка пальца должна упираться во втулку: винт не должен зажимать каретку. Винты для штатных ушек и качалки SG90 остаются по размеру сервопривода; центральный винт — из его комплекта.</p>
<h2>Общие настройки для первой печати</h2><p>Сопло 0,4 мм, слой 0,20 мм; для щупа 0,16 мм. Температуры взять из профиля фактического пластика. Brim 5–8 мм для вил, мачты и маленьких проставок. Параметры заполнения в карточках — начальные, они не подтверждают расчётную грузоподъёмность. Поддержки указаны отдельно для каждой ориентации.</p>
<div class="notice"><b>Проверка скольжения до печати мачты.</b> Напечатать по одной детали <a href="00_Guide_Rail.3mf">00_Guide_Rail</a> и <a href="00_Guide_Slider.3mf">00_Guide_Slider</a> из того же пластика и с теми же настройками, что мачту и каретку. Это короткие участки реальных профилей. Направляющая уже стоит вертикально; ползун лежит передней плоскостью вниз, нужны поддержки под его Т-полками. Удалить поддержки и наплыв первого слоя. Ввести Т-ползун с открытого торца направляющей. Он должен двигаться рукой без закусывания; ощутимое усилие означает, что нужна зачистка или коррекция профиля печати. Если требуется менять геометрию, изменять зазор в CAD, а не масштаб всей детали. Зазоры: по X 0,5 мм на каждую сторону; по Y по 0,6 мм спереди и сзади головки ползуна.</div>
<p>Файлы 3MF содержат геометрию и единицы, без профиля принтера, поддержек и G-code. Загружать как модель, выбрать свой принтер и материал, проверить предварительный просмотр слоёв. На принтере со столом меньше 130×174 мм площадки целиком не помещаются.</p>
<h2>Что покупать вместо печати</h2><p>Справочные стойки вынесены в Purchased_Part_References: две резьбовые М3×35, четыре М3×56, четыре высотой 11,70 мм и четыре высотой 10,45 мм. У модели стоек нет настоящей резьбы. Нестандартные высоты нужно обеспечить изготовлением или сочетанием стоек с проставками и пересчётом длины винтов. Печатать эти модели гладкими трубками и вкручивать в них винты с двух сторон нельзя.</p>
<h2>Проверка после изготовления</h2><p>Сначала примерить одну гайку, реальный SG90 и каретку в направляющих. Каретка должна ходить свободно без закусывания по всему ходу. Зазоры направляющих в CAD составляют 0,5 мм на сторону по X и по 0,6 мм до передней и задней поверхностей Т-ползунов по Y; после печати возможна зачистка. Удалить поддержки, наплывы и «слоновью ногу», прочистить отверстия. Кнопка груза крепится М3×10 с низкой полукруглой головкой высотой не более 1,7 мм, щуп — М3×10; оба с обычными гайками; в пластике резьбу нарезать не требуется.</p>
<div class="notice"><b>Границы проверки.</b> CAD-тела и STL проверены на корректность, замкнутость и единую связную деталь, круглые отверстия — по сечению CAD. Ориентации подготовлены; слайсинг на вашем профиле и физическая печать не выполнены. Щуп толщиной 1,2 мм и полка прижима 1 мм требуют пробной печати. Масса груза, усилие SG90 и прочность под нагрузкой не рассчитаны.</div>
<h2>Ориентация и поддержки</h2>'''
page='<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ПОГРУЗЧИК — детали для печати</title><style>body{margin:0;background:#f2f5f5;color:#183540;font:16px/1.6 Segoe UI,Arial}main{max-width:1120px;margin:auto;padding:32px}h1{font-size:36px;line-height:1.2}h2{line-height:1.3}small,.size{color:#55737c}.lead{font-size:20px}.notice{background:#fff1cd;border-left:4px solid #cf9b1e;padding:18px;margin:24px 0}article{background:white;border:1px solid #dbe4e5;border-radius:14px;display:grid;grid-template-columns:360px 1fr;gap:24px;padding:20px;margin:18px 0}article img{width:100%;height:auto;align-self:center}article h2{margin-top:0}a{color:#086a8b;margin-right:18px}@media(max-width:740px){main{padding:18px}article{grid-template-columns:1fr}h1{font-size:28px}}@media print{article{break-inside:avoid}body{background:white}}</style><main>'+intro+''.join(cards)+'</main></html>'
(KIT/'Printing_Guide_RU.html').write_text(page,encoding='utf-8')
(KIT/'PRINT_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
report=dict(printed_types=len(rows),printed_quantity=sum(r[2] for r in rows),coupon=True,guide_fit_samples=True,nominal_guide_clearances_mm=dict(lateral_each=.5,head_back=.6,head_retaining_lip=.6,stem_each=.8),running_fit_checks=running_fit,geometry_checks=checks,round_hole_checks=hole_checks,hex_nut_pocket_checks=hex_checks,prepared_orientations=True,three_mf_roundtrip_bounds_and_units=True,sliced=False,physically_tested=False,threaded_standoff_references=4,brass_inserts=0,ordinary_m3_nut_pockets=5)
(OUT/'Printability_Checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PRINT KIT READY:',len(rows),'types;',len(hole_checks),'round hole sections checked')
