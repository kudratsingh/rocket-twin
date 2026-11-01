import json, math, os, resource, sys, time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
sys.path.insert(0, str(Path.cwd()))
import gmsh
import numpy as np
from scripts.wo03_g80_bridge_adapter import quadratic_surface_weights

start=time.monotonic(); gmsh.initialize(); gmsh.option.setNumber('General.Terminal',0)
gmsh.option.setNumber('General.NumThreads',1)
gmsh.model.add('independent_annuli')
angles=(60,180,300); radius=25.5
surfaces=[]; centers=[]
for angle in angles:
    x=radius*math.cos(math.radians(angle)); y=radius*math.sin(math.radians(angle)); centers.append((x,y))
    outer=gmsh.model.occ.addDisk(x,y,0,4.5,4.5); inner=gmsh.model.occ.addDisk(x,y,0,1.6,1.6)
    out,_=gmsh.model.occ.cut([(2,outer)],[(2,inner)])
    surfaces.append(out[0][1])
gmsh.model.occ.synchronize()
exact=[{'area':gmsh.model.occ.getMass(2,s), 'center':gmsh.model.occ.getCenterOfMass(2,s)} for s in surfaces]
gmsh.option.setNumber('Mesh.MeshSizeMin',1.5); gmsh.option.setNumber('Mesh.MeshSizeMax',1.5)
gmsh.model.mesh.generate(2); gmsh.model.mesh.setOrder(2)
ids, xyz, _=gmsh.model.mesh.getNodes(); coords={int(i):p for i,p in zip(ids,np.asarray(xyz).reshape(-1,3),strict=True)}
ips, qw=gmsh.model.mesh.getIntegrationPoints(9,'Gauss4'); pts=np.asarray(ips).reshape(-1,3)[:,:2]
patches=[]
for s,(x,y),occ in zip(surfaces,centers,exact,strict=True):
    types, _, conns=gmsh.model.mesh.getElements(2,s); triangles=[]; dets=[]
    for typ,conn in zip(types,conns,strict=True):
        assert typ==9
        triangles.extend(np.asarray(conn).reshape(-1,6).tolist()); dets.extend(gmsh.model.mesh.getJacobians(9,ips,s)[1])
    weights,area=quadratic_surface_weights(triangles,coords,pts,qw,dets)
    center=sum((coords[i]*w for i,w in weights.items()),np.zeros(3))/area
    patches.append({'triangle_count':len(triangles),'exact_area_mm2':occ['area'],'analytic_area_mm2':math.pi*(4.5**2-1.6**2),'mesh_area_mm2':area,'exact_center_mm':list(occ['center']),'integrated_center_mm':center.tolist(),'center_error_xy_mm':(center[:2]-[x,y]).tolist()})
force_moment=[sum(50*p['integrated_center_mm'][1] for p in patches),-sum(50*p['integrated_center_mm'][0] for p in patches),0]
result={'case':'three independent known-annulus surfaces; not actual clipped bridge contact','mesh_size_mm':1.5,'areas':patches,'equal_force_moment_Nmm':force_moment,'cpu_s':resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,'wall_s':time.monotonic()-start,'maximum_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
gmsh.finalize(); Path('build/wo03-g80-traction-diagnosis-v1/annulus.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
