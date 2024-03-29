import math
import bpy


# Function to create a bake setup for metallic and roughness
def setup_bake_from_vertex_color(obj, vertex_color_layer, target_channel, image_node):
    # Ensure that the object has a material and uses nodes
    if not (
        obj.material_slots
        and obj.material_slots[0].material
        and obj.material_slots[0].material.use_nodes
    ):
        print(f"Object {obj.name} doesn't have a material with node support.")
        return

    mat = obj.material_slots[0].material
    tree = mat.node_tree

    # Try to find an existing Vertex Color node for the specified layer, or create a new one
    vcol_node = next(
        (
            node
            for node in tree.nodes
            if node.type == "VERTEX_COLOR" and node.layer_name == vertex_color_layer
        ),
        None,
    )
    if not vcol_node:
        # Create a new Vertex Color node
        vcol_node = tree.nodes.new("ShaderNodeVertexColor")
        vcol_node.layer_name = vertex_color_layer
        vcol_node.location = -200, 0  # You might want to adjust the position

    # Create an Emission node
    emission_node = tree.nodes.new("ShaderNodeEmission")
    emission_node.location = vcol_node.location.x + 400, vcol_node.location.y

    # Create a Separate RGB node to extract the correct channel
    separate_rgb_node = tree.nodes.new("ShaderNodeSeparateRGB")
    separate_rgb_node.location = vcol_node.location.x + 200, vcol_node.location.y

    # Connect the Vertex Color node to the Separate RGB node
    tree.links.new(vcol_node.outputs["Color"], separate_rgb_node.inputs["Image"])

    # Connect the target channel of Separate RGB node to the Emission node's color input
    if target_channel in separate_rgb_node.outputs:
        tree.links.new(
            separate_rgb_node.outputs[target_channel], emission_node.inputs["Color"]
        )
    else:
        print(f"Invalid target channel: {target_channel}")
        return

    # Connect the Emission node to the Material Output node (temporarily, for baking)
    mat_output_node = next(
        (node for node in tree.nodes if node.type == "OUTPUT_MATERIAL"), None
    )
    if mat_output_node:
        tree.links.new(
            emission_node.outputs["Emission"], mat_output_node.inputs["Surface"]
        )

    # Set the image node as active for baking, assuming it's a valid node object
    if image_node and image_node in tree.nodes.values():
        tree.nodes.active = image_node
    else:
        print(
            f"Specified image node is not valid or not found in the material node tree."
        )

    return emission_node, separate_rgb_node


def join_selected_objects():
    """Join all selected objects into the active object."""
    # Ensure we're in object mode
    bpy.ops.object.mode_set(mode="OBJECT")

    # Get the context
    ctx = bpy.context

    # Filter selected mesh objects
    selected_mesh_objects = [obj for obj in ctx.selected_objects if obj.type == "MESH"]

    # Proceed only if there are multiple selected mesh objects
    if len(selected_mesh_objects) > 1 and ctx.active_object in selected_mesh_objects:
        # Set the active object as the context object
        ctx.view_layer.objects.active = ctx.active_object

        # Join the objects
        bpy.ops.object.join()


def consolidate_materials(obj):
    """Consolidate all materials into one on the specified object."""
    if not obj or obj.type != "MESH":
        return

    if len(obj.material_slots) > 1:
        # Get the first material
        first_material = obj.material_slots[0].material

        # Clear all materials to start fresh
        obj.data.materials.clear()

        # Reassign the first material back to the object
        if first_material is not None:
            obj.data.materials.append(first_material)


