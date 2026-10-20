"""Target layout for the Flatbot 4040 frame (mm, assembly frame: X width, Y length, Z up).

Everything here is computed offline from cached data; no API calls except
through onshape.get() cache hits (and fresh assembly reads when asked).
"""
import sys
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import onshape as o
import numpy as np

D, A = o.DID, '97ae17cb947b54ad84147e9e'
PS1 = 'a9c92a3b22ed6eb6c2bc58e5'

# ---- frame parameters (mm) ----
W_OUT = 580          # outer width (two 800 rails + 500 crossbars)
Y0, L = -2.0, 800.0  # rail start (kept from original model) and length
P = 40.0             # profile
POST = 250.0
XR = W_OUT / 2 - P / 2                      # rail centreline |x| = 270
POST_Y = [Y0 + P, 419 - P / 2, Y0 + L - 2 * P]   # post low-Y faces: 38, 399, 718
TOP_Z0 = POST                               # top layer bottom face = 250

# brace (4040-m8-cornerbrace, JRD) local geometry
BR_CORNER = np.array([0, 135.65, 0])        # inner corner of the L
BR_HOLE1 = ('JaB', np.array([0, 105.65, 0]))   # hole in leg on face z=0 (local -Z face)
BR_HOLE2 = ('JdF', np.array([0, 135.65, 15]))  # hole in leg on face y=135.65 (local +Y face)
BORE = {'JJD': ('KN5B', np.array([0, 0, 0])), 'JnD': ('Kr5B', np.array([0, -62.07, 0])),
        'RdBD': ('ShB5B', np.array([0, -120, 0]))}


def mat(T16):
    M = np.array(T16, float).reshape(4, 4).copy(); M[:3, 3] *= 1000; return M


def flat(M):
    M = M.copy(); M[:3, 3] /= 1000; return [float(x) for x in M.reshape(-1)]


def brace_T(corner, a, b):
    """Brace whose -Z face touches the member in direction a and +Y face the member in direction b."""
    a, b = np.array(a, float), np.array(b, float)
    Yw, Zw = b, -a; Xw = np.cross(Yw, Zw)
    M = np.eye(4); M[:3, :3] = np.column_stack([Xw, Yw, Zw])
    M[:3, 3] = np.array(corner, float) - M[:3, :3] @ BR_CORNER
    return M


def local_bbox(eid, pid):
    b = o.get(f'/parts/d/{D}/w/{o.MAIN_WID}/e/{eid}/partid/{pid}/boundingboxes')
    return np.array([b['lowX'], b['lowY'], b['lowZ']]) * 1000, np.array([b['highX'], b['highY'], b['highZ']]) * 1000


def world_bbox(M, eid, pid):
    lo, hi = local_bbox(eid, pid)
    pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    w = (M @ pts.T).T[:, :3]
    return w.min(0), w.max(0)


def place_box(M, eid, pid, lo_target):
    """Keep rotation of M, translate so world bbox low corner == lo_target."""
    lo, _ = world_bbox(M, eid, pid)
    M = M.copy(); M[:3, 3] += np.array(lo_target) - lo; return M


def members():
    """name -> target low corner for every extrusion."""
    t = {}
    t['4040-800mm <3>'] = (-290, Y0, TOP_Z0)    # top left rail
    t['4040-800mm <6>'] = (250, Y0, TOP_Z0)     # top right rail
    t['4040--500mm <7>'] = (-250, Y0, TOP_Z0)           # top front bar
    t['4040--500mm <6>'] = (-250, POST_Y[1], TOP_Z0)    # top mid bar
    t['4040--500mm <5>'] = (-250, Y0 + L - P, TOP_Z0)   # top back bar
    posts = {'<6>': (-1, 0), '<5>': (1, 0), '<3>': (-1, 1), '<2>': (1, 1), '<4>': (-1, 2), '<1>': (1, 2)}
    for k, (s, i) in posts.items():
        t[f'Extrusion 40x40 - 250mm {k}'] = (-290 if s < 0 else 250, POST_Y[i], 0)
    return t


