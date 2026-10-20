"""Run with FreeCAD's freecadcmd: convert every STEP in STEP_DIR to STL in OUT_DIR (assembly coords, mm),
and write parts.json with each part's bounding box."""
import os, json, glob
import Part, Mesh, MeshPart

STEP_DIR = os.environ['STEP_DIR']
OUT_DIR = os.environ['OUT_DIR']
info = {}
for path in sorted(glob.glob(os.path.join(STEP_DIR, '*.step'))):
    name = os.path.basename(path)[:-5].replace('Flatbot Mechanical Assembly - ', '')
    shape = Part.read(path)
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.3, AngularDeflection=0.35)
    out = os.path.join(OUT_DIR, name + '.stl')
    mesh.write(out)
    b = shape.BoundBox
    info[name] = dict(stl=out, lo=[b.XMin, b.YMin, b.ZMin], hi=[b.XMax, b.YMax, b.ZMax])
json.dump(info, open(os.path.join(OUT_DIR, 'parts.json'), 'w'), indent=1)
print('converted', len(info))
