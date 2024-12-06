from math import floor
import os

from ..utils.folders import make_folder_if_not_exists
from ..places.place_info import place_info


def save_typescript_files():
    place_folder_path = place_info.place_folder_path
    this_place_name = place_info.this_place_name
    camera_names = place_info.camera_names
    segments_for_cams = place_info.segments_for_cams
    segments_info = place_info.segments_info
    trigger_names = place_info.trigger_names
    segments_order = place_info.segments_order
    wall_names = place_info.wall_names
    places_folder_path = place_info.places_folder_path
    assets_folder_path = place_info.assets_folder_path
    place_names = place_info.place_names
    floor_names = place_info.floor_names
    spot_names = place_info.spot_names
    soundspot_names = place_info.soundspot_names
    # Save the typescript files

    BACKDROP_TYPES = ["color", "depth"]

    # key is {cam_name}_{segment_name} and value is the amount of textures
    texture_amounts_by_cam_and_segment = {}

    # Save index file
    with open(place_folder_path + os.sep + this_place_name + ".ts", "w") as file:
        file.write(f'import modelFile from "./{this_place_name}.glb";\n\n')

        # Import probes
        for cam_name in camera_names:
            # import converted .env files (instead of hdr)
            file.write(
                f'import {cam_name}_probe_image from "./probes/{cam_name}.env";\n'
            )
        file.write("\n")

        # Import backdrop textures

        for cam_name in camera_names:
            # Example: (NOTE: 'start' is the segment name here)
            # import first_cam_start_color_1 from "./first_cam_start_color.ktx2";
            # import first_cam_start_depth_1 from "./first_cam_start_depth.ktx2";

            for segment_name in segments_for_cams[cam_name]:

                # The format is like this: first_cam_start_color_1
                file_name_start = f"{cam_name}_{segment_name}"

                # Loop through the files in backdrops folder that have the file_name_start, and count how many there are
                textures_amount = 0

                make_folder_if_not_exists(
                    os.path.join(place_info.place_folder_path, "backdrops")
                )

                backdrops_directory = os.path.join(place_folder_path, "backdrops")
                for file_name in os.listdir(backdrops_directory):
                    if file_name.startswith(file_name_start + "_color_"):
                        textures_amount += 1
                # Save the amount of textures for each cam and segment
                texture_amounts_by_cam_and_segment[f"{cam_name}_{segment_name}"] = (
                    textures_amount
                )
                print(f"{file_name_start} has {textures_amount} textures")

                for texture_index in range(textures_amount):
                    texture_count = texture_index + 1
                    for backdrop_type in BACKDROP_TYPES:
                        file.write(
                            f'import {file_name_start}_{backdrop_type}_{texture_count} from "./backdrops/{file_name_start}_{backdrop_type}_{texture_count}.ktx2";\n'
                        )
        file.write("\n")

        # backdropsByCamera
        # Example:
        # export const backdropsByCamera = {
        # first_cam: {
        #     start: {
        #     frameRate: 12,
        #     totalFrames: 20,
        #     maxFramesPerRow: 4,
        #     textures: [
        #         { color: first_cam_start_color_1, depth: first_cam_start_depth_1 },
        #         { color: first_cam_start_color_2, depth: first_cam_start_depth_2 },
        #     ],
        #     },
        # },
        # waterfall_cam: {
        #     start: {
        #     frameRate: 12,
        #     totalFrames: 20,
        #     maxFramesPerRow: 4,
        #     textures: [
        #         { color: waterfall_cam_start_color_1, depth: waterfall_cam_start_depth_1 },
        #         { color: waterfall_cam_start_color_2, depth: waterfall_cam_start_depth_2 },
        #     ],
        #     },
        # },
        # };

        MAX_FRAMES_PER_ROW = 4

        file.write("export const backdropsByCamera = {\n")
        for cam_name in camera_names:
            file.write(f'  "{cam_name}": {{\n')
            for segment_name in segments_for_cams[cam_name]:
                segment_info = segments_info[segment_name]
                cam_segment_info = place_info.segment_info_by_cam[cam_name][
                    segment_name
                ]
                cam_segment_framerate = cam_segment_info.framerate
                frame_step = int(
                    round(place_info.scene_framerate / cam_segment_framerate)
                )
                total_frames = floor(segment_info.total_scene_frames / frame_step)

                file.write(f'    "{segment_name}": {{\n')
                file.write(f"      frameRate: {cam_segment_framerate},\n")
                file.write(f"      totalFrames: {total_frames},\n")
                file.write(f"      maxFramesPerRow: {MAX_FRAMES_PER_ROW},\n")
                file.write(f"      textures: [\n")
                texture_amount = texture_amounts_by_cam_and_segment[
                    f"{cam_name}_{segment_name}"
                ]
                for index in range(texture_amount):
                    texture_count = index + 1
                    file.write("        {\n")
                    for backdrop_type in BACKDROP_TYPES:
                        file.write(
                            f"          {backdrop_type}: {cam_name}_{segment_name}_{backdrop_type}_{texture_count},\n"
                        )
                    file.write("        },\n")
                file.write("      ],\n")
                file.write("    },\n")
            file.write("  },\n")
        file.write("};\n")
        file.write("\n")

        # probesByCamera

        file.write("export const probesByCamera = {\n")
        for cam_name in camera_names:
            file.write(f"  {cam_name}: { cam_name}_probe_image,\n")
        file.write("};\n")

        # backdropsByCamera
        # Example:
        # export const backdropsByCamera = {
        #     first_cam: {
        #         start: {
        #         color: first_cam_color_image,
        #         depth: first_cam_depth_image,
        #         frameRate: 12,
        #         totalFrames: 14,
        #         maxFramesPerRow: 8,
        #         },
        #     },
        #     waterfall_cam: {
        #         start: {
        #         color: waterfall_cam_color_image,
        #         depth: waterfall_cam_depth_image,
        #         frameRate: 1,
        #         totalFrames: 1,
        #         maxFramesPerRow: 1,
        #         },
        #     },
        #     };

        cam_counter = 0
        file.write("export const segmentNamesByCamera = {\n")
        for cam_name in camera_names:
            file.write(f"  {cam_name}: [\n")
            for segment_name in segments_for_cams[cam_name]:
                segment_info = segments_info[segment_name]
                file.write(f"    '{segment_name}',\n")

            file.write("  ],\n")
            cam_counter += 1
        file.write("} as const;\n")

        # CameraName type
        file.write(
            "export type CameraName = keyof typeof probesByCamera & keyof typeof segmentNamesByCamera;\n"
        )
        # cameraNames array
        file.write(
            "export const cameraNames = Object.keys(probesByCamera) as Readonly<CameraName[]>;\n\n"
        )

        # videoFiles
        # file.write(
        #     "export const videoFiles = {\n" + "  backdrop: backdropVideoFile,\n" + "}\n"
        # )

        # Get the markers (sections)
        file.write("export const segmentNames = [ \n")

        # add a first marker if there's none at 0
        #  TODO maybe change the 0 to frame_start

        # # loop through all the markers
        for segment_name in segments_order:
            segment = segments_info[segment_name]
            file.write(f"  '{segment.name}', \n")

        file.write(
            "] as const; \n"
            + "export type SegmentName = typeof segmentNames[number];\n\n"
        )

        # wallNames array
        file.write("export const wallNames = [")
        for cam_name in wall_names:
            file.write(f'\n  "{ cam_name}",')
        file.write("\n] as const;\n\n")

        # floorNames array
        file.write("export const floorNames = [")
        for cam_name in floor_names:
            file.write(f'\n  "{ cam_name}",')
        file.write("\n] as const;\n\n")

        # triggerNames array
        file.write("export const triggerNames = [")
        for cam_name in trigger_names:
            file.write(f'\n  "{ cam_name}",')
        file.write("\n] as const;\n\n")

        # spotNames array
        file.write("export const spotNames = [")
        for cam_name in spot_names:
            file.write(f'\n  "{ cam_name}",')
        file.write("\n] as const;\n\n")

        # soundspotNames array
        file.write("export const soundspotNames = [")
        for cam_name in soundspot_names:
            file.write(f'\n  "{ cam_name}",')
        file.write("\n] as const;\n\n")

        file.write(
            "export type WallName = typeof wallNames[number];\n"
            + "export type FloorName = typeof floorNames[number];\n"
            + "export type TriggerName = typeof triggerNames[number];\n"
            + "export type SpotName = typeof spotNames[number];\n\n"
            + "export type SoundspotName = typeof soundspotNames[number];\n\n"
        )

        file.write(
            "export const placeInfo = {\n"
            + "  modelFile,\n"
            + "  backdropsByCamera,\n"
            + "  cameraNames,\n"
            + "  segmentNames,\n"
            + "  segmentNamesByCamera,\n"
            + "  wallNames,\n"
            + "  floorNames,\n"
            + "  triggerNames,\n"
            + "  spotNames,\n"
            + "  soundspotNames,\n"
            + "  probesByCamera,\n"
            + "} as const;\n"
        )

        # places_folder_path

    # Save all places index file
    with open(places_folder_path + os.sep + "places.ts", "w") as file:
        for cam_name in place_names:
            file.write(
                f'import {{ placeInfo as {cam_name}Info }} from "./{cam_name}/{cam_name}";\n'
            )

        file.write("\n")
        file.write("export const placeInfoByName = {\n")

        for cam_name in place_names:
            file.write(f"  {cam_name}: {cam_name}Info,\n")
        file.write("} as const;\n")

        file.write(
            "\n"
            + "export type PlaceName = keyof typeof placeInfoByName;\n\n"
            + "export const placeNames = Object.keys(placeInfoByName) as PlaceName[];\n\n"
            + "type PlaceInfoByName = typeof placeInfoByName;\n\n"
            + "export type CameraNameByPlace = {\n"
            + '  [P_PlaceName in PlaceName]: PlaceInfoByName[P_PlaceName]["cameraNames"][number];\n'
            + "};\n\n"
            + "export type CameraNameFromPlace<\n"
            + "T_Place extends keyof PlaceInfoByName\n"
            + '> = keyof PlaceInfoByName[T_Place]["segmentNamesByCamera"];\n\n'
            + "export type AnyCameraName = CameraNameByPlace[PlaceName];\n\n"
            + "export type SpotNameByPlace = {\n"
            + '  [P_PlaceName in PlaceName]: PlaceInfoByName[P_PlaceName]["spotNames"][number];\n'
            + "};\n"
            + "export type AnySpotName = SpotNameByPlace[PlaceName];\n\n"
            + "export type SoundspotNameByPlace = {\n"
            + '  [P_PlaceName in PlaceName]: PlaceInfoByName[P_PlaceName]["soundspotNames"][number];\n'
            + "};\n"
            + "export type AnySoundspotName = SoundspotNameByPlace[PlaceName];\n\n"
            + "export type SegmentNameByPlace = {\n"
            + '  [P_PlaceName in PlaceName]: PlaceInfoByName[P_PlaceName]["segmentNames"][number];\n'
            + "};\n"
            + "export type SegmentNameByCameraByPlace = {\n"
            + "  [P_Place in keyof PlaceInfoByName]: {\n"
            + '    [P_Cam in keyof PlaceInfoByName[P_Place]["segmentNamesByCamera"]]: keyof PlaceInfoByName[P_Place]["segmentNamesByCamera"][P_Cam];\n'
            + "  };\n"
            + "};\n"
            + "export type SegmentNameFromCameraAndPlace<\n"
            + "  T_Place extends keyof PlaceInfoByName,\n"
            + '  T_Cam extends keyof PlaceInfoByName[T_Place]["segmentNamesByCamera"]\n'
            + '> = keyof PlaceInfoByName[T_Place]["segmentNamesByCamera"][T_Cam];\n'
            + "export type AnySegmentName = SegmentNameByPlace[PlaceName];\n\n"
            + "export type TriggerNameByPlace = {\n"
            + '  [P_PlaceName in PlaceName]: PlaceInfoByName[P_PlaceName]["triggerNames"][number];\n'
            + "};\n"
            + "export type AnyTriggerName = TriggerNameByPlace[PlaceName];\n\n"
            + "export type WallNameByPlace = {\n"
            + '  [P_PlaceName in PlaceName]: PlaceInfoByName[P_PlaceName]["wallNames"][number];\n'
            + "};\n"
            + "export type AnyWallName = WallNameByPlace[PlaceName];\n\n"
        )

        file.write("\n" + "export const allCameraNames = [\n")
        for cam_name in place_names:
            file.write(f"  ...{cam_name}Info.cameraNames,\n")
        file.write("];\n")
