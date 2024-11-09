import os

import bpy

from ...places.place_info import PlaceInfo, place_info
from ...utils.folders import make_folder_if_not_exists
from ...utils.getters.get_things import get_scene


def setup_place_info_paths():
    scene = get_scene()

    # get absolute path:

    place_info.path = os.path.normpath(bpy.data.filepath)
    place_info.parts = place_info.path.split(os.sep)

    place_info.parent_folder_path = os.sep.join(place_info.parts[:-1])
    place_info.grandparent_folder_path = os.sep.join(place_info.parts[:-2])
    place_info.renders_folder_path = place_info.parent_folder_path + os.sep + "renders"

    make_folder_if_not_exists(place_info.renders_folder_path)

    scene.render.filepath = place_info.renders_folder_path

    print(f"renders_folder_path: {place_info.renders_folder_path}")
    print(f"filepath: {scene.render.filepath}")

    place_info.full_filename = place_info.parts[-1]
    place_info.full_filename_parts = place_info.full_filename.split(".")
    place_info.this_place_name = place_info.full_filename_parts[-2]


def setup_and_get_places_info():
    # Get place names from folder names (folders with <placeName>.ts files)
    with os.scandir(place_info.grandparent_folder_path) as directory_iterator:
        for directory in directory_iterator:
            if directory.is_dir():
                looped_place_has_main_file = False
                with os.scandir(
                    f"{place_info.grandparent_folder_path}{os.sep}{directory.name}"
                ) as place_folder:
                    looped_place_name = directory.name
                    print(f"looped_place_name: {looped_place_name}")
                    # print(f"place_info: {place_info}")
                    print(f"place_info.place_names: {place_info.place_names}")
                    for place_file in place_folder:
                        if not place_file.name.startswith(".") and place_file.is_file():
                            if place_file.name.startswith(looped_place_name):
                                looped_place_has_main_file = True
                if looped_place_has_main_file:
                    place_info.place_names.append(looped_place_name)
