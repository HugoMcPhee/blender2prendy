from ...places.place_info import place_info
from ...utils.getters.get_things import get_collections


def setup_and_get_triggers_info():
    collections = get_collections()

    # Collect trigger names
    for object in collections["triggers"].objects:
        if object.type == "MESH":
            place_info.trigger_names.append(object.name)
