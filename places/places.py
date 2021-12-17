from .collection_instances import focus_instance
from .convert_exportable_curves import (
    convert_floor_curves,
    convert_wall_curves,
    delete_meshes,
    revert_curve_names,
)
from .get_cam_floor_point import get_cam_floor_point
from .make_cam_frustum_mesh import make_cam_frustum_mesh
from .combine_videos import combine_videos
from .custom_render_video import custom_render_video
import bpy
import os
import subprocess
from math import radians
from mathutils import Euler, Vector
from collections import namedtuple
from ..dump import dump
from .save_typescript_files import save_typescript_files
from ..get_things import get_scene, get_collections, get_view_layer
from .make_camcube import make_camcube


# custom ui imports
from bpy.props import (
    BoolProperty,
    BoolVectorProperty,
    IntProperty,
    EnumProperty,
    PointerProperty,
)
from bpy.types import (
    Panel,
    Menu,
    Operator,
    PropertyGroup,
)
from bpy.utils import register_class, unregister_class
from operator import itemgetter


# from Robert Gützkow at https://blender.stackexchange.com/a/160758
def include_only_one_collection(
    view_layer: bpy.types.ViewLayer, collection_to_include: bpy.types.Collection
):
    view_layer = get_view_layer()

    for layer_collection in view_layer.layer_collection.children:
        if layer_collection.collection != collection_to_include:
            layer_collection.exclude = True
        else:
            layer_collection.exclude = False


def enable_all_child_collections(collection_to_include_name: bpy.types.StringProperty):
    view_layer = get_view_layer()

    # NOTE HAVE to loop through view_layer ?? , can't loop through collection.children ohwell
    for collection in view_layer.layer_collection.children[
        collection_to_include_name
    ].children:
        # print(collection.name)
        collection.exclude = False


def add_collection_to_scene(new_name):
    scene = get_scene()
    collections = get_collections()

    if new_name not in collections:
        scene.collection.children.link(collections.new(new_name))


def add_collection_to_exportable_collection(new_name):
    collections = get_collections()

    if new_name not in collections["Exportable"].children:
        collections["Exportable"].children.link(collections.new(new_name))


def add_collection_to_cameras(new_name):
    collections = get_collections()
    if new_name not in collections["cameras"].children:
        collections["cameras"].children.link(collections.new(new_name))


def isStartName(name):
    return name == "start"


def justReturnFalse(name):
    return False


# time is the render start time for the segment
Segment = namedtuple("Segment", ["name", "duration", "time", "frameStart", "frameEnd"])


#  60 so it can be divided into lots of others ( 1, 2, 5, 6, 10, 12, 15, 20, 30 )
scene_framerate = 60

original_resolution_x = 1280  # = scene.render.resolution_x
original_resolution_y = 720  # = scene.render.resolution_y

filepath = ""
path = ""
parts = path.split(os.sep)

parent_folder_path = ""
grandparent_folder_path = ""

full_filename = ""
full_filename_parts = ""
this_place_name = ""


place_names = []
camera_names = []
wall_names = []
floor_names = []
trigger_names = []
spot_names = []
soundspot_names = []

segments_info = {}
segments_order = []


segments_for_cams = {}  # { camName: segmentNames[] }

# for quickly keeping track of data for each mesh
hidden_to_cams_for_meshes = {}  # { meshName: camNames[] }

# for quickly accessing the hidden meshes for each camera
hidden_meshes_for_cams = {}  # { camName: meshNames[] }

meshnames_that_were_disabled_in_render = []

# bpy.data.worlds["World"].node_tree.nodes["Volume Scatter"].inputs[0].default_value
original_world_volume_color = ""


# total_frames = scene.frame_end - scene.frame_start
total_frames = 1 - 1
total_time = total_frames / scene_framerate
# chosen_framerate = scene_framerate / scene.frame_step
chosen_framerate = scene_framerate / 1
one_frame_time = 1 / chosen_framerate

first_frame = 9999
last_frame = -9999


# ----------------------------------------------------------------------------------------
# Setup everything


