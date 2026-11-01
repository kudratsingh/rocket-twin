import copy,hashlib,json,resource,sys,time
from pathlib import Path
import numpy as np,yaml
root=Path.cwd();sys.path.insert(0,str(root));out=Path(sys.argv[1]).resolve();run=out.parent/'wo03-g80-canopy-stage3-v1'
from src.vehicle.schema import Vehicle
from src.vehicle.mass import mass_properties
from src.sim.inputs import prepare
start=time.process_time()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ident(v):return hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest()
supervision=json.loads((run/'supervision.json').read_text());assert supervision['status']=='completed_not_qualified' and supervision['source_unchanged']
for p,h in supervision['source_before'].items():assert sha(Path(p))==h,p
a=yaml.safe_load((run/'sensitivity.yaml').read_text());b=copy.deepcopy(a);p=next(x for x in b['parts'] if x['id']=='canopy_line_connector_sensitivity');assert p['build'] is None
p['build']={'method':'assembled','cost_usd':0.,'generator':'accounting_allowance','notes':'Estimated unpriced mass allocation for possible lines or connectors; zero is a schema placeholder, not a price or free item. No physical item, packed shape, or CAD mass established.'};p['learn']='Estimated 5 g accounting allocation for possible lines or connectors, not a defined physical part or a supplier tolerance. The inherited mathematical envelope is solely a mass-distribution assumption and does not represent measured packed geometry.'
va=Vehicle.model_validate(a);vb=Vehicle.model_validate(b);ids=json.loads((run/'identities.json').read_text());assert ident(va)==ids['sensitivity'];assert len(vb.parts)==73
q=copy.deepcopy(b);pp=next(x for x in q['parts'] if x['id']=='canopy_line_connector_sensitivity');pp['build']=None;pp['learn']=next(x for x in a['parts'] if x['id']=='canopy_line_connector_sensitivity')['learn'];assert q==a
cfg=yaml.safe_load((run/'cases.yaml').read_text());bench=yaml.safe_load((root/'configs/wo02.yaml').read_text());checks={}
for name,c in cfg['cases'].items():
 c=dict(c)
 if c.pop('vehicle')!='sensitivity':continue
 case={'dt_s':cfg['step_s'],'max_time_s':cfg['horizon_s'],'sensor_noise':False,'elevation_m':float(bench['elevation_m']),'wind_north_mps':0.,'wind_east_mps':0.,'gust_amplitude_mps':0.,**c}
 x=prepare(va,case);y=prepare(vb,case);checks[name]={}
 for key,u,v in zip(x._fields,x,y):
  u=np.asarray(u);v=np.asarray(v);assert u.shape==v.shape and u.dtype==v.dtype and np.array_equal(u,v,equal_nan=True),key
  checks[name][key]={'shape':list(u.shape),'dtype':str(u.dtype),'sha256':hashlib.sha256(u.tobytes()).hexdigest()}
for f in (0.,1.):
 x=mass_properties(va,f);y=mass_properties(vb,f);assert x.mass_kg==y.mass_kg and x.cg_m==y.cg_m and x.cg_lateral_m==y.cg_lateral_m and np.array_equal(x.inertia_kg_m2,y.inertia_kg_m2) and x.budget_kg==y.budget_kg
cad=hashlib.sha256(b''.join(p.read_bytes() for p in sorted((root/'src/cad').glob('*.py')))).hexdigest();assert cad=='344f646f81e15d42ab54e7d996179581d638c6046bf1d006935b028709eca53f'
(out/'sensitivity-metadata.yaml').write_text(yaml.safe_dump(b,sort_keys=False));result={'original_identity':ident(va),'corrected_identity':ident(vb),'cad_revision_sha256':cad,'corrected_sha256':sha(out/'sensitivity-metadata.yaml'),'original_sha256':sha(run/'sensitivity.yaml'),'scope':'Only allowance learn/build fields changed; all sensitivity case prepare arrays bitwise identical in current pinned source; loaded/burnout mass CG tensor budget identical. Nominal case uses unchanged original nominal spec.','builder_array_checks':checks,'original_build_check_historical':False,'corrected_has_all_build_metadata':all(x.build is not None for x in vb.parts),'cost_zero_is_unpriced_placeholder':True,'acceptance':False,'cpu_s':time.process_time()-start,'source_before_after_match':all(sha(Path(p))==h for p,h in supervision['source_before'].items())};assert result['source_before_after_match'];(out/'equivalence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'identity':result['corrected_identity'],'cpu_s':result['cpu_s'],'arrays':{k:len(v) for k,v in checks.items()},'all_build':result['corrected_has_all_build_metadata']}))
