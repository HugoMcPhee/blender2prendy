import os
from collections import namedtuple

import bpy

# custom ui imports
from bpy.props import BoolVectorProperty

from .place_info import PlaceInfo, Segment, empty_field

from ..get_things import get_collections, get_scene
from .collections import add_collection_to_cameras
from .make_camcube import make_camcube


def is_start_name(name):
    return name == "start"


def just_return_false(name):
    return False


def update_items_and_variables(place_info: PlaceInfo):
    scene = get_scene()
    collections = get_collections()

    # update_blender_refs()

    place_info.original_resolution_x = scene.render.resolution_x
    place_info.original_resolution_y = scene.render.resolution_y

    place_info.filepath = bpy.path.basename(bpy.data.filepath)
    if place_info.filepath:
        scene.render.filepath = place_info.filepath

    # Get absolute path:

    place_info.path = os.path.normpath(bpy.data.filepath)
    place_info.parts = place_info.path.split(os.sep)

    place_info.parent_folder_path = os.sep.join(place_info.parts[:-1])
    place_info.grandparent_folder_path = os.sep.join(place_info.parts[:-2])

    place_info.full_filename = place_info.parts[-1]
    place_info.full_filename_parts = place_info.full_filename.split(".")
    place_info.this_place_name = place_info.full_filename_parts[-2]

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
    place_info.hidden_to_cams_for_meshes = {}
    place_info.hidden_meshes_for_cams = {}

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

    # Get place names from folder names (folders with <placeName>.ts files)
    with os.scandir(place_info.grandparent_folder_path) as directory_iterator:
        for directory in directory_iterator:
            if directory.is_dir():
                looped_place_has_main_file = False
                with os.scandir(
                    f"{place_info.grandparent_folder_path}{os.sep}{directory.name}"
                ) as place_folder:
                    looped_place_name = directory.name
                    print(f"looped_place_name: {looped_place_name}")
                    # print(f"place_info: {place_info}")
                    print(f"place_info.place_names: {place_info.place_names}")
                    for place_file in place_folder:
                        if not place_file.name.startswith(".") and place_file.is_file():
                            if place_file.name.startswith(looped_place_name):
                                looped_place_has_main_file = True
                if looped_place_has_main_file:
                    place_info.place_names.append(looped_place_name)

    # Create a default camera theres no cameras in Exportable/cameras
    if (
        len(collections["cameras"].objects) is 0
        and len(collections["cameras"].children) is 0
    ):
        # create the first camera
        new_cam = bpy.data.cameras.new("default camera")
        new_cam.lens = 18
        new_cam_object = bpy.data.objects.new("default camera", new_cam)
        collections["cameras"].objects.link(new_cam_object)

    # turn camera objects into collections if theyre only objects
    for looped_object in collections["cameras"].objects:
        if looped_object.type == "CAMERA" and not looped_object.data.type == "PANO":
            add_collection_to_cameras(looped_object.name)
            # select the looped camera
            bpy.context.view_layer.objects.active = looped_object
            # Remove selected objects from all collections
            # bpy.ops.collection.objects_remove_all()
            looped_object.users_collection[0].objects.unlink(looped_object)
            # move the new camcube to the cameras collection
            collections[looped_object.name].objects.link(looped_object)

    # Rename camera objects if in a collection

    for looped_collection in collections["cameras"].children:
        looped_collection.name = looped_collection.name.replace(".", "_")
        looped_collection.name = looped_collection.name.replace(" ", "_")

        this_cam_has_a_cambox = False
        found_main_camera = None

        looped_cam_name = looped_collection.name

        place_info.camera_names.append(looped_cam_name)
        child_camBox_counter = 1
        for child_object in looped_collection.objects:
            if child_object.type == "CAMERA" and not child_object.data.type == "PANO":
                # rename the camera object and the camera
                child_object.name = looped_cam_name
                child_object.data.name = looped_cam_name
                found_main_camera = child_object

            elif not (child_object.type == "CAMERA") and not (
                child_object.type == "EMPTY"
            ):
                child_object.name = (
                    f"camBox_{looped_cam_name}.{str(child_camBox_counter)}"
                )
                this_cam_has_a_cambox = True
                child_camBox_counter += 1

        if not this_cam_has_a_cambox:
            make_camcube(found_main_camera)

        # cam_objects = [
        #     ob for ob in scene.objects if ob.type == "CAMERA" and ob.data.type != "PANO"
        # ]

        for child_object in looped_collection.objects:
            if child_object.type == "MESH":
                child_object.display_type = "WIRE"
                child_object.visible_camera = True
                child_object.visible_camera = False
                child_object.visible_diffuse = False
                child_object.visible_glossy = False
                child_object.visible_transmission = False
                child_object.visible_volume_scatter = False
                child_object.visible_shadow = False
            elif child_object.type == "EMPTY":
                # Check the near and far depth points to set the camera clipping
                if (
                    child_object.name == f"{looped_cam_name}_depth"
                    or child_object.name == f"{looped_cam_name}_depth_far"
                ):
                    # Get their world space positions as vectors
                    point_pos = child_object.matrix_world.translation
                    cam_pos = found_main_camera.matrix_world.translation
                    distance = (point_pos - cam_pos).length
                    found_main_camera.data.clip_end = distance
                if child_object.name == f"{looped_cam_name}_depth_near":
                    # Get their world space positions as vectors
                    point_pos = child_object.matrix_world.translation
                    cam_pos = found_main_camera.matrix_world.translation
                    distance = (point_pos - cam_pos).length
                    found_main_camera.data.clip_start = distance

    # Rename walls
    child_wall_counter = 1
    for looped_object in collections["walls"].objects:
        if looped_object.type == "MESH" or looped_object.type == "CURVE":
            looped_object.name = looped_object.name.replace(".", "_")
            looped_object.name = looped_object.name.replace(" ", "_")
            # looped_object.name = "wall" + "_" + str(child_wall_counter)
            place_info.wall_names.append(looped_object.name)
            child_wall_counter += 1

    # Rename floors
    child_floor_counter = 1
    for looped_object in collections["floors"].objects:
        if looped_object.type == "MESH" or looped_object.type == "CURVE":
            looped_object.name = looped_object.name.replace(".", "_")
            looped_object.name = looped_object.name.replace(" ", "_")
            # looped_object.name = "floor" + "_" + str(child_floor_counter)
            place_info.floor_names.append(looped_object.name)
            child_floor_counter += 1

    # Collect trigger names
    for looped_object in collections["triggers"].objects:
        if looped_object.type == "MESH":
            place_info.trigger_names.append(looped_object.name)

    # Collect spot names
    for looped_object in collections["spots"].objects:
        if looped_object.type == "EMPTY":
            place_info.spot_names.append(looped_object.name)

    # Collect soundspot names
    for looped_object in collections["soundspots"].objects:
        if looped_object.type == "EMPTY":
            place_info.soundspot_names.append(looped_object.name)

    # Collect segment names and times

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

    # Add segment toggles prop to cameras ------------------
    # print("hidden to cams toggles")

    default_segments_toggled = map(is_start_name, place_info.segments_order)
    # print("________________________")
    # print("default_segments_toggled")
    # dump(default_segments_toggled)

    bpy.types.Object.segment_toggles = BoolVectorProperty(
        size=len(place_info.segments_order), default=default_segments_toggled
    )

    for looped_collection in collections["cameras"].children:
        for child_object in looped_collection.objects:
            if child_object.type == "CAMERA" and not child_object.data.type == "PANO":
                camera_object = child_object

                segment_names_for_cam = []
                for segment_name in place_info.segments_order:
                    should_render_segment = camera_object.segment_toggles[
                        place_info.segments_order.index(segment_name)
                    ]
                    if should_render_segment:
                        segment_names_for_cam.append(segment_name)

                place_info.segments_for_cams[camera_object.name] = segment_names_for_cam

    # print("________________________________")

    # Add hidden to cams toggles prop to meshes in "Details" collection ------------------
    limited_camera_names = place_info.camera_names[:32]

    default_hidden_to_cams_toggled = map(just_return_false, limited_camera_names)
    bpy.types.Object.hidden_to_cam_toggles = BoolVectorProperty(
        size=len(limited_camera_names), default=default_hidden_to_cams_toggled
    )

    def do_for_each_child(looped_child_item):
        # print(looped_child_item.name)
        if hasattr(looped_child_item, "type"):
            looped_child_object = looped_child_item
            if (
                looped_child_object.type == "MESH"
                or looped_child_object.instance_type == "COLLECTION"
            ):
                # print(looped_child_object.name)
                mesh_object = looped_child_object
                #
                hidden_cams_names_for_mesh = []
                for camera_name in limited_camera_names:
                    should_hide_for_cam = mesh_object.hidden_to_cam_toggles[
                        limited_camera_names.index(camera_name)
                    ]
                    if should_hide_for_cam:
                        hidden_cams_names_for_mesh.append(camera_name)
                        # if not hasattr(hidden_meshes_for_cams, camera_name):
                        if not camera_name in place_info.hidden_meshes_for_cams:
                            place_info.hidden_meshes_for_cams[camera_name] = []
                        place_info.hidden_meshes_for_cams[camera_name].append(
                            mesh_object.name
                        )

                place_info.hidden_to_cams_for_meshes[
                    mesh_object.name
                ] = hidden_cams_names_for_mesh

    def recurvise_for_meshes_in_collection(top_collection, levels=10):
        def recurse(looped_item, depth):
            if depth > levels:
                print("at limit")
                return

            item_is_collection = hasattr(looped_item, "objects")
            # print(f"{looped_item.name} {item_is_collection}")

            if item_is_collection:
                # print(f"{looped_item.name}")
                # loop inner objects
                for child in looped_item.objects:
                    recurse(child, depth + 1)
                # loop other collections
                for child in looped_item.children:
                    recurse(child, depth + 1)
            else:
                # print(f"         {looped_item.name}")
                do_for_each_child(looped_item)
                # loop inner objects
                for child in looped_item.children:
                    recurse(child, depth + 1)

        recurse(top_collection, 0)

    recurvise_for_meshes_in_collection(collections["Details"])