def update_items_and_variables():

    scene = get_scene()
    collections = get_collections()

    global filepath
    global path
    global parts
    global parent_folder_path
    global grandparent_folder_path
    global full_filename
    global full_filename_parts
    global this_place_name
    global this_place_name
    global place_names
    global camera_names
    global wall_names
    global floor_names
    global trigger_names
    global spot_names
    global soundspot_names
    global segments_info
    global segments_order
    global segments_for_cams
    global hidden_to_cams_for_meshes
    global hidden_meshes_for_cams
    global total_frames
    global total_time
    global chosen_framerate
    global one_frame_time
    global first_frame
    global last_frame

    # update_blender_refs()

    original_resolution_x = scene.render.resolution_x
    original_resolution_y = scene.render.resolution_y

    filepath = bpy.path.basename(bpy.data.filepath)
    if filepath:
        scene.render.filepath = filepath

    # Get absolute path:

    path = os.path.normpath(bpy.data.filepath)
    parts = path.split(os.sep)

    parent_folder_path = os.sep.join(parts[:-1])
    grandparent_folder_path = os.sep.join(parts[:-2])

    full_filename = parts[-1]
    full_filename_parts = full_filename.split(".")
    this_place_name = full_filename_parts[-2]
    this_place_name = this_place_name

    place_names = []
    camera_names = []
    wall_names = []
    floor_names = []
    trigger_names = []
    spot_names = []
    soundspot_names = []

    segments_info = {}
    segments_order = []

    segments_for_cams = {}
    hidden_to_cams_for_meshes = {}
    hidden_meshes_for_cams = {}

    # total_frames = scene.frame_end - scene.frame_start
    # total_time = total_frames / scene_framerate
    # chosen_framerate = scene_framerate / scene.frame_step
    # one_frame_time = 1 / chosen_framerate

    #  Get the first and last frames https://blender.stackexchange.com/a/28007
    first_frame = 9999
    last_frame = -9999

    for action in bpy.data.actions:
        if action.frame_range[1] > last_frame:
            last_frame = action.frame_range[1]
        if action.frame_range[0] < first_frame:
            first_frame = action.frame_range[0]

    # use the start marker as the frame start if it's there
    for m in scene.timeline_markers:
        if m.frame == 0 or m.name == "start":
            first_frame = m.frame

    scene.frame_start = first_frame
    scene.frame_end = last_frame

    total_frames = scene.frame_end - scene.frame_start
    total_time = total_frames / scene_framerate
    chosen_framerate = scene_framerate / scene.frame_step
    one_frame_time = 1 / chosen_framerate
    print("one_frame_time")
    print(one_frame_time)

    # Get place names from folder names (folders with index files)
    with os.scandir(grandparent_folder_path) as it:
        for entry in it:
            if entry.is_dir():
                looped_place_has_index_file = False
                with os.scandir(
                    f"{grandparent_folder_path}{os.sep}{entry.name}"
                ) as place_folder:
                    for place_file in place_folder:
                        if not place_file.name.startswith(".") and place_file.is_file():
                            if place_file.name.startswith("index"):
                                looped_place_has_index_file = True
                if looped_place_has_index_file:
                    place_names.append(entry.name)

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
        # print(f"looped_collection.name{looped_collection.name}")
        looped_collection.name = looped_collection.name.replace(".", "_")
        looped_collection.name = looped_collection.name.replace(" ", "_")

        this_cam_has_a_cambox = False
        found_main_camera = None

        camera_names.append(looped_collection.name)
        child_camBox_counter = 1
        for looped_child_object in looped_collection.objects:
            if (
                looped_child_object.type == "CAMERA"
                and not looped_child_object.data.type == "PANO"
            ):
                # rename the camera object and the camera
                looped_child_object.name = looped_collection.name
                looped_child_object.data.name = looped_collection.name
                found_main_camera = looped_child_object
            elif not (looped_child_object.type == "CAMERA"):
                looped_child_object.name = (
                    f"camBox_{looped_collection.name}.{str(child_camBox_counter)}"
                )
                this_cam_has_a_cambox = True
                child_camBox_counter += 1

        if not this_cam_has_a_cambox:
            make_camcube(found_main_camera)

        # cam_objects = [
        #     ob for ob in scene.objects if ob.type == "CAMERA" and ob.data.type != "PANO"
        # ]

        for looped_child_object in looped_collection.objects:
            if looped_child_object.type == "MESH":
                looped_child_object.display_type = "WIRE"
                looped_child_object.visible_camera = True
                looped_child_object.visible_camera = False
                looped_child_object.visible_diffuse = False
                looped_child_object.visible_glossy = False
                looped_child_object.visible_transmission = False
                looped_child_object.visible_volume_scatter = False
                looped_child_object.visible_shadow = False

    # Rename walls
    child_wall_counter = 1
    for looped_object in collections["walls"].objects:
        if looped_object.type == "MESH" or looped_object.type == "CURVE":
            looped_object.name = looped_object.name.replace(".", "_")
            looped_object.name = looped_object.name.replace(" ", "_")
            # looped_object.name = "wall" + "_" + str(child_wall_counter)
            wall_names.append(looped_object.name)
            child_wall_counter += 1

    # Rename floors
    child_floor_counter = 1
    for looped_object in collections["floors"].objects:
        if looped_object.type == "MESH" or looped_object.type == "CURVE":
            looped_object.name = looped_object.name.replace(".", "_")
            looped_object.name = looped_object.name.replace(" ", "_")
            # looped_object.name = "floor" + "_" + str(child_floor_counter)
            floor_names.append(looped_object.name)
            child_floor_counter += 1

    # Collect trigger names
    for looped_object in collections["triggers"].objects:
        if looped_object.type == "MESH":
            trigger_names.append(looped_object.name)

    # Collect spot names
    for looped_object in collections["spots"].objects:
        if looped_object.type == "EMPTY":
            spot_names.append(looped_object.name)

    # Collect soundspot names
    for looped_object in collections["soundspots"].objects:
        if looped_object.type == "EMPTY":
            soundspot_names.append(looped_object.name)

    # Collect segment names and times

    has_start_marker = False

    # check if it also doesnt already have a start frame

    for m in scene.timeline_markers:
        if m.frame == 0 or m.name == "start":
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

    for m in sorted_markers:
        marker_time = (m.frame - scene.frame_start) / scene.render.fps
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

        edited_name = m.name
        if isStartName(m.name):
            edited_name = "start"
            segments_order.insert(0, edited_name)
        else:
            segments_order.append(edited_name)

        segments_info[edited_name] = Segment(
            name=edited_name,
            duration=marker_duration,
            time=marker_time,
            frameStart=m.frame,
            frameEnd=next_marker_frame,
        )

        current_marker_index += 1

    # Add segment toggles prop to cameras ------------------
    # print("hidden to cams toggles")

    default_segments_toggled = map(isStartName, segments_order)
    # print("________________________")
    # print("default_segments_toggled")
    # dump(default_segments_toggled)

    for looped_collection in collections["cameras"].children:
        for looped_child_object in looped_collection.objects:
            if (
                looped_child_object.type == "CAMERA"
                and not looped_child_object.data.type == "PANO"
            ):
                camera_object = looped_child_object

                segment_names_for_cam = []
                for segment_name in segments_order:
                    should_render_segment = camera_object.segment_toggles[
                        segments_order.index(segment_name)
                    ]
                    if should_render_segment:
                        segment_names_for_cam.append(segment_name)

                segments_for_cams[camera_object.name] = segment_names_for_cam

    bpy.types.Object.segment_toggles = BoolVectorProperty(
        size=len(segments_order), default=default_segments_toggled
    )

    # print("________________________________")

    # Add hidden to cams toggles prop to meshes in "Details" collection ------------------
    limited_camera_names = camera_names[:32]

    default_hidden_to_cams_toggled = map(justReturnFalse, limited_camera_names)
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
                        if not camera_name in hidden_meshes_for_cams:
                            hidden_meshes_for_cams[camera_name] = []
                        hidden_meshes_for_cams[camera_name].append(mesh_object.name)

                hidden_to_cams_for_meshes[mesh_object.name] = hidden_cams_names_for_mesh

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


