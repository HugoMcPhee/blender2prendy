from ...places.place_info import place_info
from ...utils.getters.get_things import get_collections


def setup_and_get_spots_info():
    collections = get_collections()

    # Collect trigger names
    for object in collections["spots"].objects:
        if object.type == "EMPTY":
            place_info.spot_names.append(object.name)
