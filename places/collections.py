import bpy
from ..get_things import get_scene, get_collections, get_view_layer


# from Robert Gützkow at https://blender.stackexchange.com/a/160758
def include_only_one_collection(
    view_layer: bpy.types.ViewLayer, collection_to_include: bpy.types.Collection
):
    view_layer = get_view_layer()

    for layer_collection in view_layer.layer_collection.children:
        if layer_collection.collection != collection_to_include:
            layer_collection.exclude = True
        else:
            layer_collection.exclude = False


def enable_all_child_collections(collection_to_include_name: bpy.types.StringProperty):
    view_layer = get_view_layer()

    # NOTE HAVE to loop through view_layer ?? , can't loop through collection.children ohwell
    for collection in view_layer.layer_collection.children[
        collection_to_include_name
    ].children:
        # print(collection.name)
        collection.exclude = False


def add_collection_to_scene(new_name):
    scene = get_scene()
    collections = get_collections()

    if new_name not in collections:
        scene.collection.children.link(collections.new(new_name))


def add_collection_to_exportable_collection(new_name):
    collections = get_collections()

    if new_name not in collections["Exportable"].children:
        collections["Exportable"].children.link(collections.new(new_name))


def add_collection_to_cameras(new_name):
    collections = get_collections()
    if new_name not in collections["cameras"].children:
        collections["cameras"].children.link(collections.new(new_name))
