import os
import subprocess


def combine_videos(parent_folder_path, camera_names, segments_for_cams):

    # join_color_vids.txt
    with open(parent_folder_path + os.sep + "join_color_vids.txt", "w") as file:

        # Import videos
        file.write(
            "# tells the video joiner the names and order of the color videos \n"
        )
        for looped_cam_name in camera_names:
            for segment_name in segments_for_cams[looped_cam_name]:
                file.write(f"file '{looped_cam_name}_{segment_name}.mp4'\n")
        file.write("\n")

    # join_depth_vids.txt
    with open(parent_folder_path + os.sep + "join_depth_vids.txt", "w") as file:

        # Import videos
        file.write(
            "# tells the video joiner the names and order of the depth videos \n"
        )
        for looped_cam_name in camera_names:
            for segment_name in segments_for_cams[looped_cam_name]:
                file.write(f"file '{looped_cam_name}_{segment_name}_depth.mp4'\n")
        file.write("\n")

    combineVideosCommand_color = f'C:\\ffmpeg -f concat -i "join_color_vids.txt" -c copy -y "{parent_folder_path}{os.sep}color.mp4"  -hide_banner -loglevel error'
    combineVideosCommand_depth = f'C:\\ffmpeg -f concat -i "join_depth_vids.txt" -c copy -y "{parent_folder_path}{os.sep}depth.mp4"  -hide_banner -loglevel error'
    combineColorAndDepthVertically = f'C:\\ffmpeg -i "{parent_folder_path}{os.sep}color.mp4" -i "{parent_folder_path}{os.sep}depth.mp4" -filter_complex vstack=inputs=2 "{parent_folder_path}{os.sep}backdrops.mp4"'

    # subprocess.run(f"cd {parent_folder_path}")
    subprocess.run(combineVideosCommand_color, cwd=parent_folder_path)
    subprocess.run(combineVideosCommand_depth, cwd=parent_folder_path)
    subprocess.run(combineColorAndDepthVertically, cwd=parent_folder_path)

    # TODO Delete the text files here? (are the subprocess done?)
