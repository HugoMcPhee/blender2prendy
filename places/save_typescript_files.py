import os


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

    # Save index file
    with open(parent_folder_path + os.sep + "index.ts", "w") as file:

        file.write(f'import modelFile from "./{this_place_name}.glb";\n\n')

        # Import videos
        file.write(f'import colorVideoFile from "./color.mp4";\n')
        file.write(f'import depthVideoFile from "./depth.mp4";\n')

        # Import probes
        for looped_name in camera_names:

            # import converted .env files (instead of hdr)
            file.write(
                f'import {looped_name}_probe_image from "./{looped_name}_probe.env";\n'
            )
        file.write("\n")

        # probesByCamera

        file.write("export const probesByCamera = {\n")
        for cam_name in camera_names:
            file.write(f"  {cam_name}: { cam_name}_probe_image,\n")
        file.write("};\n")

        # segmentTimesByCamera
        total_time_counted = 0
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
        file.write(
            "export const videoFiles = {\n"
            + "  color: colorVideoFile,\n"
            + "  depth: depthVideoFile,\n"
            + "}\n"
        )

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
        for looped_name in wall_names:
            file.write(f'\n  "{ looped_name}",')
        file.write("\n] as const;\n\n")

        # floorNames array
        file.write("export const floorNames = [")
        for looped_name in floor_names:
            file.write(f'\n  "{ looped_name}",')
        file.write("\n] as const;\n\n")

        # triggerNames array
        file.write("export const triggerNames = [")
        for looped_name in trigger_names:
            file.write(f'\n  "{ looped_name}",')
        file.write("\n] as const;\n\n")

        # spotNames array
        file.write("export const spotNames = [")
        for looped_name in spot_names:
            file.write(f'\n  "{ looped_name}",')
        file.write("\n] as const;\n\n")

        # soundspotNames array
        file.write("export const soundspotNames = [")
        for looped_name in soundspot_names:
            file.write(f'\n  "{ looped_name}",')
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
            + "  videoFiles,\n"
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
    with open(grandparent_folder_path + os.sep + "index.ts", "w") as file:

        for looped_name in place_names:
            file.write(
                f'import {{ placeInfo as {looped_name}Info }} from "./{looped_name}";\n'
            )

        file.write("\n")
        file.write("export const placeInfoByName = {\n")

        for looped_name in place_names:
            file.write(f"  {looped_name}: {looped_name}Info,\n")
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
        for looped_name in place_names:
            file.write(f"  ...{looped_name}Info.cameraNames,\n")
        file.write("];\n")
