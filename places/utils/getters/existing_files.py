import os
import shutil
import subprocess
import time
import bpy

from ....places.clean_and_render_place.make_place_gltf import make_place_gltf
from ....utils.folders import get_plugin_folder
from ....utils.getters.get_things import get_collections, get_scene, get_view_layer
from ....places.place_info import place_info


def get_render_frames_folder_path(cam_name, segment_name, is_depth_video=False):
    backdrop_type = "color"
    if is_depth_video:
        backdrop_type = "depth"
    return os.path.join(
        place_info.renders_folder_path, cam_name, segment_name, backdrop_type
    )


def get_render_exists(cam_name, segment_name, is_depth_video=False):
    path = get_render_frames_folder_path(cam_name, segment_name, is_depth_video)
    return os.path.isdir(path)


def get_backdrop_texture_exists(cam_name, segment_name, is_depth_video=False):
    backdrop_texures_path = os.path.join(place_info.parent_folder_path, "backdrops")
    backdrop_type = "color"
    if is_depth_video:
        backdrop_type = "depth"

    first_texture_name = f"{cam_name}_{segment_name}_{backdrop_type}_1.ktx2"
    return os.path.isfile(os.path.join(backdrop_texures_path, first_texture_name))


def get_probe_texture_exists(cam_name):
    probe_texures_path = os.path.join(place_info.parent_folder_path, "probes")
    texture_name = f"{cam_name}.env"
    return os.path.isfile(os.path.join(probe_texures_path, texture_name))