def braces():
    """name -> (corner, a, b, member1 name, member2 name). New braces get names 'NEW <tag>'."""
    out = {}
    Xs = {-1: -XR, 1: XR}
    yF, yM, yB = POST_Y[0], POST_Y[1] + P / 2, POST_Y[2] + P   # 38, 419, 758
    post = {(-1, 0): '<6>', (1, 0): '<5>', (-1, 1): '<3>', (1, 1): '<2>', (-1, 2): '<4>', (1, 2): '<1>'}
    rail_b = {-1: '4040-800mm <2>', 1: '4040-800mm <1>'}
    rail_t = {-1: '4040-800mm <3>', 1: '4040-800mm <6>'}
    old_bot = {(-1, 0): '<18>', (1, 0): '<17>', (-1, 1): '<13>', (1, 1): '<14>', (-1, 2): '<16>', (1, 2): '<15>'}
    for s in (-1, 1):
        for i in range(3):
            pn = 'Extrusion 40x40 - 250mm ' + post[(s, i)]
            for lvl, z, a in (('bot', 0, (0, 0, -1)), ('top', TOP_Z0, (0, 0, 1))):
                if i == 0:   corner, b = (Xs[s], yF, z), (0, 1, 0)       # in front of front post, on rail
                elif i == 2: corner, b = (Xs[s], yB, z), (0, -1, 0)      # behind back post, on rail
                else:        corner, b = (s * 250, yM, z), (s, 0, 0)     # inboard of mid post, on mid bar
                m1 = (rail_b[s] if lvl == 'bot' else rail_t[s]) if i != 1 else \
                     ('4040--500mm <3>' if lvl == 'bot' else '4040--500mm <6>')
                name = ('4040-m8-cornerbrace ' + old_bot[(s, i)]) if lvl == 'bot' else f'NEW post-top {s:+d}{i}'
                out[name] = (corner, a, b, m1, pn)
    # top crossbar-to-rail braces (mirror of the bottom layer pattern)
    zc = TOP_Z0 + P / 2
    bars = {'F': ('4040--500mm <7>', yF, (0, -1, 0)), 'Ma': ('4040--500mm <6>', POST_Y[1], (0, 1, 0)),
            'Mb': ('4040--500mm <6>', POST_Y[1] + P, (0, -1, 0)), 'B': ('4040--500mm <5>', Y0 + L - P, (0, 1, 0))}
    for s in (-1, 1):
        for k, (bar, y, b) in bars.items():
            out[f'NEW bar-top {s:+d}{k}'] = ((s * 250, y, zc), (s, 0, 0), b, rail_t[s], bar)
    return out


def csM(cs):
    M = np.eye(4); x = np.array(cs['xAxis']); z = np.array(cs['zAxis']); y = np.cross(z, x)
    M[:3, :3] = np.column_stack([x, y, z]); M[:3, 3] = np.array(cs['origin']) * 1000; return M


def face_facing(pid, R, direction):
    """Largest planar face of part pid whose world outward normal (rotation R) equals direction."""
    from geom import faces
    d = np.array(direction, float)
    best = [f for f in faces(pid) if np.allclose(R @ np.array(f['n'], float), d, atol=1e-6)]
    return max(best, key=lambda f: f['area'])['id']


def offset_params(Rel):
    """Rel = C_A^-1 C_B (target). Must be a rotation about Z (+translation)."""
    Rm = Rel[:3, :3]
    assert np.allclose(Rm[2], [0, 0, 1], atol=1e-6) and np.allclose(Rm[:, 2], [0, 0, 1], atol=1e-6), Rm
    ang = np.degrees(np.arctan2(Rm[1, 0], Rm[0, 0]))
    return Rel[:3, 3], ang


def set_offset(feat, off, ang=0.0):
    for p in feat['parameters']:
        pid = p['parameterId']
        if pid == 'mateOffsetEnabled': p['value'] = True
        for i, ax in enumerate('XYZ'):
            if pid == f'mateOffsetDistance{ax}': p['expression'] = f'{off[i]:.4f} mm'; p['value'] = off[i] / 1000
        if pid == 'rotationType': p['value'] = 'ABOUT_Z'
        if pid == 'rotation': p['expression'] = f'{ang:.4f} deg'; p['value'] = float(np.radians(ang))
    return feat
