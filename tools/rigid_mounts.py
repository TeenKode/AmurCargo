# Loaded by build_photo.py after component placement, before all exports.
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepCheck import BRepCheck_Analyzer
component('mechanical_fixings','Крепёж SG90, мачты и датчиков','Авторские номинальные М2/М3 и скачанные М3×12','Резьба условная; размеры стержней и посадочные оси заданы')
component('upper_structure','Стойки и крепёж верхней площадки','Четыре стойки М3×56, винты снизу и сверху','Площадка прикручена к четырём стойкам; стойки закреплены на несущей площадке')
component('carrier','Несущая площадка электроники','Авторская пластина 130×174×4 и четыре проставки 8 мм','Четыре потайных М3×20 в существующие отверстия шасси')

def bolt(name,dia,length,tip,axis=(0,0,1),head_r=None,head_h=None,key='mechanical_fixings',motion=None):
 axis=np.array(axis,dtype=float);tip=np.array(tip,dtype=float);head=tip+axis*length
 sh=fuse([cyl(dia/2,length,*tip,d=tuple(axis)),cyl(head_r or dia*.92,head_h or dia,*head,d=tuple(axis))])
 add(key,name,sh,'#a5b2bb',motion=motion);return sh
def washer(name,x,y,z):
 sh=BRepAlgoAPI_Cut(cyl(3.5,.5,x,y,z),cyl(1.7,2,x,y,z-.5)).Shape();add('mechanical_fixings',name,sh,'#b9c4ca');return sh
def nut(name,flat,thick,hole,point,axis=(0,0,1),key='mechanical_fixings',motion=None):
 axis=np.array(axis,dtype=float);u=np.array([1.,0,0]) if abs(axis[0])<.5 else np.array([0.,1,0]);v=np.cross(axis,u);p=np.array(point,dtype=float)
 poly=BRepBuilderAPI_MakePolygon()
 for a in range(6):
  pt=p+flat/math.sqrt(3)*(math.cos(a*math.pi/3)*u+math.sin(a*math.pi/3)*v);poly.Add(gp_Pnt(*pt))
 poly.Close();sh=BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(poly.Wire()).Face(),gp_Vec(*(axis*thick))).Shape()
 sh=BRepAlgoAPI_Cut(sh,cyl(hole,thick+1,*(p-axis*.5),d=tuple(axis))).Shape();add(key,name,sh,'#b0bbc2',motion=motion);return sh
def flat_screw(name,length,wide_face,axis,key='mechanical_fixings'):
 a=np.array(axis,dtype=float);p=np.array(wide_face)-a*length
 sh=fuse([cyl(1.5,length-1.7,*p,d=tuple(a)),BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(*(np.array(wide_face)-a*1.7)),gp_Dir(*a)),1.5,3,1.7).Shape()])
 add(key,name,sh,'#aebbc4');return sh

# Main mast directly bears on the chassis. Four screws use the actual mesh's holes.
for i,(x,y) in enumerate(MAST_HOLES):
 washer('Mast_base_washer_'+str(i),x,y,52.95)
 add('mechanical_fixings','Mast_base_M3x12_'+str(i),step('Screw_M3x12.step'),'#aab7c0',translation(x,y,53.45))
 if i<2:nut('Mast_base_nut_'+str(i),5.5,2.4,1.65,(x,y,42.54))
for i,z in enumerate((84.75,111.95)):
 bolt('SG90_ear_M2x10_'+str(i),2,10,(-12,97,z),(0,-1,0),1.75,2)
 nut('SG90_ear_nut_'+str(i),4,1.6,1.1,(-12,94,z),(0,1,0))
for x in (-38,10):
 for z in (83,125):
  bolt('SG90_bracket_M3x12_'+str(x)+'_'+str(z),3,12,(x,102,z),(0,-1,0),2.75,3)
  nut('SG90_bracket_nut_'+str(x)+'_'+str(z),5.5,2.4,1.65,(x,99,z),(0,1,0))

