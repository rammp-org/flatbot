"""Render one image per assembly step (Assembly tab of the BOM sheet).

Run headless:
  /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/render/render_steps.py -- MESH_DIR OUT_DIR

MESH_DIR holds the STLs + parts.json from step_to_stl.py and placements.json from placements.py.
Parts added in a step are terracotta, earlier parts light grey, later parts hidden. Light-mode
colors from the alex-style tokens.
"""
import bpy, json, os, re, sys
from mathutils import Matrix, Vector

MESH_DIR, OUT_DIR = sys.argv[sys.argv.index('--') + 1:][:2]
os.makedirs(OUT_DIR, exist_ok=True)

def hexrgb(h, a=1.0):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)

INK, DONE, NEW, DECK = '#0b0b0b', '#b9b9b4', '#c4532a', '#e6e6e3'

FRONT, REAR = Vector((-1.0, -1.25, 0.95)), Vector((-1.0, 1.25, 0.95))
VIEW = {7: REAR, 8: REAR}                  # camera direction per step (default FRONT)
HIDE_TOP_DECK = {7, 9}                     # look into the bottom bay
STEPS = {
    2: 'Bottom frame', 3: 'Posts', 4: 'Top frame', 5: 'Casters', 6: 'Decks',
    7: 'Power', 8: 'Compute and network', 9: 'Drive (powered build)',
}


def step_of(base, zc, zmax):
    if base.startswith(('4040 extrusion - 800', '4040 extrusion - 500')):
        return 2 if zmax <= 1 else 4
    if base.startswith('4040 extrusion - 250'):
        return 3
    if base.startswith('3540 corner bracket'):
        return 2 if zc < 0 else 3 if zc < 125 else 4
    if base.startswith('Caster'):
        return 5
    if base.startswith('Deck'):
        return 6
    if base.startswith(('Battery', 'Bus bar', 'Buck')):
        return 7
    if base.startswith(('Jetson', 'PoE', 'ESP32')):
        return 8
    if base.startswith(('Case-top', 'H-mount')):
        return 9
    return None


# ---- scene ----
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        pass
scene.render.resolution_x, scene.render.resolution_y = 1400, 1000
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('w'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 1.0

sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 2.5
sun.rotation_euler = (0.75, -0.35, -0.9)
scene.collection.objects.link(sun)

scene.render.use_freestyle = True
scene.render.line_thickness_mode = 'ABSOLUTE'
scene.render.line_thickness = 1.3
fs = bpy.context.view_layer.freestyle_settings
fs.crease_angle = 2.1          # ~120 deg: real edges, not tessellation facets
ls = fs.linesets[0] if fs.linesets else fs.linesets.new('lines')
ls.select_silhouette = ls.select_border = ls.select_crease = True
if ls.linestyle is None:
    ls.linestyle = bpy.data.linestyles.new('ink')
ls.linestyle.color = hexrgb(INK)[:3]
ls.linestyle.thickness = 1.3


def material(name, hexcol):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = hexrgb(hexcol)
    p.inputs['Roughness'].default_value = 1.0
    return m

MAT = {'done': material('done', DONE), 'new': material('new', NEW), 'deck': material('deck', DECK)}

# ---- parts ----
parts = json.load(open(os.path.join(MESH_DIR, 'parts.json')))
places = json.load(open(os.path.join(MESH_DIR, 'placements.json')))
meshes = {}
for name, info in parts.items():
    base = re.sub(r' \(\d+\)$', '', name)
    if base not in meshes:
        bpy.ops.wm.stl_import(filepath=info['stl'])
        ob = bpy.context.selected_objects[0]
        ob.data.materials.clear()
        ob.data.materials.append(None)          # one slot; each object sets its own material
        meshes[base] = (ob.data, Vector(info['lo']), Vector(info['hi']))
        bpy.data.objects.remove(ob)

objs = []      # (object, step, is_deck)
for base, Ms in places.items():
    if base not in meshes:
        continue
    data, lo, hi = meshes[base]
    for M in Ms:
        ob = bpy.data.objects.new(base, data)
        ob.matrix_world = Matrix(M)
        scene.collection.objects.link(ob)
        ob.material_slots[0].link = 'OBJECT'
        corners = [ob.matrix_world @ Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
        zs = [c.z for c in corners]
        objs.append((ob, step_of(base, (min(zs) + max(zs)) / 2, max(zs)), base, min(zs)))

# ---- camera: orthographic, from the front-left and above; same framing for every step ----
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 1450
TARGET = Vector((0, 400, 60))


def aim(direction):
    cam.location = TARGET + direction.normalized() * 3000
    cam.rotation_euler = (TARGET - cam.location).to_track_quat('-Z', 'Y').to_euler()

cam.data.clip_end = 10000
scene.collection.objects.link(cam)
scene.camera = cam


def show(step):
    for ob, s, base, zmin in objs:
        deck = base.startswith('Deck')
        new = step is not None and s == step
        if s is None:
            ob.hide_render = True
            continue
        # with the top deck hidden, also hide what sits on it, so nothing floats
        cut = step in HIDE_TOP_DECK and (base.startswith('Deck Top') or zmin >= 289)
        ob.hide_render = (step is not None and s > step) or cut
        ob.material_slots[0].material = MAT['new'] if new else MAT['deck'] if deck else MAT['done']


for step in list(STEPS) + [None]:
    show(step)
    aim(VIEW.get(step, FRONT))
    scene.render.filepath = os.path.join(OUT_DIR, f'step_{step}.png' if step else 'complete.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', scene.render.filepath)
