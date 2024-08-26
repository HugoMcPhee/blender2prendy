import os
import shutil
import subprocess


def combine_videos(
    renders_folder_path, place_folder_path, camera_names, segments_for_cams
):
    # join_color_vids.txt
    with open(renders_folder_path + os.sep + "join_color_vids.txt", "w") as file:
        # Import videos
        file.write(
            "# tells the video joiner the names and order of the color videos \n"
        )
        for looped_cam_name in camera_names:
            for segment_name in segments_for_cams[looped_cam_name]:
                file.write(f"file '{looped_cam_name}_{segment_name}.mp4'\n")
        file.write("\n")

    # join_depth_vids.txt
    with open(renders_folder_path + os.sep + "join_depth_vids.txt", "w") as file:
        # Import videos
        file.write(
            "# tells the video joiner the names and order of the depth videos \n"
        )
        for looped_cam_name in camera_names:
            for segment_name in segments_for_cams[looped_cam_name]:
                file.write(f"file '{looped_cam_name}_{segment_name}_depth.mp4'\n")
        file.write("\n")

    combineVideosCommand_color = [
        "ffmpeg",
        "-f",
        "concat",
        "-i",
        "join_color_vids.txt",
        "-c",
        "copy",
        "-y",
        f"{renders_folder_path}{os.sep}color.mp4",
        "-hide_banner",
        "-loglevel",
        "error",
    ]
    combineVideosCommand_depth = [
        "ffmpeg",
        "-f",
        "concat",
        "-i",
        "join_depth_vids.txt",
        "-c",
        "copy",
        "-y",
        f"{renders_folder_path}{os.sep}depth.mp4",
        "-hide_banner",
        "-loglevel",
        "error",
    ]

    video_quality = "23"
    keyframes = "1"

    combineColorAndDepthVertically = [
        "ffmpeg",
        "-i",
        f"{renders_folder_path}{os.sep}color.mp4",
        "-i",
        f"{renders_folder_path}{os.sep}depth.mp4",
        "-filter_complex",
        "vstack=inputs=2",
        "-vcodec",
        "libx264",
        "-crf",
        video_quality,
        "-g",
        keyframes,
        "-y",
        "-movflags",
        "faststart",
        f"{renders_folder_path}{os.sep}backdrops.mp4",
        "-hide_banner",
        "-loglevel",
        "error",
    ]

    # subprocess.run(f"cd {parent_folder_path}")
    subprocess.run(combineVideosCommand_color, cwd=renders_folder_path)
    subprocess.run(combineVideosCommand_depth, cwd=renders_folder_path)
    subprocess.run(combineColorAndDepthVertically, cwd=renders_folder_path)

    # Delete the text files here? (are the subprocess done?)
    os.remove(renders_folder_path + os.sep + "join_color_vids.txt")
    os.remove(renders_folder_path + os.sep + "join_depth_vids.txt")

    # move the backdrops.mp4 to the place folder, if it exists
    if os.path.exists(renders_folder_path + os.sep + "backdrops.mp4"):
        shutil.move(
            renders_folder_path + os.sep + "backdrops.mp4",
            place_folder_path + os.sep + "backdrops.mp4",
        )