# Separate carrier: eight millimetres above the stock plate, clear of stock fasteners.
CARRIER_HOLES=[(-44.37235,-82.16035),(44.59835,-82.1604),(-42.379,70.8394),(42.5884,70.8394)]
carrier=box(-65,-97,55.95,65,77,59.95)
for x0,x1 in ((-66,-50),(50,66)):carrier=BRepAlgoAPI_Cut(carrier,box(x0,-1,55,x1,71,61)).Shape()
for x,y in CARRIER_HOLES:
 carrier=BRepAlgoAPI_Cut(carrier,cyl(1.7,6,x,y,55)).Shape()
 cone=BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(x,y,58.25),gp_Dir(0,0,1)),1.5,3,1.7).Shape();carrier=BRepAlgoAPI_Cut(carrier,cone).Shape()
for x in (-60,60):
 for y in (-75,75):carrier=BRepAlgoAPI_Cut(carrier,cyl(1.7,6,x,y,55)).Shape()
board_holes=[(x-50.67,y+3.71) for x,y in ((2.54,13.97),(17.78,66.04),(45.72,66.04),(50.8,13.97))]+[(x+8.5,y+13.5) for x,y in ((3,3),(3,40),(40,3),(40,40))]
carrier=BRepAlgoAPI_Cut(carrier,cyl(1.7,6,5.2,17.68,55)).Shape()
for x,y in board_holes:
 carrier=BRepAlgoAPI_Cut(carrier,cyl(1.7,6,x,y,55)).Shape()
 carrier=BRepAlgoAPI_Cut(carrier,BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(x,y,55.95),gp_Dir(0,0,1)),3,1.5,1.7).Shape()).Shape()
# Captive battery bank: end/side stops plus two straps through four slots.
carrier=fuse([carrier,box(-46,-93,59.95,46,-90.7,62.95),box(-46,-3.3,59.95,46,-1,62.95),box(-47.2,-89,59.95,-45.3,-5,62.95),box(45.3,-89,59.95,47.2,-5,62.95)])
for x in (-48.5,48.5):
 for y in (-65,-30):carrier=BRepAlgoAPI_Cut(carrier,box(x-.65,y-1.5,55,x+.65,y+1.5,61)).Shape()
add('carrier','Electronics_carrier',carrier,'#567687');designed['15_Electronics_Carrier']=transform(carrier,translation(65,97,-55.95))
riser=BRepAlgoAPI_Cut(cyl(3.5,8),cyl(1.7,10,0,0,-1)).Shape();designed['18_Carrier_Riser']=riser
for i,(x,y) in enumerate(CARRIER_HOLES):
 add('carrier','Carrier_riser_'+str(i),riser,'#9caeb9',translation(x,y,47.95))
 flat_screw('Carrier_M3x20_'+str(i),20,(x,y,59.95),(0,0,1),'carrier')
 nut('Carrier_nut_'+str(i),5.5,2.4,1.65,(x,y,42.54),key='carrier')

post=BRepAlgoAPI_Cut(cyl(3,56),cyl(1.6,58,0,0,-1)).Shape();designed['16_Upper_Tray_Post']=post
for x in (-60,60):
 for y in (-75,75):
  suffix=str(x)+'_'+str(y);add('upper_structure','Tray_post_'+suffix,post,'#8d9ba5',translation(x,y,59.95))
  bolt('Tray_post_bottom_M3x10_'+suffix,3,10,(x,y,65.95),(0,0,-1),2.75,3,key='upper_structure')
  sh=BRepAlgoAPI_Cut(cyl(3.5,.5,x,y,118.95),cyl(1.7,2,x,y,118.5)).Shape();add('upper_structure','Tray_top_washer_'+suffix,sh,'#b9c4ca')
  bolt('Tray_top_M3x12_'+suffix,3,12,(x,y,107.45),head_r=2.75,head_h=3,key='upper_structure')
component('breadboard_tape','Крепление макетки на скотч','Две полоски двустороннего скотча толщиной 0,5 мм','По указанию пользователя; приклеены между площадкой и плоским основанием макетки')
for x in (-18,18):add('breadboard_tape','Breadboard_tape_'+str(x),box(x-5,-87,118.95,x+5,67,119.45),'#cbd6da')
# Both PCBs now use all four of their own mounting holes, on the separate carrier.
for i,(x,y) in enumerate(board_holes):
 flat_screw('PCB_lower_M3x8_'+str(i),8,(x,y,55.95),(0,0,-1))
 pcb_top=73.3 if i<4 else 72
 if i not in (0,3,4):bolt('PCB_upper_M3x6_'+str(i),3,6,(x,y,pcb_top-6),head_r=2.75,head_h=3)
