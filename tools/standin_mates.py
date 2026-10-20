"""Fasten each stand-in to the deck plate it sits on.

Pass 1 makes zero-offset mates between the part's top face centroid and the deck's
top face centroid, so Onshape reports both connector frames (matedCS, part-local).
Pass 2 deletes them and recreates each with the offset that keeps the part where the
Part Studio put it. Stand-ins and decks are both inserted at T(0, -2 mm, 0), so the
offset is C_deck^-1 . C_part in Part Studio coordinates.
"""
import sys, json
from urllib.parse import quote
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import onshape as o, numpy as np
from mates import fastened
from layout import csM, offset_params

A = '97ae17cb947b54ad84147e9e'
BASE = f'/assemblies/d/{o.DID}/w/{o.WID}/e/{A}'
PS, DECKS = '87c907c98594804e388ca806', '5ebde287e928614ffe52d286'
DECK_FACE = {'Deck Top - back': 'RwDy', 'Deck Bottom - back': 'SOCSB'}


def top_face(eid, pid):
    bd = o.get(f'/partstudios/d/{o.DID}/w/{o.WID}/e/{eid}/bodydetails')
    b = next(b for b in bd['bodies'] if b['id'] == pid)
    return max((f for f in b['faces'] if f['surface']['type'] == 'PLANE' and
                f['surface']['normal']['z'] * (1 if f['orientation'] else -1) > 0.99),
               key=lambda f: f['box']['maxCorner']['z'])['id']


def mate_name(i, d):
    return f'{i["name"]} ~ {d["name"][:-4]}'


def main():
    asm = o.get(BASE + '?includeMateFeatures=true&includeNonSolids=false', fresh=True)
    r = asm['rootAssembly']
    by = {i['name'].rsplit(' <', 1)[0]: i for i in r['instances']}
    parts = [i for i in r['instances'] if i.get('elementId') == PS]
    jobs = []
    for i in parts:
        top = 'Deck Top - back' if i['name'][:3] in ('Jet', 'PoE', 'ESP') or 'disconnect' in i['name'] else 'Deck Bottom - back'
        jobs.append((i, by[top], top_face(PS, i['partId']), DECK_FACE[top]))
    # pass 1 (skips parts that already have their mate, so a rerun picks up where it stopped)
    have = {f['featureData']['name']: f['id'] for f in r['features']}
    taken = set()   # an existing mate counts for only one instance (older mates were named without the <n>)
    fids = {}
    for i, d, fa, fb in jobs:
        f = have.get(mate_name(i, d)) or have.get(f'{i["name"][:-4]} ~ {d["name"][:-4]}')
        fids[i['id']] = f if f not in taken else None
        taken.add(f)
    new = {i['id'] for i, d, fa, fb in jobs if not fids[i['id']]}
    for i, d, fa, fb in jobs:
        if i['id'] not in new:
            continue
        res = o.post(BASE + '/features', {"feature": fastened(mate_name(i, d), i['id'], fa, d['id'], fb, inference='CENTROID')})
        fids[i['id']] = res['feature']['featureId']
    asm = o.get(BASE + '?includeMateFeatures=true&includeNonSolids=false', fresh=True)
    feats = {f['id']: f['featureData'] for f in asm['rootAssembly']['features']}
    # pass 2
    for i, d, fa, fb in jobs:
        if i['id'] not in new:
            continue
        ents = feats[fids[i['id']]]['matedEntities']
        Ca = csM(next(e for e in ents if e['matedOccurrence'] == [i['id']])['matedCS'])
        Cb = csM(next(e for e in ents if e['matedOccurrence'] == [d['id']])['matedCS'])
        off, ang = offset_params(np.linalg.inv(Cb) @ Ca)
        o.request('DELETE', BASE + f'/features/featureid/{quote(fids[i["id"]], safe="")}')
        res = o.post(BASE + '/features', {"feature": fastened(mate_name(i, d), i['id'], fa, d['id'], fb,
                                                              off=tuple(round(float(x), 4) for x in off), rot_deg=round(float(ang), 4), inference='CENTROID')})
        print(i['name'], np.round(off, 2), round(ang, 1), res['featureState']['featureStatus'])
    print('calls', o.calls_used())


if __name__ == '__main__':
    main()
