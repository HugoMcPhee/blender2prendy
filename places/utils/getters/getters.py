from ....places.place_info import place_info


def get_limited_cam_names():
    return place_info.camera_names[:32]
