from pathlib import Path
import sys,json,base64,hashlib,math
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/cadlibs'))
import trimesh
from OCP.STEPControl import STEPControl_Reader,STEPControl_Writer,STEPControl_AsIs
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut,BRepAlgoAPI_Fuse
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder,BRepPrimAPI_MakeCone,BRepPrimAPI_MakePrism
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace,BRepBuilderAPI_MakePolygon
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE,TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.gp import gp_Pnt,gp_Dir,gp_Ax2,gp_Trsf,gp_Vec
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
O=R/'simulator';P=(R/'mechanics')/'Fork_Adapters';P.mkdir(exist_ok=True)
src=Path(__file__).resolve()
def box(x,y,z,X,Y,Z):return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),X-x,Y-y,Z-z).Shape()
def cyl(radius,length,x,y,z,d=(0,1,0)):return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(*d)),radius,length).Shape()
def move(shape,x=0,y=0,z=0):
 t=gp_Trsf();t.SetTranslation(gp_Vec(x,y,z));return BRepBuilderAPI_Transform(shape,t,True).Shape()
def mesh(shape):
 unifier=ShapeUpgrade_UnifySameDomain(shape,True,True,True);unifier.Build();shape=unifier.Shape()
 assert BRepCheck_Analyzer(shape).IsValid();BRepMesh_IncrementalMesh(shape,.1,False,.18,True).Perform();ex=TopExp_Explorer(shape,TopAbs_FACE);v=[];f=[]
 while ex.More():
  face=TopoDS.Face(ex.Current());loc=TopLoc_Location();tri=BRep_Tool.Triangulation_s(face,loc)
  if tri:
   offset=len(v)
   for i in range(1,tri.NbNodes()+1):
    p=tri.Node(i).Transformed(loc.Transformation());v.append((p.X(),p.Y(),p.Z()))
   for i in range(1,tri.NbTriangles()+1):
    a,b,c=tri.Triangle(i).Get();f.append((offset+a-1,offset+(c if face.Orientation()==TopAbs_REVERSED else b)-1,offset+(b if face.Orientation()==TopAbs_REVERSED else c)-1))
  ex.Next()
 m=trimesh.Trimesh(v,f,process=True);m.merge_vertices(digits_vertex=5);m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices()
 if not m.is_watertight:
  edges,count=np.unique(np.sort(m.edges,axis=1),axis=0,return_counts=True);print('BAD EDGES',[(m.vertices[e].tolist(),int(n)) for e,n in zip(edges[count!=2],count[count!=2])][:25],flush=True)
 assert m.is_watertight and m.is_winding_consistent and m.volume>0,(m.is_watertight,m.is_winding_consistent,m.volume)
 parent=list(range(len(m.vertices)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for a,b in m.edges_unique:parent[find(int(a))]=find(int(b))
 assert len({find(i) for i in range(len(parent))})==1
 return m
records=[];items=[]
def export(name,shape,quantity=1):
 m=mesh(shape);w=STEPControl_Writer();w.Transfer(shape,STEPControl_AsIs);w.Write(str(P/(name+'.step')))
 bed=m.copy();bed.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]));bed.apply_translation(-bed.bounds[0]);bed.export(P/(name+'_Print_Orientation.stl'))
 records.append(dict(name=name,quantity=quantity,valid_brep=True,watertight=True,single_connected_body=True,volume_mm3=float(m.volume),dimensions_mm=m.extents.tolist()));return m
def add(name,m,profile=None,offset=0,color='#e8b53f'):
 v=(m.vertices+np.array([0,118,2+offset])).astype('<f4');q=dict(name=name,component='moving',color=color,alpha=1,motion='lift',vertices=base64.b64encode(v.tobytes()).decode(),indices=base64.b64encode(m.faces.astype('<u4').tobytes()).decode())
 if profile:q['fork_profile']=profile
 items.append(q)
# Flat rear face: nothing on this printed plate projects towards the mast.
# Broad crossbars join the central strip and both fork rails in the first layer.
spine=box(-35,0,54,35,4,94)
pieces=[box(-8,0,0,8,4,58),box(-9.5,0,18,9.5,4,34)]
for z0,z1 in [(0,8),(30,38)]:pieces.append(box(-27.5,0,z0,27.5,2,z1))
for side in (-1,1):
 lo,hi=(9.5,19.5) if side>0 else (-19.5,-9.5)
 pieces.append(box(lo,0,0,hi,2,58))
 a,b=(19.5,27.5) if side>0 else (-27.5,-19.5)
 pieces.append(box(a,0,0,b,8,58))
for piece in pieces:spine=BRepAlgoAPI_Fuse(spine,piece).Shape()
# Original carriage mounting pattern and full drive-pin travel slot.
for x in (-25,25):
 for z in (70,84):spine=BRepAlgoAPI_Cut(spine,cyl(1.7,4.4,x,-.2,z)).Shape()
spine=BRepAlgoAPI_Cut(spine,box(-16,-.1,70,16,4.1,78)).Shape()
spine=BRepAlgoAPI_Cut(spine,box(-16,-.1,87,-8,4.1,95)).Shape()
# Body of the cargo switch passes through the plate, not through its four
# mounting holes. Its native envelope is X +/-4.022, local Z 12.9..19.1.
spine=BRepAlgoAPI_Cut(spine,box(-4.5,-.2,12,4.5,4.2,20)).Shape()
for x,z in [(-6,23),(6,23),(-5,30.25),(5,30.25)]:spine=BRepAlgoAPI_Cut(spine,cyl(1.7,4.4,x,-.2,z)).Shape()
for side in (-1,1):
 for z in (10,22,36,48):spine=BRepAlgoAPI_Cut(spine,cyl(1.3,6.8,side*19.5,5,z,d=(side,0,0))).Shape()
