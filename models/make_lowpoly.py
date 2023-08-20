import bpy


def merge_vertex_colors(obj):
    """Merge multiple vertex color layers of the object into one."""

    if not obj or obj.type != "MESH":
        return

    mesh = obj.data

    # Ensure the object has vertex colors
    if len(mesh.vertex_colors) <= 1:
        return  # nothing to merge

    # Merge vertex colors
    merged_vcol_layer = mesh.vertex_colors.new(name="MergedVCol")
    default_color = [0, 0, 0, 1]  # Default color (usually black with alpha of 1)

    for loop_index in range(len(merged_vcol_layer.data)):
        for vcol_layer in mesh.vertex_colors:
            color = vcol_layer.data[loop_index].color
            if color != default_color:
                merged_vcol_layer.data[loop_index].color = color
                break  # Once a valid color is found, skip to the next loop_index

    # Remove original vertex color layers
    while len(mesh.vertex_colors) > 1:
        mesh.vertex_colors.remove(mesh.vertex_colors[0])

    # 1. Delete all materials on the object until left with one
    while len(obj.material_slots) > 1:
        bpy.ops.object.material_slot_remove({"object": obj})

    # 2. Update the remaining material's "Color Attribute" shader node to use the new vertex colors layer
    mat = obj.material_slots[0].material if obj.material_slots else None
    if mat and mat.use_nodes:
        tree = mat.node_tree
        color_attr_node = tree.nodes.get("Color Attribute", None)
        if color_attr_node:
            color_attr_node.layer_name = "MergedVCol"


def set_smooth_shading(object, OnOff=True):
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

    # Get the selected object, this is the hipoly
    active_object = bpy.context.view_layer.objects.active
    hipoly_object = active_object
    merge_vertex_colors(hipoly_object)

    original_name = hipoly_object.name

    # Rename it to <name>_hipoly
    hipoly_object.name = original_name + "_hipoly"
    # Duplicate it, and replace _hipoly with _lowpoly
    lowpoly_object = hipoly_object.copy()
    lowpoly_object.data = hipoly_object.data.copy()
    lowpoly_object.animation_data_clear()
    lowpoly_object.name = original_name + "_lowpoly"
    # scene.objects.link(lowpoly_object)

    bpy.context.collection.objects.link(lowpoly_object)

    # For the lowpoly, decimate it (can set the number)

    lowpoly_mesh = lowpoly_object.data
    lowpoly_poly_amount = len(lowpoly_mesh.polygons)
    decimate_ratio = targetPolys / lowpoly_poly_amount

    # Add decimate modifier to lowpoly object
    decimateModifier = lowpoly_object.modifiers.new(name="Decimate", type="DECIMATE")
    decimateModifier.ratio = decimate_ratio

    # Set the lowpoly mesh as active
    bpy.context.view_layer.objects.active = lowpoly_object
    bpy.ops.object.modifier_apply(modifier="Decimate")

    set_smooth_shading(lowpoly_object, True)

    # ---------------------------------------------
    # xatlus uv unwrap
    bpy.context.scene.pack_tool.bruteForce = True
    bpy.context.scene.pack_tool.resolution = colorTextureSize

    original_view_type = bpy.context.area.ui_type
    bpy.context.area.ui_type = "VIEW_3D"

    # lowpoly_object.select_set(True)
    hipoly_object.hide_set(True)
    bpy.context.view_layer.objects.active = lowpoly_object

    bpy.ops.object.setup_unwrap()

    bpy.context.area.ui_type = original_view_type

    # ---------------------------------------------
    # Material

    original_material = lowpoly_object.active_material
    original_material.name = original_name + "_hipoly_mat"

    lowpoly_object.active_material = original_material.copy()
    lowpoly_material = lowpoly_object.active_material
    lowpoly_material.name = original_name + "_mat"

    # ---------------------------------------------
    # Nodes

    tree = lowpoly_material.node_tree

    # Delete the vertex color node

    vertex_color_node = tree.nodes["Color Attribute"]
    tree.nodes.remove(vertex_color_node)

    # -----------------
    # Color

    color_image = bpy.data.images.new(
        "color", width=colorTextureSize, height=colorTextureSize
    )
    # Create a new texture 'color', and set the color to grey
    # In Shader nodes, create an 'Image Texture', select 'color' and connect it to the 'Base Color' of the 'Principled BSDF'

    main_material_node = tree.nodes["Principled BSDF"]

    # create image node

    image_node = tree.nodes.new(type="ShaderNodeTexImage")
    image_node.name = "image_node"
    image_node.location = -400, 400
    image_node.image = color_image

    # link nodes
    links = tree.links
    links.new(image_node.outputs[0], main_material_node.inputs[0])

    # -----------------
    # Normal
    # Create a new texture 'normal'
    # In shading create a normalMap and connect it to ‘normal’
    # Create a 'Image Texture' , select 'normal', then color-space 'Non-Color', and connect to Normal map color

    normal_image = bpy.data.images.new(
        "normal", width=colorTextureSize, height=colorTextureSize
    )
    normal_image.colorspace_settings.name = "Non-Color"

    normal_image_node = tree.nodes.new(type="ShaderNodeTexImage")
    normal_image_node.name = "normal_image_node"
    normal_image_node.location = -500, 0
    normal_image_node.image = normal_image

    normal_map_node = tree.nodes.new(type="ShaderNodeNormalMap")
    normal_map_node.name = "normal_map_node"
    normal_map_node.location = -200, 0

    links.new(normal_image_node.outputs[0], normal_map_node.inputs[1])
    links.new(normal_map_node.outputs[0], main_material_node.inputs[22])

    # -----------------------------
    # Baking
    # -----------------------------

    # ---------------------
    # Diffuse

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

    # ---------------------
    # Normal

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
