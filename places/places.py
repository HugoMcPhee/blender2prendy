from math import radians

import bpy

# custom ui imports
from mathutils import Euler, Vector

from .place_info import PlaceInfo
from .update_items_and_variables import update_items_and_variables

from ..get_things import get_collections, get_scene, get_view_layer
from .collections import (
    add_collection_to_exportable_collection,
    add_collection_to_scene,
    enable_all_child_collections,
)

# ----------------------------------------------------------------------------------------
# Setup everything


def setup_video_rendering(place_info: PlaceInfo):
    update_items_and_variables(place_info)

    scene = get_scene()

    scene.render.resolution_x = place_info.original_resolution_x
    scene.render.resolution_y = place_info.original_resolution_y

    scene.render.image_settings.file_format = "PNG"
    # NOTE videos aren't rendered directly anymore, images are then converted to videos with ffmpeg
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


def toggle_depth_visible_objects(isToggled=True):
    view_layer = get_view_layer()
    # NOTE HAVE to loop through view_layer ?? , can't loop through collection.children ohwell
    for collection in view_layer.layer_collection.children["Details"].children:
        if collection.name == "visible_to_depth":
            collection.exclude = not isToggled


def toggle_probe_visible_objects(isToggled=True):
    view_layer = get_view_layer()
    # NOTE HAVE to loop through view_layer ?? , can't loop through collection.children ohwell
    for collection in view_layer.layer_collection.children["Details"].children:
        if collection.name == "visible_to_probe":
            collection.exclude = not isToggled


# not needed! might help if stopping "make videos" before it finshed
def reenable_all_meshes(place_info: PlaceInfo):
    global meshnames_that_were_disabled_in_render

    for cam_name in place_info.hidden_meshes_for_cams:
        for mesh_name in place_info.hidden_meshes_for_cams[cam_name]:
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


def hide_meshes_for_camera(place_info: PlaceInfo, cam_name, isDepth=False):
    global meshnames_that_were_disabled_in_render
    # hide meshes to camera that should be hidden
    if cam_name in place_info.hidden_meshes_for_cams:
        for mesh_name in place_info.hidden_meshes_for_cams[cam_name]:
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


def setup_cam_background():
    scene = get_scene()

    try:
        # get background image struct
        active_cam = scene.camera.name
        bg_images = bpy.data.objects[active_cam].data.background_images.items()
        # get background image data, if it exists in struct
        found_background_image = bg_images[0][1].image
        scene.node_tree.nodes["image_node"].image = found_background_image
        scene.node_tree.nodes["switch_background"].check = True
        scene.render.film_transparent = True
        scene.view_settings.view_transform = "Standard"

        # image_scale = bg_images[0][1].scale
    except:
        scene.node_tree.nodes["switch_background"].check = False
        scene.render.film_transparent = False
        print("No Background Found")


def setup_place(place_info: PlaceInfo, the_render_quality, the_framerate):
    scene = get_scene()

    # -------------------------------------------------
    # Add collections if they're not there
    # -------------------------------------------------
    print("setting up place")
    add_collection_to_scene("Exportable")
    add_collection_to_exportable_collection("walls")
    add_collection_to_exportable_collection("triggers")
    add_collection_to_exportable_collection("cameras")
    add_collection_to_exportable_collection("floors")
    add_collection_to_exportable_collection("spots")
    add_collection_to_exportable_collection("soundspots")
    add_collection_to_scene("Details")

    enable_all_child_collections("Exportable")
    update_items_and_variables(place_info)

    # -------------------------------------------------
    # Set up options
    # -------------------------------------------------

    scene.render.engine = "CYCLES"
    bpy.context.view_layer.cycles.denoising_store_passes = True
    bpy.context.view_layer.use_pass_z = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.render.use_motion_blur = True
    scene.cycles.use_denoising = True

    scene.render.fps = place_info.scene_framerate

    scene.frame_step = int(round(place_info.scene_framerate / the_framerate))
    scene.frame_start = int(place_info.first_frame)
    scene.frame_end = int(place_info.last_frame)

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

    render_layers_node.location = 0, 0

    # create back-image toggle switch node
    switch_background_node = tree.nodes.new(type="CompositorNodeSwitch")
    switch_background_node.name = "switch_background"
    switch_background_node.location = 600, 250

    # create image node
    image_node = tree.nodes.new(type="CompositorNodeImage")
    image_node.name = "image_node"
    image_node.location = 0, 400

    setup_cam_background()

    # image_node.image = bpy.data.images['YOUR_IMAGE_NAME']

    # create scale node
    scale_node = tree.nodes.new(type="CompositorNodeScale")
    scale_node.name = "background_scale"
    scale_node.location = 200, 350
    scale_node.space = "RENDER_SIZE"
    scale_node.frame_method = "CROP"

    # create alpha over node
    alpha_over_node = tree.nodes.new(type="CompositorNodeAlphaOver")
    alpha_over_node.name = "alpha_over"
    alpha_over_node.location = 400, 300

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
    switch_depth_node = tree.nodes.new(type="CompositorNodeSwitch")
    switch_depth_node.name = "switch_depth"
    switch_depth_node.location = 700, 0

    # create output node
    comp_node = tree.nodes.new("CompositorNodeComposite")
    comp_node.location = 900, 0

    # link nodes
    links = tree.links

    # choose image from first (current?) camera

    # choose crop

    # link image to scale
    links.new(image_node.outputs[0], scale_node.inputs[0])
    # link scale to alpha over
    links.new(scale_node.outputs[0], alpha_over_node.inputs[1])
    # link alpha over to background switch
    links.new(alpha_over_node.outputs[0], switch_background_node.inputs[1])
    # render image to alpha over
    links.new(render_layers_node.outputs[0], alpha_over_node.inputs[2])
    # link render image to background switch
    links.new(render_layers_node.outputs[0], switch_background_node.inputs[0])
    # link background switch to depth switch
    links.new(switch_background_node.outputs[0], switch_depth_node.inputs[0])
    #

    # depth to subtract , subtract to divide, divide to depth toggle switch
    links.new(render_layers_node.outputs[2], subtract_node.inputs[0])
    links.new(subtract_node.outputs[0], divide_node.inputs[0])
    links.new(divide_node.outputs[0], switch_depth_node.inputs[1])
    # link render to denoiser
    links.new(render_layers_node.outputs[3], denoise_node.inputs[0])
    links.new(render_layers_node.outputs[4], denoise_node.inputs[1])
    links.new(render_layers_node.outputs[5], denoise_node.inputs[2])

    # link denoiser to switch
    # links.new(denoise_node.outputs[0], switch_node.inputs[0])

    # link rendered image to switch
    # links.new(render_layers_node.outputs[0], switch_depth_node.inputs[0])

    # link switch to output
    links.new(switch_depth_node.outputs[0], comp_node.inputs[0])

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
        new_driver_variable.targets[
            0
        ].data_path = 'node_tree.nodes["switch_depth"].check'
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
    # NOTE motion_blur_shutter should be 0 for depth, but it crashes with GPU Optix rendering in cycles x
    add_depth_switch_driver(scene, "render.motion_blur_shutter", 0.5, 0.1)
    # now done before render
    # '"Filmic"', '"Raw"'
    # add_depth_switch_driver(scene, "view_settings.view_transform", 2.1, 4.1)
    # '"sRGB"', '"Raw"'
    add_depth_switch_driver(scene, "sequencer_colorspace_settings.name", 11.0, 10.0)
    add_depth_switch_driver(tree.nodes["Denoise"], "mute", False, True)
    # Set options for video rendering (now that the nodes are created)
    setup_video_rendering(place_info)
