import hashlib,json,sys,time,resource
from pathlib import Path
import yaml,numpy as np
root=Path.cwd();sys.path.insert(0,str(root));out=Path(sys.argv[2]).resolve()
from src.vehicle.schema import Vehicle
from src.vehicle.mass import mass_properties
from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import evaluate_preliminary
from scripts.wo03_integrated_report import add_growth
ids=json.loads((out/'identities.json').read_text());vs={}
for n in ('nominal','sensitivity'):
 v=Vehicle.model_validate(yaml.safe_load((out/(n+'.yaml')).read_text())); assert hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest()==ids[n];vs[n]=v
started=time.monotonic()
if sys.argv[1]=='static':
 result={}
 for name,v in vs.items():
  ref=evaluate_preliminary(v,compare=True);cp=center_of_pressure(v);states={}
  for f in (0.,1.):
   m=mass_properties(v,f);g=add_growth(m,.05,1.212);g['static_margin_cal']=(cp-g['cg_station_m'])/v.airframe['body_diameter_m'];states[str(f)]={'mass_kg':m.mass_kg,'cg_m':m.cg_m,'inertia_kg_m2':m.inertia_kg_m2.tolist(),'static_margin_cal':(cp-m.cg_m)/v.airframe['body_diameter_m'],'full_growth':g}
  result[name]={'independent_static':ref,'states':states}
else:
 import jax
 from scripts.wo02_sim import metrics
 from src.sim.inputs import prepare
 from src.sim import env
 from src.sim.reference import reference_flight
 cfg=yaml.safe_load((out/'cases.yaml').read_text());setting=yaml.safe_load((root/'configs/wo02.yaml').read_text());result=[]
 for name,c in cfg['cases'].items():
  c=dict(c);v=vs[c.pop('vehicle')]; case={'dt_s':cfg['step_s'],'max_time_s':cfg['horizon_s'],'sensor_noise':False,'elevation_m':float(setting['elevation_m']),'wind_north_mps':0.,'wind_east_mps':0.,'gust_amplitude_mps':0.,**c};p=prepare(v,case);final,t=env.rollout(p,jax.random.PRNGKey(0),steps=36000);final.rigid.block_until_ready();t=np.asarray(t);m=metrics(final,t,p)
  if not m['finite'] or not np.isfinite(t).all() or m['guide_exit_s']<0: raise ValueError('invalid trajectory '+name)
  hits=np.flatnonzero(t[:,38]>0);landing=None
  if len(hits):
   i=max(int(hits[0])-1,0);vn,ve,vd=map(float,t[i,4:7]);landing={'signed_down_mps':vd,'total_ground_speed_mps':float(np.linalg.norm([vn,ve,vd])),'vertical_screen_6mps':0<=vd<=6,'total_6mps_diagnostic':float(np.linalg.norm([vn,ve,vd]))<=6,'sample':'last pre-landed, 5ms'}
  ref=reference_flight(v,case) if name=='nominal_calm' else None;errs={k:abs(m[k]-ref[k])/max(abs(ref[k]),1e-9) for k in ('apogee_agl_m','apogee_time_s')} if ref else None
  result.append({'name':name,'case':case,'metrics':m,'landing':landing,'guide_pass':m['guide_exit_mps']>=15,'rocketpy':ref,'reference_errors':errs,'reference_5pct_pass':max(errs.values())<=.05 if errs else None});(out/'flight-partial.json').write_text(json.dumps(result,indent=2)+'\n');print(name,flush=True)
u=resource.getrusage(resource.RUSAGE_SELF);(out/(sys.argv[1]+'-result.json')).write_text(json.dumps({'result':result,'cpu_s':u.ru_utime+u.ru_stime,'wall_s':time.monotonic()-started,'peak_rss_bytes':u.ru_maxrss},indent=2)+'\n')
