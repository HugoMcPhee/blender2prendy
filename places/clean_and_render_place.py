import os
import subprocess

import bpy
from .place_info import PlaceInfo

from .places import (
    hide_meshes_for_camera,
    reenable_all_meshes,
    reenable_hidden_meshes,
    setup_cam_background,
    setup_camera_probes,
    setup_probe_rendering,
    setup_video_rendering,
    toggle_depth_hidden_objects,
    toggle_depth_visible_objects,
    toggle_probe_visible_objects,
    toggle_world_volume,
    update_items_and_variables,
)

from ..get_things import get_collections, get_scene, get_view_layer
from .collections import include_only_one_collection
from .combine_videos import combine_videos
from .convert_exportable_curves import (
    convert_floor_curves,
    delete_meshes,
    revert_curve_names,
)
from .custom_render_video import custom_render_video
from .save_typescript_files import save_typescript_files

# custom ui imports


# -------------------------------------------------
# Original clean and render place
# -------------------------------------------------


def clean_and_render_place(
    place_info: PlaceInfo,
    should_rerender,
    should_overwrite_render,
    should_convert_probes,
    the_best_lighting_frame,
):
    scene = get_scene()
    collections = get_collections()
    view_layer = get_view_layer()

    update_items_and_variables(place_info)

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
            f"{place_info.parent_folder_path}{os.sep}{cam_collection.name}"
        )
        probe_output_path = f"{render_output_path_start}_probe.hdr"

        def getVideoPath(camName, segmentName, isDepthVideo=False):
            video_output_path_pre = (
                f"{place_info.parent_folder_path}{os.sep}{camName}_{segmentName}"
            )

            if not isDepthVideo:
                return f"{video_output_path_pre}.mp4"
            else:
                return f"{video_output_path_pre}_depth.mp4"

        segment_names_for_cam = place_info.segments_for_cams[camera_object.name]

        if should_rerender:
            print(f"Set camera {looped_object.name}")
            reenable_all_meshes(place_info)
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

                    setup_video_rendering(place_info)
                    # toggle the depth toggle off
                    scene.node_tree.nodes["switch_depth"].check = False
                    toggle_world_volume(True)
                    toggle_depth_hidden_objects(True)
                    toggle_depth_visible_objects(False)
                    toggle_probe_visible_objects(False)
                    scene.view_settings.view_transform = "Filmic"

                    reenable_hidden_meshes()
                    hide_meshes_for_camera(place_info, camera_object.name, False)

                    setup_cam_background()
                    # render without the depth name
                    custom_render_video(
                        camName=camera_object.name,
                        segmentName=segment_name,
                        chosen_framerate=place_info.chosen_framerate,
                        parent_folder_path=place_info.parent_folder_path,
                        segments_info=place_info.segments_info,
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

                    setup_video_rendering(place_info)
                    scene.camera = camera_object
                    # toggle the depth toggle on
                    scene.node_tree.nodes["switch_depth"].check = True
                    scene.camera = camera_object
                    toggle_world_volume(False)
                    toggle_depth_hidden_objects(False)
                    toggle_depth_visible_objects(True)
                    toggle_probe_visible_objects(False)
                    scene.view_settings.view_transform = "Raw"

                    reenable_hidden_meshes()
                    hide_meshes_for_camera(place_info, camera_object.name, True)

                    # customRenderVideo(video_output_path_with_depth)
                    custom_render_video(
                        camName=camera_object.name,
                        segmentName=segment_name,
                        chosen_framerate=place_info.chosen_framerate,
                        parent_folder_path=place_info.parent_folder_path,
                        segments_info=place_info.segments_info,
                        fileNamePost="_depth",
                    )

                    scene.view_settings.view_transform = "Filmic"

                    reenable_hidden_meshes()

                    # scene.camera.data.clip_start = originalClipStart
                    # scene.camera.data.clip_end = originalClipEnd

            # setup_probe_rendering
            reenable_all_meshes(place_info)

    # create join instructions for videos, and join videos

    # combine all the camera names into a join_color_vids.txt and join_depth_vids.txt
    combine_videos(
        parent_folder_path=place_info.parent_folder_path,
        camera_names=place_info.camera_names,
        segments_for_cams=place_info.segments_for_cams,
    )

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
    convertProbesCommand = f"{place_info.parent_folder_path}"

    # subprocess.run(
    #     "npx github:HugoMcPhee/hdr-to-babylon-env 128", cwd=parent_folder_path
    # )
    if should_convert_probes:
        subprocess.call(
            f"cd {place_info.parent_folder_path} && npx github:HugoMcPhee/hdr-to-babylon-env 128",
            shell=True,
        )
    print("delete frames")
    print("all done :)")
