from dataclasses import dataclass, field
from typing import Dict, List, TypeAlias

from bpy.props import BoolProperty, IntProperty, StringProperty

from ..utils.getters.get_things import make_empty_field

# Collected data for a place, from different properties and other tjhings from the blender file

StringList = List[str]
StringListMap = Dict[str, StringList]


@dataclass
class Segment:
    name: str
    duration: float
    time: float  # the render start time for the segment
    frameStart: int
    frameEnd: int
    total_scene_frames: int


@dataclass
class CamSegmentInfo:
    framerate: int
    can_render: bool


# Maps a segment name to its CamSegmentInfo
CamSegmentInfoBySegment = Dict[str, CamSegmentInfo]  # { segment_name: CamSegmentInfo }

# Maps a camera name to its segments dictionary
CamSegmentInfoBySegmentByCam = Dict[
    str, CamSegmentInfoBySegment
]  # { cam_name: { segment_name: CamSegmentInfo } }


@dataclass
class PlaceInfo:
    # --------
    # Files
    filepath: str = ""
    path: str = ""
    parts: StringList = make_empty_field(list)

    place_folder_path: str = ""
    renders_folder_path: str = ""
    places_folder_path: str = ""
    assets_folder_path: str = ""

    full_filename: str = ""
    full_filename_parts: str = ""
    this_place_name: str = ""

    # --------
    # Scene
    place_names: StringList = make_empty_field(list)
    camera_names: StringList = make_empty_field(list)
    wall_names: StringList = make_empty_field(list)
    floor_names: StringList = make_empty_field(list)
    trigger_names: StringList = make_empty_field(list)
    spot_names: StringList = make_empty_field(list)
    soundspot_names: StringList = make_empty_field(list)
    #  60 so it can be divided into lots of others ( 1, 2, 5, 6, 10, 12, 15, 20, 30 )
    scene_framerate: int = 60
    original_resolution_x: int = 1440  # = scene.render.resolution_x
    original_resolution_y: int = 1440  # = scene.render.resolution_y
    segments_info: Dict[str, Segment] = field(default_factory=dict)
    segments_order: StringList = make_empty_field(list)
    segments_for_cams: StringListMap = make_empty_field(
        dict
    )  # { cam_name: segment_names[]
    segment_info_by_cam: CamSegmentInfoBySegmentByCam = make_empty_field(
        dict
    )  # { cam_name: SegmentInfoForCam }
    # for quickly keeping track of data for each mesh  { meshName: cam_names[] }
    hidden_to_cams_by_mesh: StringListMap = make_empty_field(dict)
    # for quickly accessing the hidden meshes for each camera { cam_name: meshNames[] }
    hidden_meshes_by_cam: StringListMap = make_empty_field(dict)
    meshnames_that_were_disabled_in_render: StringList = make_empty_field(list)
    # bpy.data.worlds["World"].node_tree.nodes["Volume Scatter"].inputs[0].default_value
    original_world_volume_color: str = ""

    # --------
    # Frames
    total_scene_frames: int = 1 - 1  # scene.frame_end - scene.frame_start

    first_frame: int = 9999
    last_frame: int = -9999


place_info = PlaceInfo()
