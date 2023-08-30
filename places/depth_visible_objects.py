import bpy
from ..get_things import get_view_layer


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
