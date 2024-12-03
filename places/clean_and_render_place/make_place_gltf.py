import os
import shutil
import subprocess
import time
import bpy

from ...utils.folders import get_plugin_folder

from ...utils.getters.get_things import get_collections, get_scene, get_view_layer
from ..cam_background import setup_cam_background
from ...utils.collections import (
    include_only_one_collection,
    include_only_two_collections,
)
from ..combine_videos import combine_videos
from ..convert_exportable_curves import (
    convert_floor_curves,
    delete_meshes,
    revert_curve_names,
)
from ..custom_render_video import custom_render_video
from ..place_info import place_info
from ...places.places import (
    update_items_and_variables,
)
from ..hide_meshes import (
    hide_meshes_for_camera,
    reenable_all_meshes,
    reenable_hidden_meshes,
)
from ..depth_visible_objects import (
    set_faster_depth_materials,
    toggle_depth_hidden_objects,
    toggle_depth_visible_objects,
    toggle_world_volume,
    unset_faster_depth_materials,
)
from ..probes import (
    setup_camera_probes,
    setup_probe_rendering,
    toggle_probe_visible_objects,
)
from ..save_typescript_files import save_typescript_files


def make_place_gltf():
    scene = get_scene()
    collections = get_collections()
    view_layer = get_view_layer()

    update_items_and_variables()

    # Change active collection To Exportable

    collection_to_include = collections["Exportable"]
    include_only_one_collection(view_layer, collection_to_include)

    #
    # temporary_wall_meshes_to_export = convert_wall_curves()
    temporary_floor_meshes_to_export = convert_floor_curves()

    #  deselect currently selected
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    # select only the exportable stuff
    for obj in collections["Exportable"].all_objects:
        obj.select_set(True)

    # deselect all panoramic probe cameras
    for obj in collections["cameras"].all_objects:
        # print(obj.name)
        if obj.type == "CAMERA" and obj.data.type == "PANO":
            obj.select_set(False)

    # Export gltf glb file
    bpy.ops.export_scene.gltf(
        export_format="GLB",
        export_cameras=True,
        export_apply=True,
        export_animations=True,
        filepath=place_info.place_folder_path
        + os.sep
        + place_info.this_place_name
        + ".glb",
        use_selection=True,
        export_hierarchy_full_collections=True,
    )

    return temporary_floor_meshes_to_export  # TODO return multiple things here maybe
