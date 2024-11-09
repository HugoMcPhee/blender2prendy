from ...utils.folders import rename_object_to_snake_case
from ...utils.getters.get_things import get_collections
from ...places.place_info import PlaceInfo, Segment, make_empty_field, place_info


# Rename and get info for walls
def setup_and_get_walls_info():
    collections = get_collections()

    for object in collections["walls"].objects:
        if object.type == "MESH" or object.type == "CURVE":
            rename_object_to_snake_case(object)
            place_info.wall_names.append(object.name)
