from ..select_object import select_object
from ..get_things import get_collections
import bpy

TEMP_CURVE_PREFIX = "temp_renamed_curve_"
# to convert the wall and floor curves to meshes for exporting (and removing the created meshes)


def convert_curves_in_collection(collection_name):
    collections = get_collections()
    print("convert_wall_curves")
    temporary_meshes_to_export = []
    # loop through the objects inside 'walls' that are curves
    for looped_object in collections[collection_name].objects:
        if looped_object.type == "CURVE":
            original_name = looped_object.name
            looped_object.name = f"{TEMP_CURVE_PREFIX}{original_name}"

            select_object(looped_object)
            bpy.ops.object.convert(target="MESH", keep_original=True)
            bpy.context.view_layer.objects.active.name = original_name
            # now the new mesh is selected
            temporary_meshes_to_export.append(bpy.context.view_layer.objects.active)

    return temporary_meshes_to_export


def convert_wall_curves():
    return convert_curves_in_collection("walls")


def convert_floor_curves():
    return convert_curves_in_collection("floors")


def delete_meshes(meshes_list):
    for looped_mesh in meshes_list:
        select_object(looped_mesh)
        bpy.ops.object.delete(use_global=False, confirm=False)
        # looped_mesh.delete
        # bpy.data.objects
        # bpy.data.objects.remove(looped_mesh, do_unlink=True)


def revert_curve_names(collection_name):
    collections = get_collections()
    # loop through the objects inside 'walls' that are curves
    for looped_object in collections[collection_name].objects:
        if looped_object.type == "CURVE":
            looped_object.name = looped_object.name.removeprefix(TEMP_CURVE_PREFIX)

    # deselect eveything
    # bpy.ops.object.select_all(action="DESELECT")
    # temp_flat_cube.select_set(True)
    # bpy.context.view_layer.objects.active = temp_flat_cube