def setup_video_rendering():
    update_items_and_variables()

    scene = get_scene()

    scene.render.resolution_x = original_resolution_x
    scene.render.resolution_y = original_resolution_y

    scene.render.image_settings.file_format = "PNG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.ffmpeg.constant_rate_factor = "PERC_LOSSLESS"
    scene.render.ffmpeg.gopsize = 4
    scene.node_tree.nodes["Denoise"].use_hdr = True

    # for faster performance
    scene.render.use_persistent_data = True


def toggle_world_volume(isToggled=True):
    global original_world_volume_color

    world_nodes = bpy.data.worlds["World"].node_tree.nodes

    volume_inputs = []

    if "Principled Volume" in world_nodes:
        volume_inputs = world_nodes["Principled Volume"].inputs
    elif "Volume Scatter" in world_nodes:
        volume_inputs = world_nodes["Volume Scatter"].inputs
    else:
        return

    density_input = volume_inputs[2]
    volume_color_input = volume_inputs[0]

    if isToggled:
        if not original_world_volume_color:
            original_world_volume_color = volume_color_input.default_value
        density_input.default_value = 0.0013
        volume_color_input.default_value = original_world_volume_color
    else:
        density_input.default_value = 0
        original_world_volume_color = volume_color_input.default_value
        volume_color_input.default_value = (0, 0, 0, 1)


def toggle_depth_hidden_objects(isToggled=True):
    view_layer = get_view_layer()
    # NOTE HAVE to loop through view_layer ?? , can't loop through collection.children ohwell
    for collection in view_layer.layer_collection.children["Details"].children:
        if collection.name == "hidden_to_depth":
            collection.exclude = not isToggled


# not needed! might help if stopping "make videos" before it finshed
def reenable_all_meshes():
    global meshnames_that_were_disabled_in_render

    for cam_name in hidden_meshes_for_cams:
        for mesh_name in hidden_meshes_for_cams[cam_name]:
            mesh_object = bpy.data.objects[mesh_name]
            mesh_object.hide_render = False
            mesh_object.visible_camera = True


def reenable_hidden_meshes():
    global meshnames_that_were_disabled_in_render
    # re-enable previously hidden meshes
    for mesh_name in meshnames_that_were_disabled_in_render:
        mesh_object = bpy.data.objects[mesh_name]
        mesh_object.visible_camera = True
        mesh_object.hide_render = False
    meshnames_that_were_disabled_in_render = []


