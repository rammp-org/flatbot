"""Offline analysis of the cached assembly: world-space boxes for frame parts."""
import sys, itertools
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import onshape as o
D, W, A = o.DID, o.WID, '97ae17cb947b54ad84147e9e'
PS1, FS = 'a9c92a3b22ed6eb6c2bc58e5', '55434a5471a2fed1380e0a4e'
asm = o.get(f'/assemblies/d/{D}/w/{W}/e/{A}?includeMateFeatures=true&includeMateConnectors=true&includeNonSolids=false')
r = asm['rootAssembly']
inst = {i['id']: i for i in r['instances']}
occ = {x['path'][0]: x for x in r['occurrences']}
BB = {}
def bbox(e, p):
    b = o.get(f'/parts/d/{D}/w/{o.MAIN_WID}/e/{e}/partid/{p}/boundingboxes')
    return [b['lowX'], b['lowY'], b['lowZ']], [b['highX'], b['highY'], b['highZ']]
def world(iid):
    i = inst[iid]; lo, hi = bbox(i['elementId'], i['partId'])
    T = occ[iid]['transform']
    pts = [[sum(T[r*4+c]*v for c, v in enumerate(p)) + T[r*4+3] for r in range(3)]
           for p in itertools.product(*zip(lo, hi))]
    return [min(p[k] for p in pts)*1000 for k in range(3)], [max(p[k] for p in pts)*1000 for k in range(3)]
FRAME = ('JJD', 'JnD', 'RdBD')
