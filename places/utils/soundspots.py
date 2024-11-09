from ...places.place_info import place_info
from ...utils.getters.get_things import get_collections


def setup_and_get_soundspots_info():
    collections = get_collections()

    # Collect trigger names
    for object in collections["soundspots"].objects:
        if object.type == "EMPTY":
            place_info.soundspot_names.append(object.name)
