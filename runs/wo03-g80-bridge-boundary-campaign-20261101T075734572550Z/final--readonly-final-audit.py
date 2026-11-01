import itertools,json,resource,sys,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(10,10));start=time.monotonic();sys.path.insert(0,str(Path.cwd()))
import gmsh,numpy as np
from scripts.wo03_g80_bridge_fea import parse_native_dat
out=Path('build/wo03-g80-bridge-area-budget-coarse-v1');p=out/'bridge_1p5mm';m=json.loads((p/'mesh-meta.json').read_text());con={int(k):v for k,v in m['all_c3d10_connectivity'].items()};sets=m['material_element_ids'];coords={int(k):v for k,v in m['coordinates_mm'].items()};support=set(m['support_node_ids'])
edgeidx={(0,1):4,(1,2):5,(0,2):6,(0,3):7,(1,3):8,(2,3):9}
def face_map(ids):
 result={}
 for eid in ids:
  row=con[int(eid)]
  for i,j,k in itertools.combinations(range(4),3):
   corner=tuple(sorted((row[i],row[j],row[k])))
   mids=tuple(sorted(row[edgeidx[tuple(sorted(e))]] for e in ((i,j),(j,k),(i,k))))
   result.setdefault(corner,set()).add(mids)
 return result
bridge=face_map(sets['G11']);interfaces=[]
for index in range(6):
 film=face_map(sets[f'EPOXY_{index}']); shared=set(bridge)&set(film); mismatched=[f for f in shared if bridge[f]!=film[f]]
 interfaces.append({'film':f'EPOXY_{index}','shared_corner_faces':len(shared),'matching_all_six_nodes_faces':len(shared)-len(mismatched),'mismatched_midside_faces':len(mismatched),'nonunique_corner_face_records':sum(len(bridge[f])!=1 or len(film[f])!=1 for f in shared)})
sections=parse_native_dat(p/'case.dat');support_displacements=[];load_intersections=[]
for step,key in [(1,'EQUAL'),(2,'SINGLE')]:
 u=sections[(step,'displacements','ALL')];support_rows=[r for r in u if r['id'] in support];load=set(map(int,m['step_nodal_forces_N'][key]));support_displacements.append({'step':step,'support_node_rows':len(support_rows),'maximum_absolute_reported_displacement_mm':max(abs(v) for r in support_rows for v in r['values'])});load_intersections.append({'step':step,'support_and_loaded_nodes':len(support&load)})
# Reconstruct the saved discrete connectivity in memory; no mesh generation.
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',1)
try:
 gmsh.model.add('saved_discrete_tets_read_only');gmsh.model.addDiscreteEntity(3,1)
 ids=sorted(coords);gmsh.model.mesh.addNodes(3,1,ids,[x for n in ids for x in coords[n]])
 eids=sorted(con);raw=[]
 for eid in eids:
  row=con[eid];raw.extend(row[i] for i in (0,1,2,3,4,5,6,7,9,8))
 gmsh.model.mesh.addElementsByType(1,11,eids,raw)
 points,weights=gmsh.model.mesh.getIntegrationPoints(11,'Gauss2')
 if len(weights)!=4:raise ValueError('Expected four tetrahedral integration points')
 xyz=np.asarray(points).reshape(-1,3);a,b=.585410196625,.138196601125
 expected=np.array([[b,b,b],[a,b,b],[b,a,b],[b,b,a]])
 if not np.allclose(xyz,expected,rtol=0,atol=1e-12):raise ValueError('Unexpected native four-point coordinates')
 _,det,_=gmsh.model.mesh.getJacobians(11,points,1);det=np.asarray(det)
 if len(det)!=4*len(eids) or not np.isfinite(det).all():raise ValueError('Invalid Jacobian coverage')
 jac={'method':'Gmsh Jacobian API on in-memory saved connectivity; Gmsh Gauss2 four-point coordinates','point_count_per_element':4,'sample_count':len(det),'minimum':float(det.min()),'nonpositive_count':int(np.count_nonzero(det<=0)),'max_to_min_ratio_not_quality_metric':float(det.max()/det.min()) if det.min()>0 else None,'mesh_generate_called':False,'native_ip_order_verified':False}
finally:gmsh.finalize()
r={'six_node_interface_faces':interfaces,'support_displacements':support_displacements,'loaded_nodes_that_are_constrained':load_intersections,'saved_connectivity_four_point_jacobian':jac,'cpu_s':resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,'wall_s':time.monotonic()-start,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'solver_invoked':False,'mesh_generated':False};(out/'readonly-final-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
