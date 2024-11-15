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
    total_frames: int


@dataclass
class CamSegmentInfo:
    framerate: int
    can_render: bool


CamSegmentInfoBySegment = Dict[str, CamSegmentInfo]  # { camName: SegmentInfoForCam }
CamSegmentInfoBySegmentByCam = Dict[
    str, CamSegmentInfoBySegment
]  # { segmentName: SegmentsForCam }


@dataclass
class PlaceInfo:
    # --------
    # Files
    filepath: str = ""
    path: str = ""
    parts: StringList = make_empty_field(list)

    parent_folder_path: str = ""
    renders_folder_path: str = ""
    grandparent_folder_path: str = ""

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
    )  # { camName: segmentNames[]
    segment_info_by_cam: CamSegmentInfoBySegmentByCam = make_empty_field(
        dict
    )  # { camName: segmentNames[]
    # for quickly keeping track of data for each mesh  { meshName: camNames[] }
    hidden_to_cams_by_mesh: StringListMap = make_empty_field(dict)
    # for quickly accessing the hidden meshes for each camera { camName: meshNames[] }
    hidden_meshes_by_cam: StringListMap = make_empty_field(dict)
    meshnames_that_were_disabled_in_render: StringList = make_empty_field(list)
    # bpy.data.worlds["World"].node_tree.nodes["Volume Scatter"].inputs[0].default_value
    original_world_volume_color: str = ""

    # --------
    # Frames
    total_frames: int = 1 - 1  # scene.frame_end - scene.frame_start
    total_time: float = 1
    # chosen_framerate = scene_framerate / scene.frame_step
    chosen_framerate: float = 1
    one_frame_time: float = 1

    first_frame: int = 9999
    last_frame: int = -9999

    # Set initial values based on other values
    def __post_init__(self):
        self.total_time: float = self.total_frames / self.scene_framerate
        self.chosen_framerate = self.scene_framerate / 1
        self.one_frame_time = 1 / self.chosen_framerate


place_info = PlaceInfo()
