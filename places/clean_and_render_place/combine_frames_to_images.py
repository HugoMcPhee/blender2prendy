import os
import shutil
import subprocess

from ...places.utils.getters.existing_files import get_render_frames_folder_path
from ...places.place_info import place_info
from ...utils.folders import get_plugin_folder


def combine_frames_to_images(cam_name, segment_name, is_depth_video=False):
    # Run the node script to combine the frames into images
    plugin_path = get_plugin_folder()
    rendered_frames_path = get_render_frames_folder_path(
        cam_name, segment_name, is_depth_video
    )

    backdrop_type = "color"
    if is_depth_video:
        backdrop_type = "depth"

    node_script_path = os.path.join(
        plugin_path, "nodeScripts", "combineFrames", "combineFrames.js"
    )
    subprocess.run(
        ["node", node_script_path],
        cwd=rendered_frames_path,
    )
    ktx2_arguments_string = "--bcmp"
    if is_depth_video:
        ktx2_arguments_string = "--bcmp --target_type R --qlevel 5"

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

            # move the new ktx2 file to the place folder , in the backdrops directory, and also rename the texture from texture1 to use the cam_name, segment_name, and backdrop_type with the number that used to be in the texture name

            # if  place_info.parent_folder_path/backdrops doesn't exist, create it
            if not os.path.exists(
                os.path.join(place_info.parent_folder_path, "backdrops")
            ):
                os.makedirs(os.path.join(place_info.parent_folder_path, "backdrops"))

            new_ktx2_file_path = os.path.join(
                place_info.parent_folder_path,
                "backdrops",
                f"{cam_name}_{segment_name}_{backdrop_type}_{file.replace('texture', '').replace('.png', '')}.ktx2",
            )
            shutil.move(
                os.path.join(rendered_frames_path, ktx2_file_name),
                new_ktx2_file_path,
            )
