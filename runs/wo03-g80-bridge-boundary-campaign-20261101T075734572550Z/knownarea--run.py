import json,os,subprocess,sys,time
from pathlib import Path
out=Path('build/wo03-g80-washer-area-budget-v1');p=json.loads((out/'plan.json').read_text())
if p['sum_absolute_disk_deficits_mm2']>p['sum_deficit_limit_mm2']:raise ValueError('Pre-execution sum-deficit bound failed')
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
start=time.monotonic()
try:
 child=subprocess.run([sys.executable,str(out/'case.py')],env=env,capture_output=True,text=True,timeout=10)
 (out/'case.log').write_text(child.stdout+child.stderr)
 if child.returncode:raise RuntimeError(f'Known case failed with code {child.returncode}')
 result=json.loads(child.stdout);result['process_wall_s']=time.monotonic()-start
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
except Exception as e:
 (out/'stop.json').write_text(json.dumps({'status':'stopped','error':str(e)},indent=2)+'\n');raise
