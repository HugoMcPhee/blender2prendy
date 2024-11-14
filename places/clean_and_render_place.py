import os
import shutil
import subprocess
import bpy

from ..utils.folders import get_plugin_folder

from ..utils.getters.get_things import get_collections, get_scene, get_view_layer
from ..places.cam_background import setup_cam_background
from ..utils.collections import (
    include_only_one_collection,
    include_only_two_collections,
)
from ..places.combine_videos import combine_videos
from ..places.convert_exportable_curves import (
    convert_floor_curves,
    delete_meshes,
    revert_curve_names,
)
from ..places.custom_render_video import custom_render_video
from ..places.place_info import place_info
from ..places.places import (
    setup_video_rendering,
    update_items_and_variables,
)
from ..places.hide_meshes import (
    hide_meshes_for_camera,
    reenable_all_meshes,
    reenable_hidden_meshes,
)
from ..places.depth_visible_objects import (
    set_faster_depth_materials,
    toggle_depth_hidden_objects,
    toggle_depth_visible_objects,
    toggle_world_volume,
    unset_faster_depth_materials,
)
from ..places.probes import (
    setup_camera_probes,
    setup_probe_rendering,
    toggle_probe_visible_objects,
)
from ..places.save_typescript_files import save_typescript_files


def get_render_frames_folder_path(camName, segmentName, is_depth_video=False):
    backdrop_type = "color"
    if is_depth_video:
        backdrop_type = "depth"
    return os.path.join(
        place_info.renders_folder_path, camName, segmentName, backdrop_type
    )


def get_render_exists(camName, segmentName, is_depth_video=False):
    path = get_render_frames_folder_path(camName, segmentName, is_depth_video)
    return os.path.isdir(path)


def combine_frames_to_images(camName, segmentName, is_depth_video=False):
    # Run the node script to combine the frames into images
    plugin_path = get_plugin_folder()
    rendered_frames_path = get_render_frames_folder_path(
        camName, segmentName, is_depth_video
    )

    node_script_path = os.path.join(
        plugin_path, "nodeScripts", "combineFrames", "combineFrames.js"
    )
    subprocess.run(
        ["node", node_script_path],
        cwd=rendered_frames_path,
    )
    ktx2_arguments_string = "--bcmp"
    # if is_depth_video:
    #     ktx2_arguments_string = "--uastc --uastc_level 1 --astc"

    # find all files in rendered_frames_path that have the extension .png
    for file in os.listdir(rendered_frames_path):
        if file.endswith(".png"):
            # check if the file starts with "texture"
            if not file.startswith("texture"):
                continue
            ktx2_file_name = file.replace(".png", ".ktx2")
            make_ktx2_texture_command = (
                f"toktx --2d {ktx2_arguments_string} {ktx2_file_name} {file}"
            )
            # convert the png to ktx2
            print(f"running {make_ktx2_texture_command}")
            subprocess.run(
                make_ktx2_texture_command,
                shell=True,
                cwd=rendered_frames_path,
            )

            # move the new ktx2 file to the place folder , in the backdrops directory, and also rename the texture from texture1 to use the camName, segmentName, and backdrop_type with the number that used to be in the texture name

            # if  place_info.parent_folder_path/backdrops doesn't exist, create it
            if not os.path.exists(
                os.path.join(place_info.parent_folder_path, "backdrops")
            ):
                os.makedirs(os.path.join(place_info.parent_folder_path, "backdrops"))

            new_ktx2_file_path = os.path.join(
                place_info.parent_folder_path,
                "backdrops",
                f"{camName}_{segmentName}_{file.replace('texture', '').replace('.png', '')}.ktx2",
            )
            shutil.move(
                os.path.join(rendered_frames_path, ktx2_file_name),
                new_ktx2_file_path,
            )


# -------------------------------------------------
# Original clean and render place
# -------------------------------------------------


