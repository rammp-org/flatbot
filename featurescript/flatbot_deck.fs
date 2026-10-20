FeatureScript 3070;
import(path : "onshape/std/geometry.fs", version : "3070.0");

/**
 * Flatbot deck plates.
 *
 * Builds the laser-cut deck plates that sit on the Flatbot 4040 frame:
 *   - Bottom deck: sits on the bottom frame (Z = 0) and is notched around the six
 *     vertical posts and the corner braces at their feet.
 *   - Top deck: sits on the top frame (Z = post length + profile), no notches.
 * Each deck can be split across the middle crossbar so the halves fit a smaller
 * laser bed; the split line runs down the middle of the crossbar so each half
 * rests on half of it.
 *
 * Coordinates: X across the robot (centred), Y from the front face of the frame
 * (Y = 0) towards the back, Z up from the top face of the bottom frame.
 *
 * Mounting holes sit on the centre lines of the rails and end crossbars, which is
 * where the single T-slot of a 40-series 4040 profile runs, so they line up with
 * M8 hammer-head T-nuts.
 */

const FRAME_LENGTH_BOUNDS = { (meter) : [0.2, 0.8, 3], (centimeter) : 80, (millimeter) : 800, (inch) : 31.5, (foot) : 2.625 } as LengthBoundSpec;
const FRAME_WIDTH_BOUNDS = { (meter) : [0.2, 0.58, 3], (centimeter) : 58, (millimeter) : 580, (inch) : 22.8, (foot) : 1.9 } as LengthBoundSpec;
const PROFILE_BOUNDS = { (meter) : [0.01, 0.04, 0.2], (centimeter) : 4, (millimeter) : 40, (inch) : 1.5, (foot) : 0.125 } as LengthBoundSpec;
const POST_BOUNDS = { (meter) : [0.01, 0.25, 2], (centimeter) : 25, (millimeter) : 250, (inch) : 10, (foot) : 0.82 } as LengthBoundSpec;
const MID_BOUNDS = { (meter) : [0.05, 0.401, 3], (centimeter) : 40.1, (millimeter) : 401, (inch) : 15.8, (foot) : 1.3 } as LengthBoundSpec;
const THICKNESS_BOUNDS = { (meter) : [0.0005, 0.00635, 0.05], (centimeter) : 0.635, (millimeter) : 6.35, (inch) : 0.25, (foot) : 0.0208 } as LengthBoundSpec;
const CLEARANCE_BOUNDS = { (meter) : [0, 0.0015, 0.02], (centimeter) : 0.15, (millimeter) : 1.5, (inch) : 0.06, (foot) : 0.005 } as LengthBoundSpec;
const OVERHANG_BOUNDS = { (meter) : [0, 0, 0.1], (centimeter) : 0, (millimeter) : 0, (inch) : 0, (foot) : 0 } as LengthBoundSpec;
const HOLE_BOUNDS = { (meter) : [0, 0.0085, 0.03], (centimeter) : 0.85, (millimeter) : 8.5, (inch) : 0.34, (foot) : 0.028 } as LengthBoundSpec;
const SPACING_BOUNDS = { (meter) : [0.02, 0.16, 1], (centimeter) : 16, (millimeter) : 160, (inch) : 6.3, (foot) : 0.525 } as LengthBoundSpec;

annotation { "Feature Type Name" : "Flatbot deck",
             "Feature Type Description" : "Parametric laser-cut deck plates for the Flatbot 4040 frame, with post notches and T-nut mounting holes." }
