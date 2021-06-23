from ..select_object import select_object
from ..get_things import get_collections
import bpy

# to convert the wall and floor curves to meshes for exporting (and removing the created meshes)


def convert_wall_curves():
    collections = get_collections()
    print("convert_wall_curves")
    temporary_wall_meshes_to_export = []
    # loop through the objects inside 'walls' that are curves
    for looped_object in collections["walls"].objects:
        if looped_object.type == "CURVE":
            select_object(looped_object)
            bpy.ops.object.convert(target="MESH", keep_original=True)
            # now the new mesh is selected
            temporary_wall_meshes_to_export.append(
                bpy.context.view_layer.objects.active
            )

    return temporary_wall_meshes_to_export


def convert_floor_curves():
    collections = get_collections()
    print("convert_floor_curves")
    temporary_floor_meshes_to_export = []
    # loop through the objects inside 'walls' that are curves
    for looped_object in collections["floors"].objects:
        if looped_object.type == "CURVE":
            select_object(looped_object)
            bpy.ops.object.convert(target="MESH", keep_original=True)
            # now the new mesh is selected
            temporary_floor_meshes_to_export.append(
                bpy.context.view_layer.objects.active
            )

    return temporary_floor_meshes_to_export


def delete_meshes(meshes_list):
    for looped_mesh in meshes_list:
        select_object(looped_mesh)
        bpy.ops.object.delete(use_global=False, confirm=False)
        # looped_mesh.delete
        # bpy.data.objects
        # bpy.data.objects.remove(looped_mesh, do_unlink=True)

    # deselect eveything
    # bpy.ops.object.select_all(action="DESELECT")
    # temp_flat_cube.select_set(True)
    # bpy.context.view_layer.objects.active = temp_flat_cube