component('uno_clip','Боковой прижим Arduino','Авторский прижим и М3×25','Две задние точки на винтах, передняя часть удерживается прижимом; разъёмы свободны')
clip=fuse([box(2.67,12.68,59.95,7.8,22.68,74.3),box(2,12.68,73.3,7.8,22.68,74.3)])
clip=BRepAlgoAPI_Cut(clip,cyl(1.7,17,5.2,17.68,59)).Shape();add('uno_clip','UNO_edge_clip',clip,'#637f90')
designed['19_UNO_Edge_Clip']=transform(clip,translation(-2,-12.68,-59.95))
bolt('UNO_clip_M3x25',3,25,(5.2,17.68,49.3),head_r=2.75,head_h=3)
nut('UNO_clip_nut',5.5,2.4,1.65,(5.2,17.68,53.55))
component('battery_restraint','Стяжки аккумуляторного блока','Две стяжки в пазах несущей площадки','Упрощённый контур; удерживают элементы и держатели в ограничителях')
for y in (-65,-30):
 strap=fuse([box(-48.9,y-1,55.15,48.9,y+1,55.95),box(-48.9,y-1,55.95,-48.1,y+1,82.58),box(48.1,y-1,55.95,48.9,y+1,82.58),box(-48.9,y-1,81.78,48.9,y+1,82.58)])
 add('battery_restraint','Battery_strap_'+str(y),strap,'#343e46')

# Sensor carrier and solder pads; the optical components are not loose in a plastic hole.
component('sensor_board','Монтажная плата датчиков','Авторская плата 80×20×1,6 мм','Закреплена вместе с планкой; выводы датчиков припаяны к контактным площадкам')
pcb=box(-40,88.35735,8.34,40,108.35735,9.94)
for x in (-23.8757,24.10195):pcb=BRepAlgoAPI_Cut(pcb,cyl(1.7,3,x,95.35735,8)).Shape()
for x in (-16,0,16):
 for dx in (-1.9,1.9):pcb=BRepAlgoAPI_Cut(pcb,cyl(.45,3,x+dx,95.35735,8)).Shape()
 for dx in (-.68,1.06):pcb=BRepAlgoAPI_Cut(pcb,cyl(.45,3,x+dx,103.15735,8)).Shape()
add('sensor_board','Sensor_PCB',pcb,'#276c58')
for i,x in enumerate((-23.8757,24.10195)):bolt('Sensor_bar_M3x8_'+str(i),3,8,(x,95.35735,13.94),(0,0,-1),2.75,3)

# Cargo switch: four pins on a small PCB, supported by two fork bosses.
component('cargo_switch_mount','Плата и крепёж кнопки груза','Плата 18×18×1,6, два М3×10 с гайками','Плата на двух бобышках вил; упругий щуп закреплён отдельно двумя М3×10 с гайками')
pcb=box(-9,115,10,9,116.6,28)
for x in (-6,6):pcb=BRepAlgoAPI_Cut(pcb,cyl(1.7,3,x,114.5,25,d=(0,1,0))).Shape()
for x,z in [(-3.5,20.2),(-3.5,15.2),(3.5,20.8),(3.5,15.8)]:pcb=BRepAlgoAPI_Cut(pcb,cyl(.7,3,x,114.5,z,d=(0,1,0))).Shape()
add('cargo_switch_mount','Cargo_switch_PCB',pcb,'#276c58',motion='lift')
for x in (-6,6):
 bolt('Cargo_switch_M3x10_'+str(x),3,10,(x,125,25),(0,-1,0),2.85,1.65,motion='lift')
 nut('Cargo_switch_nut_'+str(x),5.5,2.4,1.5,(x,122,25),(0,1,0),key='mechanical_fixings',motion='lift')
for x in (-5,5):
 bolt('Feeler_anchor_M3x10_'+str(x),3,10,(x,113.2,32.25),(0,1,0),2.75,3,motion='lift')
 nut('Feeler_anchor_nut_'+str(x),5.5,2.4,1.5,(x,115.6,32.25),(0,1,0),key='mechanical_fixings',motion='lift')

