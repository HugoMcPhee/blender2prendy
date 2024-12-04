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
    command = ["node", node_script_path]
    if is_depth_video:
        command.append(" --depth")
    subprocess.run(
        command,
        cwd=rendered_frames_path,
    )

    # for quick testing, use lower fast quality settings
    # ktx2_arguments_string = "--encode etc1s"
    # if is_depth_video:
    #     ktx2_arguments_string = "--encode etc1s --target_type R"

    # ktx2_arguments_string = "--encode etc1s --qlevel 254 --clevel 5"
    # if is_depth_video:
    #     ktx2_arguments_string = "--encode etc1s --qlevel 254 --clevel 5 --target_type R"

    # ktx2_arguments_string = "--encode etc1s --qlevel 128 --clevel 4"
    # if is_depth_video:
    #     ktx2_arguments_string = "--encode etc1s --qlevel 128 --clevel 4 --target_type R"

    # ktx2_arguments_string = "--encode etc1s --qlevel 255 --clevel 5"
    # if is_depth_video:
    #     ktx2_arguments_string = "--encode etc1s --qlevel 255 --clevel 5 --target_type R"
    ktx2_arguments_string = "--encode etc1s --qlevel 5"
    if is_depth_video:
        ktx2_arguments_string = "--encode etc1s --qlevel 5 --target_type R"

    # ktx2_arguments_string = "--encode uastc --uastc_quality 1 --zcmp 19"
    # if is_depth_video:
    #     ktx2_arguments_string = "--encode uastc --uastc_quality 4 --target_type R --assign_oetf linear --zcmp 19"

    existing_backdrop_textures_name_prefix = (
        f"{cam_name}_{segment_name}_{backdrop_type}_"
    )
    # delete any files in the backdrops folder that have the same prefix
    for old_file in os.listdir(os.path.join(place_info.place_folder_path, "backdrops")):
        if old_file.startswith(existing_backdrop_textures_name_prefix):
            os.remove(os.path.join(place_info.place_folder_path, "backdrops", old_file))

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

            # if  place_info.place_folder_path/backdrops doesn't exist, create it
            if not os.path.exists(
                os.path.join(place_info.place_folder_path, "backdrops")
            ):
                os.makedirs(os.path.join(place_info.place_folder_path, "backdrops"))

            new_ktx2_file_path = os.path.join(
                place_info.place_folder_path,
                "backdrops",
                f"{cam_name}_{segment_name}_{backdrop_type}_{file.replace('texture', '').replace('.png', '')}.ktx2",
            )
            shutil.move(
                os.path.join(rendered_frames_path, ktx2_file_name),
                new_ktx2_file_path,
            )
