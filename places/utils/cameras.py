import bpy
from bpy.props import (
    BoolVectorProperty,
    CollectionProperty,
    PointerProperty,
)

from ...places.custom_props import CamSegmentProps

from ...utils.collections import add_collection_folder_to_cameras
from ...places.make_camcube import make_camcube
from ...places.place_info import CamSegmentInfo, place_info
from ...places.utils.checkers import (
    is_cam_focus_point,
    is_non_pano_camera,
    is_start_name,
)
from ...places.utils.meshes import mesh_to_secret_wireframe
from ...utils.folders import rename_object_to_snake_case
from ...utils.getters.get_things import get_collections


def update_camera_clip_from_point(camera, object):
    """
    Update the camera's clip start and end based on the distance to the point.
    """
    cam_name = camera.name
    # Check the near and far depth points to set the camera clipping
    if object.name == f"{cam_name}_depth" or object.name == f"{cam_name}_depth_far":
        # Get their world space positions as vectors
        point_pos = object.matrix_world.translation
        cam_pos = camera.matrix_world.translation
        distance = (point_pos - cam_pos).length
        camera.data.clip_end = distance
    if object.name == f"{cam_name}_depth_near":
        # Get their world space positions as vectors
        point_pos = object.matrix_world.translation
        cam_pos = camera.matrix_world.translation
        distance = (point_pos - cam_pos).length
        camera.data.clip_start = distance


# turn a camera object into a collection folder if it's only a camera object
def turn_cam_into_collection_folder(cam_object):
    collections = get_collections()

    add_collection_folder_to_cameras(cam_object.name)
    # select the looped camera
    bpy.context.view_layer.objects.active = cam_object
    # remove selected objects from it's collection (the cameras collection)
    cam_object.users_collection[0].objects.unlink(cam_object)
    # move the new camera to the cameras collection
    collections[cam_object.name].objects.link(cam_object)


# Check if there are any cameras in the main cameras collection
def get_has_any_cameras():
    collections = get_collections()
    has_any_cams = (
        len(collections["cameras"].objects) is not 0
        and len(collections["cameras"].children) is not 0
    )
    return has_any_cams


def make_default_camera():
    collections = get_collections()

    # create the first camera
    new_cam = bpy.data.cameras.new("default camera")
    new_cam.lens = 18
    new_cam_object = bpy.data.objects.new("default camera", new_cam)
    collections["cameras"].objects.link(new_cam_object)


def setup_and_get_cameras_info():
    collections = get_collections()

    # if not get_has_any_cameras():
    #     make_default_camera()

    # turn camera objects into collections if they're only objects
    for object in collections["cameras"].objects:
        if is_non_pano_camera(object):
            turn_cam_into_collection_folder(object)

    # loop all camera collection folders
    for cam_folder_collection in collections["cameras"].children:
        # rename sub collections in the camera folder, like cam.001 to cam_001
        rename_object_to_snake_case(cam_folder_collection)

        cam_name = cam_folder_collection.name
        place_info.camera_names.append(cam_name)

        this_cam_has_a_cambox = False
        found_main_camera = None

        child_cam_box_counter = 0

        # loop all items in the camera collection folder to rename
        # and find the main camera
        for object in cam_folder_collection.objects:
            if is_non_pano_camera(object):
                # rename the camera object and the camera inside
                object.name = cam_name
                object.data.name = cam_name
                found_main_camera = object

            # it's a focus point, ensure it has the came name as a prefix
            elif is_cam_focus_point(object):
                if not object.name.startswith(cam_name):
                    object.name = f"{cam_name}_{object.name}"

            # if it's anything else, then it's a cambox, curves and meshes can both be camboxes
            elif not (object.type == "CAMERA") and not (object.type == "EMPTY"):
                child_cam_box_counter += 1
                object.name = f"cambox_{cam_name}_{str(child_cam_box_counter)}"
                this_cam_has_a_cambox = True

        if not this_cam_has_a_cambox:
            make_camcube(found_main_camera)

        # loop again to update other things
        for object in cam_folder_collection.objects:
            if object.type == "MESH":
                mesh_to_secret_wireframe(object)
            elif object.type == "EMPTY":
                # Check the near and far depth points to set the camera clipping
                update_camera_clip_from_point(found_main_camera, object)


def update_cam_segment_infos(cam_data, segment_names):
    # Clear existing items
    # cam_data.cam_segment_infos.clear()
    # Populate with new segment names
    for index, name in enumerate(segment_names):
        # Check if the segment already exists
        if not any(item.segment_name == name for item in cam_data.cam_segment_infos):
            item = cam_data.cam_segment_infos.add()
            item.segment_name = name
            # Set default values if needed
            item.framerate = "12"
            item.can_render = index == 0

    # Loop all items in cam_data.cam_segment_infos and remove any that are not in segment_names
    for item in cam_data.cam_segment_infos:
        if item.segment_name not in segment_names:
            cam_data.cam_segment_infos.remove(item)


# Add segment toggles prop to cameras
def setup_cameras_segments_info():
    collections = get_collections()

    default_segments_toggled = map(is_start_name, place_info.segments_order)

    bpy.types.Camera.segment_toggles = BoolVectorProperty(
        size=len(place_info.segments_order), default=default_segments_toggled
    )

    bpy.types.Camera.cam_segment_infos = CollectionProperty(type=CamSegmentProps)

    def setup_cam_object(cam_object):
        update_cam_segment_infos(cam_object.data, place_info.segments_order)
        segment_names_for_cam = []
        new_place_info_cam_segment_info = {}

        for segment_index, segment_name in enumerate(place_info.segments_order):
            # should_render_segment = cam_object.data.segment_toggles[segment_index]
            # find the segment in the cam_data.cam_segment_infos, and check if it can render
            segment_info = next(
                (
                    item
                    for item in cam_object.data.cam_segment_infos
                    if item.segment_name == segment_name
                ),
                None,
            )
            should_render_segment = segment_info.can_render
            if should_render_segment:
                segment_names_for_cam.append(segment_name)
            # Update place_info.segment_info_by_cam with the segment info
            new_place_info_cam_segment_info[segment_name] = CamSegmentInfo(
                framerate=int(segment_info.framerate),
                can_render=should_render_segment,
            )

        place_info.segments_for_cams[cam_object.name] = segment_names_for_cam
        place_info.segment_info_by_cam[cam_object.name] = (
            new_place_info_cam_segment_info
        )

    for cam_folder_collection in collections["cameras"].children:
        for object in cam_folder_collection.objects:
            if is_non_pano_camera(object):
                setup_cam_object(object)
