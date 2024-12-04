import bpy

from ..utils.getters.get_things import get_view_layer


def toggle_depth_hidden_objects(isToggled=True):
    view_layer = get_view_layer()
    # NOTE HAVE to loop through view_layer ?? , can't loop through collection.children ohwell
    for collection in view_layer.layer_collection.children["Details"].children:
        if collection.name == "hidden_to_depth":
            collection.exclude = not isToggled


def toggle_depth_visible_objects(isToggled=True):
    view_layer = get_view_layer()
    # NOTE HAVE to loop through view_layer ?? , can't loop through collection.children ohwell
    for collection in view_layer.layer_collection.children["Details"].children:
        if collection.name == "visible_to_depth":
            collection.exclude = not isToggled


def toggle_world_volume(isToggled=True):
    global original_world_volume_color

    world_nodes = bpy.data.worlds["World"].node_tree.nodes

    volume_inputs = []

    if "Principled Volume" in world_nodes:
        volume_inputs = world_nodes["Principled Volume"].inputs
    elif "Volume Scatter" in world_nodes:
        volume_inputs = world_nodes["Volume Scatter"].inputs
    else:
        return

    density_input = volume_inputs[2]
    volume_color_input = volume_inputs[0]

    if isToggled:
        if not original_world_volume_color:
            original_world_volume_color = volume_color_input.default_value
        density_input.default_value = 0.0013
        volume_color_input.default_value = original_world_volume_color
    else:
        density_input.default_value = 0
        original_world_volume_color = volume_color_input.default_value
        volume_color_input.default_value = (0, 0, 0, 1)


def set_faster_depth_materials():
    # Create a simple diffuse material for override
    override_material = bpy.data.materials.new(name="OverrideMaterial")
    override_material.use_nodes = True
    node_tree = override_material.node_tree

    # Clear existing nodes and create a simple Diffuse BSDF
    node_tree.nodes.clear()
    diffuse_node = node_tree.nodes.new(type="ShaderNodeBsdfDiffuse")
    output_node = node_tree.nodes.new(type="ShaderNodeOutputMaterial")

    # Connect the Diffuse BSDF to the Material Output
    node_tree.links.new(diffuse_node.outputs["BSDF"], output_node.inputs["Surface"])

    # Apply Material Override
    view_layer = bpy.context.view_layer
    view_layer.material_override = override_material


def unset_faster_depth_materials():
    view_layer = bpy.context.view_layer

    # Remove Material Override after rendering
    view_layer.material_override = None
