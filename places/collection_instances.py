import bpy
import os
from math import radians
from mathutils import Euler, Vector
from ..utils.dump import dump

saved_view_matrix = None
saved_view_rotation = None
# saved_view_location = None


def get_region_3d():

    # found_area = None
    found_area = bpy.context.area

    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            found_area = area

    found_space = found_area.spaces[0]

    for space in found_area.spaces:
        if space.type == "VIEW_3D":
            found_space = space

    return found_space.region_3d


def focus_instance():
    global saved_view_matrix
    global saved_view_rotation
    # global saved_view_location

    default_scene = bpy.data.scenes["Scene"]
    current_scene = bpy.context.window.scene

    # TODO  focus on all objects in the scene after it's set

    # dump(saved_view_rotation)
    # if (current_scene.name == "Scene"):

    is_selecting_collection_instance = False
    is_in_defaut_scene = current_scene == default_scene

    selected_object = bpy.context.view_layer.objects.active

    if (
        hasattr(selected_object, "instance_type")
        and selected_object.instance_type == "COLLECTION"
    ):
        found_collection = selected_object.instance_collection
        if found_collection is not None:
            is_selecting_collection_instance = True

    # if current_scene == default_scene:
    if is_selecting_collection_instance:
        # maybe a command to jump to the selected col-instances collection in the correct scene

        if is_in_defaut_scene:
            found_region3d = get_region_3d()
            saved_view_matrix = found_region3d.view_matrix.copy()
            saved_view_rotation = found_region3d.view_rotation.copy()
            # saved_view_location = found_region3d.view_location
            print("saving view matrix")

        item_name = found_collection.name
        item_scene = bpy.data.scenes[item_name]
        print(item_name)

        bpy.context.window.scene = item_scene
        # focus on the collection
        bpy.ops.object.select_all(action="SELECT")
        # bpy.ops.view3d.localview(frame_selected=True)
        #  could focus on the objects in the collection with the same name, so it doesn't focus on stuff like lights ? :)
        bpy.ops.view3d.view_selected()

    else:
        bpy.context.window.scene = default_scene
        found_region3d = get_region_3d()
        print("loading view matrix")
        print(saved_view_matrix)
        if saved_view_matrix is not None:
            setattr(found_region3d, "view_matrix", saved_view_matrix)
        if saved_view_rotation is not None:
            setattr(found_region3d, "view_rotation", saved_view_rotation)
        # found_region3d.view_matrix = saved_view_matrix
        # found_region3d.view_rotation = saved_view_rotation
        # found_region3d.view_location = saved_view_location

    # dump(selected_object)

    # switch to normal scene
    # bpy.data.scenes[ 'Scene' ]
    # oh check if not in that scene and switch to it!
