import bpy


def get_scene():
    scene = bpy.context.scene
    return scene


def get_collections():
    collections = bpy.data.collections
    return collections


def get_view_layer():
    scene = get_scene()
    # view_layer = scene.view_layers["View Layer"]
    view_layer = bpy.context.view_layer
    return view_layer