def hide_meshes_for_camera(cam_name, isDepth=False):

    global meshnames_that_were_disabled_in_render
    # hide meshes to camera that should be hidden
    if cam_name in hidden_meshes_for_cams:
        for mesh_name in hidden_meshes_for_cams[cam_name]:
            print(mesh_name)
            mesh_object = bpy.data.objects[mesh_name]
            if isDepth:
                mesh_object.hide_render = True
            else:
                mesh_object.visible_camera = False
            meshnames_that_were_disabled_in_render.append(mesh_name)
    else:
        print(f"{cam_name} has no hidden meshes :)")


def setup_probe_rendering():
    scene = get_scene()

    scene.render.resolution_x = 256
    scene.render.resolution_y = 128

    scene.render.image_settings.file_format = "HDR"
    scene.node_tree.nodes["Denoise"].use_hdr = True


def setup_camera_probes():
    collections = get_collections()
    # Loop through current cameras and add probes if needed

    for cam_collection in collections["cameras"].children:
        probe_object = None
        camera_object = None
        for child_object in cam_collection.objects:
            if child_object.type == "CAMERA":
                if child_object.data.type == "PANO":
                    probe_object = child_object
                else:
                    child_object.name = cam_collection.name
                    camera_object = child_object
        if probe_object is None:
            bpy.ops.object.camera_add(
                location=[0, 10, 20],
                rotation=[radians(90), radians(0), radians(180)],
            )
            # https://blender.stackexchange.com/questions/132112/whats-the-blender-2-8-command-for-adding-an-object-to-a-collection-using-python
            # our created camera is the active one
            probe_object = bpy.context.active_object
            # Remove (active) object from all collections not used in a scene
            bpy.ops.collection.objects_remove_all()
            # add it to our specific collection
            cam_collection.objects.link(probe_object)
            # https://blender.stackexchange.com/questions/26852/python-move-object-on-local-axis
            # 15 blender units in z-direction
            dist_z = Vector((0.0, 0.0, -15))
            rotationMAT = camera_object.rotation_euler.to_matrix()
            rotationMAT.invert()
            # project the vector to the world using the rotation matrix
            zVector = dist_z @ rotationMAT
            probe_object.location = camera_object.location + zVector
            # probe_object.location = camera_object.location + Vector((0, -3, -2))

        probe_object.rotation_euler = Euler(
            (radians(90), radians(0), radians(180)), "XYZ"
        )
        probe_object.data.type = "PANO"
        probe_object.data.cycles.panorama_type = "EQUIRECTANGULAR"
        probe_object.name = f"{camera_object.name}_probe"
        # show an axis instead of the camera
        probe_object.show_axis = True
        probe_object.data.display_size = 0.01

        # add custom properties to the camera
        # camera_object.


