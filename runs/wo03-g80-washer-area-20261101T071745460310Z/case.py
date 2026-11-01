import json, math, os, resource, sys, time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
root=Path.cwd();sys.path.insert(0,str(root))
import gmsh
import numpy as np
from scripts.wo03_g80_bridge_adapter import quadratic_surface_weights
outer_n, inner_n = map(int,sys.argv[1:]); start=time.monotonic()
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',1)
try:
    gmsh.model.add('annulus');o=gmsh.model.occ.addDisk(0,0,0,4.5,4.5);i=gmsh.model.occ.addDisk(0,0,0,1.7,1.7)
    out,_=gmsh.model.occ.cut([(2,o)],[(2,i)]);gmsh.model.occ.synchronize();face=out[0][1]
    curves=gmsh.model.getBoundary([(2,face)],oriented=False); observed={}
    for dim,tag in curves:
        length=gmsh.model.occ.getMass(dim,tag)
        label='outer' if abs(length-2*math.pi*4.5)<1e-8 else 'inner' if abs(length-2*math.pi*1.7)<1e-8 else None
        if label is None or label in observed: raise ValueError('Unexpected annulus boundary')
        observed[label]=tag
    if set(observed)!={'outer','inner'}:raise ValueError('Missing boundary')
    for label,n in [('outer',outer_n),('inner',inner_n)]: gmsh.model.mesh.setTransfiniteCurve(observed[label],n+1)
    gmsh.option.setNumber('Mesh.MeshSizeMax',1.5);gmsh.model.mesh.generate(2);gmsh.model.mesh.setOrder(2)
    ids,xyz,_=gmsh.model.mesh.getNodes(); coords={int(n):v for n,v in zip(ids,np.asarray(xyz).reshape(-1,3),strict=True)}
    types,_,connectivity=gmsh.model.mesh.getElements(2,face)
    if list(types)!=[9]:raise ValueError('Expected quadratic triangles')
    triangles=np.asarray(connectivity[0]).reshape(-1,6);ips,weights=gmsh.model.mesh.getIntegrationPoints(9,'Gauss6');points=np.asarray(ips).reshape(-1,3)[:,:2]
    jac=gmsh.model.mesh.getJacobians(9,ips,face)[1]
    w,area=quadratic_surface_weights(triangles,coords,points,weights,jac)
    centroid=sum((coords[n]*v for n,v in w.items()),np.zeros(3))/area
    segments={}
    for label,tag in observed.items():
        t,ids_edge,_=gmsh.model.mesh.getElements(1,tag)
        if list(t)!=[8]:raise ValueError('Expected quadratic boundary edges')
        segments[label]=len(ids_edge[0])
    if segments!={'outer':outer_n,'inner':inner_n}:raise ValueError('Unexpected boundary segment count')
    def arc_area(r,n):
        theta=2*math.pi/n
        return n*r*r*(4*math.sin(theta/2)/3-math.sin(theta)/6)
    exact=math.pi*(4.5**2-1.7**2); outer_approx=arc_area(4.5,outer_n);inner_approx=arc_area(1.7,inner_n)
    analytic_mesh_area=outer_approx-inner_approx
    result={'outer_segments':outer_n,'inner_segments':inner_n,'nodes':len(ids),'triangles':len(triangles),'exact_area_mm2':exact,'mesh_area_mm2':area,'signed_error_mm2':area-exact,'analytic_quadratic_arc_area_mm2':analytic_mesh_area,'integration_minus_arc_area_mm2':area-analytic_mesh_area,'outer_arc_area_error_mm2':outer_approx-math.pi*4.5**2,'inner_arc_area_error_mm2':inner_approx-math.pi*1.7**2,'mesh_centroid_mm':centroid.tolist(),'area_guard_pass':abs(area-exact)<=.0002,'elapsed_wall_s':time.monotonic()-start,'cpu_s':resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    print(json.dumps(result,indent=2),flush=True)
finally:gmsh.finalize()