spineMesh=export('01_Removable_Fork_Spine',spine);add('Fork_spine_removable',spineMesh)
# The taper is horizontal. The underside stays flat and the retaining lip
# follows the same outline across the final 3 mm of the arm.
ARM_BLADE_WIDTH = 6
ARM_TIP_WIDTH = 3
ARM_TIP_Y = 56
ARM_TAPER_LENGTH = 12
ARM_TAPER_START_Y = ARM_TIP_Y - ARM_TAPER_LENGTH
ARM_CENTER_X = 13

def blade_section(center_x, start_y, z, height):
    ys = [start_y]
    if start_y < ARM_TAPER_START_Y:
        ys.append(ARM_TAPER_START_Y)
    ys.append(ARM_TIP_Y)
    half_widths = [
        (ARM_BLADE_WIDTH - (ARM_BLADE_WIDTH - ARM_TIP_WIDTH)
         * max(0, y - ARM_TAPER_START_Y) / ARM_TAPER_LENGTH) / 2
        for y in ys
    ]
    stations = list(zip(ys, half_widths))
    polygon = BRepBuilderAPI_MakePolygon()
    for y, half_width in stations:
        polygon.Add(gp_Pnt(center_x - half_width, y, z))
    for y, half_width in reversed(stations):
        polygon.Add(gp_Pnt(center_x + half_width, y, z))
    polygon.Close()
    face = BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
    return BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, height)).Shape()

for side,label in [(-1,'Left'),(1,'Right')]:
 lo,hi=(9.5,19.5) if side>0 else (-19.5,-9.5)
 arm=box(lo,2,0,hi,8,27)
 arm=BRepAlgoAPI_Fuse(arm,blade_section(side*ARM_CENTER_X,8,0,4)).Shape()
 arm=BRepAlgoAPI_Fuse(arm,blade_section(side*ARM_CENTER_X,53,4,2)).Shape()
 # Side screws preserve the former front envelope while providing a full
 # 6 mm engagement in the side column. Nothing projects behind the spine.
 for z in (10,22):
  arm=BRepAlgoAPI_Cut(arm,cyl(1.7,10.4,side*9.3,5,z,d=(side,0,0))).Shape()
  cone=BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(side*9.5,5,z),gp_Dir(side,0,0)),3,1.7,1.5).Shape();arm=BRepAlgoAPI_Cut(arm,cone).Shape()
 m=export('02_Fork_Arm_'+label,arm)
 for profile,dz in [('low',0),('high',26)]:
  add('Fork_arm_'+label+'_'+profile,m,profile,dz)
  for z in (10,22):
   screw=BRepAlgoAPI_Fuse(cyl(1.5,14.7,side*10.8,5,z,d=(side,0,0)),BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(side*9.5,5,z),gp_Dir(side,0,0)),2.8,1.5,1.3).Shape()).Shape();add('Fork_arm_M3x16_'+label+'_'+str(z)+'_'+profile,mesh(screw),profile,dz,'#a5b2bb')
# Separate tiny spacers preserve the existing button PCB position. The spine
# itself can now start flat on the print bed without supports or floating layers.
spacer=BRepAlgoAPI_Cut(cyl(3.5,1.4,0,-1.4,0),cyl(1.7,1.8,0,-1.6,0)).Shape()
sm=export('03_Cargo_Button_Spacer',spacer,2)
for x,label in [(-6,'Left'),(6,'Right')]:
 placed=sm.copy();placed.apply_translation([x,0,23]);add('Cargo_button_spacer_'+label,placed,color='#aab4be')
coupon=box(0,0,0,42,18,12)
for x,d in [(8,2.5),(21,2.6),(34,2.7)]:coupon=BRepAlgoAPI_Cut(coupon,cyl(d/2,8.8,x,9,12,d=(0,0,-1))).Shape()
export('00_M3_Plastic_Fit_Coupon',coupon)
(O/'Fork_Adaptation_Meshes.json').write_text(json.dumps(items),encoding='utf-8')
report=dict(revision='R5',source=str(src.relative_to(R)),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),parts=records,removable_arms=True,same_arms_for_both_heights=True,arm_screws='4 x M3x16 countersunk, from inner side, directly into PETG',pilot_diameter_mm=2.6,pilot_depth_mm=6.8,nominal_thread_engagement_mm=6,arm_seat_y_mm=2,arm_root_thickness_mm=6,side_column_width_mm=8,upper_station_offset_mm=26,fork_top_low_mm=6,fork_top_high_mm=32,gap_mm=20,outer_span_mm=32,tip_width_mm=ARM_TIP_WIDTH,tip_gap_mm=2*ARM_CENTER_X-ARM_TIP_WIDTH,taper_length_mm=ARM_TAPER_LENGTH,lip_height_mm=2,vertical_cargo_lift_mm=7.703,carriage_fasteners_preserved=True,assembly_y_mm=118,flat_back=True,no_rear_receiver_rails=True,min_crossbar_width_mm=8,button_window_mm=[9,8],button_window_local_z_mm=[12,20],button_spacer_quantity=2,button_spacer_thickness_mm=1.4,spine_requires_supports=False,previous_spine_volume_mm3=35164.48721345762,spine_material_reduction_percent=round(100*(1-spineMesh.volume/35164.48721345762),1),physical_print_tested=False)
(O/'Fork_Adaptation_Checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
# Remove only this task's superseded one-piece adapter exports.
for stem in ('Wide_Low_Fork','Vertical_High_Fork'):
 for suffix in ('.step','.stl','_Print_Orientation.stl'):
  old=P/(stem+suffix)
  if old.exists():old.unlink()
print(json.dumps(report))