def setup_place(the_render_quality, the_framerate):
    scene = get_scene()

    # -------------------------------------------------
    # Add collections if they're not there
    # -------------------------------------------------
    print("HEREEREER")
    add_collection_to_scene("Exportable")
    add_collection_to_exportable_collection("walls")
    add_collection_to_exportable_collection("triggers")
    add_collection_to_exportable_collection("cameras")
    add_collection_to_exportable_collection("floors")
    add_collection_to_exportable_collection("spots")
    add_collection_to_exportable_collection("soundspots")
    add_collection_to_scene("Details")

    enable_all_child_collections("Exportable")
    update_items_and_variables()

    # -------------------------------------------------
    # Set up options
    # -------------------------------------------------

    scene.render.engine = "CYCLES"
    bpy.context.view_layer.cycles.denoising_store_passes = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.render.use_motion_blur = True
    scene.cycles.use_denoising = True

    scene.render.fps = scene_framerate

    scene.frame_step = int(round(scene_framerate / the_framerate))
    scene.frame_start = first_frame
    scene.frame_end = last_frame

    # allow frame dropping in the viewport so the speed is right :)
    scene.sync_mode = "FRAME_DROP"

    setup_camera_probes()

    #  Note crashes somehwere after here ----------------------------------------------

    # -------------------------------------------------
    # Adding compositing nodes
    # -------------------------------------------------

    # switch on nodes and get reference
    scene.use_nodes = True
    tree = scene.node_tree

    # clear default nodes
    for node in tree.nodes:
        tree.nodes.remove(node)
    # create RenderLayers node
    # ISSUE HERE
    # CompositorNodeRLayers crashes blender
    # but the default denoise might be fine so will try that
    render_layers_node = tree.nodes.new(type="CompositorNodeRLayers")

    # image_node.image = bpy.data.images['YOUR_IMAGE_NAME']
    render_layers_node.location = 0, 0

    # create Subtract node
    subtract_node = tree.nodes.new(type="CompositorNodeMath")
    subtract_node.operation = "SUBTRACT"
    subtract_node.location = 300, -200

    # create Divide node
    divide_node = tree.nodes.new(type="CompositorNodeMath")
    divide_node.operation = "DIVIDE"
    divide_node.location = 480, -200

    # create Denoise node
    denoise_node = tree.nodes.new(type="CompositorNodeDenoise")
    denoise_node.use_hdr = False
    denoise_node.location = 300, 0

    # create depth toggle switch node
    switch_node = tree.nodes.new(type="CompositorNodeSwitch")
    switch_node.location = 700, 0

    # create output node
    comp_node = tree.nodes.new("CompositorNodeComposite")
    comp_node.location = 900, 0
    # link nodes
    links = tree.links
    # depth to subtract , subtract to divide, divide to depth toggle switch
    links.new(render_layers_node.outputs[2], subtract_node.inputs[0])
    links.new(subtract_node.outputs[0], divide_node.inputs[0])
    links.new(divide_node.outputs[0], switch_node.inputs[1])
    # link render to denoiser
    links.new(render_layers_node.outputs[3], denoise_node.inputs[0])
    links.new(render_layers_node.outputs[4], denoise_node.inputs[1])
    links.new(render_layers_node.outputs[5], denoise_node.inputs[2])

    # link denoiser to switch
    # links.new(denoise_node.outputs[0], switch_node.inputs[0])

    # link rendered image to switch
    links.new(render_layers_node.outputs[0], switch_node.inputs[0])

    # link switch to output
    links.new(switch_node.outputs[0], comp_node.inputs[0])

    def remove_drivers_for_this(objectToChange):
        #    remove existing drivers
        if hasattr(objectToChange, "animation_data"):
            if hasattr(objectToChange.animation_data, "drivers"):
                drivers_data = objectToChange.animation_data.drivers
                for looped_driver in drivers_data:
                    objectToChange.driver_remove(looped_driver.data_path, -1)

    def add_depth_switch_driver(
        objectToChange, propToChange, colorModeValue, depthModeValue
    ):
        # Adding driver
        new_driver = objectToChange.driver_add(propToChange).driver
        new_driver.type = "SCRIPTED"
        new_driver_variable = new_driver.variables.new()
        new_driver_variable.targets[0].id_type = "SCENE"
        new_driver_variable.targets[0].id = scene
        new_driver_variable.targets[0].data_path = 'node_tree.nodes["Switch"].check'
        new_driver.expression = (
            f"{depthModeValue} if int(var) == 1 else {colorModeValue}"
        )

    # -------------------------------------------------
    # Removing current drivers
    # -------------------------------------------------

    remove_drivers_for_this(scene)
    remove_drivers_for_this(tree)

    # -------------------------------------------------
    # Adding drivers to depth toggle nodes
    # -------------------------------------------------

    # Adding subtract driver
    subtract_driver = subtract_node.inputs[1].driver_add("default_value").driver
    subtract_driver.type = "AVERAGE"
    subtract_driver_variable = subtract_driver.variables.new()
    subtract_driver_variable.targets[0].id_type = "SCENE"
    subtract_driver_variable.targets[0].id = scene
    subtract_driver_variable.targets[0].data_path = "camera.data.clip_start"

    # Adding divide driver
    divide_driver = divide_node.inputs[1].driver_add("default_value").driver
    divide_driver.type = "AVERAGE"
    divide_driver_variable = divide_driver.variables.new()
    divide_driver_variable.targets[0].id_type = "SCENE"
    divide_driver_variable.targets[0].id = scene
    divide_driver_variable.targets[0].data_path = "camera.data.clip_end"

    # Add other drivers for depth stuff
    add_depth_switch_driver(scene, "cycles.samples", the_render_quality, 1)
    add_depth_switch_driver(scene, "render.motion_blur_shutter", 0.5, 0.0)
    # '"Filmic"', '"Raw"'
    add_depth_switch_driver(scene, "view_settings.view_transform", 2.1, 4.1)
    # '"sRGB"', '"Raw"'
    add_depth_switch_driver(scene, "sequencer_colorspace_settings.name", 11.0, 10.0)
    add_depth_switch_driver(tree.nodes["Denoise"], "mute", False, True)
    # Set options for video rendering (now that the nodes are created)
    setup_video_rendering()


# -----------------------------------------------------------------------------------------

# -------------------------------------------------
# Original clean and render place
# -------------------------------------------------


