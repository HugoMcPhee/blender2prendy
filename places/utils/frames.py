import bpy

from ...places.place_info import place_info
from ...utils.getters.get_things import get_scene


def setup_frames_info():
    scene = get_scene()

    # total_frames = scene.frame_end - scene.frame_start
    # total_time = total_frames / scene_framerate
    # chosen_framerate = scene_framerate / scene.frame_step
    # one_frame_time = 1 / chosen_framerate

    #  Get the first and last frames https://blender.stackexchange.com/a/28007
    place_info.first_frame = 9999
    place_info.last_frame = -9999

    for action in bpy.data.actions:
        if action.frame_range[1] > place_info.last_frame:
            place_info.last_frame = action.frame_range[1]
        if action.frame_range[0] < place_info.first_frame:
            place_info.first_frame = action.frame_range[0]

    # use the start marker as the frame start if it's there
    for marker in scene.timeline_markers:
        if marker.frame == 0 or marker.name == "start":
            place_info.first_frame = marker.frame

    scene.frame_start = int(place_info.first_frame)
    scene.frame_end = int(place_info.last_frame)

    place_info.total_frames = scene.frame_end - scene.frame_start
    place_info.total_time = place_info.total_frames / place_info.scene_framerate
    place_info.chosen_framerate = place_info.scene_framerate / scene.frame_step
    place_info.one_frame_time = 1 / place_info.chosen_framerate
