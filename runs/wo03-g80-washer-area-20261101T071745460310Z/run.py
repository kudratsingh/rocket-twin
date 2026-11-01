import json, os, resource, subprocess, sys, time
from pathlib import Path
out=Path('build/wo03-g80-washer-area-known-v1'); plan=json.loads((out/'plan.json').read_text()); records=[]; start=time.monotonic()
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
try:
    for level in plan['levels']:
        before=resource.getrusage(resource.RUSAGE_CHILDREN)
        child=subprocess.run([sys.executable,str(out/'case.py'),str(level['outer_segments']),str(level['inner_segments'])],capture_output=True,text=True,timeout=10,env=env)
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        used=(after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime)
        row={'level':level,'returncode':child.returncode,'measured_child_cpu_s':used,'stdout':child.stdout,'stderr':child.stderr}
        records.append(row);(out/'progress.json').write_text(json.dumps(records,indent=2)+'\n')
        if child.returncode:raise RuntimeError('invalid case; see progress.json')
        result=json.loads(child.stdout)
        if abs(result['integration_minus_arc_area_mm2'])>1e-8:raise ValueError('analytic/integration disagreement')
        if sum(r['measured_child_cpu_s'] for r in records)>10:raise RuntimeError('insufficient remaining CPU reservation for final case')
    (out/'result.json').write_text(json.dumps({'status':'three_levels_complete','levels':[json.loads(r['stdout']) for r in records],'child_cpu_s':sum(r['measured_child_cpu_s'] for r in records),'total_wall_s':time.monotonic()-start},indent=2)+'\n')
except Exception as exc:
    (out/'stop.json').write_text(json.dumps({'error':str(exc),'completed':len(records)},indent=2)+'\n');raise
