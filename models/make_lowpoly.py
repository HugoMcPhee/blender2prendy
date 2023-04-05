import bpy
import os
from math import radians
from mathutils import Euler, Vector

# from .dump import dump


# -------------------------------------------------
# Setup model stuff
# -------------------------------------------------

# colorTextureSize = 1024
# colorTextureSize = 512
# colorTextureSize = 256
# TODO parameter
# targetPolys = 15000
# targetPolys = 7500
# targetPolys = 3750
# targetPolys = 4000
# targetPolys = 2000


def set_shading(object, OnOff=True):
    """Set the shading mode of an object
    True means turn smooth shading on.
    False means turn smooth shading off.
    """
    if not object:
        return
    if not object.type == "MESH":
        return
    if not object.data:
        return
    polygons = object.data.polygons
    polygons.foreach_set("use_smooth", [OnOff] * len(polygons))
    object.data.update()


def make_lowpoly(colorTextureSize, targetPolys):

    # get the scene
    scene = bpy.context.scene

    example = "hello"

    print(f"make_lowpoly {example}")

    # After selecting the hipoly

    # Get the selected object
    active_object = bpy.context.view_layer.objects.active
    hipoly_object = active_object

    original_name = hipoly_object.name

    # Rename it name_hipoly
    hipoly_object.name = original_name + "_hipoly"
    # Duplicate it, and replace _hipoly with _lowpoly
    lowpoly_object = hipoly_object.copy()
    lowpoly_object.data = hipoly_object.data.copy()
    lowpoly_object.animation_data_clear()
    lowpoly_object.name = original_name + "_lowpoly"
    # scene.objects.link(lowpoly_object)

    bpy.context.collection.objects.link(lowpoly_object)

    # For the lowpoly, decimate it to about 15,000 by default (can set the number)
    # Shade smooth
    # hipoly_mesh = hipoly_object.data
    # hipoly_object.shade_smooth(True)

    # lowpoly_object.hide_viewport = True

    lowpoly_mesh = lowpoly_object.data

    lowpoly_poly_amount = len(lowpoly_mesh.polygons)

    TARGET_PERCENT = targetPolys / lowpoly_poly_amount

    # Add decimate modifier to lowpoly object
    # decimateModifier = lowpoly_object.modifier_add(name="Decimate", type="DECIMATE")

    decimateModifier = lowpoly_object.modifiers.new(name="Decimate", type="DECIMATE")
    # decimateModifier.ratio = 0.1
    decimateModifier.ratio = TARGET_PERCENT

    # set the lowpoly mesh as active
    bpy.context.view_layer.objects.active = lowpoly_object
    bpy.ops.object.modifier_apply(modifier="Decimate")

    set_shading(lowpoly_object, True)

    # ---------------------------------
    # xatlus
    bpy.context.scene.pack_tool.bruteForce = True
    bpy.context.scene.pack_tool.resolution = colorTextureSize

    original_view_type = bpy.context.area.ui_type
    bpy.context.area.ui_type = "VIEW_3D"

    # lowpoly_object.select_set(True)
    hipoly_object.hide_set(True)
    bpy.context.view_layer.objects.active = lowpoly_object

    bpy.ops.object.setup_unwrap()

    bpy.context.area.ui_type = original_view_type

    # ------------------------
    # Material

    original_material = lowpoly_object.active_material
    original_material.name = original_name + "_hipoly_mat"

    lowpoly_object.active_material = original_material.copy()
    lowpoly_material = lowpoly_object.active_material
    lowpoly_material.name = original_name + "_mat"

    # nodes -------------------------------------------------------------

    tree = lowpoly_material.node_tree

    # Delete the vertex color node

    vertex_color_node = tree.nodes["Vertex Color"]
    tree.nodes.remove(vertex_color_node)

    # color -----

    color_image = bpy.data.images.new(
        "color", width=colorTextureSize, height=colorTextureSize
    )
    # Create a new texture ‘color’ , use the size (1024) and set the color to grey
    # In Shading, create an ‘Image Texture’, select ‘color’ and connect it to the ‘Base Color’

    # clear default nodes
    # for node in tree.nodes:
    #     tree.nodes.remove(node)

    main_material_node = tree.nodes["Principled BSDF"]

    # create image node

    image_node = tree.nodes.new(type="ShaderNodeTexImage")
    image_node.name = "image_node"
    image_node.location = -400, 400
    image_node.image = color_image
    # image_node

    # link nodes
    links = tree.links

    links.new(image_node.outputs[0], main_material_node.inputs[0])

    # choose image from first (current?) camera

    # choose crop

    # link image to scale
    # links.new(image_node.outputs[0], scale_node.inputs[0])

    # normal -----
    # Create a new texture ‘normal’ , use the size (1024)
    # In shading create a normalMap and connect it to ‘normal’
    # Create a ‘Image Texture’ , select ‘normal’, then color-space ‘Non-Color’, and connect to Normal map color

    normal_image = bpy.data.images.new(
        "normal", width=colorTextureSize, height=colorTextureSize
    )
    normal_image.colorspace_settings.name = "Non-Color"

    normal_image_node = tree.nodes.new(type="ShaderNodeTexImage")
    normal_image_node.name = "normal_image_node"
    normal_image_node.location = -500, 0
    normal_image_node.image = normal_image
    # bpy.data.images["color"].colorspace_settings.name = 'Non-Color'

    normal_map_node = tree.nodes.new(type="ShaderNodeNormalMap")
    normal_map_node.name = "normal_map_node"
    normal_map_node.location = -200, 0

    links.new(normal_image_node.outputs[0], normal_map_node.inputs[1])
    links.new(normal_map_node.outputs[0], main_material_node.inputs[22])

    # normal_image_node.

    # -----------------------------
    # Baking
    # -----------------------------

    # (diffuse) ---------------------

    # Set the renderer to cycles
    scene.render.engine = "CYCLES"
    # Set bake type to diffuse
    scene.cycles.bake_type = "DIFFUSE"

    # In ‘Contribution’ check Color, and uncheck indirect and direct
    scene.render.bake.use_pass_direct = False
    scene.render.bake.use_pass_indirect = False
    scene.render.bake.use_pass_color = True

    # Check ‘selected to active’
    scene.render.bake.use_selected_to_active = True

    # Set extrusion to 0.07
    scene.render.bake.cage_extrusion = 0.07

    # deselect all nodes
    for node in tree.nodes:
        node.select = False

    # Select the color image texture node
    image_node.select = True
    tree.nodes.active = image_node

    hipoly_object.hide_set(False)

    # Select hipoly, then lowpoly, and press Bake
    hipoly_object.select_set(True)
    lowpoly_object.select_set(True)
    bpy.context.view_layer.objects.active = lowpoly_object
    bpy.ops.object.bake(type="DIFFUSE")

    # (normal) ---------------------

    # Change Bake type to normal, and keep settings
    scene.cycles.bake_type = "NORMAL"

    # Select the ‘normal’ image texture node
    # deselect all nodes
    for node in tree.nodes:
        node.select = False

    # Select the normal image texture node
    normal_image_node.select = True
    tree.nodes.active = normal_image_node

    # Select hipoly, then lowpoly, and press Bake
    bpy.ops.object.bake(type="NORMAL")

    # hipoly_object.hide_viewport = True  # not the r\real way to hide
    hipoly_object.hide_set(True)
