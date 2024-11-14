import os
import time

import bpy

from ..utils.getters.get_things import get_collections, get_scene, get_view_layer


def custom_render_video(
    camName,
    segmentName,
    renders_folder_path,
    segments_info,
    chosen_framerate,
    isDepth=False,
):
    scene = get_scene()

    # segments_info, chosen_framerate paramerter
    # get_renders_folder_path()

    # set backdrop_type to "color" or "depth" based on isDepth
    backdrop_type = "color"
    if isDepth:
        backdrop_type = "depth"

    nested_dir_path = os.path.join(renders_folder_path, camName, segmentName)
    os.makedirs(nested_dir_path, exist_ok=True)
    # make a directory for color and depth (for the frames)
    frames_dir = os.path.join(nested_dir_path, backdrop_type)
    os.makedirs(frames_dir, exist_ok=True)

    frame_image_folder_path = (
        # f"{renders_folder_path}{os.sep}{camName}_{segmentName}{fileNamePost}"
        f"{frames_dir}{os.sep}"
    )

    segment_info = segments_info[segmentName]
    amount_of_frames_full = scene.frame_end - scene.frame_start
    amount_of_frames_for_segment = segment_info.frameEnd - segment_info.frameStart
    amount_of_frames_saved = int(round(amount_of_frames_for_segment / scene.frame_step))
    nested_dir_path = os.path.join(renders_folder_path, camName, segmentName)

    # video_output_path = (
    #     f"{renders_folder_path}{os.sep}{camName}_{segmentName}{fileNamePost}"
    # )
    # video_output_path = f"{renders_folder_path}{os.sep}{camName}_{segmentName}"
    # video_quality = "23"
    # keyframes = "1"

    # renders each image frame manually so they can have sequential names like image0000 image0001 instead of frame0000, frame0006

    frame_image_path = f"{frame_image_folder_path}{os.sep}frame"

    for stepcounter in range(0, amount_of_frames_saved):
        framenumber = segment_info.frameStart + (stepcounter * scene.frame_step)
        scene.render.filepath = f"{frame_image_path}{str(stepcounter).zfill(4)}.png"
        scene.frame_set(framenumber)
        # make sure to render to 8bit png not 16bit
        scene.render.image_settings.file_format = "PNG"
        # or 'RGBA' if alpha is needed
        scene.render.image_settings.color_mode = "RGB"
        # Ensure this is a string, not an integer
        scene.render.image_settings.color_depth = "8"
        scene.render.image_settings.compression = 15

        bpy.ops.render.render(animation=False, write_still=True)
        time.sleep(0.1)

    # shutil.copyfile(
    #     f"{frame_image_path}{str(amount_of_frames_saved - 1).zfill(4)}.png",
    #     f"{frame_image_path}{str(amount_of_frames_saved ).zfill(4)}.png",
    # )

    # makeVideoCommand = f'ffmpeg -framerate {chosen_framerate} -f image2 -i "{frame_image_path}%04d.png" -vcodec libx264 -crf {video_quality} -g {keyframes} -vf "fps={chosen_framerate},format=yuv420p,scale=1600:900" -y -movflags faststart "{video_output_path}.mp4" -hide_banner -loglevel error'
    # makeVideoCommand = [
    #     "ffmpeg",
    #     "-framerate",
    #     str(chosen_framerate),
    #     "-f",
    #     "image2",
    #     "-i",
    #     f"{frame_image_path}%04d.png",
    #     "-vcodec",
    #     "libx264",
    #     "-crf",
    #     str(video_quality),
    #     "-g",
    #     str(keyframes),
    #     "-vf",
    #     f"fps={chosen_framerate},format=yuv420p,scale=1440:1440",
    #     "-y",
    #     "-movflags",
    #     "faststart",
    #     f"{video_output_path}.mp4",
    #     "-hide_banner",
    #     "-loglevel",
    #     "error",
    # ]
    # -movflags faststart is for starting video fast on web?
    # NOTE -g might be depricated soon?

    # print("launching ffmpeg")
    print("done making frames")
    # print("making video from frames")
    # subprocess.run(makeVideoCommand)
    # print("delete frames")
    # delete frame images
    # shutil.rmtree(frame_image_folder_path)