export const flatbotDeck = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Group Name" : "Frame", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Frame length (rail length)" }
            isLength(definition.frameLength, FRAME_LENGTH_BOUNDS);

            annotation { "Name" : "Frame width (outside of rails)" }
            isLength(definition.frameWidth, FRAME_WIDTH_BOUNDS);

            annotation { "Name" : "Profile size" }
            isLength(definition.profile, PROFILE_BOUNDS);

            annotation { "Name" : "Post length (vertical extrusions)" }
            isLength(definition.postLength, POST_BOUNDS);

            annotation { "Name" : "Middle crossbar: front face distance from frame front" }
            isLength(definition.midOffset, MID_BOUNDS);
        }

        annotation { "Group Name" : "Plates", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Bottom deck", "Default" : true }
            definition.bottomDeck is boolean;

            annotation { "Name" : "Top deck", "Default" : true }
            definition.topDeck is boolean;

            annotation { "Name" : "Split each deck at middle crossbar", "Default" : true }
            definition.split is boolean;

            annotation { "Name" : "Sheet thickness" }
            isLength(definition.thickness, THICKNESS_BOUNDS);

            annotation { "Name" : "Overhang past frame" }
            isLength(definition.overhang, OVERHANG_BOUNDS);

            annotation { "Name" : "Notch clearance (bottom deck)" }
            isLength(definition.clearance, CLEARANCE_BOUNDS);
        }

        annotation { "Group Name" : "Mounting holes", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Hole diameter (0 = none)" }
            isLength(definition.holeDiameter, HOLE_BOUNDS);

            annotation { "Name" : "Max hole spacing" }
            isLength(definition.holeSpacing, SPACING_BOUNDS);
        }
    }
    {
        const L = definition.frameLength;
        const W = definition.frameWidth;
        const P = definition.profile;
        const t = definition.thickness;
        const m = definition.overhang;
        const c = definition.clearance;
        const mid = definition.midOffset;
        const splitY = mid + P / 2;

        if (mid < 2 * P || mid + P > L - 2 * P)
            throw regenError("Middle crossbar must leave room for the corner posts", ["midOffset"]);
        if (W < 5 * P)
            throw regenError("Frame is too narrow for the profile size", ["frameWidth"]);

        var decks = [];
        if (definition.bottomDeck)
            decks = append(decks, { "name" : "Bottom", "z" : 0 * meter, "notched" : true });
        if (definition.topDeck)
            decks = append(decks, { "name" : "Top", "z" : definition.postLength + P, "notched" : false });

        for (var d in decks)
        {
            var pieces = [];
            if (definition.split)
                pieces = [{ "name" : "front", "y0" : -m, "y1" : splitY },
                          { "name" : "back", "y0" : splitY, "y1" : L + m }];
            else
                pieces = [{ "name" : "", "y0" : -m, "y1" : L + m }];

            for (var pc in pieces)
            {
                const pid = id + (d.name ~ pc.name);
                fCuboid(context, pid + "plate", {
                            "corner1" : vector(-W / 2 - m, pc.y0, d.z),
                            "corner2" : vector(W / 2 + m, pc.y1, d.z + t)
                        });
                const plate = qCreatedBy(pid + "plate", EntityType.BODY);

                var cutters = [];
                var n = 0;
                const zLo = d.z - t;
                const zHi = d.z + 2 * t;

                if (d.notched)
                {
                    // Corner posts: post plus the brace on its outboard side, both on the rail.
                    // Middle posts: post on the rail plus the brace inboard on the crossbar.
                    var boxes = [];
                    for (var s in [-1, 1])
                    {
                        const xEdge = s * (W / 2 + m + P);
                        boxes = append(boxes, [s * (W / 2 - P - c), -m - P, xEdge, 2 * P + c]);
                        boxes = append(boxes, [s * (W / 2 - P - c), L - 2 * P - c, xEdge, L + m + P]);
                        boxes = append(boxes, [s * (W / 2 - 2 * P - c), mid - c, xEdge, mid + P + c]);
                    }
                    for (var b in boxes)
                    {
                        fCuboid(context, pid + ("notch" ~ n), {
                                    "corner1" : vector(b[0], b[1], zLo),
                                    "corner2" : vector(b[2], b[3], zHi)
                                });
                        cutters = append(cutters, qCreatedBy(pid + ("notch" ~ n), EntityType.BODY));
                        n += 1;
                    }
                }

                if (definition.holeDiameter > 0 * meter)
                {
                    for (var h in deckHoles(definition, d.notched, pc.y0, pc.y1, splitY))
                    {
                        fCylinder(context, pid + ("hole" ~ n), {
                                    "bottomCenter" : vector(h[0], h[1], zLo),
                                    "topCenter" : vector(h[0], h[1], zHi),
                                    "radius" : definition.holeDiameter / 2
                                });
                        cutters = append(cutters, qCreatedBy(pid + ("hole" ~ n), EntityType.BODY));
                        n += 1;
                    }
                }

                if (size(cutters) > 0)
                {
                    opBoolean(context, pid + "cut", {
                                "tools" : qUnion(cutters),
                                "targets" : plate,
                                "operationType" : BooleanOperationType.SUBTRACTION
                            });
                }

                var partName = "Deck " ~ d.name;
                if (pc.name != "")
                    partName = partName ~ " - " ~ pc.name;
                setProperty(context, { "entities" : plate, "propertyType" : PropertyType.NAME, "value" : partName });
            }
        }
    });

/** Evenly spaced points from a to b (inclusive), at most `spacing` apart, at least two. */
function spread(a is ValueWithUnits, b is ValueWithUnits, spacing is ValueWithUnits) returns array
{
    if (b - a < spacing / 4)
        return [];
    const count = max(2, ceil((b - a) / spacing) + 1);
    var out = [];
    for (var i = 0; i < count; i += 1)
        out = append(out, a + (b - a) * i / (count - 1));
    return out;
}

/** Hole centres (x, y) for the deck piece spanning y0..y1. */
function deckHoles(definition is map, notched is boolean, y0 is ValueWithUnits, y1 is ValueWithUnits, splitY is ValueWithUnits) returns array
{
    const L = definition.frameLength;
    const W = definition.frameWidth;
    const P = definition.profile;
    const c = definition.clearance;
    const mid = definition.midOffset;
    const e = max(definition.holeDiameter, P / 2);   // edge distance from notches and the split edge
    const s = definition.holeSpacing;
    const xRail = W / 2 - P / 2;

    // Rail line runs (y ranges) that are clear of posts, braces and the split.
    var runs = [];
    if (notched)
        runs = [[2 * P + c + e, mid - c - e], [mid + P + c + e, L - 2 * P - c - e]];
    else
        runs = [[P / 2, L - P / 2]];

    var pts = [];
    for (var r in runs)
    {
        const a = max(r[0], y0 + (y0 > 0 * meter ? e : 0 * meter));
        const b = min(r[1], y1 - (y1 < L ? e : 0 * meter));
        if (b <= a)
            continue;
        for (var y in spread(a, b, s))
            pts = concatenateArrays([pts, [[-xRail, y], [xRail, y]]]);
    }

    // End crossbars (front and back). On the top deck the rail holes already sit at the
    // corners, so the outermost points of this row are dropped.
    const xEnd = notched ? W / 2 - P - c - e : xRail;
    for (var y in [P / 2, L - P / 2])
    {
        if (y < y0 || y > y1)
            continue;
        const row = spread(-xEnd, xEnd, s);
        for (var i = 0; i < size(row); i += 1)
        {
            if (!notched && (i == 0 || i == size(row) - 1))
                continue;
            pts = append(pts, [row[i], y]);
        }
    }
    return pts;
}
