"""Add the component stand-ins (one "Flatbot stand-in" feature each) to the Components Part Studio."""
import sys, json
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import onshape as o

FS = 'a8582993435e3566e681793a'    # Flatbot Stand-in (FeatureScript)
PS = '87c907c98594804e388ca806'    # Components (stand-ins)

# name, vendor, description, color, (X, Y, Z) size mm, level, (cx, cy) mm
PARTS = [
    ('Battery 48V 20Ah', 'LOLRKO', 'ASIN B0DR24K984. 250x126x68 brick, ~4.1 kg. Leads exit one 126x68 end. Strap down.', 'BLUE', (250, 126, 68), 'BOTTOM', (0, 570)),
    ('Bus bar 150A (+)', 'Avelis', 'ASIN B0FX9LFDT9 (2-pack). 137x23x38, 2x M4 holes 96.5 mm apart.', 'RED', (137, 23, 38), 'BOTTOM', (-70, 680)),
    ('Bus bar 150A (-)', 'Avelis', 'ASIN B0FX9LFDT9 (2-pack). 137x23x38, 2x M4 holes 96.5 mm apart.', 'BLACK', (137, 23, 38), 'BOTTOM', (-70, 720)),
    ('Buck converter 48V to 12-28V 90W', 'GZFNTS', 'ASIN B0H6LXJFSC. 72x44x25 body, ears 83 mm apart. One for the Jetson, one for the Kinova arm.', 'GREY', (72, 44, 25), 'BOTTOM', (130, 700)),
    ('Buck converter 48V to 12-28V 90W', 'GZFNTS', 'ASIN B0H6LXJFSC. 72x44x25 body, ears 83 mm apart. Second unit: Kinova arm.', 'GREY', (72, 44, 25), 'BOTTOM', (190, 650)),
    ('Jetson AGX Orin 64GB Dev Kit', 'NVIDIA', 'ASIN B0BYGB3WV4. 110x110x71.65. Alt: Seeed reComputer Robotics J5012 (210x180x87).', 'GREY', (110, 110, 71.65), 'TOP', (0, 600)),
    ('PoE++ switch 8-port', 'LINOVISION', 'ASIN B09XDY8R9G (POE-SW508G). 46W x 110D x 163H on DIN rail; ports on 163x46 front face.', 'BLACK', (46, 110, 163), 'TOP', (-170, 600)),
    ('ESP32-P4-WIFI6-POE-ETH', 'Waveshare', 'ASIN B0G259RFX5. 68x55 board, M2.5 holes on 48x33. Height estimated.', 'GREEN', (55, 68, 20), 'TOP', (150, 520)),
    ('Battery disconnect switch 300A', 'VSTM', 'ASIN B0DBVMSNJ2. 65x65 flange, 4 holes on 54.5 square, ~50 above panel.', 'RED', (65, 65, 50), 'TOP', (200, 715)),
]


def q(pid, v):
    return {"btType": "BTMParameterQuantity-147", "isInteger": False, "value": 0.0, "units": "", "expression": f"{v} mm", "parameterId": pid}

def s(pid, v):
    return {"btType": "BTMParameterString-149", "value": v, "parameterId": pid}

def e(pid, enum, v):
    return {"btType": "BTMParameterEnum-145", "namespace": NS, "enumName": enum, "value": v, "parameterId": pid}


cur = o.get(f'/featurestudios/d/{o.DID}/w/{o.WID}/e/{FS}', fresh=True)
NS = f"e{FS}::m{cur['sourceMicroversion']}"

if __name__ == '__main__':
    only = {int(a) for a in sys.argv[1:]}     # PARTS indices to add; default all
    for k, (name, vendor, desc, col, (sx, sy, sz), lvl, (cx, cy)) in enumerate(PARTS):
        if only and k not in only:
            continue
        feat = {"btType": "BTMFeature-134", "featureType": "flatbotStandin", "namespace": NS, "name": name + (" (arm)" if "Kinova arm." in desc else ""),
                "parameters": [s('partName', name), s('vendor', vendor), s('description', desc),
                               e('color', 'StandinColor', col), q('sizeX', sx), q('sizeY', sy), q('sizeZ', sz),
                               e('level', 'StandinLevel', lvl), q('centerX', cx), q('centerY', cy), q('baseZ', 0),
                               q('postLength', 250), q('profile', 40), q('thickness', 6.35)]}
        r = o.post(f'/partstudios/d/{o.DID}/w/{o.WID}/e/{PS}/features', {"feature": feat})
        print(name, r['featureState']['featureStatus'])
    print('calls', o.calls_used())