def clean_and_render_place(
    should_rerender,
    should_overwrite_render,
    should_convert_probes,
    the_best_lighting_frame,
):
    scene = get_scene()
    collections = get_collections()
    view_layer = get_view_layer()

    update_items_and_variables()

    # Change active collection To Exportable

    collection_to_include = collections["Exportable"]
    include_only_one_collection(view_layer, collection_to_include)

    #
    # temporary_wall_meshes_to_export = convert_wall_curves()
    temporary_floor_meshes_to_export = convert_floor_curves()

    #  deselect currently selected
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    # select only the exportable stuff
    for obj in collections["Exportable"].all_objects:
        obj.select_set(True)

    # deselect all panoramic probe cameras
    for obj in collections["cameras"].all_objects:
        # print(obj.name)
        if obj.type == "CAMERA" and obj.data.type == "PANO":
            obj.select_set(False)

    # Export gltf glb file
    bpy.ops.export_scene.gltf(
        export_format="GLB",
        export_cameras=True,
        export_apply=True,
        export_animations=True,
        filepath=parent_folder_path + os.sep + this_place_name + ".glb",
        use_selection=True,
    )

    # delete_meshes(temporary_wall_meshes_to_export)
    delete_meshes(temporary_floor_meshes_to_export)

    # revert_curve_names("walls")
    revert_curve_names("floors")

    # Change active collection To Details
    collection_to_include = collections["Details"]
    include_only_one_collection(view_layer, collection_to_include)

    #  Add probes if they're missing
    setup_camera_probes()

    for cam_collection in collections["cameras"].children:
        probe_object = None
        camera_object = None
        for looped_object in cam_collection.objects:
            if looped_object.type == "CAMERA":
                if looped_object.data.type == "PANO":
                    probe_object = looped_object
                else:
                    camera_object = looped_object

        render_output_path_start = f"{parent_folder_path}{os.sep}{cam_collection.name}"
        probe_output_path = f"{render_output_path_start}_probe.hdr"

        def getVideoPath(camName, segmentName, isDepthVideo=False):
            video_output_path_pre = (
                f"{parent_folder_path}{os.sep}{camName}_{segmentName}"
            )

            if not isDepthVideo:
                return f"{video_output_path_pre}.mp4"
            else:
                return f"{video_output_path_pre}_depth.mp4"

        segment_names_for_cam = segments_for_cams[camera_object.name]

        if should_rerender:
            print(f"Set camera {looped_object.name}")
            reenable_all_meshes()
            # render probe
            if not os.path.isfile(probe_output_path) or should_overwrite_render:
                scene.camera = probe_object
                original_resolution_x = scene.render.resolution_x
                original_resolution_y = scene.render.resolution_y
                setup_probe_rendering()
                # toggle the depth toggle off
                scene.node_tree.nodes["Switch"].check = False
                # set the frame for the best lighting
                scene.frame_set(the_best_lighting_frame)
                # render with the probe name
                scene.render.filepath = probe_output_path
                bpy.ops.render.render(animation=False, write_still=True)
                scene.render.resolution_x = original_resolution_x
                scene.render.resolution_y = original_resolution_y

            # find all the segments enabled for this camera
            for segment_name in segment_names_for_cam:
                print(f"rendering {segment_name}")
                # customRenderVideo(camera_object.name, segment_name, "")
                originalClipStart = scene.camera.data.clip_start
                originalClipEnd = scene.camera.data.clip_end

                # render color videos
                if (
                    not os.path.isfile(
                        getVideoPath(
                            camName=camera_object.name,
                            segmentName=segment_name,
                            isDepthVideo=False,
                        )
                    )
                    or should_overwrite_render
                ):
                    scene.camera = camera_object

                    originalClipStart = scene.camera.data.clip_start
                    originalClipEnd = scene.camera.data.clip_end

                    scene.camera.data.clip_start = 0.1
                    scene.camera.data.clip_end = 10000

                    setup_video_rendering()
                    # toggle the depth toggle off
                    scene.node_tree.nodes["Switch"].check = False
                    toggle_world_volume(True)
                    toggle_depth_hidden_objects(True)

                    reenable_hidden_meshes()
                    hide_meshes_for_camera(camera_object.name, False)

                    # render without the depth name
                    custom_render_video(
                        camName=camera_object.name,
                        segmentName=segment_name,
                        chosen_framerate=chosen_framerate,
                        parent_folder_path=parent_folder_path,
                        segments_info=segments_info,
                        fileNamePost="",
                    )

                    reenable_hidden_meshes()

                    scene.camera.data.clip_start = originalClipStart
                    scene.camera.data.clip_end = originalClipEnd

                # render depth video
                if (
                    not os.path.isfile(
                        getVideoPath(
                            camName=camera_object.name,
                            segmentName=segment_name,
                            isDepthVideo=True,
                        )
                    )
                    or should_overwrite_render
                ):

                    # originalClipStart = 0.1
                    # originalClipEnd = 50
                    # originalClipStart = scene.camera.data.clip_start
                    # originalClipEnd = scene.camera.data.clip_end

                    # scene.camera.data.clip_start = 0.1
                    # scene.camera.data.clip_end = 50

                    setup_video_rendering()
                    scene.camera = camera_object
                    # toggle the depth toggle on
                    scene.node_tree.nodes["Switch"].check = True
                    scene.camera = camera_object
                    toggle_world_volume(False)
                    toggle_depth_hidden_objects(False)

                    reenable_hidden_meshes()
                    hide_meshes_for_camera(camera_object.name, True)

                    # customRenderVideo(video_output_path_with_depth)
                    custom_render_video(
                        camName=camera_object.name,
                        segmentName=segment_name,
                        chosen_framerate=chosen_framerate,
                        parent_folder_path=parent_folder_path,
                        segments_info=segments_info,
                        fileNamePost="_depth",
                    )

                    reenable_hidden_meshes()

                    # scene.camera.data.clip_start = originalClipStart
                    # scene.camera.data.clip_end = originalClipEnd

            # setup_probe_rendering
            reenable_all_meshes()

    # create join instructions for videos, and join videos

    # combine all the camera names into a join_color_vids.txt and join_depth_vids.txt
    combine_videos(
        parent_folder_path=parent_folder_path,
        camera_names=camera_names,
        segments_for_cams=segments_for_cams,
    )

    # Save the typescript files
    save_typescript_files(
        parent_folder_path,
        this_place_name,
        camera_names,
        segments_for_cams,
        segments_info,
        one_frame_time,
        trigger_names,
        segments_order,
        wall_names,
        grandparent_folder_path,
        place_names,
        floor_names,
        spot_names,
        soundspot_names,
    )
    print("done :) ✨, converting probes ")
    convertProbesCommand = f"{parent_folder_path}"

    # subprocess.run(
    #     "npx github:HugoMcPhee/hdr-to-babylon-env 128", cwd=parent_folder_path
    # )
    if should_convert_probes:
        subprocess.call(
            f"cd {parent_folder_path} && npx github:HugoMcPhee/hdr-to-babylon-env 128",
            shell=True,
        )

    print("delete frames")

    print("all done :)")


