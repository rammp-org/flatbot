"""Planar-face lookup from cached Part Studio body details (part-local mm)."""
import sys
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import onshape as o
PS1 = 'a9c92a3b22ed6eb6c2bc58e5'
V = lambda d: [d['x'] * 1000, d['y'] * 1000, d['z'] * 1000]

def faces(pid, eid=PS1):
    bd = o.get(f'/partstudios/d/{o.DID}/w/{o.MAIN_WID}/e/{eid}/bodydetails')
    b = next(b for b in bd['bodies'] if b['id'] == pid)
    out = []
    for f in b['faces']:
        if f['surface']['type'] != 'PLANE': continue
        lo, hi = V(f['box']['minCorner']), V(f['box']['maxCorner'])
        n = V(f['surface']['normal']); n = [x / 1000 for x in n]
        if not f['orientation']: n = [-x for x in n]
        out.append(dict(id=f['id'], n=[round(x) for x in n], lo=lo, hi=hi,
                        c=[(a + b) / 2 for a, b in zip(lo, hi)], area=f['area'] * 1e6))
    return out
