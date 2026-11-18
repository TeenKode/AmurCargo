from pathlib import Path
from collections import Counter
import struct, math
root=Path(__file__).resolve().parents[1]/'outputs'/'AmurCargo_Kit'/'Print_Parts'
root.mkdir(parents=True,exist_ok=True)

def build(name,solids,cuts=()):
    # Exact orthogonal CSG on box-boundary coordinates; external faces only.
    axes=[sorted({round(b[i],5) for b in list(solids)+list(cuts)}|{round(b[i+3],5) for b in list(solids)+list(cuts)}) for i in range(3)]
    xs,ys,zs=axes
    def inside(pt,b):return all(b[i]<pt[i]<b[i+3] for i in range(3))
    filled=set()
    for i in range(len(xs)-1):
      for j in range(len(ys)-1):
       for k in range(len(zs)-1):
        pt=((xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2,(zs[k]+zs[k+1])/2)
        if any(inside(pt,b) for b in solids) and not any(inside(pt,b) for b in cuts):filled.add((i,j,k))
    triangles=[]
    for i,j,k in sorted(filled):
      x,X=xs[i:i+2];y,Y=ys[j:j+2];z,Z=zs[k:k+2]
      faces=[((-1,0,0),[(x,y,z),(x,y,Z),(x,Y,Z),(x,Y,z)]),((1,0,0),[(X,y,z),(X,Y,z),(X,Y,Z),(X,y,Z)]),((0,-1,0),[(x,y,z),(X,y,z),(X,y,Z),(x,y,Z)]),((0,1,0),[(x,Y,z),(x,Y,Z),(X,Y,Z),(X,Y,z)]),((0,0,-1),[(x,y,z),(x,Y,z),(X,Y,z),(X,y,z)]),((0,0,1),[(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)])]
      for delta,quad in faces:
       if tuple(a+b for a,b in zip((i,j,k),delta)) not in filled:
        triangles.extend([(delta,(quad[0],quad[1],quad[2])),(delta,(quad[0],quad[2],quad[3]))])
    edges=Counter()
    volume=0
    for normal,t in triangles:
      for a,b in zip(t,t[1:]+t[:1]):edges[tuple(sorted((a,b)))]+=1
      a,b,c=t
      volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    assert all(v==2 for v in edges.values()),name+' non-manifold'
    assert volume>0,name+' bad orientation'
    path=root/(name+'.stl')
    with path.open('wb') as f:
      f.write(name.encode().ljust(80,b' '));f.write(struct.pack('<I',len(triangles)))
      for normal,tri in triangles:f.write(struct.pack('<12fH',*normal,*tri[0],*tri[1],*tri[2],0))
    print(name,'triangles',len(triangles),'closed edges',len(edges),'volume mm3',round(volume))
    return triangles

forks=[(-35,0,0,35,4,70),(-9,4,0,-3,54,4),(3,4,0,9,54,4)]
# Holes 30 mm above matching carriage holes lower the forks below the chassis deck.
cuts=[(x-1.7,-1,z-1.7,x+1.7,5,z+1.7) for x in (-25,25) for z in (46,60)]
models=[('01_Fork_Pair_Gap18',build('01_Fork_Pair_Gap18',forks,cuts))]
mast=[(-45,-15,0,45,65,5),(-40,0,5,40,5,125)]
for x in (-27,27):
 mast.extend([(x-7.3,5,5,x-4.3,16.5,120),(x+4.3,5,5,x+7.3,16.5,120),(x-4.3,13.5,5,x-2.8,16.5,120),(x+2.8,13.5,5,x+4.3,16.5,120)])
cuts=[(x-1.7,y-4,-1,x+1.7,y+4,6) for x in (-35,35) for y in (-8,50)]
cuts.append((-24,-1,25,4,6,85)) # window for the servo shaft and crank
models.append(('02_Mast',build('02_Mast',mast,cuts)))
carriage=[(-35,18,0,35,24,40)]
for x in (-27,27):carriage.extend([(x-4,7,0,x+4,13,40),(x-2,13,0,x+2,18,40)])
cuts=[(x-1.7,17,z-1.7,x+1.7,25,z+1.7) for x in (-25,25) for z in (16,30)]
cuts.append((-12,17,18,12,25,22))
models.append(('03_Carriage',build('03_Carriage',carriage,cuts)))
# Trial servo mounting plate: verify the actual SG90 body and flange dimensions.
mount=[(-23,0,0,23,4,30)]
cuts=[(-12,-1,8,12,5,22)]
cuts += [(x-1,-1,12,x+1,5,18) for x in (-14,14)]
cuts += [(x-1.7,-1,z-1.7,x+1.7,5,z+1.7) for x in (-20,20) for z in (5,25)]
build('04_SG90_Trial_Plate',mount,cuts)
# Connect this arm to the original servo horn; never force it onto the spline.
arm=[(-6,-6,0,24,6,4),(16.6,-1.4,4,19.4,1.4,16)]
cuts=[(-1.6,-1.6,-1,1.6,1.6,5),(7,-1,-1,9,1,5)]
build('05_Crank_R18_Trial',arm,cuts)
bar=[(-40,-7,0,40,13,4)]
cuts=[]
for x in (-22,0,22):
 cuts.extend([(x-3,-3,-1,x+3,3,5),(x-1.8,6,-1,x+1.8,9.6,5)])
cuts.extend([(x-1.7,-1.7,-1,x+1.7,1.7,5) for x in (-35,35)])
build('06_LDR_Trial_Bar',bar,cuts)

# Preview uses the actual STL triangles; parts shown separately, not in assembly.
from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGB',(1350,650),'white');draw=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
for n,(name,tris) in enumerate(models):
 pts=[v for normal,t in tris for v in t]
 def project(v): x,y,z=v;return (0.85*x-0.55*y,0.28*x+0.35*y-z)
 pp=[project(v) for v in pts];xmin=min(x for x,y in pp);xmax=max(x for x,y in pp);ymin=min(y for x,y in pp);ymax=max(y for x,y in pp)
 scale=min(375/(xmax-xmin),470/(ymax-ymin))
 def screen(v):x,y=project(v);return (n*450+35+(x-xmin)*scale,75+(y-ymin)*scale)
 for normal,tri in sorted(tris,key=lambda nt:sum(sum(v) for v in nt[1])):
  if normal[0]*0.55+normal[1]*0.85+normal[2]*0.5<0:continue
  shade=int(175+45*normal[2]-20*normal[0]);color=(max(0,shade-55),min(255,shade+5),min(255,shade+25))
  draw.polygon([screen(v) for v in tri],fill=color)
 draw.text((n*450+30,595),['1. Вилы под перемычку','2. Мачта с направляющими','3. Каретка'][n],font=font,fill='#13354B')
im.save(root.parent/'Parts_Preview.png')
