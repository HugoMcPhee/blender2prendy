import os
import time

import bpy

from ..utils.getters.get_things import get_collections, get_scene, get_view_layer
from ..places.place_info import place_info


def custom_render_video(
    cam_name,
    segment_name,
    renders_folder_path,
    segments_info,
    is_depth=False,
):
    # Exit early
    return

    scene = get_scene()

    # Render once to make sure everything setup TODO make this much lower resolution
    original_resolution_x = scene.render.resolution_x
    original_resolution_y = scene.render.resolution_y
    scene.render.resolution_x = 1
    scene.render.resolution_y = 1
    bpy.ops.render.render(animation=False, write_still=False)
    scene.render.resolution_x = original_resolution_x
    scene.render.resolution_y = original_resolution_y

    # segments_info, chosen_framerate paramerter
    # get_renders_folder_path()

    # set backdrop_type to "color" or "depth" based on is_depth
    backdrop_type = "color"
    if is_depth:
        backdrop_type = "depth"

    nested_dir_path = os.path.join(renders_folder_path, cam_name, segment_name)
    os.makedirs(nested_dir_path, exist_ok=True)
    # make a directory for color and depth (for the frames)
    frames_dir = os.path.join(nested_dir_path, backdrop_type)
    os.makedirs(frames_dir, exist_ok=True)

    frame_image_folder_path = (
        # f"{renders_folder_path}{os.sep}{cam_name}_{segment_name}{fileNamePost}"
        f"{frames_dir}{os.sep}"
    )

    cam_segment_info = place_info.segment_info_by_cam[cam_name][segment_name]

    # Get the segment framerate for this camera
    cam_segment_framerate = cam_segment_info.framerate
    scene.frame_step = int(round(place_info.scene_framerate / cam_segment_framerate))

    segment_info = segments_info[segment_name]
    amount_of_frames_full = scene.frame_end - scene.frame_start
    amount_of_frames_for_segment = segment_info.frameEnd - segment_info.frameStart
    amount_of_frames_saved = int(round(amount_of_frames_for_segment / scene.frame_step))
    nested_dir_path = os.path.join(renders_folder_path, cam_name, segment_name)

    # renders each image frame manually so they can have sequential names like image0000 image0001 instead of frame0000, frame0006

    frame_image_path = f"{frame_image_folder_path}{os.sep}frame"

    # delete all png files in the folder
    for file in os.listdir(frame_image_folder_path):
        if file.endswith(".png"):
            os.remove(os.path.join(frame_image_folder_path, file))

    for stepcounter in range(0, amount_of_frames_saved):
        framenumber = segment_info.frameStart + (stepcounter * scene.frame_step)
        scene.render.filepath = f"{frame_image_path}{str(stepcounter).zfill(4)}.png"
        scene.frame_set(framenumber)
        # make sure to render to 8bit png not 16bit
        scene.render.image_settings.file_format = "PNG"
        # or 'RGBA' if alpha is needed
        scene.render.image_settings.color_mode = "RGB"
        # Ensure this is a string, not an integer
        scene.render.image_settings.color_depth = "8"
        scene.render.image_settings.compression = 15

        time.sleep(0.01)
        bpy.ops.render.render(animation=False, write_still=True)

    print("done making frames")
