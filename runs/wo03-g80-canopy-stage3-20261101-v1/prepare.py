import copy,hashlib,json,sys
from pathlib import Path
import yaml
root=Path.cwd();sys.path.insert(0,str(root))
from src.vehicle.schema import Vehicle
out=Path(sys.argv[1]).resolve(); d=yaml.safe_load((out.parent/'wo03-g80-canopy-preflight-v1/candidate.yaml').read_text()); v=Vehicle.model_validate(d)
def ident(v):return hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest()
assert ident(v)=='f7b8af96f50ce96d6091f1da177198eb82a0797e42cb6874d98d5b5d7e6a8899'
p=copy.deepcopy(next(p for p in d['parts'] if p['id']=='parachute'));p.update(id='canopy_line_connector_sensitivity',mass_kg=.005,cad=None,cad_mass=None,learn='Estimated 5 g line and connector bookkeeping sensitivity only, not measured hardware. Existing mathematical envelope is reused for mass distribution, not a packed shape or CAD claim.',engineering=None,build=None);d['parts'].append(p);v2=Vehicle.model_validate(d);assert len(v2.parts)==73
(out/'nominal.yaml').write_text(yaml.safe_dump(yaml.safe_load((out.parent/'wo03-g80-canopy-preflight-v1/candidate.yaml').read_text()),sort_keys=False)); (out/'sensitivity.yaml').write_text(yaml.safe_dump(d,sort_keys=False))
(out/'identities.json').write_text(json.dumps({'nominal':ident(v),'sensitivity':ident(v2),'note':'5g separate estimated part reuses baseline envelope as mathematical distribution; no CAD mass'},indent=2)+'\n'); print(ident(v2))
