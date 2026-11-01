import hashlib,json,os,resource,shutil,sys,time,traceback
from pathlib import Path
import numpy as np,yaml
from scripts.wo03_elmer_bridge_diagnostic import ROOT,CONFIG,inputs,read_vtu,reciprocal,sha
from scripts.wo03_owned_process import run_owned,darwin_process_callbacks
out=ROOT/'build/wo03-elmer-bridge-single-continuation-v1'
old=ROOT/'build/wo03-elmer-bridge-diagnostic-v1'
rec={'status':'preflight_started','qualification':False,'original_packet':'stopped; EQUAL separately read-only recovered','native_single_invoked':False}
t0=time.monotonic()
def save():
 u=resource.getrusage(resource.RUSAGE_SELF); rec['parent_cpu_s']=u.ru_utime+u.ru_stime; rec['parent_peak_rss_bytes']=u.ru_maxrss; rec['wall_s']=time.monotonic()-t0; (out/'record.json').write_text(json.dumps(rec,indent=2)+'\n')
try:
 resource.setrlimit(resource.RLIMIT_CPU,(120,120))
 cfg=yaml.safe_load(CONFIG.read_text()); assert not cfg['native_execution_authorized'] and not cfg['required_ci_confirmed']
 driver=ROOT/'scripts/wo03_elmer_bridge_diagnostic.py'; review=old/'preflight-reviewed.json'; recovery=old/'equal-readonly-recovery.json'; archive=old/'equal-readonly-displacements.npz'
 assert sha(driver)=='8a74b89fc5e29811b5148f0602f8ed972942f9a73d33f863e56159e3f7cfd399'; assert sha(review)=='0276b360862ee163e400f322deaa553a50edceee588894e7ccabf9fcd558c071'
 recovered=json.loads(recovery.read_text()); assert recovered['status']=='read_only_evaluation_complete' and recovered['field_result']['strict_force_status']=='pass' and recovered['files_unchanged'] and recovered['prefix_unchanged']; assert sha(archive)==recovered['displacement_archive_sha256']
 for p,h in recovered['file_sha256_after'].items(): assert sha(p)==h, p
 original=json.loads((old/'native/record.json').read_text()); assert original['status']=='stopped' and original['inputs_unchanged'] and original['source_unchanged']
 d=inputs(cfg); pinpaths=[driver,review,recovery,archive,CONFIG,ROOT/cfg['solver'],ROOT/cfg['module'],ROOT/cfg['source_deck'],ROOT/cfg['source_metadata'],ROOT/cfg['input_review'],old/'native/record.json',Path(__file__)]
 rec['sha256_before']={str(p):sha(p) for p in pinpaths}; rec['prefix_sha256_before']=d['prefix_hash']; rec['runtime_sha256_before']=d['runtime_hash']; rec['status']='preflight_passed'; save()
 ar=np.load(archive,allow_pickle=False); ids=ar['node_ids']; values=ar['displacements_m']; assert len(ids)==42715 and set(ids.tolist())==set(d['nodes']) and values.shape==(42715,3) and values.dtype==np.float64 and np.isfinite(values).all(); uequal={int(n):values[i] for i,n in enumerate(ids)}
 case=out/'single'; case.mkdir(); shutil.copytree(d['prepared']/'mesh',case/'mesh'); folder=case/'case'; folder.mkdir(); shutil.copyfile(d['prepared']/'single/case.sif',folder/'case.sif')
 assert sha(folder/'case.sif')==sha(d['prepared']/'single/case.sif')
 for p in (d['prepared']/'mesh').iterdir(): assert sha(p)==sha(case/'mesh'/p.name)
 env=dict(os.environ)
 for n in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'): env[n]='1'
 env['ELMER_HOME']=str(d['prefix'].resolve()); env['ELMER_LIB']=str((d['prefix']/'share/elmersolver/lib').resolve())
 solver=ROOT/cfg['solver']; cmd='import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(120,120));os.execv('+repr(str(solver))+',['+repr(str(solver))+',"case.sif"])'
 rss,desc=darwin_process_callbacks(); rec['status']='native_running'; rec['native_single_invoked']=True; save()
 st=run_owned([sys.executable,'-c',cmd],log_path=folder/'solver.log',status_path=folder/'status.json',wall_limit_s=120,rss_callback=rss,descendants_callback=desc,rss_limit_bytes=2147483648,cwd=folder,env=env)
 rec['native_status']={k:v for k,v in st.items() if k not in ('cpu_samples','rss_samples','descendant_samples','sample_times_s')}
 lines=(folder/'solver.log').read_text(errors='replace').splitlines(); unused='solver 1              linear system abort not converged'; count=sum(x.strip().lower()==unused for x in lines)
 for line in lines:
  x=line.strip().lower()
  if x==unused: continue
  if 'fatal:' in x or 'error:' in x or 'not converged' in x: raise ValueError('Native failure text: '+line)
 log='\n'.join(lines).lower(); assert 'directsolver: using direct method: umfpack' in log and 'elmer solver: all done' in log
 expected=case/'field_t0001.vtu'; found=list(case.rglob('field_t0001.vtu')); assert found==[expected],f'Unexpected VTUs: {found}'; assert 'VtuOutputSolver: Writing the vtu file: ../field_t0001.vtu' in lines
 result,usingle=read_vtu(expected,d['nodes'],d['support'],d['loads'][1]); rec.update(single_result=result,vtu_sha256=sha(expected),ignored_exact_unused_keyword_count=count); save()
 if result['strict_force_status']!='pass': raise ValueError('Strict force unavailable or failed')
 rec['reciprocity']=reciprocal(d['loads'][0],uequal,d['loads'][1],usingle); rec['status']='diagnostic_complete_not_qualified' if rec['reciprocity']['status']=='consistent_with_output_encoding' else 'stopped_reciprocity_outside_encoding_bound'
except Exception as e:
 rec.update(status='stopped',error=repr(e),traceback=traceback.format_exc())
finally:
 try:
  if 'pinpaths' in locals():
   rec['sha256_after']={str(p):sha(p) for p in pinpaths}; rec['sources_unchanged']=rec['sha256_after']==rec['sha256_before']; dd=inputs(cfg); rec['prefix_unchanged']=dd['prefix_hash']==rec['prefix_sha256_before']; rec['runtime_unchanged']=dd['runtime_hash']==rec['runtime_sha256_before']; assert rec['sources_unchanged'] and rec['prefix_unchanged'] and rec['runtime_unchanged']
 except Exception as e: rec.update(status='stopped',postcheck_error=repr(e))
 save()
 print(json.dumps({k:rec.get(k) for k in ('status','error','postcheck_error','single_result','reciprocity','sources_unchanged','prefix_unchanged','runtime_unchanged','parent_cpu_s','wall_s')},indent=2))
