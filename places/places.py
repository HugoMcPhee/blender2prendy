import bpy

from ..utils.getters.get_things import get_collections, get_scene, get_view_layer
from ..places.cam_background import setup_cam_background
from ..utils.collections import (
    add_collection_to_exportable_collection,
    add_collection_to_scene,
    enable_all_child_collections,
)
from .place_info import place_info
from .probes import setup_camera_probes
from .update_items_and_variables import update_items_and_variables


# ----------------------------------------------------------------------------------------
# Setup everything


def setup_video_rendering():
    update_items_and_variables()

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
    # scene.node_tree.nodes["Denoise"].use_hdr = True

    # for faster performance
    scene.render.use_persistent_data = True


def setup_place(the_render_quality, the_framerate):
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
    update_items_and_variables()

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

    # create value node for camera near clip
    near_clip_value_node = tree.nodes.new(type="CompositorNodeValue")
    near_clip_value_node.name = "near_clip"
    near_clip_value_node.location = 300, -400

    # create value node for camera far clip (below the near clip node)
    far_clip_value_node = tree.nodes.new(type="CompositorNodeValue")
    far_clip_value_node.name = "far_clip"
    far_clip_value_node.location = 300, -500

    # create a clip_range subtract node to subtract the near clip from the far clip (to the right of the clip value nodes)
    clip_range_node = tree.nodes.new(type="CompositorNodeMath")
    clip_range_node.name = "clip_range"
    clip_range_node.operation = "SUBTRACT"
    clip_range_node.location = 480, -450

    # create Subtract depth node
    subtract_depth_node = tree.nodes.new(type="CompositorNodeMath")
    subtract_depth_node.name = "subtract_depth"
    subtract_depth_node.operation = "SUBTRACT"
    subtract_depth_node.location = 300, -200

    # create Divide depth node
    divide_depth_node = tree.nodes.new(type="CompositorNodeMath")
    divide_depth_node.name = "divide_depth"
    divide_depth_node.operation = "DIVIDE"
    divide_depth_node.location = 480, -200

    # create a max Math node, with a max value of 0 to the right of the divide node
    max_node = tree.nodes.new(type="CompositorNodeMath")
    max_node.operation = "MAXIMUM"
    max_node.inputs[1].default_value = 0
    max_node.location = 660, -200

    # create a min Math node, with a min value of 1
    min_node = tree.nodes.new(type="CompositorNodeMath")
    min_node.operation = "MINIMUM"
    min_node.inputs[1].default_value = 1
    min_node.location = 840, -200

    # create Denoise node
    # denoise_node = tree.nodes.new(type="CompositorNodeDenoise")
    # denoise_node.use_hdr = False
    # denoise_node.location = 300, 0

    # create depth toggle switch node
    switch_depth_node = tree.nodes.new(type="CompositorNodeSwitch")
    switch_depth_node.name = "switch_depth"
    switch_depth_node.location = 700, 0

    # create output node
    comp_node = tree.nodes.new("CompositorNodeComposite")
    comp_node.location = 900, 0

    # -------------------------------------------------
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

    # connect the camera near clip values to the subtract node
    links.new(near_clip_value_node.outputs[0], subtract_depth_node.inputs[1])
    # connect the clip_range_node to the divide node
    links.new(clip_range_node.outputs[0], divide_depth_node.inputs[0])
    # subtract the near clip from the far clip in the clip_range_node
    links.new(far_clip_value_node.outputs[0], clip_range_node.inputs[0])
    links.new(near_clip_value_node.outputs[0], clip_range_node.inputs[1])

    # connect the clip range to the divide depth node
    links.new(clip_range_node.outputs[0], divide_depth_node.inputs[1])

    # depth to subtract
    links.new(render_layers_node.outputs[2], subtract_depth_node.inputs[0])
    # subtract to divide
    links.new(subtract_depth_node.outputs[0], divide_depth_node.inputs[0])
    # connect the divide node to the max node
    links.new(divide_depth_node.outputs[0], max_node.inputs[0])
    # connect the max node to the min node
    links.new(max_node.outputs[0], min_node.inputs[0])
    # min to depth toggle switch
    links.new(min_node.outputs[0], switch_depth_node.inputs[1])
    # link render to denoiser
    # links.new(render_layers_node.outputs[3], denoise_node.inputs[0])
    # links.new(render_layers_node.outputs[4], denoise_node.inputs[1])
    # links.new(render_layers_node.outputs[5], denoise_node.inputs[2])

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
        new_driver_variable.targets[0].data_path = (
            'node_tree.nodes["switch_depth"].check'
        )
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

    # Adding cam near driver to cam near value node
    subtract_driver = near_clip_value_node.outputs[0].driver_add("default_value").driver
    subtract_driver.type = "AVERAGE"
    subtract_driver_variable = subtract_driver.variables.new()
    subtract_driver_variable.targets[0].id_type = "SCENE"
    subtract_driver_variable.targets[0].id = scene
    subtract_driver_variable.targets[0].data_path = "camera.data.clip_start"

    # Adding divide driver
    divide_driver = far_clip_value_node.outputs[0].driver_add("default_value").driver
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
    # add_depth_switch_driver(scene, "sequencer_colorspace_settings.name", 11.0, 10.0)

    # NOTE maybe FIXME ? this broke going from blender 3.3 to 4.0
    # add_depth_switch_driver(tree.nodes["Denoise"], "mute", False, True)
    # Set options for video rendering (now that the nodes are created)
    setup_video_rendering()
