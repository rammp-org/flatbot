"""Build the list of frame mates (offline) from the target layout."""
import sys, json
sys.path.insert(0, __file__.rsplit('/', 1)[0]); from layout import *

PID = {'4040-800mm': 'JnD', '4040--500mm': 'JJD', 'Extrusion 40x40 - 250mm': 'RdBD', '4040-m8-cornerbrace': 'JRD'}
pid_of = lambda name: PID[name.rsplit(' <', 1)[0]]


def snap(M):
    M = M.copy(); M[:3, :3] = np.round(M[:3, :3]); return M


def load(fresh=False):
    asm = o.get(f'/assemblies/d/{D}/w/{o.WID}/e/{A}?includeMateFeatures=true&includeMateConnectors=true&includeNonSolids=false', fresh=fresh)
    return asm


def build(asm):
    inst = asm['rootAssembly']['instances']
    byname = {i['name']: i['id'] for i in inst}
    occ = {x['path'][0]: mat(x['transform']) for x in asm['rootAssembly']['occurrences']}
    main = o.get(f'/assemblies/d/{D}/w/{o.MAIN_WID}/e/{A}?includeMateFeatures=true&includeMateConnectors=true&includeNonSolids=false')
    occ.update({x['path'][0]: mat(x['transform']) for x in main['rootAssembly']['occurrences'] if x['path'][0] in occ})  # original rotations
    old = {f'4040-m8-cornerbrace <{k}>' for k in list(range(1, 9)) + list(range(13, 19))}
    newb = sorted([n for n in byname if 'brace' in n and n not in old], key=lambda s: int(s.split('<')[1][:-1]))
    tags = [n for n in braces() if n.startswith('NEW')]
    assert len(newb) == len(tags), (newb, tags)
    alias = dict(zip(tags, newb))
    T = {}
    for n, lo in members().items():
        T[n] = place_box(snap(occ[byname[n]]), PS1, pid_of(n), lo)
    for n in ['4040-800mm <1>', '4040-800mm <2>', '4040--500mm <3>']:
        T[n] = occ[byname[n]]            # bottom members already mated
    BR = {}
    for tag, (c, a, b, m1, m2) in braces().items():
        n = alias.get(tag, tag); T[n] = brace_T(c, a, b); BR[n] = (a, b, m1, m2, tag)
    plan = []
    def mate(brace, hole, direction, member):
        face = face_facing(pid_of(member), T[member][:3, :3], direction)
        plan.append(dict(name=f'{member.split(" <")[0][-6:]}{member[-4:]} ~ brace{brace[-4:]}',
                         A=byname[brace], Aent=hole, Apid='JRD', An=brace,
                         B=byname[member], Bent=face, Bpid=pid_of(member), Bn=member))
    for n, (a, b, m1, m2, tag) in BR.items():
        lvl_top = 'top' in tag
        if 'post' in tag or tag.startswith('4040'):
            if not lvl_top:
                mate(n, 'JaB', a, m1)              # bottom post brace -> rail / mid bar
                mate(n, 'JdF', b, m2)              # post -> that brace
            else:
                mate(n, 'JdF', b, m2)              # top post brace -> post
                if m1.startswith('4040-800mm') and ('0' == tag[-1]):
                    mate(n, 'JaB', a, m1)          # top rail -> front top post brace
        else:
            mate(n, 'JaB', a, m1)                  # top bar brace -> top rail
            if tag.startswith('NEW bar-top -1') and (tag[-1] in 'FB' or tag.endswith('Ma')):
                mate(n, 'JdF', b, m2)              # top bar -> one of its braces
    return plan, T, byname, alias
