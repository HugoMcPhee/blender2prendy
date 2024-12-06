from ..places.interface.meshes import register_mesh_properties
from ..places.place_info import place_info
from ..places.utils.cameras import (
    setup_and_get_cameras_info,
    setup_cameras_segments_info,
)
from ..places.utils.floors import setup_and_get_floors_info
from ..places.utils.frames import setup_frames_info
from ..places.utils.meshes import setup_mesh_objects
from ..places.utils.places import setup_and_get_places_info, setup_place_info_paths
from ..places.utils.segments import setup_and_get_segments_info
from ..places.utils.soundspots import setup_and_get_soundspots_info
from ..places.utils.spots import setup_and_get_spots_info
from ..places.utils.triggers import setup_and_get_triggers_info
from ..places.utils.walls import setup_and_get_walls_info
from ..utils.getters.get_things import get_scene


def setup_reolutions():
    scene = get_scene()

    place_info.original_resolution_x = scene.render.resolution_x
    place_info.original_resolution_y = scene.render.resolution_y


def setup_empty_place_info_data():

    place_info.place_names = []
    place_info.camera_names = []
    place_info.wall_names = []
    place_info.floor_names = []
    place_info.trigger_names = []
    place_info.spot_names = []
    place_info.soundspot_names = []

    place_info.segments_info = {}
    place_info.segments_order = []

    place_info.segments_for_cams = {}
    place_info.hidden_to_cams_by_mesh = {}
    place_info.hidden_meshes_by_cam = {}


def update_items_and_variables():
    setup_reolutions()

    setup_place_info_paths()
    setup_empty_place_info_data()

    setup_frames_info()

    setup_and_get_places_info()
    setup_and_get_cameras_info()
    setup_and_get_walls_info()
    setup_and_get_floors_info()
    setup_and_get_triggers_info()
    setup_and_get_spots_info()
    setup_and_get_soundspots_info()
    setup_and_get_segments_info()

    setup_cameras_segments_info()

    register_mesh_properties(None, None)
    setup_mesh_objects()

    # Show all place_info in console as stringified object
    # print(place_info)
