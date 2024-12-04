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


def setup_depth_render():
    """Sets up the scene for rendering the depth."""
    scene = get_scene()

    setup_video_rendering()
    # toggle the depth toggle on
    scene.node_tree.nodes["switch_depth"].check = True
    # Optimize rendering settings
    scene.cycles.samples = 1  # Minimal samples for speed
    # NOTE motion_blur_shutter should be 0 for depth, but it crashed with GPU Optix rendering in cycles x
    scene.render.motion_blur_shutter = 0
    toggle_world_volume(False)
    toggle_depth_hidden_objects(False)
    toggle_depth_visible_objects(True)
    toggle_probe_visible_objects(False)
    scene.view_settings.view_transform = "Raw"
    scene.sequencer_colorspace_settings.name = "sRGB"
    scene.view_settings.use_hdr_view = False
    scene.cycles.use_denoising = False
    reenable_hidden_meshes()
    hide_meshes_for_camera(scene.camera.name, True)
    set_faster_depth_materials()


# unset_faster_depth_materials()

# scene.view_settings.view_transform = "Khronos PBR Neutral"
# scene.sequencer_colorspace_settings.name = (
#     "Khronos PBR Neutral sRGB"
# )
# scene.view_settings.use_hdr_view = False

# reenable_hidden_meshes()

# scene.camera.data.clip_start = originalClipStart
# scene.camera.data.clip_end = originalClipEnd
