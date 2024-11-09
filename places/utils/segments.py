from collections import namedtuple

from ...places.utils.checkers import is_start_name

from ...places.place_info import Segment, place_info
from ...utils.getters.get_things import get_collections, get_scene


# Collect segment names and times
def setup_and_get_segments_info():
    scene = get_scene()
    collections = get_collections()

    has_start_marker = False

    # check if it also doesnt already have a start frame

    for marker in scene.timeline_markers:
        if marker.frame == 0 or marker.name == "start":
            has_start_marker = True
    if not has_start_marker:
        new_first_marker = scene.timeline_markers.new("start", frame=0)

    SimpleMarker = namedtuple("SimpleMarker", ["name", "frame"])

    sorted_markers = []
    for marker in scene.timeline_markers:
        sorted_markers.append(SimpleMarker(frame=marker.frame, name=marker.name))
    sorted_markers.sort(key=lambda x: x.frame)

    # loop through all the markers
    current_marker_index = 0

    for marker in sorted_markers:
        marker_time = (marker.frame - scene.frame_start) / scene.render.fps
        next_marker_time = 0
        next_marker_frame = 0
        next_marker_index = current_marker_index + 1

        if len(sorted_markers) > next_marker_index:
            next_marker = sorted_markers[current_marker_index + 1]
            next_marker_time = (
                next_marker.frame - scene.frame_start
            ) / scene.render.fps
            next_marker_frame = next_marker.frame
        else:
            next_marker_time = (scene.frame_end - scene.frame_start) / scene.render.fps
            next_marker_frame = scene.frame_end

        # print(f"marker_time:{marker_time} next_marker_time: {next_marker_time}")
        print(f"marker_time:{marker_time} next_marker_time: {next_marker_time}")
        marker_duration = next_marker_time - marker_time

        edited_name = marker.name
        if is_start_name(marker.name):
            edited_name = "start"
            place_info.segments_order.insert(0, edited_name)
        else:
            place_info.segments_order.append(edited_name)

        place_info.segments_info[edited_name] = Segment(
            name=edited_name,
            duration=marker_duration,
            time=marker_time,
            frameStart=marker.frame,
            frameEnd=next_marker_frame,
        )

        current_marker_index += 1
