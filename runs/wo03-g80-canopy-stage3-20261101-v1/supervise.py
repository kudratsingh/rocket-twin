import hashlib,json,os,sys
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root));out=Path(sys.argv[1]).resolve()
from scripts.wo03_owned_process import run_owned,darwin_process_callbacks
files=[out/x for x in ['prepare.py','worker.py','supervise.py','nominal.yaml','sensitivity.yaml','identities.json','cases.yaml']]+[root/'configs/wo02.yaml',root/'configs/sim-model.yaml',root/'scripts/wo02_sim.py',root/'scripts/wo03_integrated_report.py',root/'scripts/wo03_owned_process.py']
for folder in ['src/sim','src/vehicle','src/cad']:files+=list((root/folder).glob('*.py'))
import yaml
motor=yaml.safe_load((out/'nominal.yaml').read_text())['motor']['curve'];files += [root/motor,(root/motor).with_suffix('.yaml')]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
before=hashes();rec={'status':'started','source_before':before,'limits':{'setup_reserve_cpu_s':30,'static_cpu_wall_s':60,'flight_cpu_wall_s':120,'rss_bytes':2147483648,'total_ceiling_cpu_s':600,'one_worker_requested':True},'acceptance':False};(out/'supervision.json').write_text(json.dumps(rec,indent=2)+'\n')
env=dict(os.environ)
for x in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS'):env[x]='1'
rss,desc=darwin_process_callbacks()
try:
 for name,cap in [('static',60),('flight',120)]:
  launch=f'import resource,os,sys;resource.setrlimit(resource.RLIMIT_CPU,({cap},{cap}));os.execv(sys.executable,[sys.executable,{str(out/"worker.py")!r},{name!r},{str(out)!r}])'
  run_owned([sys.executable,'-c',launch],log_path=out/(name+'.log'),status_path=out/(name+'-status.json'),wall_limit_s=cap,rss_callback=rss,descendants_callback=desc,rss_limit_bytes=2147483648,cwd=root,env=env)
  result=json.loads((out/(name+'-result.json')).read_text());assert name!='flight' or len(result['result'])==5
  if hashes()!=before:raise ValueError('source changed')
 rec['status']='completed_not_qualified'
except Exception as e:
 rec.update(status='stopped',error=repr(e));raise
finally:
 rec['source_after']=hashes();rec['source_unchanged']=rec['source_after']==before
 for name in ('static','flight'):
  p=out/(name+'-status.json')
  if p.exists():rec[name]=json.loads(p.read_text())
 (out/'supervision.json').write_text(json.dumps(rec,indent=2)+'\n')