# Horn fixed to its shaft through an access hole; the printed crank uses two horn holes.
bolt('Horn_central_M2x6',2,6,(-12,98,93),(0,1,0),1.75,2,motion='crank')
for radius in (7,13):
 x=-12+radius*math.cos(math.radians(70));z=93-radius*math.sin(math.radians(70))
 bolt('Crank_horn_M1_4x6_'+str(radius),1.4,6,(x,102,z),(0,1,0),1.3,1.2,motion='crank')

# Caster plate and chassis hole grids have slightly different pitches; centre them first.
component('caster_fixings','Крепёж опорного ролика','Четыре М3×16, шайбы и гайки','Оси выбраны внутри пересечения штатных отверстий ролика и шасси')
for i,(x,y) in enumerate(((-14.6498,-91.40595),(14.8582,-91.40595),(-14.6498,-67.905425),(14.8582,-67.905425))):
 sh=BRepAlgoAPI_Cut(cyl(3.5,.5,x,y,47.95),cyl(1.7,2,x,y,47.5)).Shape();add('caster_fixings','Caster_washer_'+str(i),sh,'#b9c4ca')
 bolt('Caster_M3x16_'+str(i),3,16,(x,y,32.45),head_r=2.75,head_h=3,key='caster_fixings')
 nut('Caster_nut_'+str(i),5.5,2.4,1.65,(x,y,34.57555),key='caster_fixings')

# Structural interfaces are checked separately from collision checks.
joint_pairs=[('SG90','SG90_mount_plate'),('SG90_mount_plate','Mast'),('Mast','User_RobotChassis.001_0'),('Electronics_carrier','Carrier_riser_0'),('Electronics_tray','Tray_post_-60_-75'),('MB102_envelope','Breadboard_tape_-18'),('Electronics_tray','Breadboard_tape_-18'),('Sensor_bar','Sensor_PCB'),('Sensor_PCB','Sensor_standoff_0'),('Fork_pair','Cargo_switch_PCB'),('Fork_pair','Cargo_feeler'),('Drive_pin_sleeve_4x3_2x11','Drive_pin_nut_M3'),('Drive_pin_M3x16','Drive_pin_retaining_washer')]
index={it['name']:it for it in items};joint_rows=[]
for i in range(4):joint_pairs.append(('Mast_base_M3x12_'+str(i),'Mast_base_washer_'+str(i)))
for i in range(2):joint_pairs.append(('SG90_ear_M2x10_'+str(i),'SG90'))
for x in (-38,10):
 for z in (83,125):joint_pairs.append(('SG90_bracket_M3x12_'+str(x)+'_'+str(z),'SG90_mount_plate'))
for x in (-60,60):
 for y in (-75,75):
  suffix=str(x)+'_'+str(y)
  joint_pairs.extend([('Tray_post_bottom_M3x10_'+suffix,'Electronics_carrier'),('Tray_top_M3x12_'+suffix,'Tray_top_washer_'+suffix),('Tray_post_'+suffix,'Electronics_tray'),('Tray_post_'+suffix,'Electronics_carrier')])
for x in (-25,25):
 for z in (48,62):joint_pairs.append(('Fork_screw_'+str(x)+'_'+str(z),'Fork_pair'))
for i in range(4):joint_pairs.extend([('Caster_M3x16_'+str(i),'Caster_washer_'+str(i)),('Carrier_M3x20_'+str(i),'Electronics_carrier')])
for a,b in joint_pairs:
 if a not in index or b not in index:continue
 dist=BRepExtrema_DistShapeShape(index[a]['shape'],index[b]['shape']).Value()
 joint_rows.append(dict(a=a,b=b,gap_mm=dist));assert dist<.011,(a,b,dist)
(OUT/'Mounting_Audit.json').write_text(json.dumps(dict(mast_shift_toward_chassis_mm=20,mast_footprint_mm=[100,34,5],mast_base_holes_xy=MAST_HOLES,carrier_holes_xy=CARRIER_HOLES,servo_ear_screws='2 x M2x10',servo_bracket_screws='4 x M3x12',upper_tray_posts='4 x M3, length 56 mm',joint_contacts=joint_rows,thread_representation='simplified, not a thread fit check'),ensure_ascii=False,indent=2),encoding='utf-8')