# -------------------------------------------------
# Adding tool panel stuff
# -------------------------------------------------


def onUpdate_show_camcubes(self, context):
    collections = get_collections()
    # update_blender_refs()
    for looped_collection in collections["cameras"].children:
        for looped_cam_box in looped_collection.objects:
            # hide or show each camera collider mesh
            if looped_cam_box.type == "MESH":
                looped_cam_box.hide_set(not self.show_camcubes)
                looped_cam_box.hide_render = not self.show_camcubes


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------


class RenderTools_Properties(PropertyGroup):
    should_rerender: BoolProperty(
        name="Make videos", description="Render videos?", default=False
    )
    should_overwrite_render: BoolProperty(
        name="Overwrite renders",
        description="If false, only missing videos / hdr images are rendered",
        default=False,
    )
    should_convert_probes: BoolProperty(
        name="Convert probes",
        description="Convert the .hdr to .ennv for babylonjs",
        default=False,
    )

    the_framerate: IntProperty(
        name="Framerate", description="The Video framerate", default=12, min=1, max=60
    )
    the_render_quality: IntProperty(
        name="Quality", description="The render samples", default=2, min=1, max=500
    )
    the_best_lighting_frame: IntProperty(
        name="Best lighting frame",
        description="The frame to render the lighting probes from",
        default=12,
        min=0,
        max=500,
    )
    my_framerate_enum: EnumProperty(
        name="framerate",
        description="choose one of the framerates",
        items=[
            ("60", "60", ""),
            ("30", "30", ""),
            ("20", "20", ""),
            ("15", "15", ""),
            ("12", "12", ""),
            ("10", "10", ""),
            ("6", "6", ""),
            ("5", "5", ""),
            ("3", "3", ""),
            ("2", "2", ""),
            ("1", "1", "good for trying stuff out"),
        ],
    )
    show_camcubes: BoolProperty(
        name="show camera cubes",
        description="show/hide the camera collision meshes",
        default=True,
        update=onUpdate_show_camcubes,
    )


# ------------------------------------------------------------------------
#    Operators (buttons)
# ------------------------------------------------------------------------


class RenderTools_Operator_SetupPlace(Operator):
    bl_label = "Setup Place"
    bl_idname = "wm.setup_place"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        setup_place(mytool.the_render_quality, int(mytool.my_framerate_enum))
        return {"FINISHED"}


class RenderTools_Operator_RenderVideos(Operator):
    bl_label = "Rerender videos"
    bl_idname = "wm.render_videos"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        clean_and_render_place(
            mytool.should_rerender,
            mytool.should_overwrite_render,
            mytool.should_convert_probes,
            mytool.the_best_lighting_frame,
        )
        return {"FINISHED"}


class RenderTools_Operator_MakeCamFrustumMesh(Operator):
    bl_label = "Make Camera Frustum Mesh"
    bl_idname = "wm.make_camera_frustum_mesh"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool  # to use properties set in the ui
        make_cam_frustum_mesh(scene.camera)
        return {"FINISHED"}


class RenderTools_Operator_CheckCamFloorPoint(Operator):
    bl_label = "Check Camera Floor Point"
    bl_idname = "wm.make_check_camera_floor_point"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        scene = context.scene
        get_cam_floor_point(scene.camera)
        return {"FINISHED"}


class RenderTools_Operator_MakeCameraCube(Operator):
    bl_label = "Make Camera Cube"
    bl_idname = "wm.make_camera_cube"

    # @classmethod
    # def poll(cls, context):
    #     return context.active_object is not None

    def execute(self, context):
        scene = context.scene
        make_camcube(scene.camera)
        return {"FINISHED"}


