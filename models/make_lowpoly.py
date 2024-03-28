import math
import bpy


def join_selected_objects():
    """Join all selected objects into the active object."""
    # Ensure we're in object mode
    bpy.ops.object.mode_set(mode="OBJECT")

    # Get the context
    ctx = bpy.context

    # Ensure there is an active object and it's a mesh
    if ctx.active_object and ctx.active_object.type == "MESH":
        # Store the active object
        active_obj = ctx.active_object

        # Select only mesh objects (excluding the active object for now)
        for obj in ctx.selected_objects:
            if obj.type == "MESH" and obj != active_obj:
                obj.select_set(True)
            else:
                obj.select_set(False)

        # Make sure the active object is also selected
        active_obj.select_set(True)

        # Use the active object as the context object
        ctx.view_layer.objects.active = active_obj

        # Join the objects
        bpy.ops.object.join()

        # Optional: you might want to rename the joined object here
        # active_obj.name = "NewJoinedObjectName"
    else:
        print("No active mesh object selected.")


def merge_vertex_colors_and_consolidate_materials(obj):
    """Merge multiple vertex color layers into one and consolidate materials into one, ensuring vertex colors are preserved."""

    if not obj or obj.type != "MESH":
        return

    mesh = obj.data

    # Ensure the object has vertex colors
    if mesh.vertex_colors:
        # Merge vertex colors
        merged_vcol_layer = mesh.vertex_colors.new(name="MergedVCol")
        default_color = [0, 0, 0, 1]  # Default color

        for loop_index in range(len(merged_vcol_layer.data)):
            for vcol_layer in mesh.vertex_colors:
                color = vcol_layer.data[loop_index].color
                if color != default_color:
                    merged_vcol_layer.data[loop_index].color = color
                    break

        # Remove original vertex color layers, except the newly created merged layer
        for vcol_layer in mesh.vertex_colors:
            if vcol_layer.name != "MergedVCol":
                mesh.vertex_colors.remove(vcol_layer)

    # Consolidate materials into one without using bpy.ops
    if len(obj.material_slots) > 1:
        # Get the first material
        first_material = obj.material_slots[0].material

        # Clear all materials to start fresh
        obj.data.materials.clear()

        # Reassign the first material back to the object
        if first_material is not None:
            obj.data.materials.append(first_material)

    # Update the material to use the new merged vertex color layer, if the object has a material
    if (
        obj.material_slots
        and obj.material_slots[0].material
        and obj.material_slots[0].material.use_nodes
    ):
        mat = obj.material_slots[0].material
        tree = mat.node_tree
        # Find or create a Vertex Color node
        vcol_node = (
            tree.nodes.new("ShaderNodeVertexColor")
            if "MergedVCol" not in tree.nodes
            else tree.nodes["MergedVCol"]
        )
        vcol_node.layer_name = "MergedVCol"
        # Connect this node to the Base Color of the Principled BSDF shader, if not already connected
        bsdf_node = tree.nodes.get("Principled BSDF")
        if bsdf_node:
            tree.links.new(vcol_node.outputs["Color"], bsdf_node.inputs["Base Color"])


def make_lowpoly(colorTextureSize, targetPolys):
    # get the scene
    scene = bpy.context.scene

    join_selected_objects()

    # Get the selected object, this is the hipoly
    active_object = bpy.context.view_layer.objects.active
    hipoly_object = active_object
    merge_vertex_colors_and_consolidate_materials(hipoly_object)

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
    # xatlus uv unwrap
    # bpy.context.scene.pack_tool.bruteForce = True
    # bpy.context.scene.pack_tool.resolution = colorTextureSize

    # original_view_type = bpy.context.area.ui_type
    # bpy.context.area.ui_type = "VIEW_3D"

    # # lowpoly_object.select_set(True)
    # hipoly_object.hide_set(True)
    # bpy.context.view_layer.objects.active = lowpoly_object

    # bpy.ops.object.setup_unwrap()

    # bpy.context.area.ui_type = original_view_type

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
    links.new(normal_map_node.outputs[0], main_material_node.inputs[5])

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
