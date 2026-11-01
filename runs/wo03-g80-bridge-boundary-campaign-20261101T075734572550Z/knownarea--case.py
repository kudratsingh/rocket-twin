import json,math,resource,sys,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(10,10));start=time.monotonic()
sys.path.insert(0,str(Path.cwd()))
import gmsh,numpy as np,yaml
from scripts.wo03_g80_washer_boundary import apply_washer_boundary,verify_source_hashes
from scripts.wo03_g80_bridge_adapter import quadratic_surface_weights
cfg=yaml.safe_load(Path('configs/studies/wo03-g80-washer-boundary-area-budget.yaml').read_text())
source_hashes=verify_source_hashes('.',cfg)
r0,r1=cfg['patch_outer_radius_mm'],cfg['patch_inner_radius_mm'];n0=cfg['full_circle_equivalent_segments']['outer'];n1=cfg['full_circle_equivalent_segments']['inner']
def deficit(r,n):return math.pi*r*r-n*r*r*(4*math.sin(math.pi/n)/3-math.sin(2*math.pi/n)/6)
outer_deficit,inner_deficit=deficit(r0,n0),deficit(r1,n1);bound=abs(outer_deficit)+abs(inner_deficit)
if bound>cfg['maximum_sum_absolute_disk_area_deficits_mm2']:raise ValueError('Analytic noncancellation area bound failed')
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',1)
try:
 gmsh.model.add('budget_annulus');outer=gmsh.model.occ.addCircle(0,0,0,r0);inner=gmsh.model.occ.addCircle(0,0,0,r1)
 face=gmsh.model.occ.addPlaneSurface([gmsh.model.occ.addCurveLoop([outer]),gmsh.model.occ.addCurveLoop([inner])]);gmsh.model.occ.synchronize()
 control=apply_washer_boundary(gmsh,[{'face_tags':[face],'center_xyz_mm':[0.,0.,0.]}],outer_radius=r0,inner_radius=r1,outer_segments=n0,inner_segments=n1,tolerance=cfg['curve_match_tolerance_mm'])
 gmsh.option.setNumber('Mesh.MeshSizeMax',cfg['bulk_mesh_target_mm']);gmsh.model.mesh.generate(2);gmsh.model.mesh.setOrder(2)
 ids,xyz,_=gmsh.model.mesh.getNodes();coords={int(n):p for n,p in zip(ids,np.asarray(xyz).reshape(-1,3),strict=True)}
 types,_,conn=gmsh.model.mesh.getElements(2,face)
 if list(types)!=[9]:raise ValueError('Expected quadratic triangles')
 triangles=np.asarray(conn[0]).reshape(-1,6);ips,qw=gmsh.model.mesh.getIntegrationPoints(9,'Gauss6');pts=np.asarray(ips).reshape(-1,3)[:,:2]
 det=np.asarray(gmsh.model.mesh.getJacobians(9,ips,face)[1]);
 if len(det)==0 or not np.isfinite(det).all() or float(det.min())<=0:raise ValueError('Invalid surface Jacobians')
 weights,area=quadratic_surface_weights(triangles,coords,pts,qw,det);center=sum((coords[n]*w for n,w in weights.items()),np.zeros(3))/area
 exact=math.pi*(r0*r0-r1*r1);analytic=exact-outer_deficit+inner_deficit;error=area-exact
 if abs(area-analytic)>1e-8 or abs(error)>cfg['existing_mesh_patch_area_guard_mm2'] or np.linalg.norm(center)>1e-8:raise ValueError('Known-case area, centroid or analytic agreement failed')
 seg={}
 for c in control['patches'][0]['curves']:
  t,edges,_=gmsh.model.mesh.getElements(1,c['curve_tag']);seg[c['ring']]=len(edges[0])
 if seg!={'outer':n0,'inner':n1}:raise ValueError('Unexpected actual boundary segment count')
 u=resource.getrusage(resource.RUSAGE_SELF)
 result={'status':'known_case_passed','exact_area_mm2':exact,'mesh_area_mm2':area,'signed_area_error_mm2':error,'analytic_quadratic_arc_area_mm2':analytic,'integration_minus_analytic_mm2':area-analytic,'outer_disk_deficit_mm2':outer_deficit,'inner_disk_deficit_mm2':inner_deficit,'sum_absolute_disk_deficits_mm2':bound,'centroid_mm':center.tolist(),'minimum_surface_jacobian':float(det.min()),'nodes':len(ids),'triangles':len(triangles),'segments':seg,'controls':control,'source_hashes':source_hashes,'cpu_s':u.ru_utime+u.ru_stime,'wall_s':time.monotonic()-start,'peak_rss_bytes':u.ru_maxrss,'actual_bridge_mesh':False}
 print(json.dumps(result,indent=2),flush=True)
finally:gmsh.finalize()