class RenderTools_Operator_TryNewScript(Operator):
    bl_label = "Try New Script"
    bl_idname = "wm.try_new_script"

    # @classmethod
    # def poll(cls, context):
    #     return context.active_object is not None

    def execute(self, context):
        scene = context.scene
        print("test")
        focus_instance()
        # convert_wall_curves(scene.camera)
        return {"FINISHED"}


# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------


class RenderTools_Panel(Panel):
    # Video Backdrops
    bl_label = "Place Exporting"
    bl_idname = "OBJECT_PT_rendertools_panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        layout.operator("wm.setup_place", text="Setup Place", icon="SHADERFX")
        layout.operator("wm.render_videos", text="Make Place", icon="SCENE")
        layout.prop(mytool, "should_rerender")
        layout.prop(mytool, "should_overwrite_render")
        layout.prop(mytool, "should_convert_probes")
        layout.separator()
        layout.prop(mytool, "my_framerate_enum")
        layout.prop(mytool, "the_render_quality")
        layout.separator()
        layout.prop(mytool, "the_best_lighting_frame")
        layout.separator()
        layout.prop(mytool, "show_camcubes")
        # trying
        layout.operator(
            "wm.make_camera_frustum_mesh",
            text="Make Camera Frustum Mesh",
            icon="VIEW_CAMERA",
        )
        layout.operator(
            "wm.make_check_camera_floor_point",
            text="Make Check Camera Floor Point",
            icon="VIEW_CAMERA",
        )
        layout.operator(
            "wm.make_camera_cube",
            text="Make Camera Cube",
            icon="VIEW_CAMERA",
        )
        layout.operator(
            "wm.try_new_script",
            text="Try New Script",
            icon="OUTLINER_OB_GREASEPENCIL",
        )


# ------------------------------------------------------------------------
#    GUI Registration
# ------------------------------------------------------------------------


# Toggle Segments for Cams --------------------------


def toggle_all_segments(self, context):
    for i, flag in enumerate(self.segment_toggles):
        self.segment_toggles[i] = self.toggle_all_segments
    return None


class SegmentTogglePanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Toggle Segments Panel"
    bl_idname = "OBJECT_PT_toggle_segments"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        theObject = context.object
        should_show = theObject.type == "CAMERA" and theObject.data.type != "PANO"
        return should_show

    def draw(self, context):

        layout = self.layout
        column = layout.column()

        theObject = context.object
        camera_object = None

        if theObject.type == "CAMERA" and theObject.data.type != "PANO":
            camera_object = theObject

            column.prop(camera_object, "toggle_all_segments", text="SELECT ALL")
            column = layout.column(align=True)
            for i, name in enumerate(segments_order):
                column.prop(
                    camera_object, "segment_toggles", index=i, text=name, toggle=True
                )


# Toggle Mesh visiblity for Cams --------------------------
# allow each mesh to be turned off for a camera
def toggle_all_hidden_to_cams(self, context):
    for i, flag in enumerate(self.hidden_to_cam_toggles):
        self.hidden_to_cam_toggles[i] = self.toggle_all_hidden_to_cams
    return None


class HiddenToCamTogglePanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Toggle Hidden To Cams"
    bl_idname = "OBJECT_PT_toggle_hidden_to_cams"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        theObject = context.object

        should_show = (
            theObject.type == "MESH" or theObject.instance_type == "COLLECTION"
        )
        return should_show

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        theObject = context.object
        mesh_object = None

        if theObject.type == "MESH" or theObject.instance_type == "COLLECTION":
            mesh_object = theObject
            column.prop(mesh_object, "toggle_all_hidden_to_cams", text="SELECT ALL")
            column = layout.column(align=True)
            for i, name in enumerate(camera_names):
                column.prop(
                    mesh_object,
                    "hidden_to_cam_toggles",
                    index=i,
                    text=name,
                    toggle=True,
                )


classes = (
    # properties
    RenderTools_Properties,
    #  buttons
    RenderTools_Operator_SetupPlace,
    RenderTools_Operator_RenderVideos,
    RenderTools_Operator_MakeCamFrustumMesh,
    RenderTools_Operator_CheckCamFloorPoint,
    # panels
    RenderTools_Panel,
    SegmentTogglePanel,
    HiddenToCamTogglePanel,
    RenderTools_Operator_MakeCameraCube,
    RenderTools_Operator_TryNewScript,
)


def register_places():
    for loopedClass in classes:
        register_class(loopedClass)

    bpy.types.Scene.my_tool = PointerProperty(type=RenderTools_Properties)
    bpy.types.Object.toggle_all_segments = BoolProperty(update=toggle_all_segments)

    # Adding custom camera props
    bpy.types.Camera.my_prop = bpy.props.BoolProperty(
        name="My Property", description="This is my bpy.props boolean prop"
    )


def unregister_places():
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool
