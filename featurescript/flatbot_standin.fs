FeatureScript 3070;
import(path : "onshape/std/geometry.fs", version : "3070.0");

/**
 * Flatbot component stand-in.
 *
 * One feature makes one box-shaped placeholder for an off-the-shelf part
 * (battery, PoE switch, Jetson, bus bar, ...) sitting on a Flatbot deck. The box
 * gets the part name, vendor and description (Amazon ASIN) so it shows up in the
 * assembly BOM. Replace it with the vendor's CAD once you have it.
 *
 * Coordinates match the "Flatbot deck" feature: X across the robot (centred),
 * Y from the front face of the frame (Y = 0) towards the back, Z up from the
 * top face of the bottom frame. "Bottom deck" and "Top deck" put the box on the
 * upper face of that deck plate.
 */

export enum StandinLevel
{
    annotation { "Name" : "Bottom deck" }
    BOTTOM,
    annotation { "Name" : "Top deck" }
    TOP,
    annotation { "Name" : "Custom height" }
    CUSTOM
}

export enum StandinColor
{
    annotation { "Name" : "Dark grey (electronics)" }
    GREY,
    annotation { "Name" : "Black" }
    BLACK,
    annotation { "Name" : "Red" }
    RED,
    annotation { "Name" : "Green (circuit board)" }
    GREEN,
    annotation { "Name" : "Copper" }
    COPPER,
    annotation { "Name" : "Blue" }
    BLUE
}

const SIZE_BOUNDS = { (meter) : [0.001, 0.1, 2], (centimeter) : 10, (millimeter) : 100, (inch) : 4, (foot) : 0.33 } as LengthBoundSpec;
const POS_BOUNDS = { (meter) : [-2, 0, 2], (centimeter) : 0, (millimeter) : 0, (inch) : 0, (foot) : 0 } as LengthBoundSpec;
const POST_BOUNDS = { (meter) : [0.01, 0.25, 2], (centimeter) : 25, (millimeter) : 250, (inch) : 10, (foot) : 0.82 } as LengthBoundSpec;
const PROFILE_BOUNDS = { (meter) : [0.01, 0.04, 0.2], (centimeter) : 4, (millimeter) : 40, (inch) : 1.5, (foot) : 0.125 } as LengthBoundSpec;
const THICKNESS_BOUNDS = { (meter) : [0.0005, 0.00635, 0.05], (centimeter) : 0.635, (millimeter) : 6.35, (inch) : 0.25, (foot) : 0.0208 } as LengthBoundSpec;

annotation { "Feature Type Name" : "Flatbot stand-in",
             "Feature Type Description" : "Box placeholder for an off-the-shelf component on a Flatbot deck, with BOM name, vendor and ASIN." }
export const flatbotStandin = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Group Name" : "Part", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Part name", "Default" : "Component" }
            definition.partName is string;

            annotation { "Name" : "Vendor", "Default" : "" }
            definition.vendor is string;

            annotation { "Name" : "Description (ASIN, notes)", "Default" : "" }
            definition.description is string;

            annotation { "Name" : "Color", "Default" : StandinColor.GREY }
            definition.color is StandinColor;
        }

        annotation { "Group Name" : "Size", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Size X (across robot)" }
            isLength(definition.sizeX, SIZE_BOUNDS);

            annotation { "Name" : "Size Y (front to back)" }
            isLength(definition.sizeY, SIZE_BOUNDS);

            annotation { "Name" : "Size Z (height)" }
            isLength(definition.sizeZ, SIZE_BOUNDS);
        }

        annotation { "Group Name" : "Placement", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Sits on", "Default" : StandinLevel.BOTTOM }
            definition.level is StandinLevel;

            annotation { "Name" : "Centre X (0 = robot centreline)" }
            isLength(definition.centerX, POS_BOUNDS);

            annotation { "Name" : "Centre Y (from frame front)" }
            isLength(definition.centerY, POS_BOUNDS);

            if (definition.level == StandinLevel.CUSTOM)
            {
                annotation { "Name" : "Bottom face Z" }
                isLength(definition.baseZ, POS_BOUNDS);
            }
        }

        annotation { "Group Name" : "Frame (match the Flatbot deck feature)", "Collapsed By Default" : true }
        {
            annotation { "Name" : "Post length" }
            isLength(definition.postLength, POST_BOUNDS);

            annotation { "Name" : "Profile size" }
            isLength(definition.profile, PROFILE_BOUNDS);

            annotation { "Name" : "Deck thickness" }
            isLength(definition.thickness, THICKNESS_BOUNDS);
        }
    }
    {
        var z0 = definition.thickness;
        if (definition.level == StandinLevel.TOP)
            z0 = definition.postLength + definition.profile + definition.thickness;
        else if (definition.level == StandinLevel.CUSTOM)
            z0 = definition.baseZ;

        const c = vector(definition.centerX, definition.centerY, z0);
        const h = vector(definition.sizeX / 2, definition.sizeY / 2, 0 * meter);
        fCuboid(context, id + "box", {
                    "corner1" : c - h,
                    "corner2" : c + h + vector(0 * meter, 0 * meter, definition.sizeZ)
                });

        const body = qCreatedBy(id + "box", EntityType.BODY);
        setProperty(context, { "entities" : body, "propertyType" : PropertyType.NAME, "value" : definition.partName });
        if (definition.vendor != "")
            setProperty(context, { "entities" : body, "propertyType" : PropertyType.VENDOR, "value" : definition.vendor });
        if (definition.description != "")
            setProperty(context, { "entities" : body, "propertyType" : PropertyType.DESCRIPTION, "value" : definition.description });
        setProperty(context, { "entities" : body, "propertyType" : PropertyType.APPEARANCE, "value" : standinColor(definition.color) });
    });

function standinColor(c is StandinColor) returns Color
{
    if (c == StandinColor.BLACK)
        return color(0.12, 0.12, 0.12);
    if (c == StandinColor.RED)
        return color(0.75, 0.15, 0.12);
    if (c == StandinColor.GREEN)
        return color(0.1, 0.45, 0.25);
    if (c == StandinColor.COPPER)
        return color(0.78, 0.47, 0.25);
    if (c == StandinColor.BLUE)
        return color(0.2, 0.4, 0.75);
    return color(0.3, 0.32, 0.35);
}
