"""Write /tmp/flatbot_mesh/placements.json: part base name -> list of 4x4 world transforms (mm),
from the Onshape assembly occurrences. Identical parts are interchangeable, so the per-part
STEP files ("name (n)") just get matched to that name's occurrences in order."""
import sys, json, re
sys.path.insert(0, __file__.rsplit('/', 2)[0]); import onshape as o
from layout import mat

A = '97ae17cb947b54ad84147e9e'
asm = o.get(f'/assemblies/d/{o.DID}/w/{o.WID}/e/{A}?includeNonSolids=false', fresh='--fresh' in sys.argv)
r = asm['rootAssembly']
names = {i['id']: i for i in r['instances']}
for s in asm['subAssemblies']:
    names.update({i['id']: i for i in s['instances']})
out = {}
for oc in r['occurrences']:
    i = names[oc['path'][-1]]
    if i['type'] != 'Part':
        continue
    base = re.sub(r' <\d+>$', '', i['name'])
    out.setdefault(base, []).append(mat(oc['transform']).tolist())
json.dump(out, open('/tmp/flatbot_mesh/placements.json', 'w'))
print({k: len(v) for k, v in out.items()}, 'calls', o.calls_used())
