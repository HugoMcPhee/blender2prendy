import os
import shutil
import subprocess
import time

import bpy

from ...places.clean_and_render_place.combine_frames_to_images import (
    combine_frames_to_images,
)
from ...places.clean_and_render_place.make_place_gltf import make_place_gltf
from ...places.place_info import place_info
from ...places.places import setup_video_rendering, update_items_and_variables
from ...places.utils.getters.existing_files import (
    get_backdrop_texture_exists,
    get_probe_texture_exists,
)
from ...utils.collections import (
    include_only_one_collection,
    include_only_two_collections,
)
from ...utils.folders import get_plugin_folder
from ...utils.getters.get_things import get_collections, get_scene, get_view_layer
from ..cam_background import setup_cam_background
from ..combine_videos import combine_videos
from ..convert_exportable_curves import (
    convert_floor_curves,
    delete_meshes,
    revert_curve_names,
)
from ..custom_render_video import custom_render_video
from ..depth_visible_objects import (
    set_faster_depth_materials,
    toggle_depth_hidden_objects,
    toggle_depth_visible_objects,
    toggle_world_volume,
    unset_faster_depth_materials,
)
from ..hide_meshes import (
    hide_meshes_for_camera,
    reenable_all_meshes,
    reenable_hidden_meshes,
)
from ..probes import (
    setup_camera_probes,
    setup_probe_rendering,
    toggle_probe_visible_objects,
)
from ..save_typescript_files import save_typescript_files


def setup_color_render():
    """Sets up the scene for rendering in color."""
    scene = get_scene()
    collections = get_collections()
    view_layer = get_view_layer()

    setup_video_rendering()

    # Change active collection To Details
    collection_to_include = collections["Details"]
    include_only_one_collection(view_layer, collection_to_include)
    time.sleep(0.1)  # wait for the collection to change

    # Optimize rendering settings
    scene.cycles.samples = place_info.render_quality
    scene.render.motion_blur_shutter = 0.5
    toggle_world_volume(True)
    toggle_depth_hidden_objects(True)
    toggle_depth_visible_objects(False)
    toggle_probe_visible_objects(False)
    scene.view_settings.view_transform = "Khronos PBR Neutral"
    scene.sequencer_colorspace_settings.name = "Khronos PBR Neutral sRGB"
    scene.view_settings.use_hdr_view = False
    scene.cycles.use_denoising = True
    reenable_hidden_meshes()
    hide_meshes_for_camera(scene.camera.name, False)
    setup_cam_background()
    unset_faster_depth_materials()
