import json,resource,time
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(20,20));start=time.monotonic()
from scripts.wo03_g80_bridge_fea import parse_native_dat
p=Path('build/wo03-g80-bridge-area-budget-coarse-v1/bridge_1p5mm');m=json.loads((p/'mesh-meta.json').read_text());conn={int(k):list(map(int,v)) for k,v in m['all_c3d10_connectivity'].items()};mat={k:set(map(int,v)) for k,v in m['material_element_ids'].items()}; nodes={k:set(n for e in ids for n in conn[e]) for k,ids in mat.items()}
# Connected components of shared node IDs across all ten-node tetrahedra.
parent={n:n for row in conn.values() for n in row}
def find(n):
 while parent[n]!=n:
  parent[n]=parent[parent[n]];n=parent[n]
 return n
def union(a,b):
 a,b=find(a),find(b)
 if a!=b:parent[b]=a
for row in conn.values():
 for n in row[1:]:union(row[0],n)
components=defaultdict(set)
for n in parent:components[find(n)].add(n)
interfaces=[]
for film in m['film_surface_ownership']:
 name=film['epoxy_material']; common=nodes['G11'] & nodes[name]; face=set(film['bridge_interface']['node_ids']);back=set(film['rail_back']['node_ids']);
 interfaces.append({'material':name,'bridge_epoxy_shared_nodes':len(common),'intended_interface_nodes':len(face),'interface_not_shared':len(face-common),'shared_not_on_recorded_interface':len(common-face),'rail_face_nodes':len(back),'rail_face_not_epoxy_nodes':len(back-nodes[name]),'rail_face_not_support':len(back-set(m['support_node_ids']))})
# Independently expand only the actual explicit SUPPORT deck set and all boundary cards.
section='';support=set();boundaries=[];cards=[]
for line in (p/'case.inp').open():
 t=line.strip()
 if t.startswith('*'):
  section=t.upper();cards.append(section);continue
 if section=='*NSET,NSET=SUPPORT':support.update(int(x) for x in t.split(',') if x)
 elif section.startswith('*BOUNDARY') and t:boundaries.append(t)
face_sets=[set(face['rail_back']['node_ids']) for face in m['film_surface_ownership']];face_union=set().union(*face_sets);meta_support=set(m['support_node_ids'])
# Raw table independent from parser: discover step header, RF header, then rows.
raw={};step=None;active=False
import re
marker=re.compile(r'^\s*S\s+T\s+E\s+P\s+(\d+)\s*$',re.I)
for line in (p/'case.dat').open():
 hit=marker.match(line)
 if hit:step=int(hit.group(1));active=False;continue
 if re.match(r'^\s*forces\s*\([^)]*\)\s+for set\s+SUPPORT\s+and time',line,re.I):
  if step in raw:raise ValueError('duplicate RF block')
  raw[step]=[];active=True;continue
 if active:
  f=line.split()
  if not f:continue
  if len(f)==4 and f[0].isdigit():raw[step].append((int(f[0]),*[Decimal(x.replace('D','E')) for x in f[1:]]))
  else:active=False
sections=parse_native_dat(p/'case.dat');tab=[]
for step,rr in sorted(raw.items()):
 parsed=sections[(step,'forces','SUPPORT')]; rids=[r[0] for r in rr];pids=[r['id'] for r in parsed];sums=[sum((row[i] for row in rr),Decimal(0)) for i in (1,2,3)];psum=[sum(row['values'][i] for row in parsed) for i in range(3)]
 tab.append({'step':step,'raw_rows':len(rr),'unique_raw_nodes':len(set(rids)),'parsed_rows':len(parsed),'raw_parser_same_node_order':rids==pids,'raw_support_missing':len(support-set(rids)),'raw_support_extra':len(set(rids)-support),'raw_decimal_sum_N':[str(x) for x in sums],'parser_sum_N':psum})
result={'mesh_node_count':len(m['coordinates_mm']),'element_count':len(conn),'used_nodes':len(parent),'unused_mesh_nodes':len(set(map(int,m['coordinates_mm']))-set(parent)), 'connected_component_count':len(components),'component_node_counts_sorted':sorted((len(v) for v in components.values()),reverse=True),'interfaces':interfaces,'deck_support_nodes':len(support),'meta_support_nodes':len(meta_support),'six_rail_face_nodes':len(face_union),'deck_vs_meta_support_symmetric_difference':len(support^meta_support),'deck_vs_six_face_union_symmetric_difference':len(support^face_union),'boundary_cards':boundaries,'other_mpc_cards':[x for x in cards if x.startswith(('*MPC','*TIE','*EQUATION','*COUPLING','*RIGID BODY'))],'raw_rf_blocks':tab,'elapsed_wall_s':time.monotonic()-start,'cpu_s':resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'solver_run':False}
Path('build/wo03-g80-bridge-area-budget-coarse-v1/readonly-mesh-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
