import os
import shutil
import subprocess
import time
import bpy

from ...places.clean_and_render_place.combine_frames_to_images import (
    combine_frames_to_images,
)

from ...places.utils.getters.existing_files import (
    get_backdrop_texture_exists,
    get_probe_texture_exists,
)

from ...places.clean_and_render_place.make_place_gltf import make_place_gltf

from ...utils.folders import get_plugin_folder

from ...utils.getters.get_things import get_collections, get_scene, get_view_layer
from ..cam_background import setup_cam_background
from ...utils.collections import (
    include_only_one_collection,
    include_only_two_collections,
)
from ..combine_videos import combine_videos
from ..convert_exportable_curves import (
    convert_floor_curves,
    delete_meshes,
    revert_curve_names,
)
from ..custom_render_video import custom_render_video
from ...places.place_info import place_info
from ...places.places import (
    setup_video_rendering,
    update_items_and_variables,
)
from ..hide_meshes import (
    hide_meshes_for_camera,
    reenable_all_meshes,
    reenable_hidden_meshes,
)
from ..depth_visible_objects import (
    set_faster_depth_materials,
    toggle_depth_hidden_objects,
    toggle_depth_visible_objects,
    toggle_world_volume,
    unset_faster_depth_materials,
)
from ..probes import (
    setup_camera_probes,
    setup_probe_rendering,
    toggle_probe_visible_objects,
)
from ..save_typescript_files import save_typescript_files


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

    temporary_floor_meshes_to_export = make_place_gltf()

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
            filepath=place_info.place_folder_path
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
    time.sleep(0.1)  # wait for the collection to change

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

        cam_name = camera_object.name
        render_output_path_start = f"{place_info.renders_folder_path}{os.sep}{cam_name}"
        probe_output_path = f"{render_output_path_start}_probe.hdr"

        segment_names_for_cam = place_info.segments_for_cams[camera_object.name]

        if should_rerender:
            print(f"Set camera {looped_object.name}")
            reenable_all_meshes()
            # render probe
            if not get_probe_texture_exists(cam_name) or should_overwrite_render:
                print(f"rendering probe {cam_name}")
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
                scene.view_settings.use_hdr_view = True
                # scene.view_settings.view_transform = "Khronos PBR Neutral"
                scene.sequencer_colorspace_settings.name = "Khronos PBR Neutral sRGB"

                scene.cycles.use_denoising = True

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

                color_textures_exist = get_backdrop_texture_exists(
                    camera_object.name, segment_name, is_depth_video=False
                )
                depth_textures_exist = get_backdrop_texture_exists(
                    camera_object.name, segment_name, is_depth_video=True
                )

                # render color videos
                if not color_textures_exist or should_overwrite_render:
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
                    scene.view_settings.use_hdr_view = False
                    scene.cycles.use_denoising = True

                    reenable_hidden_meshes()
                    hide_meshes_for_camera(camera_object.name, False)

                    setup_cam_background()
                    # render without the depth name
                    custom_render_video(
                        cam_name=camera_object.name,
                        segment_name=segment_name,
                        renders_folder_path=place_info.renders_folder_path,
                        segments_info=place_info.segments_info,
                    )

                    reenable_hidden_meshes()

                    scene.camera.data.clip_start = originalClipStart
                    scene.camera.data.clip_end = originalClipEnd

                    combine_frames_to_images(
                        camera_object.name, segment_name, is_depth_video=False
                    )

                # render depth video
                if not depth_textures_exist or should_overwrite_render:

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
                    scene.view_settings.use_hdr_view = False
                    scene.cycles.use_denoising = False

                    reenable_hidden_meshes()
                    hide_meshes_for_camera(camera_object.name, True)

                    set_faster_depth_materials()

                    # customRenderVideo(video_output_path_with_depth)
                    custom_render_video(
                        cam_name=camera_object.name,
                        segment_name=segment_name,
                        renders_folder_path=place_info.renders_folder_path,
                        segments_info=place_info.segments_info,
                        is_depth=True,
                    )

                    unset_faster_depth_materials()

                    scene.view_settings.view_transform = "Khronos PBR Neutral"
                    scene.sequencer_colorspace_settings.name = (
                        "Khronos PBR Neutral sRGB"
                    )
                    scene.view_settings.use_hdr_view = False

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
    #     place_folder_path=place_info.place_folder_path,
    #     camera_names=place_info.camera_names,
    #     segments_for_cams=place_info.segments_for_cams,
    # )

    # Save the typescript files
    save_typescript_files()
    print("done :) ✨, converting probes ")

    # subprocess.run(
    #     "npx github:HugoMcPhee/hdr-to-babylon-env 128", cwd=place_folder_path
    # )
    if should_convert_probes:
        subprocess.call(
            f"cd {place_info.renders_folder_path} && npx github:HugoMcPhee/hdr-to-babylon-env 128",
            shell=True,
        )
        # move all .env files from the renders folder to the parent folder

        # if  place_info.place_folder_path/backdrops doesn't exist, create it
        probe_textures_path = os.path.join(place_info.place_folder_path, "probes")
        if not os.path.exists(probe_textures_path):
            os.makedirs(probe_textures_path)

        for file in os.listdir(place_info.renders_folder_path):
            if file.endswith("_probe.env"):
                new_file_name = file.replace("_probe.env", ".env")
                shutil.move(
                    os.path.join(place_info.renders_folder_path, file),
                    os.path.join(probe_textures_path, new_file_name),
                )

    print("delete frames")
    print("all done :)")