def make_lowpoly(colorTextureSize, targetPolys):
    # get the scene
    scene = bpy.context.scene

    join_selected_objects()

    # Get the selected object, this is the hipoly
    active_object = bpy.context.view_layer.objects.active
    hipoly_object = active_object
    consolidate_materials(hipoly_object)

    bpy.ops.object.shade_smooth()  # make the high poly object shaded smooth

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
    hipoly_object.select_set(False)
    bpy.context.view_layer.objects.active = lowpoly_object
    bpy.ops.object.modifier_apply(modifier="Decimate")

    # set_smooth_shading(lowpoly_object, True)
    bpy.ops.object.shade_smooth()

    # ---------------------------------------------
    # blender uv unwrap and pack

    bpy.context.view_layer.objects.active = lowpoly_object

    original_view_type = bpy.context.area.ui_type
    bpy.context.area.ui_type = "VIEW_3D"

    # Ensure the object's context is correct
    hipoly_object.select_set(False)
    bpy.context.view_layer.objects.active = lowpoly_object
    lowpoly_object.select_set(True)

    # Create a UV Map if it doesn't exist
    if not lowpoly_object.data.uv_layers:
        bpy.ops.mesh.uv_texture_add()

    # Switch to Edit Mode
    bpy.ops.object.mode_set(mode="EDIT")

    # Save the original value of use_uv_select_sync
    original_sync_setting = bpy.context.scene.tool_settings.use_uv_select_sync

    # Set use_uv_select_sync to True to synchronize edit mode and UV selection
    bpy.context.scene.tool_settings.use_uv_select_sync = True

    # Select all faces
    bpy.ops.mesh.select_all(action="SELECT")

    # Apply Smart UV Project with specific options
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(66),  # Convert 66 degrees to radians
        island_margin=0.0,
        area_weight=0.0,
        correct_aspect=True,
        scale_to_bounds=False,
    )

    # Pack Islands with specific options
    bpy.ops.uv.pack_islands(
        udim_source="CLOSEST_UDIM",
        rotate=True,
        rotate_method="ANY",
        scale=True,
        merge_overlap=False,
        margin_method="SCALED",
        margin=0.001,
        pin=False,
        pin_method="LOCKED",
        shape_method="CONCAVE",
    )

    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.context.area.ui_type = original_view_type

    # Restore the original value of use_uv_select_sync
    bpy.context.scene.tool_settings.use_uv_select_sync = original_sync_setting

    # ---------------------------------------------
    # Material

    original_material = lowpoly_object.active_material
    original_material.name = original_name + "_hipoly_mat"

    lowpoly_object.active_material = original_material.copy()
    lowpoly_material = lowpoly_object.active_material
    lowpoly_material.name = original_name + "_mat"

    hipoly_material = hipoly_object.active_material
    # ---------------------------------------------
    # Nodes

    lowTree = lowpoly_material.node_tree
    hiTree = hipoly_material.node_tree

    # Delete the vertex color node

    vertex_color_node = lowTree.nodes["Color Attribute"]
    lowTree.nodes.remove(vertex_color_node)

    # -----------------
    # Color

    color_image = bpy.data.images.new(
        "color", width=colorTextureSize, height=colorTextureSize
    )
    # Create a new texture 'color', and set the color to grey
    # In Shader nodes, create an 'Image Texture', select 'color' and connect it to the 'Base Color' of the 'Principled BSDF'

    main_material_node = lowTree.nodes["Principled BSDF"]

    # create image node

    image_node = lowTree.nodes.new(type="ShaderNodeTexImage")
    image_node.name = "image_node"
    image_node.location = -400, 400
    image_node.image = color_image

    # link nodes
    links = lowTree.links
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

    normal_image_node = lowTree.nodes.new(type="ShaderNodeTexImage")
    normal_image_node.name = "normal_image_node"
    normal_image_node.location = -500, 0
    normal_image_node.image = normal_image

    normal_map_node = lowTree.nodes.new(type="ShaderNodeNormalMap")
    normal_map_node.name = "normal_map_node"
    normal_map_node.location = -200, 0

    links.new(normal_image_node.outputs[0], normal_map_node.inputs[1])
    links.new(normal_map_node.outputs[0], main_material_node.inputs[5])

    # -----------------
    # Metallic

    metallic_image = bpy.data.images.new(
        "metallic", width=colorTextureSize, height=colorTextureSize
    )
    metallic_image.colorspace_settings.name = "Non-Color"

    metallic_image_node = lowTree.nodes.new(type="ShaderNodeTexImage")
    metallic_image_node.name = "metallic_image_node"
    metallic_image_node.location = -500, -100
    metallic_image_node.image = metallic_image

    # Note: No need to create a separate node to modify the metallic channel.
    # It's a single value channel, not a vector like normal maps.

    # link nodes
    links.new(metallic_image_node.outputs[0], main_material_node.inputs["Metallic"])

    # -----------------
    # Roughness

    roughness_image = bpy.data.images.new(
        "roughness", width=colorTextureSize, height=colorTextureSize
    )
    roughness_image.colorspace_settings.name = "Non-Color"

    roughness_image_node = lowTree.nodes.new(type="ShaderNodeTexImage")
    roughness_image_node.name = "roughness_image_node"
    roughness_image_node.location = -500, -200
    roughness_image_node.image = roughness_image

    # link nodes
    links.new(roughness_image_node.outputs[0], main_material_node.inputs["Roughness"])

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
    for node in lowTree.nodes:
        node.select = False

    # Select the color image texture node
    image_node.select = True
    lowTree.nodes.active = image_node

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
    for node in lowTree.nodes:
        node.select = False

    # Select the normal image texture node
    normal_image_node.select = True
    lowTree.nodes.active = normal_image_node

    # Select hipoly, then lowpoly, and press Bake
    bpy.ops.object.bake(type="NORMAL")

    # ---------------------
    # Metallic Bake

    # Create the temporary bake setup for metallic and roughness
    # Metallic uses the green channel, and Roughness uses the red channel

    # Bake Metallic
    emission_node_metallic, separate_rgb_node_metallic = setup_bake_from_vertex_color(
        hipoly_object, "Col.001", "G", metallic_image_node
    )

    # Select the metallic image texture node
    metallic_image_node.select = True
    lowTree.nodes.active = metallic_image_node  # Switch active node to metallic
    bpy.ops.object.bake(type="EMIT")

    # Bake Roughness
    emission_node_roughness, separate_rgb_node_roughness = setup_bake_from_vertex_color(
        hipoly_object, "Col.001", "R", roughness_image_node
    )

    # Select the roughness image texture node
    roughness_image_node.select = True
    lowTree.nodes.active = roughness_image_node  # Switch active node to roughness
    bpy.ops.object.bake(type="EMIT")

    # Remove temporary nodes
    # tree = hipoly_object.material_slots[0].material.node_tree
    hiNodes = hiTree.nodes
    if emission_node_metallic and emission_node_metallic.name != "Dummy":
        hiNodes.remove(emission_node_metallic)
    if separate_rgb_node_metallic and separate_rgb_node_metallic.name != "Dummy":
        hiNodes.remove(separate_rgb_node_metallic)
    if emission_node_roughness and emission_node_roughness.name != "Dummy":
        hiNodes.remove(emission_node_roughness)
    if separate_rgb_node_roughness and separate_rgb_node_roughness.name != "Dummy":
        hiNodes.remove(separate_rgb_node_roughness)

    # ----------------------------------------------------------
    # Hide

    # hipoly_object.hide_viewport = True  # not the r\real way to hide
    hipoly_object.hide_set(True)
