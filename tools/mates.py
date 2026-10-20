"""Build Fastened-mate feature JSON between two implicit connectors (CENTER of a circular edge, or CENTROID of a face)."""
import random, string

def _id():
    return 'F' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))

def _q(v, unit='mm'):
    return {"btType": "BTMParameterQuantity-147", "isInteger": False, "value": 0.0, "units": "",
            "expression": f"{v}*{unit}"}

def _connector(fid, occ_path, edge_id, inference="CENTER"):
    return {"btType": "BTMMateConnector-66", "featureType": "mateConnector", "implicit": True,
            "isAuxiliaryTreeMateConnector": False, "version": 9, "name": "Mate connector",
            "featureId": fid, "nodeId": fid, "isHidden": True, "suppressed": False,
            "parameters": [
                {"btType": "BTMParameterEnum-145", "enumName": "Origin type", "value": "ON_ENTITY", "parameterId": "originType"},
                {"btType": "BTMParameterQueryWithOccurrenceList-67", "parameterId": "originQuery", "queries": [
                    {"btType": "BTMInferenceQueryWithOccurrence-1083", "inferenceType": inference,
                     "secondDeterministicId": "", "secondEntityQuery": "",
                     "path": occ_path, "deterministicIds": [edge_id]}]},
                {"btType": "BTMParameterBoolean-144", "value": False, "parameterId": "realign"},
                {"btType": "BTMParameterBoolean-144", "value": False, "parameterId": "transform"},
                {"btType": "BTMParameterBoolean-144", "value": False, "parameterId": "flipPrimary"},
                {"btType": "BTMParameterEnum-145", "enumName": "Reorient secondary axis", "value": "PLUS_X", "parameterId": "secondaryAxisType"},
            ]}

def fastened(name, occA, edgeA, occB, edgeB, off=(0, 0, 0), rot_axis='ABOUT_Z', rot_deg=0,
             flip=False, secondary='PLUS_X', inference='CENTER'):
    ca, cb = _id(), _id()
    params = [
        {"btType": "BTMParameterEnum-145", "enumName": "Mate type", "value": "FASTENED", "parameterId": "mateType"},
        {"btType": "BTMParameterQueryWithOccurrenceList-67", "parameterId": "mateConnectorsQuery", "queries": [
            {"btType": "BTMFeatureQueryWithOccurrence-157", "path": [], "featureId": ca, "queryData": ""},
            {"btType": "BTMFeatureQueryWithOccurrence-157", "path": [], "featureId": cb, "queryData": ""}]},
        {"btType": "BTMParameterBoolean-144", "value": any(off) or bool(rot_deg), "parameterId": "mateOffsetEnabled"},
        dict(_q(off[0]), parameterId="mateOffsetDistanceX"),
        dict(_q(off[1]), parameterId="mateOffsetDistanceY"),
        dict(_q(off[2]), parameterId="mateOffsetDistanceZ"),
        {"btType": "BTMParameterEnum-145", "enumName": "Rotation axis", "value": rot_axis, "parameterId": "rotationType"},
        dict(_q(rot_deg, 'deg'), parameterId="rotation"),
        {"btType": "BTMParameterBoolean-144", "value": flip, "parameterId": "primaryAxisAlignment"},
        {"btType": "BTMParameterEnum-145", "enumName": "Reorient secondary axis", "value": secondary, "parameterId": "secondaryAxisAlignment"},
    ]
    return {"btType": "BTMMate-64", "featureType": "mate", "name": name, "version": 2,
            "mateConnectors": [_connector(ca, [occA], edgeA, inference), _connector(cb, [occB], edgeB, inference)],
            "parameters": params}
