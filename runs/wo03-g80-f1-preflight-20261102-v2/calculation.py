"""One bounded dedicated-G80 preflight; scalar joint screens, never qualification."""
from __future__ import annotations
import argparse,hashlib,json,math,resource,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from src.vehicle.schema import load_vehicle
from src.vehicle.mass import mass_properties
from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import screen_launch
from src.vehicle.reference import compare_rocketpy

SPEC=Path('configs/vehicle/candidates/g80-f1.yaml')
def compute():
 v=load_vehicle(SPEC); p=mass_properties(v); cp=center_of_pressure(v); by={a.id:a for a in v.parts}
 guides={}
 for rail in [1.5,1.8,1.971]:
  vv=v.model_copy(deep=True);vv.design.rail_length_m=rail
  roots={}
  for speed in [15.,15.5]:
   lo,hi=.3,1.5
   for _ in range(22):
    mid=(lo+hi)/2
    if screen_launch(vv,study_nominal_mass_kg=mid-.05)['rail_exit_speed_mps']>=speed:lo=mid
    else:hi=mid
   roots[str(speed)]=(lo+hi)/2
  guides[str(rail)]=roots
 cases=[]
 for name,extra,probe in [('nominal_full_growth',0,0),('adverse_20g_aft_motor_probe',.020,.0128)]:
  mass=p.mass_kg+.05+extra
  mom=p.mass_kg*p.cg_m+(.05+extra)*v.airframe['length_m']+by['motor'].resolved_mass_kg*probe
  cg=mom/mass
  # Full tensor about shifted CG, including point growth. Envelope/model estimate, not CAD reconciled.
  tensor=p.inertia_kg_m2.copy();shift=cg-p.cg_m
  tensor+=p.mass_kg*np.diag([0,shift**2,shift**2])
  tensor+=(.05+extra)*np.diag([0,(v.airframe['length_m']-cg)**2,(v.airframe['length_m']-cg)**2])
  if probe:
   old=by['motor'].cg_station_m;delta=by['motor'].resolved_mass_kg*((old+probe-cg)**2-(old-cg)**2)
   tensor+=np.diag([0,delta,delta])
  b=mass_properties(v,1);bo_cg=(b.mass_kg*b.cg_m+(.05+extra)*v.airframe['length_m']+ (by['motor'].resolved_mass_kg-v.motor.propellant_mass_kg)*probe)/(b.mass_kg+.05+extra)
  row={'id':name,'mass_kg':mass,'cg_m':cg,'cp_m':cp,'margin_cal':(cp-cg)/.066675,'burnout_margin_cal':(cp-bo_cg)/.066675,'inertia_kg_m2':tensor.tolist(),'growth_allowance_kg':.05,'additional_aft_kg':extra,'motor_cg_probe_m':probe,'guides':{},'historical_mean_recovery_DF3_N':{str(vel):3*mass*(vel**2/(2*.3)+9.80665) for vel in [5,20.4]}}
  for rail in [1.5,1.8,1.971]:
   vv=v.model_copy(deep=True);vv.design.rail_length_m=rail
   r=screen_launch(vv,study_nominal_mass_kg=mass-.05)
   row['guides'][str(rail)]={'speed_mps':r['rail_exit_speed_mps'],'formal_headroom_g':1000*(guides[str(rail)]['15.0']-mass),'planning_headroom_g':1000*(guides[str(rail)]['15.5']-mass),'formal_pass':r['rail_exit_speed_mps']>=15,'planning_pass':r['rail_exit_speed_mps']>=15.5}
  cases.append(row)
 f=by['fin_set'].geometry;s=f['span_m'];r=f['root_chord_m'];t=f['tip_chord_m'];h=f['thickness_m'];area=s*(r+t)/2;ar=2*s*s/area;slope=2*math.pi*ar/(2+math.sqrt(4+ar*ar));load=40000*area*slope*math.radians(5)*3;moment=load*s*(r+2*t)/(3*(r+t));stress=6*moment/(r*h*h)
 # Tapered Euler-Bernoulli strip; all load treated at tip (conservative panel displacement).
 x=np.linspace(0,s,1001);ch=r+(t-r)*x/s;EI=1e9*ch*h**3/12
 tip_bound=float(np.trapezoid(load*(s-x)**2/EI,x))
 pressure=40000*slope*math.radians(5)*3
 aa=pressure*r;bb=pressure*(t-r)/s
 internal_moment=aa*(s-x)**2/2+bb*(s**3/3-x*s*s/2+x**3/6)
 deflection=float(np.trapezoid(internal_moment*(s-x)/EI,x))
 uniform_numerical=float(np.trapezoid((load/s)*(s-x)**3/(2*1e9*r*h**3/12),x))
 uniform_exact=load*s**3/(8*(1e9*r*h**3/12))
 # Required rotational support stiffness, not an invented clamp.
 k_required=moment*s/max(1e-9,.001-deflection) if deflection<.001 else None
 # Historical severe mechanism and separate documented inflation estimate: neither substitutes for the other.
 cds=.75*math.pi*.75**2/4;inflation={str(vel):{'q_pa':.5*1.1*vel**2,'Cx_max':2.,'unfactored_N':2*.5*1.1*vel**2*cds,'DF3_N':3*2*.5*1.1*vel**2*cds} for vel in [5,20.4]}
 ring=by['forward_ring'];th=ring.geometry['length_m'];bridge=ring.geometry['radius_m']-ring.geometry['inner_radius_m'];strip=.014
 ringcases=[]
 for name,force in [('historical_severe',max(a['historical_mean_recovery_DF3_N']['20.4'] for a in cases)),('inflation_only_severe',inflation['20.4']['DF3_N'])]:
  # Simply supported ring radial strip sensitivity under point load; width/real annular redistribution unknown.
  st=1.5*force*bridge/(strip*th*th)
  ringcases.append({'id':name,'force_N':force,'strip_width_m':strip,'span_m':bridge,'stress_pa':st,'hot5MPa_screen_pass':st<=5e6,'scope':'conservative 14mm strip sensitivity, not solved annular plate or installed support'})
 tubearea=math.pi*(.0333375**2-.032385**2)
 return {'identity':'G80_F1_fixed_conventional_v2','spec_sha256':hashlib.sha256(SPEC.read_bytes()).hexdigest(),'status':'preliminary; no CAD admission or engineering acceptance','nominal_parts_mass_kg':p.mass_kg,'parts': [{'id':a.id,'mass_kg':a.resolved_mass_kg,'cg_m':a.cg_station_m,'cost_usd':a.build.cost_usd} for a in v.parts], 'estimated_consumed_parts_cost_usd':sum(a.build.cost_usd for a in v.parts),'cases':cases,'guide_total_mass_limits_kg':guides,'fin_screen':{'q_pa':40000,'alpha_deg':5,'design_factor_once':3,'force_factored_N':load,'moment_factored_Nm':moment,'stress_pa':stress,'hot_strength_pa_estimate':5e6,'stress_pass':stress<=5e6,'panel_deflection_m':deflection,'all_load_at_tip_upper_bound_m':tip_bound,'uniform_beam_numerical_m':uniform_numerical,'uniform_beam_exact_m':uniform_exact,'uniform_beam_relative_error':abs(uniform_numerical/uniform_exact-1),'total_installed_limit_m':.001,'required_root_rotational_stiffness_Nm_rad':k_required,'installed_movement_status':'unknown; support stiffness not established','bond_couple_N':moment/.0179705,'one_side_tab_face_area_m2':.110*.0179705,'average_tab_face_shear_pa':(moment/.0179705)/(.110*.0179705),'flutter':'unavailable for installed F1; no transfer of old fin results'},'recovery':{'historical_model':'DF3*m*(v²/(2s)+g), s=.3m; energy-equivalent mean, not established peak','inflation_model':'DF3*Cx*q*CdS, Cx<=2, rho1.1, D.75/Cd.75; does not model line snatch','inflation_only_cases':inflation,'ring_strip_sensitivities':ringcases,'body_annulus_area_m2':tubearea,'body_hot2MPa_uniform_capacity_estimate_N':tubearea*2e6,'line_snatch':'unknown; relative separation speed, slack, force-extension and section masses need validation','criterion_revision':'none; historical severe preserved required pending mechanism-based decision'},'static_rocketpy':compare_rocketpy(v),'admission':{'whole_vehicle_CAD':False,'thermal':'unknown F1; no accepted temperature result','motor_retainer':'current exact shoulder/bore/lip dimensions unknown; old seat/liner removed, not replaced with assumed contact','recovery':'forward ring historical severe strip fails; inflation-only strip check distinct, anchors/installed capacity unresolved','fin_installed':'support stiffness, directional hot properties, bonds and flutter incomplete'}}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
 resource.setrlimit(resource.RLIMIT_CPU,(30,30));start=time.monotonic();result=compute();result['runtime_wall_s']=time.monotonic()-start;result['calculation_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 out=Path(args.output);out.mkdir(parents=True,exist_ok=False);(out/'specification.yaml').write_bytes(SPEC.read_bytes());(out/'calculation.py').write_bytes(Path(__file__).read_bytes());(out/'record.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['identity','nominal_parts_mass_kg','estimated_consumed_parts_cost_usd','runtime_wall_s','fin_screen','admission']},indent=2))
 print(json.dumps(result['cases'],indent=2))
 return 0
if __name__=='__main__':raise SystemExit(main())
