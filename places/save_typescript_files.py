import os
from ..places.place_info import place_info


def save_typescript_files(
    parent_folder_path,
    this_place_name,
    camera_names,
    segments_for_cams,
    segments_info,
    one_frame_time,
    trigger_names,
    segments_order,
    wall_names,
    grandparent_folder_path,
    place_names,
    floor_names,
    spot_names,
    soundspot_names,
):
    # Save the typescript files

    BACKDROP_TYPES = ["color", "depth"]
    TEXTURES_AMOUNT = (
        2  # TODO make this recorded or calculate it based on framerate and duration
    )

    # Save index file
    with open(parent_folder_path + os.sep + this_place_name + ".ts", "w") as file:
        file.write(f'import modelFile from "./{this_place_name}.glb";\n\n')

        # Import videos
        # file.write(f'import backdropVideoFile from "./backdrops.mp4";\n')

        # Import probes
        for cam_name in camera_names:
            # import converted .env files (instead of hdr)
            file.write(
                f'import {cam_name}_probe_image from "./{cam_name}_probe.env";\n'
            )
        file.write("\n")

        # Import backdrop textures
        for cam_name in camera_names:
            # Example: (NOTE: 'start' is the segment name here)
            # import first_cam_start_color_image from "./first_cam_start_color.ktx2";
            # import first_cam_start_depth_image from "./first_cam_start_depth.ktx2";
            for segment_name in segments_for_cams[cam_name]:

                # The format is like this: first_cam_start_color_1

                file_name_start = f"{cam_name}_{segment_name}"

                for texture_index in range(TEXTURES_AMOUNT):
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
                file.write(f'    "{segment_name}": {{\n')
                file.write(f"      frameRate: {place_info.chosen_framerate},\n")
                file.write(f"      totalFrames: {segment_info.total_frames},\n")
                file.write(f"      maxFramesPerRow: {MAX_FRAMES_PER_ROW},\n")
                file.write(f"      textures: [\n")
                for index in range(TEXTURES_AMOUNT):
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

        # segmentTimesByCamera
        # first_segment_name = segments_for_cams[cam_name]
        # first_segment_info = segments_info[first_segment_name]
        # first_segment_time = first_segment_info.time
        # total_time_counted = first_segment_info.time # start counting total time from 0?
        total_time_counted = 0  # start counting total time from 0, since the video starts at 0 (even if it starts at a differnt frame)

        cam_counter = 0
        file.write("export const segmentTimesByCamera = {\n")
        for cam_name in camera_names:
            file.write(f"  {cam_name}: {{\n")
            for segment_name in segments_for_cams[cam_name]:
                segment_info = segments_info[segment_name]
                file.write(f"    {segment_name}: {round(total_time_counted, 5)},\n")
                total_time_counted += segment_info.duration + one_frame_time

            file.write("  },\n")
            cam_counter += 1
        file.write("} as const;\n")

        # CameraName type
        file.write(
            "export type CameraName = keyof typeof probesByCamera & keyof typeof segmentTimesByCamera;\n"
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
        file.write("export const segmentDurations = {\n")

        # add a first marker if there's none at 0
        #  TODO maybe change the 0 to frame_start

        # # loop through all the markers
        for segment_name in segments_order:
            segment = segments_info[segment_name]
            file.write(f"  {segment.name}: {segment.duration},\n")

        file.write(
            "};\n"
            + "export type SegmentName = keyof typeof segmentDurations;\n"
            + "export const segmentNames = Object.keys(segmentDurations) as SegmentName[];\n\n"
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
            # + "  videoFiles,\n"
            + "  backdropsByCamera,\n"
            + "  cameraNames,\n"
            + "  segmentDurations,\n"
            + "  segmentNames,\n"
            + "  wallNames,\n"
            + "  floorNames,\n"
            + "  triggerNames,\n"
            + "  spotNames,\n"
            + "  soundspotNames,\n"
            + "  probesByCamera,\n"
            + "  segmentTimesByCamera,\n"
            + "} as const;\n"
        )

        # grandparent_folder_path

    # Save all places index file
    with open(grandparent_folder_path + os.sep + "places.ts", "w") as file:
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
            + '> = keyof PlaceInfoByName[T_Place]["segmentTimesByCamera"];\n\n'
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
            + '    [P_Cam in keyof PlaceInfoByName[P_Place]["segmentTimesByCamera"]]: keyof PlaceInfoByName[P_Place]["segmentTimesByCamera"][P_Cam];\n'
            + "  };\n"
            + "};\n"
            + "export type SegmentNameFromCameraAndPlace<\n"
            + "  T_Place extends keyof PlaceInfoByName,\n"
            + '  T_Cam extends keyof PlaceInfoByName[T_Place]["segmentTimesByCamera"]\n'
            + '> = keyof PlaceInfoByName[T_Place]["segmentTimesByCamera"][T_Cam];\n'
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
