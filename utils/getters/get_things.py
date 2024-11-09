from dataclasses import field
import bpy

from ...places.utils.checkers import is_non_pano_camera


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


def just_return_false(name):
    return False


def get_item(collection, id_value, id_field="id"):
    """Find an item in a collection by ID.

    Args:
        collection: The collection to search in.
        id_value: The ID value to match.
        id_field: The name of the field representing the ID (default is "id").

    Returns:
        The item with the matching ID, or None if no match is found.
    """
    return next(
        (item for item in collection if getattr(item, id_field, None) == id_value), None
    )


def make_empty_field(factory=list):
    return field(default_factory=factory)


def get_camera_in_collection(collection: bpy.types.Collection):
    for object in collection.objects:
        if is_non_pano_camera(object):
            return object
