"""Read-only A-field audit with independently derived affine reference."""
import hashlib,json,math,os,re,resource,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(10,10));start=time.monotonic()
import numpy as np,vtk,yaml
from vtk.util.numpy_support import vtk_to_numpy
vtk.vtkSMPTools.Initialize(1);vtk.vtkMultiThreader.SetGlobalMaximumNumberOfThreads(1)
root=Path.cwd();vec=root/'build/wo03-elmer-thermal-comparison-io-replan';classic=root/'build/wo03-elmer-classic-comparison-prepare-v5';out=root/'build/wo03-elmer-local-error-audit-v1';config=root/'configs/studies/wo03-thermal-error-isolation.yaml'
paths=[config,vec/'record.json',classic/'record.json']
for source in (vec,classic):
 for n in (2,4,8):paths += [source/'A'/str(n)/'case.sif',source/'A'/str(n)/'mesh/mesh.nodes',source/'A'/str(n)/'mesh/field_t0001.vtu']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths};cfg=yaml.safe_load(config.read_text());rows=[]
def block(s,name):
 m=re.search(r'^'+re.escape(name)+r'\s*\n(.*?)^End\s*$',s,re.M|re.S)
 if not m:raise ValueError('Missing unique SIF block '+name)
 return m.group(1)
def val(b,key):
 x=re.findall(r'^\s*'+re.escape(key)+r'\s*=\s*Real\s+([^\s]+)',b,re.M|re.I)
 if len(x)!=1:raise ValueError('Missing unique literal '+key)
 return float(x[0])
for label,source in [('vec',vec),('classic',classic)]:
 for level in (2,4,8):
  p=source/'A'/str(level);s=(p/'case.sif').read_text();k=val(block(s,'Material 1'),'Heat Conductivity');hot=val(block(s,'Boundary Condition 1'),'Temperature');cold=val(block(s,'Boundary Condition 2'),'External Temperature');h=val(block(s,'Boundary Condition 2'),'Heat Transfer Coefficient')
  raw=[line.split() for line in (p/'mesh/mesh.nodes').read_text().splitlines()];nodes=np.array([[float(z) for z in a[2:5]] for a in raw]);
  if len(raw)!=len({int(a[0]) for a in raw}):raise ValueError('duplicate native node id')
  lengths=np.ptp(nodes,axis=0);L=lengths[0]
  if not (np.allclose(lengths,cfg['dimensions_m'],rtol=0,atol=1e-14) and abs(nodes[:,0].min())<1e-14 and k==cfg['conductivity_w_m_k'] and hot==cfg['case_a']['hot_prescribed_k'] and cold==cfg['case_a']['cold_bulk_k'] and h==cfg['case_a']['h_w_m2_k']):raise ValueError('SIF, SI unit or source reference mismatch')
  reader=vtk.vtkXMLUnstructuredGridReader();reader.SetFileName(str(p/'mesh/field_t0001.vtu'));reader.Update();grid=reader.GetOutput();xyz=vtk_to_numpy(grid.GetPoints().GetData());names=[grid.GetPointData().GetArrayName(i) for i in range(grid.GetPointData().GetNumberOfArrays())]; matches=[name for name in names if name and name.lower()=='temperature']; assert len(matches)==1; t=vtk_to_numpy(grid.GetPointData().GetArray(matches[0]))
  if t.dtype!=np.float64 or not np.isfinite(t).all() or not np.isfinite(xyz).all() or len(nodes)!=len(xyz):raise ValueError('VTU dtype/count/finite failure')
  lookup={tuple(round(float(x),12) for x in point):i for i,point in enumerate(xyz)}
  if len(lookup)!=len(xyz):raise ValueError('nonunique VTU coordinates')
  ids=[lookup[tuple(round(float(x),12) for x in point)] for point in nodes];mapped=xyz[ids];temperatures=t[ids];mapping_error=float(np.max(np.abs(mapped-nodes)))
  if mapping_error>1e-12:raise ValueError('coordinate mapping exceeds retained tolerance')
  q=(hot-cold)/(L/k+1/h);slope=-q/k;expected=hot+slope*nodes[:,0];err=temperatures-expected;inds=np.argmax(np.abs(err));hotset=np.isclose(nodes[:,0],0,rtol=0,atol=1e-13);coldset=np.isclose(nodes[:,0],L,rtol=0,atol=1e-13);interior=~(hotset|coldset);strict_interior=np.all((nodes>1e-13)&(nodes<lengths-1e-13),axis=1)
  def maximum(mask):
   which=np.flatnonzero(mask)[np.argmax(np.abs(err[mask]))]
   return {'max_abs_error_k':float(abs(err[which])),'signed_error_k':float(err[which]),'xyz_m':nodes[which].tolist(),'count':int(np.count_nonzero(mask))}
  design=np.column_stack([np.ones(len(nodes)),nodes[:,0]/lengths[0],nodes[:,1]/lengths[1],nodes[:,2]/lengths[2]]);fit=np.linalg.lstsq(design,temperatures,rcond=None)[0];pred=design@fit;slopes=fit[1:]/lengths
  row={'path':label,'level':level,'node_count':len(nodes),'literal_sif_si':{'conductivity_w_m_k':k,'hot_k':hot,'cold_bulk_k':cold,'h_w_m2_k':h,'lengths_m':lengths.tolist()},'analytic_flux_w_m2':q,'analytic_x_slope_k_m':slope,'max_error':maximum(np.ones(len(nodes),dtype=bool)),'hot_boundary':maximum(hotset),'cold_boundary':maximum(coldset),'x_interior':maximum(interior),'strict_volume_interior':maximum(strict_interior),'affine_fit':{'intercept_k':float(fit[0]),'intercept_minus_analytic_k':float(fit[0]-hot),'x_slope_k_m':float(slopes[0]),'x_slope_minus_analytic_k_m':float(slopes[0]-slope),'y_slope_k_m':float(slopes[1]),'z_slope_k_m':float(slopes[2]),'max_abs_fit_residual_k':float(np.max(np.abs(temperatures-pred))),'rms_fit_residual_k':float(np.sqrt(np.mean((temperatures-pred)**2)))},'native_mesh_coordinate_type':'text decimal binary64 parsed','vtu_coordinate_type':str(xyz.dtype),'vtu_temperature_type':str(t.dtype),'max_mapped_coordinate_difference_m':mapping_error,'vtk_version':vtk.vtkVersion.GetVTKVersion(),'vtk_max_threads':vtk.vtkMultiThreader.GetGlobalMaximumNumberOfThreads()};rows.append(row)
after={str(p):sha(p) for p in paths};
if after!=before:raise ValueError('Saved source changed during audit')
u=resource.getrusage(resource.RUSAGE_SELF);r={'status':'read_only_completed','sources_before':before,'sources_after':after,'sources_unchanged':True,'rows':rows,'solver_invoked':False,'cpu_s':u.ru_utime+u.ru_stime,'wall_s':time.monotonic()-start,'peak_rss_bytes_macos':u.ru_maxrss};(out/'record.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'cpu_s':r['cpu_s'],'wall_s':r['wall_s'],'peak_rss_bytes_macos':r['peak_rss_bytes_macos'],'rows':rows},indent=2))
