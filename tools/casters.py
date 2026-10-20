"""Put a 6 in swivel caster under each bottom-frame corner (4 total).

The caster's top-plate hole rectangle (76.2 x 68.6 mm, inner slot ends) is centred on
the plate, so a caster at corner (sx, sy) puts one hole column on the rail's bottom
T-slot (x = sx*270) and one hole row on the end crossbar's bottom T-slot (y = 18 or 778).
Each caster is fastened to the bottom deck plate above it (same two-pass offset trick as
standin_mates.py), so it follows the frame.
"""
import sys
from urllib.parse import quote
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import onshape as o, numpy as np
from mates import fastened
from layout import csM, mat, offset_params

A = '97ae17cb947b54ad84147e9e'
BASE = f'/assemblies/d/{o.DID}/w/{o.WID}/e/{A}'
PS1, CASTER = 'a9c92a3b22ed6eb6c2bc58e5', 'RDBD'
PLATE_C = np.array([138.05, 103.2, 3.0])    # caster top-plate centre, part-local mm
TOP_FACE = 'RDBK'                           # caster top-plate upper face
HOLE_DX, HOLE_DY = 76.2 / 2, 68.6 / 2
RAIL_X, FRONT_SLOT_Y, BACK_SLOT_Y, FRAME_BOTTOM_Z = 270, 18, 778, -40
DECK = {'front': ('Deck Bottom - front', 'SJBSB'), 'back': ('Deck Bottom - back', 'SOCSB')}
OLD_MATE = 'MeAW6fa5UrnE5JfEU'


def target(sx, end):
    y = FRONT_SLOT_Y + HOLE_DY if end == 'front' else BACK_SLOT_Y - HOLE_DY
    c = np.array([sx * (RAIL_X - HOLE_DX), y, FRAME_BOTTOM_Z])
    M = np.eye(4); M[:3, 3] = c - PLATE_C
    return M


def load():
    return o.get(BASE + '?includeMateFeatures=true&includeNonSolids=false', fresh=True)['rootAssembly']


def main():
    r = load()
    if any(f['id'] == OLD_MATE for f in r['features']):
        o.request('DELETE', BASE + f'/features/featureid/{quote(OLD_MATE, safe="")}')
    casters = [i for i in r['instances'] if i.get('partId') == CASTER]
    for _ in range(4 - len(casters)):
        o.post(BASE + '/instances', {"documentId": o.DID, "elementId": PS1, "partId": CASTER})
    r = load()
    casters = sorted([i for i in r['instances'] if i.get('partId') == CASTER], key=lambda i: i['name'])
    decks = {i['name'].rsplit(' <', 1)[0]: i for i in r['instances']}
    occ = {x['path'][0]: mat(x['transform']) for x in r['occurrences'] if len(x['path']) == 1}
    corners = [(1, 'front'), (-1, 'front'), (1, 'back'), (-1, 'back')]
    jobs, fids = [], {}
    for i, (sx, end) in zip(casters, corners):
        dname, dface = DECK[end]
        name = f'Caster {"R" if sx > 0 else "L"}{end[0].upper()} ~ {dname}'
        jobs.append((i, decks[dname], dface, target(sx, end), name))
        res = o.post(BASE + '/features', {"feature": fastened(name, i['id'], TOP_FACE, decks[dname]['id'], dface, inference='CENTROID')})
        fids[i['id']] = res['feature']['featureId']
    feats = {f['id']: f['featureData'] for f in load()['features']}
    for i, d, dface, P, name in jobs:
        ents = feats[fids[i['id']]]['matedEntities']
        Ca = csM(next(e for e in ents if e['matedOccurrence'] == [i['id']])['matedCS'])
        Cb = csM(next(e for e in ents if e['matedOccurrence'] == [d['id']])['matedCS'])
        off, ang = offset_params(np.linalg.inv(occ[d['id']] @ Cb) @ (P @ Ca))
        o.request('DELETE', BASE + f'/features/featureid/{quote(fids[i["id"]], safe="")}')
        res = o.post(BASE + '/features', {"feature": fastened(name, i['id'], TOP_FACE, d['id'], dface,
                                                              off=tuple(round(float(x), 4) for x in off), rot_deg=round(float(ang), 4), inference='CENTROID')})
        print(name, np.round(off, 2), round(ang, 1), res['featureState']['featureStatus'])
    r = load()
    for x in r['occurrences']:
        if x['path'][0] in fids:
            print(x['path'][0], np.round(mat(x['transform'])[:3, 3], 2))
    print('calls', o.calls_used())


if __name__ == '__main__':
    main()