def clean_and_render_place(
    should_rerender,
    should_overwrite_render,
    should_convert_probes,
    the_best_lighting_frame,
    should_make_details_gltf,
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
        filepath=place_info.parent_folder_path
        + os.sep
        + place_info.this_place_name
        + ".glb",
        use_selection=True,
        export_hierarchy_full_collections=True,
    )

    # If we want to export the details gltf
    if should_make_details_gltf:
        collection_to_include_a = collections["Exportable"]
        collection_to_include_b = collections["Details"]
        include_only_two_collections(
            view_layer, collection_to_include_a, collection_to_include_b
        )

        for obj in collections["Details"].all_objects:
            # check if it can be selected first:
            # if obj.type == "MESH":
            obj.select_set(True)
        bpy.ops.export_scene.gltf(
            export_format="GLB",
            export_cameras=True,
            export_apply=True,
            export_animations=True,
            filepath=place_info.parent_folder_path
            + os.sep
            + place_info.this_place_name
            + "_details"
            + ".glb",
            use_selection=True,
            export_hierarchy_full_collections=True,
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

        render_output_path_start = (
            f"{place_info.renders_folder_path}{os.sep}{cam_collection.name}"
        )
        probe_output_path = f"{render_output_path_start}_probe.hdr"

        segment_names_for_cam = place_info.segments_for_cams[camera_object.name]

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
                scene.node_tree.nodes["switch_depth"].check = False
                toggle_depth_hidden_objects(True)
                toggle_depth_visible_objects(False)
                toggle_probe_visible_objects(True)
                scene.view_settings.view_transform = "Raw"

                # set the frame for the best lighting
                scene.frame_set(the_best_lighting_frame)
                # render with the probe name
                scene.render.filepath = probe_output_path
                bpy.ops.render.render(animation=False, write_still=True)
                scene.render.resolution_x = original_resolution_x
                scene.render.resolution_y = original_resolution_y
                toggle_depth_hidden_objects(True)
                toggle_probe_visible_objects(False)
                toggle_depth_visible_objects(False)

            # find all the segments enabled for this camera
            for segment_name in segment_names_for_cam:
                print(f"rendering {segment_name}")
                # customRenderVideo(camera_object.name, segment_name, "")
                originalClipStart = scene.camera.data.clip_start
                originalClipEnd = scene.camera.data.clip_end

                # render color videos
                if (
                    not get_render_exists(
                        camera_object.name, segment_name, is_depth_video=False
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
                    scene.node_tree.nodes["switch_depth"].check = False
                    toggle_world_volume(True)
                    toggle_depth_hidden_objects(True)
                    toggle_depth_visible_objects(False)
                    toggle_probe_visible_objects(False)
                    scene.view_settings.view_transform = "Khronos PBR Neutral"
                    scene.sequencer_colorspace_settings.name = (
                        "Khronos PBR Neutral sRGB"
                    )

                    reenable_hidden_meshes()
                    hide_meshes_for_camera(camera_object.name, False)

                    setup_cam_background()
                    # render without the depth name
                    custom_render_video(
                        camName=camera_object.name,
                        segmentName=segment_name,
                        chosen_framerate=place_info.chosen_framerate,
                        renders_folder_path=place_info.renders_folder_path,
                        segments_info=place_info.segments_info,
                    )

                    reenable_hidden_meshes()

                    scene.camera.data.clip_start = originalClipStart
                    scene.camera.data.clip_end = originalClipEnd

                # combine_frames_to_images(
                #     camera_object.name, segment_name, is_depth_video=False
                # )

                # render depth video
                if (
                    not get_render_exists(
                        camera_object.name, segment_name, is_depth_video=True
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
                    scene.node_tree.nodes["switch_depth"].check = True
                    scene.camera = camera_object
                    toggle_world_volume(False)
                    toggle_depth_hidden_objects(False)
                    toggle_depth_visible_objects(True)
                    toggle_probe_visible_objects(False)
                    scene.view_settings.view_transform = "Raw"
                    scene.sequencer_colorspace_settings.name = "sRGB"

                    reenable_hidden_meshes()
                    hide_meshes_for_camera(camera_object.name, True)

                    set_faster_depth_materials()

                    # customRenderVideo(video_output_path_with_depth)
                    custom_render_video(
                        camName=camera_object.name,
                        segmentName=segment_name,
                        chosen_framerate=place_info.chosen_framerate,
                        renders_folder_path=place_info.renders_folder_path,
                        segments_info=place_info.segments_info,
                        isDepth=True,
                    )

                    unset_faster_depth_materials()

                    scene.view_settings.view_transform = "Khronos PBR Neutral"
                    scene.sequencer_colorspace_settings.name = (
                        "Khronos PBR Neutral sRGB"
                    )

                    reenable_hidden_meshes()

                    # scene.camera.data.clip_start = originalClipStart
                    # scene.camera.data.clip_end = originalClipEnd
                combine_frames_to_images(
                    camera_object.name, segment_name, is_depth_video=True
                )

            # setup_probe_rendering
            reenable_all_meshes()

    # create join instructions for videos, and join videos

    # combine all the camera names into a join_color_vids.txt and join_depth_vids.txt
    # combine_videos(
    #     renders_folder_path=place_info.renders_folder_path,
    #     place_folder_path=place_info.parent_folder_path,
    #     camera_names=place_info.camera_names,
    #     segments_for_cams=place_info.segments_for_cams,
    # )

    # Save the typescript files
    save_typescript_files(
        place_info.parent_folder_path,
        place_info.this_place_name,
        place_info.camera_names,
        place_info.segments_for_cams,
        place_info.segments_info,
        place_info.one_frame_time,
        place_info.trigger_names,
        place_info.segments_order,
        place_info.wall_names,
        place_info.grandparent_folder_path,
        place_info.place_names,
        place_info.floor_names,
        place_info.spot_names,
        place_info.soundspot_names,
    )
    print("done :) ✨, converting probes ")

    # subprocess.run(
    #     "npx github:HugoMcPhee/hdr-to-babylon-env 128", cwd=parent_folder_path
    # )
    if should_convert_probes:
        subprocess.call(
            f"cd {place_info.renders_folder_path} && npx github:HugoMcPhee/hdr-to-babylon-env 128",
            shell=True,
        )
        # move all .env files from the renders folder to the parent folder
        for file in os.listdir(place_info.renders_folder_path):
            if file.endswith(".env"):
                shutil.move(
                    os.path.join(place_info.renders_folder_path, file),
                    os.path.join(place_info.parent_folder_path, file),
                )

    print("delete frames")
    print("all done :)")
