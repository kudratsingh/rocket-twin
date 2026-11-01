"""Illustrative stock mass properties using isolated staged source; no CAD."""
import hashlib,json,math,resource,time
from pathlib import Path
import numpy as np,yaml
from src.vehicle.schema import Vehicle
from src.vehicle.mass import mass_properties

start=time.monotonic(); root=Path(__file__).resolve().parents[2]; conf=root/'configs/studies/wo03-g80-capture-comparison.yaml'; cfg=yaml.safe_load(conf.read_text()); stock=cfg['stock_inventory']; source=root/cfg['source_asrun_73_spec']; staged=root/'build/wo03-g80-integration-staging/checkout'; files=[Path(__file__).resolve(),conf,source,staged/'src/vehicle/schema.py',staged/'src/vehicle/mass.py'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):sha(p) for p in files}; v=Vehicle.model_validate(yaml.safe_load(source.read_text())); original=mass_properties(v); parts={p.id:p for p in v.parts};rho=stock['material_density_kg_m3']; units=1e-3

def body_frame(angle):
 t=math.radians(angle);return np.array([[1.,0,0],[0,math.cos(t),-math.sin(t)],[0,math.sin(t),math.cos(t)]])
def position(station,radius,offset,angle):
 t=math.radians(angle);return np.array([-station*units,(radius*math.cos(t)-offset*math.sin(t))*units,(radius*math.sin(t)+offset*math.cos(t))*units])
def box(label,station,offset,angle,dims):
 L,R,T=(x*units for x in dims);m=rho*L*R*T; rot=body_frame(angle);local=np.diag([m*(R*R+T*T)/12,m*(L*L+T*T)/12,m*(L*L+R*R)/12]);return label,m,position(station,stock['radial_center_mm'],offset,angle),rot@local@rot.T

def cylinder(label,station,offset,angle,od,id_,length,axis):
 ro=od*.0005;ri=id_*.0005;L=length*units;m=rho*math.pi*(ro*ro-ri*ri)*L;ia=m*(ro*ro+ri*ri)/2;it=m*(3*(ro*ro+ri*ri)+L*L)/12;loc=np.diag([ia,it,it] if axis=='axial' else [it,it,ia]);rot=body_frame(angle);pos=np.array([-station*units,0.,0.]) if axis=='axial' else position(station,stock['radial_center_mm'],offset,angle);return label,m,pos,rot@loc@rot.T

def objects_B():
 c=stock['B'];out=[]
 for angle in stock['rotation_axes_deg']:
  for o in c['lug_tangential_centers_mm']:out.append(box('lug',c['lug_station_center_mm'],o,angle,c['lug_axial_radial_tangential_mm']))
  od,L=c['pin_diameter_length_mm'];out.append(cylinder('pin',c['pin_station_mm'],0,angle,od,0,L,'tangential'))
  od,inside,L=c['washer_od_id_thickness_mm']
  for o in c['washer_tangential_centers_mm']:out.append(cylinder('washer',c['washer_station_mm'],o,angle,od,inside,L,'tangential'))
 return out

def objects_C():
 c=stock['C'];out=[]
 for a in stock['rotation_axes_deg']:
  for o in c['strip_tangential_centers_mm']:
   out.append(box('strip',c['strip_station_center_mm'],o,a,c['strip_axial_radial_tangential_mm']))
   for st in c['lap_station_centers_mm']:out.append(box('lap_plate',st,o,a,c['lap_axial_radial_tangential_mm']))
   for st in c['pin_station_centers_mm']:
    od,L=c['pin_diameter_length_mm'];out.append(cylinder('pin',st,o,a,od,0,L,'tangential'))
    od,inside,L=c['washer_od_id_thickness_mm']
    for off in c['washer_pin_axis_offsets_mm']:out.append(cylinder('washer',st,o+off,a,od,inside,L,'tangential'))
 for st in c['ring_station_centers_mm']:
  ro,ri,L=c['ring_outer_inner_thickness_mm'];out.append(cylinder('ring',st,0,0,2*ro,2*ri,L,'axial'))
 return out

def calc(objects,credit):
 M=original.mass_kg;r0=np.array([-original.cg_m,*original.cg_lateral_m]);P=M*r0;Q=original.inertia_kg_m2+M*((r0@r0)*np.eye(3)-np.outer(r0,r0))
 for id in credit:
  p=parts[id];m=p.resolved_mass_kg;r=np.array([-p.cg_station_m,*p.cg_lateral_m]);M-=m;P-=m*r;Q-=m*p.inertia_per_kg_m2+m*((r@r)*np.eye(3)-np.outer(r,r))
 for _,m,r,I in objects:M+=m;P+=m*r;Q+=I+m*((r@r)*np.eye(3)-np.outer(r,r))
 m=.05;r=np.array([-1.212,0.,0.]);M+=m;P+=m*r;Q+=m*((r@r)*np.eye(3)-np.outer(r,r));cg=P/M;I=Q-M*((cg@cg)*np.eye(3)-np.outer(cg,cg));return {'mass_kg':M,'cg_station_m':-cg[0],'cg_lateral_body_m':cg[1:].tolist(),'inertia_body_about_cg_kg_m2':I.tolist(),'growth_mass_kg':m,'growth_station_m':1.212,'credits':credit}

res={}
for name,objs in [('B',objects_B()),('C',objects_C())]:
 counts={}
 for label,m,_,_ in objs:
  x=counts.setdefault(label,{'count':0,'mass_kg':0});x['count']+=1;x['mass_kg']+=m
 res[name]={'stock_inventory':counts,'stock_only_no_credits':calc(objs,[]),'stock_only_with_explicit_credits':calc(objs,stock['source_removal_ids'])}
after={str(p):sha(p) for p in files};u=resource.getrusage(resource.RUSAGE_SELF);out={'status':'illustrative_stock_only_not_installed','source_identity_note':'73 as-run source differs metadata-only from 6b corrected identity','source_asrun_mass_kg':original.mass_kg,'results':res,'inputs_before':before,'inputs_after':after,'inputs_unchanged':before==after,'cpu_s':u.ru_utime+u.ru_stime,'wall_s':time.monotonic()-start,'peak_rss_bytes':u.ru_maxrss,'limitations':'unclipped intersecting stock; cap/guide/body/fin anchors/shields/adhesive and actual removals undefined; not installed mass, CG, inertia or bounds'}; (root/'build/wo03-g80-capture-comparison-v1/stock-mass-record.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(res,indent=2))
